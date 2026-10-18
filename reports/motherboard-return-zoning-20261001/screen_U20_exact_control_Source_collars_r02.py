"""Frozen U20 actual control projection screen; no source/Cu edits."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import functional_barrier
from hardware_route_logic_return import mm
B=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-offland-return-r214/motor-health-U20-cell-candidate.kicad_pcb');R=B.parent/'receipt.json';O=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U20-control-screen-r02');S=Path('hardware/motherboard');assert not O.exists();O.mkdir();assert sha(B)=='05da1fad0999896b4cc64ce610e603bcd7a6203e72e38bfce25c853caf686bc1';b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,functions=native(S/'netlist.xml');domains,barriers,_,_=classify(parts,nodes,nc);mp=positioned(b,parts,nodes,nc,functions,domains,barriers);assert not mp['errors'];mp.update(actual_board_sha256=sha(B));write(O/'domain-map.json',mp);guard=ReferenceGuard(b,mp);cu={t.m_Uuid.AsString():t for t in b.GetTracks()};receipt=json.loads(R.read_text());selected=[r for r in receipt['exact_added_copper']if r['role'].startswith('U11020_input_')and'Ground'not in r['role']];selected += [dict(uuid=u,role="retained_actual_U19_Source_escape")for u in ["8b76be20-4f22-4741-b6f6-b7150c195020","cdb2b347-fd52-4b51-8258-07f2f94d7ba7","881c2e60-ce80-40f5-ba25-23299c7aa94e","3dd7e290-39bc-4c38-9bdb-7cd9ff4a697a"]];assert len(selected)==22
rows=[]
for r in selected:
 t=cu[r['uuid']];assert t.GetNetname()!='/LOGIC_GND';shapes=[(pcbnew.In1_Cu,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.2))),(pcbnew.In4_Cu,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.2)))]if t.Type()==pcbnew.PCB_VIA_T else[(pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.5)))]
 for layer,shape in shapes:
  hitrows=[]
  for foreign,project in guard.indices[layer].candidates(mm(t.GetStart()),mm(t.GetEnd()),1.2):
   if foreign=='/LOGIC_GND':continue
   hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(project)
   if hit.OutlineCount():hitrows.append(dict(foreign=foreign,exact_intersection=hit.Format(False)))
  for barrier in mp['barriers']:
   hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(functional_barrier(barrier))
   if hit.OutlineCount():hitrows.append(dict(package_barrier=barrier['reference'],exact_intersection=hit.Format(False)))
  box=shape.BBox();rows.append(dict(uuid=r['uuid'],role=r['role'],net=t.GetNetname(),reference_layer=b.GetLayerName(layer),exact_envelope=shape.Format(False),bounds_mm=[pcbnew.ToMM(v)for v in[box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]],conflicts=hitrows))
write(O/'screen.json',dict(passed=not any(r['conflicts']for r in rows),board=str(B),board_sha256=sha(B),source_receipt_sha256=sha(R),selected_actual_control_conductors=len(selected),Source_ground_rows_kept_ground_and_not_scored_as_signal=True,rows=rows,no_source_Cu_geometry_or_guard_change=True));print(json.dumps(dict(conductors=len(selected),envelopes=len(rows),conflicted=[dict(uuid=r['uuid'],role=r['role'],layer=r['reference_layer'],foreign=[c.get('foreign',c.get('package_barrier'))for c in r['conflicts']])for r in rows if r['conflicts']])),flush=True)
