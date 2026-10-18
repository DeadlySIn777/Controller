import sys,json,hashlib,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity,pad_identity
B=Path('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r584/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-cap-native-library-rotation-r592');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=pcbnew.LoadBoard(str(B));old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};changes=[];refs={'C11089','C11090','C11091','C11092'}
for f in b.GetFootprints():
 if f.GetReference()not in refs:continue
 for p in f.Pads():
  before=dict(position=mm(p.GetPosition()),orientation=p.GetOrientationDegrees(),shape=str(p.GetShape()),size=mm(p.GetSize()),net=p.GetNetname(),uuid=p.m_Uuid.AsString());p.SetOrientationDegrees(f.GetOrientationDegrees());assert(before['position'],before['shape'],before['size'],before['net'],before['uuid'])==(mm(p.GetPosition()),str(p.GetShape()),mm(p.GetSize()),p.GetNetname(),p.m_Uuid.AsString());assert(abs(before['orientation']-p.GetOrientationDegrees())%180)==0;changes.append(dict(ref=f.GetReference(),pin=p.GetNumber(),before=before,after_orientation=p.GetOrientationDegrees(),half_turn_symmetric_land_geometry_unchanged=True))
dest=O/'motherboard-Source27-native-cap-rotation-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
assert old=={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
run=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(dest)],capture_output=True,text=True);(O/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr);assert run.returncode==0;d=json.loads((O/'drc.json').read_text());(O/'receipt.json').write_text(json.dumps(dict(passed=not d['violations'],base_sha256=sha(B),board_sha256=sha(dest),exact_eight_pad_orientation_only_updates=changes,all_physical_lands_Cu_Source_endpoints_fill_geometry_retained=True,native_violations=d['violations']),indent=2));print('NATIVE_LIBRARY_ROTATION',len(d['violations']),sha(dest),flush=True)
