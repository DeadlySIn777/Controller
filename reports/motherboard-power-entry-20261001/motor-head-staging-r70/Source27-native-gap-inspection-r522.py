import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
from hardware_route_critical_digital_wip_r03 import source_clusters
A=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb')
B=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r520/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb')
O=Path('reports/motherboard-power-entry-20261001/Source27-native-gap-inspection-r522');assert not O.exists();O.mkdir()
a=pcbnew.LoadBoard(str(A));a.BuildConnectivity();b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();ps={p.m_Uuid.AsString():p for p in b.GetPads()};oldps={p.m_Uuid.AsString():p for p in a.GetPads()};omit={p.m_Uuid.AsString()for p in a.GetPads()if p.GetParentFootprint().GetReference()in ['U11032','U11034']and p.GetNumber()=='6'}
failed=[]
for g in source_clusters(a):
 g=g-omit
 if not g:continue
 q=ps[next(iter(g))];now={q.m_Uuid.AsString()}|{p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(q)if p.Type()==pcbnew.PCB_PAD_T}
 if g<=now:continue
 chunks=[];remain=set(g)
 while remain:
  p=ps[next(iter(remain))];ids={p.m_Uuid.AsString()}|{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T};s=remain&ids;remain-=s
  chunks.append([dict(ref=ps[u].GetParentFootprint().GetReference(),pin=ps[u].GetNumber(),net=ps[u].GetNetname(),position_mm=mm(ps[u].GetPosition()),uuid=u)for u in sorted(s)])
 failed.append(dict(prior_group_size=len(g),actual_chunks=chunks))
print('SOURCE_SPLITS',len(failed),json.dumps(failed,indent=2)[:16000],flush=True)
details=[]
for v in json.loads(B.with_name('drc.json').read_text())['violations']:
 if v['type']in ['lib_footprint_mismatch']:continue
 for i in v['items']:
  t=next((t for t in b.GetTracks()if t.m_Uuid.AsString()==i['uuid']),None)
  if t:details.append(dict(drc_type=v['type'],identity=identity(t)))
(O/'inspection.json').write_text(json.dumps(dict(actual_old_Source_cluster_splits=failed,actual_drc_Cu=details),indent=2));print('GAP_RECEIPT',flush=True)


