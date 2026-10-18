from pathlib import Path
import sys,shutil,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import characterize_stepgen12 as h
root=Path.cwd();out=root/'reports/pre-hardware-characterization-20261001/encoder4-mutations-r01';out.mkdir(exist_ok=False)
rtl=root/'gateware/rtl/cnc_encoder.v';bench=root/'reports/pre-hardware-characterization-20261001/tb_encoder4_limits_r01.sv'
frozen={str(p):h.sha(p)for p in(rtl,bench,Path(__file__),Path(h.__file__))}
mutations=[('double-increment',"next_count = count + 1'b1;","next_count = count + 2'd2;",'Ideal sampled encoder failed at or below one edge/corecycle'),('lost-illegal-flag',"invalid_transition <= 1;","invalid_transition <= 0;",'Illegal two-bit transition was not latched'),('lost-index-valid',"index_seen <= 1;","index_seen <= 0;",'Stationary index snapshot mismatch')]
prefix=['wsl.exe','-d','GarciaMechBuilder','--'];results=[]
for name,old,new,fatal in mutations:
 p=out/name;p.mkdir();text=rtl.read_text();assert text.count(old)==1
 (p/rtl.name).write_text(text.replace(old,new));shutil.copyfile(bench,p/bench.name);binary=p/'mutant.vvp'
 c=h.run(p,'compile',prefix+['iverilog','-g2012','-Wall','-s','tb_encoder4_limits','-o',h.linux_path(binary),h.linux_path(p/rtl.name),h.linux_path(p/bench.name)])
 assert not c['returncode'],'A compilation failure is not fault detection'
 r=h.run(p,'simulation',prefix+['vvp',h.linux_path(binary)]);text=Path(r['log']).read_text()
 detected=r['returncode']!=0 and 'FATAL:'in text and fatal in text
 results.append(dict(name=name,passed=detected,expected_runtime_fatal=fatal,original=old,replacement=new,compile=c,simulation=r,mutated_source_sha256=h.sha(p/rtl.name),fixture_sha256=h.sha(p/bench.name),binary_sha256=h.sha(binary)))
assert all(h.sha(Path(p))==v for p,v in frozen.items())
h.write(out/'receipt.json',dict(passed=all(r['passed']for r in results),input_sha256=frozen,results=results,production_source_unchanged=True,physical_qualification=False))
print(json.dumps(dict(passed=all(r['passed']for r in results),actual_compiled_copy_mutations=len(results))))
assert all(r['passed']for r in results)
