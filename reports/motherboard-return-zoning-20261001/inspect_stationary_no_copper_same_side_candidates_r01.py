"""Read-only exact Source owner/attachment review for bounded same-side repair."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import mm
B=Path('reports/motherboard-return-zoning-20261001/ROOT93-stationary-bypass-actual-r01/owned-bypass-loop-candidate.kicad_pcb')
M=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json')
R=Path('reports/motherboard-return-zoning-20261001/ROOT93-stationary-bypass-actual-r01/receipt.json')
O=Path('reports/motherboard-return-zoning-20261001/stationary-same-side-pose-feasibility-r01')
O.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
source=json.loads(Path('hardware/motherboard/design.json').read_text())['components']
owners={r['ref']:r for r in json.loads(M.read_text())['capacitors']}
cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
def pad(ref,pin):return next(p for p in fps[ref].Pads()if p.GetNumber()==pin)
rows=[]
for failed in json.loads(R.read_text())['required_remaining']:
 ref=failed['ref'];r=owners[ref];f=fps[ref]
 if ref=='C15035':continue # Connector charge bypass is separately reviewed.
 attached=[]
 for p in f.Pads():
  for item in co.GetConnectedItems(p):
   uid=item.m_Uuid.AsString()
   if uid in cu:
    t=cu[uid]
    if t.HitTest(p.GetPosition())or p.HitTest(t.GetStart())or p.HitTest(t.GetEnd()):attached.append(uid)
 cp=pad(ref,r['cap_power']);cr=pad(ref,r['cap_return'])
 devices=[dict(ref=n['ref'],pin=n['pin'],position_mm=mm(pad(n['ref'],n['pin']).GetPosition()),side=b.GetLayerName(fps[n['ref']].GetLayer()),mpn=source[n['ref']].get('mpn'))for n in r['power_nodes']]
 returns=[dict(ref=n['ref'],pin=n['pin'],position_mm=mm(pad(n['ref'],n['pin']).GetPosition()))for n in r['return_nodes']]
 rows.append(dict(ref=ref,owner=r['owner'],mpn=source[r['owner']].get('mpn'),category=r['category'],old_cap_position_mm=mm(f.GetPosition()),old_side=b.GetLayerName(f.GetLayer()),old_angle=f.GetOrientationDegrees(),actual_power_net=cp.GetNetname(),actual_return=cr.GetNetname(),actual_owner_power_nodes=devices,actual_owner_return_nodes=returns,actual_attached_copper_UUIDs=sorted(set(attached)),zero_attached_copper=not attached,original_routed_search_rejection=failed['reason']))
write(O/'inspection.json',dict(passed=True,inspection_only=True,board=str(B),board_sha256=sha(B),owners_sha256=sha(M),all_exact_stationary_rejected_rows=rows,zero_attached_copper_rows=[r['ref']for r in rows if r['zero_attached_copper']],no_pose_source_or_copper_change=True))
print(json.dumps(dict(rows=len(rows),zero_attached=[r['ref']for r in rows if r['zero_attached_copper']])))
