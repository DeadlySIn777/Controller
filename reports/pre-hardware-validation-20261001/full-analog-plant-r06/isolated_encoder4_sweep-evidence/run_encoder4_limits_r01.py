from pathlib import Path
import argparse,sys,shutil,json,re
sys.path.insert(0,str(Path.cwd()/'tools'))
import characterize_stepgen12 as h
ap=argparse.ArgumentParser(description='Ideal digital four-instance ABZ boundary sweep; no receiver or hardware rating');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
root=Path.cwd();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
rtl=root/'gateware/rtl/cnc_encoder.v';bench=root/'reports/pre-hardware-characterization-20261001/tb_encoder4_limits_r01.sv'
frozen={str(p):h.sha(p)for p in(rtl,bench,Path(__file__),Path(h.__file__))}
for p in(rtl,bench,Path(__file__),Path(h.__file__)):shutil.copyfile(p,out/p.name)
binary=out/'encoder4.vvp';prefix=['wsl.exe','-d','GarciaMechBuilder','--']
c=h.run(out,'compile',prefix+['iverilog','-g2012','-Wall','-s','tb_encoder4_limits','-o',h.linux_path(binary),h.linux_path(rtl),h.linux_path(bench)])
assert not c['returncode'],'Compilation failure is not a boundary result'
r=h.run(out,'simulation',prefix+['vvp',h.linux_path(binary)],timeout=600)
log=Path(r['log']).read_text();rows=[dict((k,int(v))for k,v in re.findall(r'(\w+)=(-?\d+)',s))for s in log.splitlines()if s.startswith('RESULT ')]
passed=r['returncode']==0 and len(rows)==72 and 'PASS encoder4 'in log
assert all(h.sha(Path(p))==v for p,v in frozen.items())
h.write(out/'receipt.json',dict(passed=passed,input_sha256=frozen,compilation=c,simulation=r,binary_sha256=h.sha(binary),rows=rows,scope='Four copies of unchanged encoder component only; ideal digital sampling,1000quadratureedges/channel/case,both signs,four relative phases,indexatrest,illegal two-bit transitions',rates_are_quadrature_edges_per_second_not_AB_cycles=True,assumed_core_hz=50000000,ideal_pass_edge_rate_hz=50000000 if passed else None,first_tested_failing_edge_rate_hz=1e9/19 if passed else None,continuous_exact_failure_boundary_proved=False,receiver_cable_metastability_or_vendor_timing_modeled=False,production_runtime_or_12encoder_expansion_qualified=False,hardware_qualified_edge_rate_hz=None,physical_validation_required=True))
print(json.dumps(dict(passed=passed,cases=len(rows),hardware_rating=None)),flush=True)
assert passed
