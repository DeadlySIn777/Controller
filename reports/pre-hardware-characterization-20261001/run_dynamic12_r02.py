from pathlib import Path
import sys,json,shutil,argparse
sys.path.insert(0,str(Path.cwd()/'tools'))
import characterize_stepgen12 as h
root=Path.cwd();p=root/'reports/pre-hardware-characterization-20261001'
ap=argparse.ArgumentParser(description='Fresh actual twelve-generator dynamic HDL run; no machine interfaces.');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
rtl=root/'gateware/rtl/cnc_stepgen.v';fixture=p/'tb_stepgen12_dynamic_r01.sv'
frozen={str(q):h.sha(q)for q in(rtl,fixture,Path(__file__),Path(h.__file__))}
for q in(rtl,fixture,Path(__file__),Path(h.__file__)):shutil.copyfile(q,out/q.name)
prefix=['wsl.exe','-d','GarciaMechBuilder','--'];runs=[]
for ticks in(100,12,9):
 binary=out/f'dynamic-{ticks}.vvp'
 c=h.run(out,f'compile-{ticks}',prefix+['iverilog','-g2012','-Wall','-s','tb_stepgen12_dynamic',*[f'-Ptb_stepgen12_dynamic.{v}={ticks}'for v in('HIGH','LOW','SETUP','HOLD')],'-o',h.linux_path(binary),h.linux_path(rtl),h.linux_path(fixture)])
 assert not c['returncode']
 r=h.run(out,f'simulation-{ticks}',prefix+['vvp',h.linux_path(binary)],timeout=600)
 text=Path(r['log']).read_text();passed=r['returncode']==0 and len([s for s in text.splitlines()if s.startswith('CHANNEL ')])==12 and 'PASS dynamic12 'in text
 runs.append(dict(ticks=ticks,passed=passed,compilation=c,simulation=r,binary_sha256=h.sha(binary)))
 print(json.dumps(dict(ticks=ticks,passed=passed)),flush=True)
assert all(h.sha(Path(q))==v for q,v in frozen.items())
h.write(out/'receipt.json',dict(passed=all(r['passed']for r in runs),input_sha256=frozen,runs=runs,scope='Twelve unchanged pulse-generator instances only; independent rates, reversals and stop segments with24 updates at assumed1kHz',production_source_unchanged=True,actual_CNC3_HAL_or_electrical_chain_included=False,measured_real_time=False,product_ratings_changed=False,physical_validation_required=True))
assert all(r['passed']for r in runs)
