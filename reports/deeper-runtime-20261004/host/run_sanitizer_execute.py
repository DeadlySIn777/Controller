"""Execute exact current ASan binaries with a namespace-correct proc mount."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from controller_config.service import read_json
from controller_config.setup_service import SetupService
from controller_lab.cnc3_configuration import prepare_configuration,verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unix(path):
    value=path.resolve().as_posix();return '/mnt/'+value[0].lower()+value[2:]
compiled=HERE/'sanitizer-r01';build=read_json(compiled/'receipt.json')
assert build['executions'][0]['stage']=='build' and build['executions'][0]['exit_code']==0
files=runtime_sources();sources=build['source_sha256']
assert set(sources)==set(files) and all(sha(ROOT/p)==h for p,h in sources.items())
out=HERE/'sanitizer-r02'
if out.exists():raise RuntimeError('exclusive sanitizer output required')
out.mkdir();(out/'bin').mkdir()
key=uuid.uuid4().hex;work='/work/deeper-cnc3-sanitizer-'+key
store=HERE/'fixtures-12/setup.json';store_before=sha(store)
manifest=prepare_configuration(SetupService(store),read_json(HERE/'fixtures-12/binding.json'),run_id=str(uuid.uuid4()),source_root=ROOT,source_files=files,encoder_mapping=read_json(HERE/'fixtures-12/encoder-mapping.json'))
verify_configuration(manifest,SetupService(store),source_root=ROOT,expected_source_files=files)
for name in ('driver-spi','manifest-probe'):
    assert sha(compiled/name)==build['artifact_sha256'][name]
    shutil.copyfile(compiled/name,out/'bin'/name)
for p in files:
    assert sha(compiled/'source'/p)==sources[p]
    target=out/'source'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(compiled/'source'/p,target)
(out/'configuration').mkdir()
(out/'configuration/runtime.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(store,out/'configuration/setup.json')
wsl=['wsl','-d','GarciaMechBuilder','-u','root','--'];rootfs='/root/.cache/controller-lab-linuxcnc/rootfs';executions=[];error=None
def run(stage,args,timeout=900):
    start=time.monotonic();log=out/(stage+'.log')
    with log.open('wb') as output:result=subprocess.run(args,stdout=output,stderr=output,timeout=timeout)
    executions.append({'stage':stage,'command':args,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3),'log_sha256':sha(log)})
    print(json.dumps({'stage':stage,'exit_code':result.returncode}),flush=True)
    if result.returncode:raise RuntimeError(stage+' failed')
try:
    run('stage-exact-sanitized-binaries',wsl+['sh',unix(HERE/'sanitizer_stage.sh'),unix(out),work])
    staged=(out/'stage-exact-sanitized-binaries.log').read_text()
    assert all(sha(out/'bin'/name) in staged for name in ('driver-spi','manifest-probe'))
    run('verify-current-copied-manifest',wsl+['chroot',rootfs,'python3',work+'/source/tools/prepare_cnc3_sim2.py','--store',work+'/configuration/setup.json','--verify',work+'/configuration/runtime.json'])
    for case in ('driver','reader'):
        run('ASan-UBSan-'+case,wsl+['timeout','-k','5','300','unshare','--mount','--pid','--ipc','--net','--fork','--kill-child','sh',unix(HERE/'sanitizer_case.sh'),work,case],timeout=330)
except Exception as exc:error=repr(exc)
unchanged=all(sha(ROOT/p)==h for p,h in sources.items())
receipt={'status':'PASS' if not error and unchanged and sha(store)==store_before else 'FAIL','error':error,'source_sha256':sources,'source_inputs_unchanged':unchanged,'settings_preserved':sha(store)==store_before,'settings_sha256':store_before,'configuration_manifest_sha256':manifest['manifest_sha256'],'executions':executions,'rootfs_work':work,'actual_current_sanitized_compile':{'receipt':'sanitizer-r01/receipt.json','sha256':sha(compiled/'receipt.json'),'compile_log_sha256':sha(compiled/'build.log'),'binary_sha256':{name:sha(out/'bin'/name) for name in ('driver-spi','manifest-probe')}},'scope':{'actual_CNC3_C_driver':True,'actual_serial_SPI':True,'compiled_RTL':True,'independent_virtual_ProviderPlant':True,'address_sanitizer':True,'undefined_behavior_sanitizer':True,'leak_detection':True,'namespace_proc_present':True,'NML_or_HAL_scheduler_rerun':False,'installed_modules_modified':False,'hardware_connections':0,'paid_API_calls':0,'physical_qualification':False},'full_requested_milestone_complete':False,'orchestration_sha256':{p.name:sha(p) for p in [Path(__file__),HERE/'sanitizer_case.sh',HERE/'sanitizer_stage.sh']},'artifact_sha256':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':receipt['status'],'error':error}),flush=True)
raise SystemExit(0 if receipt['status']=='PASS' else 1)
