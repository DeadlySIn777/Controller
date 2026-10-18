"""Prove that the actual RTL bench rejects four compiled, isolated defects."""
from pathlib import Path
import hashlib,json,sys,shutil
sys.path.insert(0,str(Path.cwd()/'tools'))
import characterize_stepgen12 as harness

root=Path.cwd();out=root/'reports/pre-hardware-characterization-20261001/stepgen12-mutation-controls-r02'
out.mkdir(parents=True,exist_ok=False)
rtl=root/'gateware/rtl/cnc_stepgen.v';bench=root/'gateware/tests/tb_stepgen12_characterization.sv'
frozen={str(p):harness.sha(p) for p in (rtl,bench,Path(harness.__file__),Path(__file__))}
prefix=['wsl.exe','-d','GarciaMechBuilder','--']
cases=[
 ('unchanged-positive',None,None,None,None),
 ('stuck-counter','rtl',"count <= dir ? count - 1'b1 : count + 1'b1;",'count <= count;','Actual emitted-edge/count mismatch'),
 ('suppressed-timing-fault','rtl','end else timing_fault <= 1;','end else timing_fault <= 0;','Worst reachable phase failed to expose all twelve timing faults'),
 ('shortened-step-high','rtl','step <= 1; high_left <= PULSE_CYCLES;','step <= 1; high_left <= PULSE_CYCLES - 1;','STEP-high violation'),
 ('silent-channel-eleven','bench','.rate(rate)','.rate(g == 11 ? 32\'sd0 : rate)','DDS requested/emitted pulse mismatch'),
]
rows=[]
for name,which,old,new,expected in cases:
 d=out/name;d.mkdir()
 a=rtl.read_text();b=bench.read_text()
 if which:
  original=a if which=='rtl' else b
  assert original.count(old)==1,(name,'Mutation must be exactly one source occurrence')
  changed=original.replace(old,new)
  if which=='rtl':a=changed
  else:b=changed
 # For the suppressed-fault control, execute the exact safe/+1 boundary
 # first so an earlier bulk pulse mismatch cannot mask the fault-mask assertion.
 if name=='suppressed-timing-fault':
  loop='for (k=0;k<12;k=k+1) begin'
  assert b.count(loop)==1
  b=b.replace(loop,'for (k=10;k<12;k=k+1) begin')
 (d/rtl.name).write_text(a);(d/bench.name).write_text(b)
 binary=d/'compiled.vvp'
 compile_run=harness.run(d,'compile',prefix+['iverilog','-g2012','-Wall','-s','tb_stepgen12_characterization','-o',harness.linux_path(binary),harness.linux_path(d/rtl.name),harness.linux_path(d/bench.name)])
 assert compile_run['returncode']==0,(name,'Compilation failure is not fault detection')
 simulation=harness.run(d,'simulation',prefix+['vvp',harness.linux_path(binary),'+cycles=4096'],timeout=600)
 log=Path(simulation['log']).read_text()
 if expected:
  detected=simulation['returncode']!=0 and 'FATAL:' in log and expected in log
 else:
  detected=simulation['returncode']==0 and 'SUMMARY rows=48 ' in log
 rows.append(dict(name=name,passed=detected,expected_fatal=expected,actual_runtime_returncode=simulation['returncode'],mutation_target=which,original=old,replacement=new,compile=compile_run,simulation=simulation,copied_inputs={p.name:harness.sha(p) for p in (d/rtl.name,d/bench.name)},compiled_binary_sha256=harness.sha(binary)))
 print(json.dumps(dict(case=name,passed=detected,expected=expected)),flush=True)
assert all(harness.sha(Path(p))==h for p,h in frozen.items()),'Production/fixture source changed during run'
result=dict(passed=all(r['passed'] for r in rows),scope='Test-sensitivity controls on compiled isolated copies only; no production RTL mutation',input_sha256=frozen,cases=rows,real_machine_interfaces_opened=False,production_RTL_changed=False,physical_validation_required=True)
harness.write(out/'receipt.json',result)
assert result['passed'],'One or more mutations escaped the specified actual-runtime assertion'
