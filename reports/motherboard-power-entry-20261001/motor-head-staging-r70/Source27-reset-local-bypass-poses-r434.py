import sys,json,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
B=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-population-r400/motherboard-staged-Source27-reset-unrouted-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-reset-local-bypass-poses-r434');assert not O.exists();O.mkdir();b=pcbnew.LoadBoard(str(B));fs={f.GetReference():f for f in b.GetFootprints()};poses={'C11089':([265.225,202.45],180),'C11090':([265.675,206.95],180),'R11082':([266.5,209.2],0),'U11037':([257.5,153],180),'C11091':([253.775,152.05],0),'C11092':([265.575,156.7],180),'R11083':([266.8,159.2],0)};old={r:[*mm(fs[r].GetPosition()),fs[r].GetOrientationDegrees()]for r in poses}
for r,(pt,ang)in poses.items():fs[r].SetPosition(xy(pt));fs[r].SetOrientationDegrees(ang)
cl=[]
for r in poses:
 for f in b.GetFootprints():
  if f.GetReference()!=r and f.GetLayer()==fs[r].GetLayer()and intersects(side_box(fs[r]),side_box(f),0):cl.append([r,f.GetReference()])
assert not cl,cl
out=O/'motherboard-staged-Source27-local-bypass-candidate.kicad_pcb';pcbnew.SaveBoard(str(out),b)
for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),out.with_suffix(e))
for q in B.parent.iterdir():
 if q.is_dir():shutil.copytree(q,O/q.name)
shutil.copyfile(B.parent/'fp-lib-table',O/'fp-lib-table');(O/'new-pose-review.json').write_text(json.dumps(dict(before=str(B),before_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),existing_Source26_poses_Cu_unchanged=True,changed_only_new_Source27_parts=poses,old_new_part_poses=old,courtyard_clear=True,receiving_VDD_CAP_route_and_return_proof_pending=True,manufacturing_ready=False),indent=2));print('NEW_BYPASS_POSES',poses,flush=True)
