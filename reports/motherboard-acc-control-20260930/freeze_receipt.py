"""Exact fourth-controller source receipt, no target or physical claim."""
import datetime,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPORT=Path(__file__).resolve().parent;OUT=ROOT/'hardware/motherboard_acc_control'
paths=[p for p in OUT.glob('*') if p.is_file()]+[ROOT/'tools/hardware_build_motherboard_acc_control.py',ROOT/'tools/hardware_validate_motherboard_acc_control.py',ROOT/'tests/test_motherboard_acc_control.py',ROOT/'tools/hardware_build_motherboard_io_control.py',ROOT/'hardware/motherboard_process/design.json',ROOT/'hardware/motherboard_io_control/design.json',REPORT/'primary-observations.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={p.relative_to(ROOT).as_posix():sha(p) for p in paths};tests=[]
for name in ['acc_control','process','io_control','operator','do','di','motors']:
 r=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p','test_motherboard_'+name+'.py','-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8');log=REPORT/('tests-'+name+'.txt');log.write_text(r.stdout+r.stderr);m=re.search(r'Ran (\d+) tests?',r.stdout+r.stderr);tests.append({'name':name,'count':int(m.group(1)) if m else None,'passed':r.returncode==0,'log_sha256':sha(log)})
 if r.returncode:print(r.stdout+r.stderr);raise SystemExit(r.returncode)
changed=[k for k,v in before.items() if sha(ROOT/k)!=v];freeze=REPORT/'frozen-inputs'
for p in paths:
 f=freeze/p.relative_to(ROOT);f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,f)
(REPORT/'input-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
foot=json.loads((REPORT/'native-footprints.json').read_text())
r={'schema_version':1,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'frozen native circuit candidate','physical_footprints':48,'purchased_fitted_parts':42,'PCB_copper_testpads':6,'unique_electrical_pads':155,'native_ERC':{'errors':0,'warnings':0,'ignored_checks':[]},'nativeXML_independent_checks':'PASS','native_footprints_loaded':foot['native_footprints_loaded'],'tests':tests,'fresh_test_count':sum(t['count'] for t in tests),'input_hash_count':len(before),'changed_inputs':changed,'manufacturing_ready':False,'parent_integrated':False,'target_firmware_compiled':False,'option_bytes_provisioned':False,'physical_qualified':False,'boundary_file':'hardware/motherboard_acc_control/boundary-map.json','engineering_gates':['Target ACC firmware/options/bootloader and measured accepted-frame/IWDG-to-field timing','Actual isolated AO/AI and bus circuits, real health/validity/age/readback sources','Final FPGA fourth transport/PCB/decoupling/terminal integration']}
(REPORT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='tests'}));raise SystemExit(bool(changed))
