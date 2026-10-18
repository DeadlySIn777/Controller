import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_map_motherboard_domains import SEEDS
p=Path('reports/motherboard-return-zoning-20261001/source25-r46-opposite-reference-bridges-r06');b=pcbnew.LoadBoard(str(p/'motherboard-own-return-bridges-candidate.kicad_pcb'));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fill=collect_native_reference_fills(b,set(SEEDS.values())-{'/CHASSIS'},[pcbnew.In1_Cu,pcbnew.In4_Cu]);d=json.loads((p/'generation.json').read_text())
for r in d['groups']:
 t=cu[r['new_copper_UUIDs'][0]];l=b.GetLayerID(r['routing_layer']);ps=[p for p in b.GetConnectivity().GetConnectedItems(t)if isinstance(p,pcbnew.PAD)and p.GetNumber()and p.GetNetname()==r['net']]
 print('group',r['net'],r['reference_layer'],r['routing_layer'],'via',r['new_ground_transfer_via_UUID'],'source',len(ps),'layer',t.GetLayer()==l,'connected',b.GetConnectivity().IsConnectedOnLayer(t,l),'fillfirst',fill[r['net'],l].Collide(t.GetEffectiveShape()),'fillany',any(fill[r['net'],l].Collide(cu[u].GetEffectiveShape())for u in r['new_copper_UUIDs']if not isinstance(cu[u],pcbnew.PCB_VIA)),flush=True)
 if r['new_ground_transfer_via_UUID']:
  v=cu[r['new_ground_transfer_via_UUID']]
  print('via',[(n,v.FlashLayer(b.GetLayerID(n)),b.GetConnectivity().IsConnectedOnLayer(v,b.GetLayerID(n)))for n in [r['reference_layer'],r['routing_layer']]],flush=True)
