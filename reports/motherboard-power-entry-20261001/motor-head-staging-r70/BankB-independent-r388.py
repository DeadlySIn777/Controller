import sys,json,hashlib,collections,math,argparse,shutil
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_populate_motherboard_pcb import pad_template
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def land_templates(f):
 c=pcbnew.FOOTPRINT(f);c.SetPosition(pcbnew.VECTOR2I(0,0))
 if c.GetLayer()==pcbnew.B_Cu:c.Flip(c.GetPosition(),False)
 c.SetOrientationDegrees(0)
 return collections.Counter(pad_template(p)for p in c.Pads())
def group(b,p):return {p.m_Uuid.AsString()}|{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T}
a=argparse.ArgumentParser();a.add_argument('--board',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--cut-net');a=a.parse_args();assert not a.out.exists();a.out.mkdir()
B=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r306/motherboard-health-U19-facing-cell-candidate.kicad_pcb');R=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r350/receipt.json');C=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-exact-private-retirement-r376/receipt.json');P=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/receipt.json');frozen={str(p):sha(p)for p in[B,R,C,P,a.board,Path(__file__),Path('hardware/motherboard/design.json')]};r=json.loads(R.read_text());cr=json.loads(C.read_text());patch=json.loads(P.read_text());assert patch['board_sha256']==sha(a.board)
b0=pcbnew.LoadBoard(str(B));b=pcbnew.LoadBoard(str(a.board));b0.BuildConnectivity();b.BuildConnectivity();fs0={f.GetReference():f for f in b0.GetFootprints()};fs={f.GetReference():f for f in b.GetFootprints()};assert set(fs0)==set(fs);poses=r['new_poses'];poses['C11060']['point_mm']=[279.30,166.5];pads0={p.m_Uuid.AsString():p for p in b0.GetPads()};pads={p.m_Uuid.AsString():p for p in b.GetPads()};assert set(pads0)==set(pads)
for ref,f in fs0.items():
 g=fs[ref];assert(f.GetFPID().GetLibNickname(),f.GetFPID().GetLibItemName(),f.GetValue())==(g.GetFPID().GetLibNickname(),g.GetFPID().GetLibItemName(),g.GetValue());assert land_templates(f)==land_templates(g),('LAND',ref);assert {(p.m_Uuid.AsString(),p.GetNumber(),p.GetNetname())for p in f.Pads()}=={(p.m_Uuid.AsString(),p.GetNumber(),p.GetNetname())for p in g.Pads()}
 if ref in poses:
  assert list(mm(g.GetPosition()))==poses[ref]['point_mm'] and g.GetOrientationDegrees()==poses[ref]['angle'],('REVIEWED_POSE',ref)
  assert g.GetLayer()==(pcbnew.B_Cu if ref.startswith('C')or ref in['R11047','R11046']else pcbnew.F_Cu),('REVIEWED_SIDE',ref)
 if ref not in poses:
  assert (mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())==(mm(g.GetPosition()),g.GetOrientationDegrees(),g.GetLayer());assert all(pad_identity(p)==pad_identity(pads[p.m_Uuid.AsString()])for p in f.Pads())
old={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};new={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};removed={x['uuid']for x in r['exact_retired_copper']}|{x['uuid']for x in cr['exact_removed_Cu']if x['uuid']in old};added={x['uuid']for x in r['exact_added_copper']}-{x['uuid']for x in cr['exact_removed_Cu']};assert set(old)-set(new)==removed;assert set(new)-set(old)==added;assert all(new.get(u)==v for u,v in old.items()if u not in removed)
prior=clusters_preserved(source_clusters(b0),b);ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};endpoints=[]
for x in r['actual_endpoint_checks']:
 p=ps[x['from_ref'],x['from_pin']];q=ps[x['to_ref'],x['to_pin']];assert p.GetNetname()==q.GetNetname()and q.m_Uuid.AsString()in group(b,p),(x,p.GetNetname(),q.GetNetname());endpoints.append(x)
thermal=[];drills=[]
for t in b.GetTracks():
 u=t.m_Uuid.AsString()
 if u not in added or not isinstance(t,pcbnew.PCB_VIA):continue
 pt=mm(t.GetPosition());rr=pcbnew.ToMM(t.GetDrillValue())/2;near=None;overlap=[]
 for p in b.GetPads():
  if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
  px,py=mm(p.GetPosition());ang=math.radians(p.GetOrientationDegrees());dx=pt[0]-px;dy=pt[1]-py;x=dx*math.cos(ang)+dy*math.sin(ang);y=-dx*math.sin(ang)+dy*math.cos(ang);w,h=mm(p.GetSize());gap=math.hypot(max(abs(x)-w/2,0),max(abs(y)-h/2,0))-rr
  z=dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),drill_edge_to_conservative_land_mm=gap)
  if near is None or gap<near['drill_edge_to_conservative_land_mm']:near=z
  if gap<0:overlap.append(z)
 if overlap:
  assert all(z['ref']=='U11011'and z['pin']=='11'for z in overlap),(u,overlap);thermal.append(dict(uuid=u,point_mm=pt,overlap=overlap,intentional_EP_power_transition=True,filled_capped_assembly_process_qualification_required=True))
 else:
  assert near['drill_edge_to_conservative_land_mm']>=.15-1e-8,(u,near);drills.append(dict(uuid=u,point_mm=pt,minimum_registration_screen_mm=.15,nearest=near))
cut=None
if a.cut_net:
 n='/motherboard_power_entry/'+a.cut_net;pp=[p for p in b.GetPads()if p.GetNetname()==n];assert len(pp)>=2;before=group(b,pp[0]);assert all(p.m_Uuid.AsString()in before for p in pp);ids={t.m_Uuid.AsString()for t in b.GetTracks()if t.GetNetname()==n};assert ids;tr=parse(without_generated_fills(a.board.read_text()));tr=[x for x in tr if not(isinstance(x,list)and x and x[0]in['segment','via']and value(child(x,'uuid')[1])in ids)];out=a.out/'actual-control-graph-cut.kicad_pcb';out.write_text(dump_board(tr));cb=pcbnew.LoadBoard(str(out));pcbnew.ZONE_FILLER(cb).Fill(cb.Zones());pcbnew.SaveBoard(str(out),cb);cb=pcbnew.LoadBoard(str(out));cb.BuildConnectivity();cp={p.m_Uuid.AsString():p for p in cb.GetPads()};assert all(group(cb,cp[p.m_Uuid.AsString()])=={p.m_Uuid.AsString()}for p in pp);cut=dict(net=n,actual_source_endpoints=[[p.GetParentFootprint().GetReference(),p.GetNumber()]for p in pp],actual_retired_Cu_UUIDs=sorted(ids),fresh_reload_detected_physical_break=True,board_sha256=sha(out))
assert all(sha(Path(p))==h for p,h in frozen.items());receipt=dict(passed=True,input_hashes=frozen,board_sha256=sha(a.board),exact_parts=len(fs),exact_manufacturer_lands_and_pin_nets_preserved=True,exact_source_pose_delta=poses,all_prior_Source_clusters=prior,exact_new_Cu=len(added),exact_retired_Cu=len(removed),exact_added_UUIDs=sorted(added),exact_retired_UUIDs=sorted(removed),actual_source_endpoints=endpoints,actual_low_current_drill_registration_checks=drills,intentional_power_EP_vias_with_unclosed_manufacturing_disposition=thermal,persisted_functional_cut=cut,strict_reference_and_loaded_power_pending=True,Source27_feed_reset_not_adopted=True,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(receipt,indent=2));print('PASS',len(added),len(removed),len(endpoints),a.cut_net,flush=True)
