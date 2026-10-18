from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stage=HERE/'stage-r02';out=HERE/'diagnostic-replay-candidate-r01'
 if out.exists():raise RuntimeError('fresh candidate required')
 shutil.copytree(stage,out,ignore=shutil.ignore_patterns('__pycache__'))
 prior=out/'inputs/prior';prior.mkdir(parents=True)
 for name in ['cnc_iol1_acquisition_master.v','cnc_iol1_diagnostic_acquisition.v']:
  shutil.copyfile(HERE/'actual-target-acquisition-r04'/name,prior/name)
 motion=ROOT/'reports/cnc3-stateful-implementation-20261001/serial-replay-candidate-r02'
 for p in [*motion.glob('cnc3_*.v'),motion/'inputs/workspace/gateware/v3/rtl/cnc3_spi_transport.v',motion/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']:
  q=out/'inputs/motion'/p.relative_to(motion);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
 shutil.copyfile(ROOT/'firmware/motherboard_iol1_readonly/vendor/Icarus/COPYING',out/'originals/Icarus-COPYING')
 for runner,a,b in [('run_acquisition_equivalence.py',"BASE=HERE.parent/'actual-target-acquisition-r04'","BASE=HERE/'inputs/prior'"),('run_acquisition_family.py',"MOTION=ROOT/'reports/cnc3-stateful-implementation-20261001/serial-replay-candidate-r02'","MOTION=HERE/'inputs/motion'")]:
  p=out/runner;s=p.read_text();assert s.count(a)==1;p.write_text(s.replace(a,b),encoding='utf8',newline='\n')
 p=out/'tb_iol1_acquisition.sv';s=p.read_text();s=s.replace('upper reserved slot bits cannot alias integrated region identity','unsupported response hardware-major nibble cannot alias expected current diagnostic major0');p.write_text(s,encoding='utf8',newline='\n')
 (out/'replay_acquisition.py').write_bytes((HERE/'replay_acquisition.py').read_bytes())
 p=out/'prepare-receipt.json';p.write_text(json.dumps({'prior_stage_hashes':{str(q.relative_to(stage)):sha(q) for q in stage.rglob('*') if q.is_file()},'motion_bundle_manifest_sha256':sha(motion/'bundle-manifest.json'),'scope':'relocatable copied code and actual protocol; response major0 is current diagnostic-profile binding, not reserved/factory revision; no new ABI or real provider completion'},indent=2)+'\n')
 files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
 (out/'bundle-manifest.json').write_text(json.dumps({'files':files,'scope':'actual readonly diagnostics, not ACTIVE/factory-qualified/output authority/CAP3/HAL'},indent=2)+'\n');print(out)
if __name__=='__main__':main()
