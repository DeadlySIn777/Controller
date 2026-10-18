"""Compare unmodified 2001 vendor models under Verilog-2005 compilation."""
from pathlib import Path
import json,hashlib,subprocess,re
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/board-finish-20261017/release-review'
OUT=BASE/'vendor-lut-verilog2005-probe-r1';OUT.mkdir(exist_ok=False)
model_dir=Path('C:/Efinity/2026.1/sim_models/verilog')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
cases=[('175_masks','vendor_lut_probe_tb',BASE/'vendor-lut-startup-probe-r1/probe_tb.sv',['efx_lut4.v']),
       ('FF_reset','ff_lut_reset_probe_tb',BASE/'vendor-ff-lut-reset-probe-r1/probe_tb.sv',['efx_ff.v','efx_lut4.v'])]
receipts=[]
for name,top,original,model_names in cases:
 d=OUT/name;d.mkdir();tb=d/'probe_tb.v';s=original.read_text()
 oracle_delta=None
 if name=='FF_reset':
  before='if(!initial_wrong||!reset_still_wrong)$fatal(1,"reported startup mechanism not reproduced");'
  after='if(initial_wrong||reset_still_wrong)$fatal(1,"Verilog2005 stable-zero initialization remains incorrect");'
  assert s.count(before)==1;s=s.replace(before,after)
  s=s.replace('FF_FED_LUT_MODEL_STARTUP_DEFECT_REPRODUCED_WITH_RESET_CONTROL','VERILOG2005_FF_LUT_STABLE_ZERO_RESET_PASS')
  oracle_delta={'before':before,'after':after,'reason':'Require expected correct reset/startup behavior under Verilog2005; stimulus/cells/parameters unchanged.'}
 tb.write_text(s)
 commands=[['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17','iverilog','-g2005','-s',top,'-o',linux(d/'probe.vvp'),*[linux(model_dir/m) for m in model_names],linux(tb)],
           ['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17','vvp',linux(d/'probe.vvp')]]
 executions=[]
 for phase,cmd in zip(['compile','execute'],commands):
  r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
  (d/(phase+'.log')).write_bytes(r.stdout);executions.append({'phase':phase,'exit':r.returncode,'argv':cmd})
  if r.returncode:break
 output=(d/'execute.log').read_text() if (d/'execute.log').exists() else ''
 assert len(executions)==2 and all(e['exit']==0 for e in executions),(name,executions,output)
 if name=='175_masks':assert 'masks=175 failures=0' in output,output
 else:assert 'VERILOG2005_FF_LUT_STABLE_ZERO_RESET_PASS' in output,output
 receipts.append({'case':name,'status':'PASS','original_probe':str(original),'original_probe_SHA256':sha(original),
  'testbench_SHA256':sha(tb),'oracle_delta':oracle_delta,'executions':executions,'output':output})
receipt={'status':'VERILOG2005_UNMODIFIED_VENDOR_MODEL_STARTUP_AND_BINARY_TRUTH_PASS',
 'cases':receipts,'vendor_models_modified':False,
 'model_SHA256':{str(model_dir/n):sha(model_dir/n) for n in ['efx_ff.v','efx_lut4.v']},
 'scope':'Primitive language-mode comparison; no whole mapped-event-engine sequential equivalence claim yet.'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'receipt_SHA256':sha(OUT/'receipt.json'),'outputs':{r['case']:r['output'] for r in receipts}}))
