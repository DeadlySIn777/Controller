import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_index_literal_reference_coverage import LiteralReferenceCoverage
from hardware_route_selected_additive import corridor_polygon
from hardware_check_return_corridors import circle
from hardware_route_logic_return import mm,identity
from hardware_zone_motherboard_returns import split_polygons
ROOT=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-clipped-reference-collars-r02');b=pcbnew.LoadBoard(str(ROOT/'motherboard-motor-bank-A-clipped-reference-candidate.kicad_pcb'));r=json.loads((ROOT/'receipt.json').read_text());idx=LiteralReferenceCoverage(b,{'/LOGIC_GND'},[pcbnew.In1_Cu,pcbnew.In4_Cu]);ts={t.m_Uuid.AsString():t for t in b.GetTracks()};vias=[t for t in ts.values()if isinstance(t,pcbnew.PCB_VIA)];rows=[]
for e in r['source_path_reference_failures']:
 if 'slot or hole'not in e['reason']:continue
 t=ts[e['uuid']]
 if isinstance(t,pcbnew.PCB_VIA)or t.GetNetname().startswith('/motherboard_power_entry/FIELD'):continue
 layer=pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu;p=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.4));f=idx.local_fill(p,'/LOGIC_GND',layer);p.BooleanSubtract(f)
 for v in vias:
  if v.GetNetname()==t.GetNetname()and tuple(v.GetPosition())in[tuple(t.GetStart()),tuple(t.GetEnd())]:p.BooleanSubtract(circle(tuple(v.GetPosition()),pcbnew.FromMM(.43)))
 missing=[]
 for v in split_polygons(p):
  z=v.BBox();box=[pcbnew.ToMM(x)for x in[z.GetX(),z.GetY(),z.GetRight(),z.GetBottom()]];centre=((box[0]+box[2])/2,(box[1]+box[3])/2);near=sorted([(math.dist(mm(v.GetPosition()),centre),identity(v))for v in vias],key=lambda x:x[0])[:4];missing.append(dict(box_mm=box,nearest_actual_vias=near))
 rows.append(dict(uuid=e['uuid'],role=e['role'],path_identity=identity(t),missing=missing));print(rows[-1],flush=True)
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/control-hole-inventory-r103.json').write_text(json.dumps(rows,indent=2))
