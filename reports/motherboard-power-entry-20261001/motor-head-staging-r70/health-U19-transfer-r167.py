import sys,json,shutil,subprocess,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_current_delivery_native import sha
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb')
O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U19-transfer-r167');O.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};ps={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};co=b.GetConnectivity();seen=set();groups=[]
for p in b.GetPads():
 u=p.m_Uuid.AsString()
 if u in seen:continue
 g={u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T};seen|=g
 if len(g)>1:groups.append((u,g))
uid='e24c8e44-4eff-45d2-b3a8-74e5bcfcd043';ts={t.m_Uuid.AsString():t for t in b.GetTracks()};v=ts[uid];before=mm(v.GetPosition());after=(345.85,178);n=v.GetNetname();assert before==(345.5875,178.0)
delta=[]
for t in b.GetTracks():
 if t.m_Uuid.AsString()==uid:t.SetPosition(xy(after))
 elif not isinstance(t,pcbnew.PCB_VIA)and t.GetNetname()==n:
  if mm(t.GetStart())==before:t.SetStart(xy(after))
  if mm(t.GetEnd())==before:t.SetEnd(xy(after))
 if identity(t)!=old[t.m_Uuid.AsString()]:delta.append(dict(uuid=t.m_Uuid.AsString(),before=old[t.m_Uuid.AsString()],after=identity(t)))
assert len(delta)==3
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();pmap={p.m_Uuid.AsString():p for p in b.GetPads()};co=b.GetConnectivity()
for u,g in groups:assert g<=({u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(pmap[u])if q.Type()==pcbnew.PCB_PAD_T}),('SOURCE',u)
assert ps=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}
D=O/'motor-health-U19-transfer-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True)
d=json.loads((O/'drc.json').read_text());assert not[v for v in d['violations']if v['severity']=='error']
(O/'receipt.json').write_text(json.dumps(dict(before_board=str(B),before_sha256=sha(B),candidate_sha256=sha(D),exact_changed_copper=delta,all_source_clusters_preserved=len(groups),all_pads_poses_netlist_source_unchanged=True,native_types=dict(collections.Counter(v['type']for v in d['violations'])),pending=['Independent strict receiving bypass and IO3 backbone checks']),indent=2))
(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[r['uuid']for r in delta],reviewed_added_zone_UUIDs=[]),indent=2))
print(D,sha(D),len(groups),flush=True)
