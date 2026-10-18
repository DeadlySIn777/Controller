import sys,json,shutil,subprocess,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_current_delivery_native import sha
from hardware_fix_motor_receiving_heads_native import FastGeometry
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U25-return-r173');O.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};groups=[];seen=set()
for p in b.GetPads():
 u=p.m_Uuid.AsString()
 if u in seen:continue
 group={u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T};seen|=group
 if len(group)>1:groups.append((u,group))
g=FastGeometry(b);pt=(333.4375,191);n=ps['C11080','2'].GetNetname();src=mm(ps['C11080','2'].GetPosition());assert all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]);assert g.clear([src,pt],n,pcbnew.B_Cu,.25)
v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v)
t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetStart(xy(src));t.SetEnd(xy(pt));t.SetLayer(pcbnew.B_Cu);t.SetWidth(pcbnew.FromMM(.25));b.Add(t);added=[dict(uuid=x.m_Uuid.AsString(),identity=identity(x))for x in[v,t]]
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();pm={p.m_Uuid.AsString():p for p in b.GetPads()}
for u,group in groups:assert group<=({u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(pm[u])if q.Type()==pcbnew.PCB_PAD_T}),('SOURCE',u)
for r,pn in[('C11080','2'),('U11025','2'),('C11055','2')]:assert ps[r,pn].m_Uuid.AsString()in{q.m_Uuid.AsString()for q in co.GetConnectedItems(v)},('ACTUAL_RETURN',r,pn)
D=O/'motor-health-U25-return-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());assert not[v for v in d['violations']if v['severity']=='error']
assert op=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};now={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert all(now[u]==x for u,x in old.items())
(O/'receipt.json').write_text(json.dumps(dict(before_board=str(B),before_sha256=sha(B),candidate_sha256=sha(D),exact_added_copper=added,prior_source_clusters_preserved=len(groups),actual_owner_cap_source_return_joined=True,all_prior_source_copper_pads_poses_preserved=True,native_types=dict(collections.Counter(v['type']for v in d['violations'])),pending=['Exact field reference collar and strict receiving-return check']),indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[r['uuid']for r in added],reviewed_added_zone_UUIDs=[]),indent=2));print(D,sha(D),flush=True)
