import json,sys,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_logic_return import mm,xy
from hardware_route_local_signals import paths
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_map_motherboard_domains import SEEDS
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-return-plane-r51/motherboard-bounded-merged-candidate.kicad_pcb')
rows=json.loads(Path('reports/motherboard-source-return-anchors-20261001/reviewed-stitches-r05/receipt.json').read_text())['actual_owned_return_groups']; names={'C6032','C17013','C14837','U14820'}
cu={t.m_Uuid.AsString():t for t in b.GetTracks()}; pads={p.m_Uuid.AsString():p for p in b.GetPads()};fps={f.GetReference():f for f in b.GetFootprints()}
for r in rows:
 if r['reference']in names and r['via_uuid']in {'956e359a-ed6a-4261-b34e-9449202ed37e','c121b849-bbbb-49ec-8623-73c6b091087b','c88fe8b0-f677-41c9-8cba-56038794faa4','d676ca83-09ea-4811-bd56-557376fe2b7d'}:
  for uid in r['new_copper_UUIDs']:b.Remove(cu[uid])
g=Geometry(b);fills=collect_native_reference_fills(b,set(SEEDS.values())-{'/CHASSIS'},[pcbnew.In1_Cu,pcbnew.In4_Cu])
for r in rows:
 if r['reference']not in names or r['via_uuid']not in {'956e359a-ed6a-4261-b34e-9449202ed37e','c121b849-bbbb-49ec-8623-73c6b091087b','c88fe8b0-f677-41c9-8cba-56038794faa4','d676ca83-09ea-4811-bd56-557376fe2b7d'}:continue
 p=pads[r['source_pad_uuid']];s=mm(p.GetPosition());l=p.GetParentFootprint().GetLayer();net=p.GetNetname(); candidates=[]
 for d in(.7,1,1.5,2,2.5,3,3.5,4,4.5,5,6):
  for k in range(64):
   q=(round(s[0]+d*math.cos(k*math.pi/32),6),round(s[1]+d*math.sin(k*math.pi/32),6))
   if g.via(q,net)and fills[net,pcbnew.In1_Cu].Contains(xy(q)):
    path=next((ps for ps in paths(s,q)if sum(math.dist(a,z)for a,z in zip(ps,ps[1:]))<=d+2 and g.clear(ps,net,l,.2)),None)
    if path:candidates.append((d,q,path))
  if candidates:break
 print(r['reference'],r['pin'],'via',candidates[:3],flush=True)
 if r['reference'].startswith('C'):
  owner=fps[r['owner']]
  for t in owner.Pads():
   if t.GetNumber()and t.GetNetname()==net and t.IsOnLayer(l):
    end=mm(t.GetPosition());pa=next((ps for ps in paths(s,end)if g.clear(ps,net,l,.2)),None)
    print('owner',owner.GetReference(),t.GetNumber(),'span',math.dist(s,end),'path',pa,flush=True)
