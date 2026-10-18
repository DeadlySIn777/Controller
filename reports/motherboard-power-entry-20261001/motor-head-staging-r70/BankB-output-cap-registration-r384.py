import sys,json,hashlib,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
B=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-exact-private-retirement-r376/motor-bank-B-native-cleared-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frozen={str(p):sha(p)for p in[B,Path(__file__)]};b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();old=source_clusters(b);ts={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pd={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};f=next(f for f in b.GetFootprints()if f.GetReference()=='C11060');assert mm(f.GetPosition())==(279.25,166.5);before={p.GetNumber():p.GetPosition()for p in f.Pads()};f.SetPosition(xy((279.30,166.5)));changed=[]
for p in f.Pads():
 for t in b.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA)or t.GetNetname()!=p.GetNetname():continue
  ends=[]
  if t.GetStart()==before[p.GetNumber()]:t.SetStart(p.GetPosition());ends.append('start')
  if t.GetEnd()==before[p.GetNumber()]:t.SetEnd(p.GetPosition());ends.append('end')
  if ends:changed.append(dict(uuid=t.m_Uuid.AsString(),exact_endpoints=ends,pin=p.GetNumber()))
assert changed;pcbnew.ZONE_FILLER(b).Fill(b.Zones());dest=O/'motor-bank-B-registration-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),dest.with_suffix(e))
for x in B.parent.iterdir():
 if x.is_dir()and(x.suffix=='.pretty'or x.name=='3dmodels'):shutil.copytree(x,O/x.name)
 elif x.name=='fp-lib-table':(O/x.name).write_text(x.read_text().replace('${KIPRJMOD}',B.parent.resolve().as_posix()))
q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();new={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};ids={v['uuid']for v in changed};assert set(ts)==set(new)and {u for u in ts if ts[u]!=new[u]}==ids;assert all(ts[u][1]==new[u][1]for u in ids);assert all(pad_identity(p)==pd[p.m_Uuid.AsString()]for p in q.GetPads()if p.GetParentFootprint().GetReference()!='C11060');proof=clusters_preserved(old,q)
run=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((O/'drc.json').read_text());assert len(d['violations'])==1 and d['violations'][0]['type']=='via_dangling'and {i['uuid']for i in d['violations'][0]['items']}=={'4b393b84-561e-44d7-a13c-f7dd8ec81ce5'};assert all(sha(Path(p))==h for p,h in frozen.items());(O/'receipt.json').write_text(json.dumps(dict(passed=True,board_sha256=sha(dest),input_hashes=frozen,exact_one_cap_pose_delta=dict(ref='C11060',before_mm=[279.25,166.5],after_mm=[279.30,166.5]),exact_attached_Cu_endpoint_delta=changed,all_old_Source_clusters=proof,native_errors=0,only_retained_baseline_C79_warning=d['violations'],no_source_parts_lands_pin_nets_or_other_Cu_changes=True,strict_reference_and_power_pending=True),indent=2));print('PASS',len(changed),sha(dest),flush=True)
