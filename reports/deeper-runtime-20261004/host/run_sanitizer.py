"""Fresh current-source actual driver/SPI/RTL/provider ASan+UBSan qualification."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from controller_config.service import read_json
from controller_config.setup_service import SetupService
from controller_lab.cnc3_configuration import prepare_configuration,verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unix(path):
    value=path.resolve().as_posix();return '/mnt/'+value[0].lower()+value[2:]
out=HERE/'sanitizer-r01'
if out.exists():raise RuntimeError('exclusive sanitizer output required')
out.mkdir()
key=uuid.uuid4().hex
work='/work/deeper-cnc3-sanitizer-'+key
rootfs='/root/.cache/controller-lab-linuxcnc/rootfs'
files=runtime_sources();before={p:sha(ROOT/p) for p in files}
store=HERE/'fixtures-12/setup.json';store_before=sha(store)
manifest=prepare_configuration(SetupService(store),read_json(HERE/'fixtures-12/binding.json'),run_id=str(uuid.uuid4()),source_root=ROOT,source_files=files,encoder_mapping=read_json(HERE/'fixtures-12/encoder-mapping.json'))
verify_configuration(manifest,SetupService(store),source_root=ROOT,expected_source_files=files)
for p in files:
    target=out/'source'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target)
(out/'configuration').mkdir()
(out/'configuration/runtime.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(store,out/'configuration/setup.json')
wsl=['wsl','-d','GarciaMechBuilder','-u','root','--']
executions=[];error=None
def run(stage,args,timeout=900):
    start=time.monotonic();log=out/(stage+'.log')
    with log.open('wb') as output:result=subprocess.run(args,stdout=output,stderr=output,timeout=timeout)
    executions.append({'stage':stage,'command':args,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3),'log_sha256':sha(log)})
    print(json.dumps({'stage':stage,'exit_code':result.returncode}),flush=True)
    if result.returncode:raise RuntimeError(stage+' failed')
try:
    run('build',wsl+['sh',unix(HERE/'sanitizer_build.sh'),unix(out),work])
    run('verify-copy',wsl+['chroot',rootfs,'python3',work+'/source/tools/prepare_cnc3_sim2.py','--store',work+'/configuration/setup.json','--verify',work+'/configuration/runtime.json'])
    run('ASan-UBSan-driver-SPI',wsl+['timeout','-k','5','300','chroot',rootfs,'env','ASAN_OPTIONS=detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1',work+'/build/driver-spi',work+'/configuration/runtime.json'],timeout=330)
    run('ASan-UBSan-manifest-controls',wsl+['chroot',rootfs,'env','ASAN_OPTIONS=detect_leaks=1:halt_on_error=1','UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1','python3',work+'/source/cnc3_runtime/tests/manifest_controls.py',work+'/build/manifest-probe',work+'/configuration/runtime.json'])
except Exception as exc:error=repr(exc)
unchanged=all(sha(ROOT/p)==h for p,h in before.items())
receipt={'status':'PASS' if not error and unchanged and sha(store)==store_before else 'FAIL','error':error,'source_sha256':before,'source_inputs_unchanged':unchanged,'settings_preserved':sha(store)==store_before,'settings_sha256':store_before,'configuration_manifest_sha256':manifest['manifest_sha256'],'executions':executions,'rootfs_work':work,'scope':{'actual_CNC3_C_driver':True,'actual_serial_SPI':True,'compiled_RTL':True,'independent_virtual_ProviderPlant':True,'address_sanitizer':True,'undefined_behavior_sanitizer':True,'leak_detection':True,'NML_or_HAL_scheduler_rerun':False,'installed_modules_modified':False,'hardware_connections':0,'paid_API_calls':0,'physical_qualification':False},'full_requested_milestone_complete':False,'runner_sha256':sha(Path(__file__)),'build_script_sha256':sha(HERE/'sanitizer_build.sh'),'artifact_sha256':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':receipt['status'],'error':error}),flush=True)
raise SystemExit(0 if receipt['status']=='PASS' else 1)
