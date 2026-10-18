from pathlib import Path
import hashlib,json,shutil,py_compile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=HERE/'stage-r02';out=HERE/'serial-replay-candidate-r01'
 if out.exists():raise RuntimeError('Fresh candidate required')
 out.mkdir()
 shutil.copytree(source/'inputs',out/'inputs');shutil.copyfile(source/'inputs.json',out/'inputs.json')
 originals=[ROOT/'gateware/v3/frozen/protocol_v3.py',ROOT/'gateware/v3/frozen/spec/protocol.json']
 for p in originals:
  q=out/'inputs/workspace'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 diag=out/'inputs/diagnostic-parallel';diag.mkdir()
 for name in ('cnc3_motion_state.v','receipt.json'):
  shutil.copyfile(HERE/'parallel-admission-diagnostic-frozen-r01'/name,diag/name)
 runners=[p for p in source.glob('run_*proof.py')]+[source/'run_spi_admission_binding.py',source/'run_serial_admission_equivalence.py']
 ledger=[]
 for p in sorted(source.glob('cnc3_*.v')):shutil.copyfile(p,out/p.name)
 for p in runners:
  s=p.read_text();changes=[]
  s='import os\n'+s
  old="'wsl','-d','GarciaMechBuilder'";count=s.count(old)
  if count!=1:raise RuntimeError(f'Distro declaration not unique: {p.name}/{count}')
  s=s.replace(old,"'wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder')")
  changes.append('CLI selected WSL distro via bounded environment value')
  for old,new in (("ROOT/'gateware/v3/frozen/protocol_v3.py'","HERE/'inputs/workspace/gateware/v3/frozen/protocol_v3.py'"),("ROOT/'gateware/v3/frozen/spec/protocol.json'","HERE/'inputs/workspace/gateware/v3/frozen/spec/protocol.json'")):
   if old in s:s=s.replace(old,new);changes.append('frozen copied codec/spec instead of mutable shared source')
  old="FROZEN=HERE.parent/'parallel-admission-diagnostic-frozen-r01'"
  if old in s:s=s.replace(old,"FROZEN=HERE/'inputs/diagnostic-parallel'");changes.append('frozen copied diagnostic comparator')
  q=out/p.name;q.write_text(s,encoding='utf8',newline='\n');py_compile.compile(str(q),doraise=True)
  ledger.append({'runner':p.name,'before_sha256':sha(p),'after_sha256':sha(q),'bounded_changes':changes,'RTL_changed':False})
 receipt={'status':'PREPARED_NOT_EXECUTED','source_runners':ledger,'exact_RTL':{p.name:sha(p) for p in out.glob('cnc3_*.v')},'codec_inputs':{str(p):sha(p) for p in originals},'no_shared_inputs_changed':True}
 (out/'prepare-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
 print(json.dumps(receipt))
if __name__=='__main__':main()
