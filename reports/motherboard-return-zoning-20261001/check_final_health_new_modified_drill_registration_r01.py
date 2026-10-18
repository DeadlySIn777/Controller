"""Exact .15 mm actual native SMD/drill registration screen for the literal health delta only."""
from pathlib import Path
import argparse,sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew as p
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
inputs={str(q):sha(q)for q in(a.before,a.board,Path(__file__))};b=p.LoadBoard(str(a.before));c=p.LoadBoard(str(a.board))
old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};vias=[t for t in c.GetTracks()if t.Type()==p.PCB_VIA_T and old.get(t.m_Uuid.AsString())!=identity(t)]
assert vias
pads=[q for q in c.GetPads()if q.GetAttribute()==p.PAD_ATTRIB_SMD and (q.GetLayerSet().Contains(p.F_Paste)or q.GetLayerSet().Contains(p.B_Paste))]
rows=[]
for v in vias:
 radius=v.GetDrillValue()//2;shape=p.SHAPE_CIRCLE(v.GetPosition(),radius+p.FromMM(.15)+1);hits=[]
 for q in pads:
  for layer in(p.F_Cu,p.B_Cu):
   if q.IsOnLayer(layer)and q.GetEffectiveShape(layer).Collide(shape,0):hits.append(dict(reference=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),pad_uuid=q.m_Uuid.AsString(),surface=c.GetLayerName(layer)))
 rows.append(dict(via_uuid=v.m_Uuid.AsString(),net=v.GetNetname(),position_nm=list(v.GetPosition()),drill_nm=v.GetDrillValue(),minimum_gap_mm=.15,one_native_IU_conservative_allowance=True,passed=not hits,actual_native_SMD_shape_contacts=hits))
assert all(sha(Path(q))==h for q,h in inputs.items())
write(a.out,dict(passed=all(r['passed']for r in rows),input_sha256=inputs,board_sha256=sha(a.board),new_or_modified_vias_checked=len(rows),actual_native_effective_rotated_SMD_shapes=True,scoped_only=True,all_inherited_via_registration_or_filled_capped_assembly_qualified=False,rows=rows,manufacturing_ready=False))
print(json.dumps(dict(passed=all(r['passed']for r in rows),checked=len(rows),failures=[r for r in rows if not r['passed']])))
if any(not r['passed']for r in rows):sys.exit(1)
