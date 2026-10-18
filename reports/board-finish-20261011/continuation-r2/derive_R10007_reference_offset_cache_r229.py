"""Compute identical full-source negative offsets once, instead of per return."""
import hashlib,json,runpy
from pathlib import Path
import psutil
H=Path(__file__).resolve().parent;source=H/'screen_R10007_HOST_existing_return_B_F_ports_r227.py';target=H/'screen_R10007_HOST_existing_return_B_F_ports_r229.py'
assert not target.exists();code=source.read_text().replace('screen-r227','screen-r229').replace('R227','R229')
needle=" for ret in returns:\n  centre=";assert code.count(needle)==1
code=code.replace(needle," interior_refs={l:s.buffer(-.075,quad_segs=128)for l,s in refs.items()}\n for ret in returns:\n  centre=")
needle="ann.intersection(s.buffer(-.075,quad_segs=128)).area for l,s in refs.items()";assert code.count(needle)==1
code=code.replace(needle,"ann.intersection(s).area for l,s in interior_refs.items()")
compile(code,str(target),'exec');target.write_text(code)
receipt={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'full_source_offset_input_and_parameters_unchanged':True,'offset_computed_once_instead_of_per_return':True,'R227_partial_progress':'14 actual source returns identified; after first two return lines61 ports; third/further progress may arrive before stop; incomplete finite census no accepted ports','native_processes_untouched':True}
p=psutil.Process(58744);assert abs(p.create_time()-1791834377.098806)<.001
assert p.cmdline()[-1].endswith('derive_R10007_broadphase_port_screen_r227.py')
receipt['stopped_only_owned_host']={'pid':p.pid,'create_time':p.create_time(),'cmdline':p.cmdline(),'cpu_seconds':sum(p.cpu_times()[:2])};p.terminate();p.wait(timeout=10)
(H/'R10007-port-screen-r229-offset-cache-derivation-and-owned-stop.json').write_text(json.dumps(receipt,indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
