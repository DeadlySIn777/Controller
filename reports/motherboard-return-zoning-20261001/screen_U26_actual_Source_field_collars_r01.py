"""Report-only exact physical U26 field-reference projection screen."""
from pathlib import Path
import sys,json,argparse
sys.path[:0]=[str(Path.cwd()/'tools')]
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import functional_barrier
from hardware_route_logic_return import mm,xy
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();B=a.board;O=a.out;assert not O.exists();O.mkdir();R=B.parent/'receipt.json';j=json.loads(R.read_text());assert j['candidate_sha256']==sha(B);b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();S=Path('hardware/motherboard');parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,f=native(S/'netlist.xml');d,bar,_,_=classify(parts,nodes,nc);mp=positioned(b,parts,nodes,nc,f,d,bar);assert not mp['errors'];mp.update(actual_board_sha256=sha(B));write(O/'domain-map.json',mp);g=ReferenceGuard(b,mp);cu={t.m_Uuid.AsString():t for t in b.GetTracks()};selected=[]
for r in j['exact_added_copper']:
 role=r['role'];t=cu[r['uuid']]
 ctrl=role=='U11026_actual_input_1' or (role.startswith('U11026_input_3_')and t.GetNetname()=='/motherboard_power_entry/FIELD_HEALTH_B_N')
 pos=role in('U11026_local_positive_transfer','U11026_own_positive_F','U11026_own_positive_B')
 if not(ctrl or pos):continue
 specs=[(l,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.2)))for l in(pcbnew.In1_Cu,pcbnew.In4_Cu)]if t.Type()==pcbnew.PCB_VIA_T else[(pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()//2+pcbnew.FromMM(.5 if ctrl else .3)))]
 for l,s in specs:selected.append((r['uuid'],role,l,s))
# Actual receiving Ground-to-existing U25 Source proposal, tied to real barrels.
fps={f.GetReference():f for f in b.GetFootprints()};u26=next(p for p in fps['U11026'].Pads()if p.GetNumber()=='2');owner=next(t for r in j['exact_added_copper']if r['role']=='U11026_actual_ground_pin_transfer' for t in[cu[r['uuid']]]);recv=next(t for r in j['exact_added_copper']if r['role']=='U11026_local_Source_return_stitch' for t in[cu[r['uuid']]]);src=(333.4375,191.0);assert u26.GetNetname()=='/motherboard_motors/FIELD_GND'
for t in(owner,recv):
 start=mm(t.GetPosition());points=[start,(start[0],189.0),(333.4375,190.25),src] if start[1]<189 else[start,src]
 for i,(s,e)in enumerate(zip(points,points[1:])):
  for l in(pcbnew.In1_Cu,pcbnew.In4_Cu):selected.append((t.m_Uuid.AsString(),'actual_U26_Ground_to_U25_Source_proposal_'+str(i),l,corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(.5))))
rows=[]
for u,role,l,s in selected:
 bb=s.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];hits=[]
 for foreign,poly in g.indices[l].candidates(tuple(bounds[:2]),tuple(bounds[2:]),1.3):
  if foreign=='/motherboard_motors/FIELD_GND':continue
  hit=pcbnew.SHAPE_POLY_SET(s);hit.BooleanIntersection(poly)
  if hit.OutlineCount():hits.append(dict(foreign=foreign,intersection=hit.Format(False)))
 for br in mp['barriers']:
  hit=pcbnew.SHAPE_POLY_SET(s);hit.BooleanIntersection(functional_barrier(br))
  if hit.OutlineCount():hits.append(dict(barrier=br['reference'],intersection=hit.Format(False)))
 rows.append(dict(uuid=u,role=role,reference_layer=b.GetLayerName(l),exact_envelope=s.Format(False),bounds_mm=bounds,conflicts=hits))
write(O/'screen.json',dict(passed=not any(r['conflicts']for r in rows),board=str(B),board_sha256=sha(B),source_map_sha256=sha(O/'domain-map.json'),rows=rows,no_board_mutation=True));print(json.dumps(dict(rows=len(rows),conflicts=[dict(role=r['role'],uuid=r['uuid'],layer=r['reference_layer'],foreign=[h.get('foreign',h.get('barrier'))for h in r['conflicts']])for r in rows if r['conflicts']])))
