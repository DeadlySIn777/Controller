import sys,json,hashlib,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
from hardware_place_owned_capacitors_native import side_box
B=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-exact-private-retirement-r376/motor-bank-B-native-cleared-candidate.kicad_pcb');S=Path('reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/candidate/motherboard');O=Path('reports/motherboard-power-entry-20261001/Source27-reset-physical-inventory-r386');assert not O.exists();O.mkdir();b=pcbnew.LoadBoard(str(B));fs={f.GetReference():f for f in b.GetFootprints()};m=json.loads((S/'design.json').read_text());r={}
for bank,latch in [('A','U11032'),('B','U11034')]:
 f=fs[latch];pt=mm(f.GetPosition());box=[pt[0]-15,pt[1]-12,pt[0]+15,pt[1]+12];ob=[]
 for ref,z in fs.items():
  bb=side_box(z)
  if bb[0]<box[2]and box[0]<bb[2]and bb[1]<box[3]and box[1]<bb[3]:ob.append(dict(ref=ref,at=mm(z.GetPosition()),angle=z.GetOrientationDegrees(),side=b.GetLayerName(z.GetLayer()),courtyard_mm=bb))
 r[bank]=dict(latch=pt,actual_obstacles=ob)
new={r:c for r,c in m['components'].items()if r not in fs};assert len(new)==10;(O/'inventory.json').write_text(json.dumps(dict(native_board=str(B),native_board_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),staged_source=str(S),source_sha256=hashlib.sha256((S/'design.json').read_bytes()).hexdigest(),existing_cells=r,actual_ten_added_components=new,no_board_or_Source_mutation=True),indent=2));print('INVENTORY',len(new),flush=True)
