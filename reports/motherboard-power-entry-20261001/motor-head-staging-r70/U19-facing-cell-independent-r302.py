"""Independent bounded six-health owner correction on actual fitted Source26 geometry."""
import sys,json,math,collections,shutil,argparse,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills,zone_definition
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_populate_motherboard_pcb import pad_template

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(v):return json.loads(json.dumps(v))
def group(b,p):return {p.m_Uuid.AsString()}|{q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T}
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cut',nargs=2);a=p.parse_args();a.out.mkdir(exist_ok=False)
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb');D=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r300/motherboard-health-U19-facing-cell-candidate.kicad_pcb');R=D.parent/'receipt.json';frozen={str(v):sha(v)for v in[B,D,R,a.board,Path(__file__)]};ledger=json.loads(R.read_text());assert ledger['candidate_sha256']==sha(D)
b0=pcbnew.LoadBoard(str(B));b1=pcbnew.LoadBoard(str(a.board));expected_board=pcbnew.LoadBoard(str(D));b0.BuildConnectivity();b1.BuildConnectivity();f0={f.GetReference():f for f in b0.GetFootprints()};f1={f.GetReference():f for f in b1.GetFootprints()};assert set(f0)==set(f1);allowed={'U11019','C11078'};p0={q.m_Uuid.AsString():q for q in b0.GetPads()};p1={q.m_Uuid.AsString():q for q in b1.GetPads()};assert set(p0)==set(p1)
for r in f0:
 x,y=f0[r],f1[r];assert (x.GetFPID().GetLibNickname(),x.GetFPID().GetLibItemName())==(y.GetFPID().GetLibNickname(),y.GetFPID().GetLibItemName())and x.GetValue()==y.GetValue(),('PART',r);assert collections.Counter(pad_template(q)for q in x.Pads())==collections.Counter(pad_template(q)for q in y.Pads()),('LAND',r);assert {(q.GetNumber(),q.m_Uuid.AsString(),q.GetNetname())for q in x.Pads()}=={(q.GetNumber(),q.m_Uuid.AsString(),q.GetNetname())for q in y.Pads()},('PIN',r)
 if r not in allowed:
  assert (mm(x.GetPosition()),x.GetOrientationDegrees(),x.GetLayer())==(mm(y.GetPosition()),y.GetOrientationDegrees(),y.GetLayer()),('POSE',r)
  for q in x.Pads():assert pad_identity(q)==pad_identity(p1[q.m_Uuid.AsString()]),('PAD',r,q.GetNumber())
expected={q.m_Uuid.AsString():plain(identity(q))for q in expected_board.GetTracks()};actual={q.m_Uuid.AsString():plain(identity(q))for q in b1.GetTracks()};assert expected==actual,'Collar-only consumer may not change physical Cu';old={q.m_Uuid.AsString():plain(identity(q))for q in b0.GetTracks()};added=set(actual)-set(old);retired=set(old)-set(actual);assert added=={q['uuid']for q in ledger['exact_added_copper']}and retired=={q['uuid']for q in ledger['exact_retired_copper']}
for u in set(old)&set(actual):assert old[u]==actual[u],('OLD_CU',u)
seen=set();groups=0
for q in b0.GetPads():
 u=q.m_Uuid.AsString()
 if u in seen:continue
 gg=group(b0,q);seen|=gg
 if len(gg)>1:assert gg<=group(b1,p1[u]),('SOURCE_SPLIT',u);groups+=1
ps={(q.GetParentFootprint().GetReference(),q.GetNumber()):q for q in b1.GetPads()if q.GetNumber()};private=[];owners=[]
for r,c,s in [('U11019','C11078','C11029'),('U11020','C11079','C11029'),('U11026','C11081','C11055')]:
 for pn,target,tp in [('5',c,'1'),('2',c,'2'),('5',s,'1'),('2',s,'2')]:
  assert ps[target,tp].m_Uuid.AsString()in group(b1,ps[r,pn]);owners.append(dict(owner=[r,pn],actual_endpoint=[target,tp],passed=True))
for r in ['U11020','U11026']:
 for pn in ['1','3','4','6']:
  q=ps[r,pn];other=[v for v in b1.GetPads()if v.GetNetname()==q.GetNetname()and v.m_Uuid.AsString()!=q.m_Uuid.AsString()];assert len(other)==1;v=other[0];assert v.m_Uuid.AsString()in group(b1,q);private.append(dict(owner=[r,pn],actual_endpoint=[v.GetParentFootprint().GetReference(),v.GetNumber()],passed=True))
drills=[]
for tr in b1.GetTracks():
 if tr.m_Uuid.AsString()not in added or not isinstance(tr,pcbnew.PCB_VIA):continue
 pt=mm(tr.GetPosition());dr=pcbnew.ToMM(tr.GetDrillValue())/2;closest=None
 for q in b1.GetPads():
  if q.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
  px,py=mm(q.GetPosition());ang=math.radians(q.GetOrientationDegrees());dx=pt[0]-px;dy=pt[1]-py;x=dx*math.cos(ang)+dy*math.sin(ang);y=-dx*math.sin(ang)+dy*math.cos(ang);w,h=mm(q.GetSize());gap=math.hypot(max(abs(x)-w/2,0),max(abs(y)-h/2,0))-dr
  assert gap>=0,('OPEN_DRILL_IN_SMD',tr.m_Uuid.AsString(),q.GetParentFootprint().GetReference(),q.GetNumber(),gap)
  if closest is None or gap<closest['drill_edge_to_conservative_land_mm']:closest=dict(ref=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),drill_edge_to_conservative_land_mm=gap)
 drills.append(dict(uuid=tr.m_Uuid.AsString(),point_mm=pt,closest_land=closest,passed=True))
cutrow=None
if a.cut:
 r,pn=a.cut;q=ps[r,pn];target=next(v for v in b1.GetPads()if v.GetNetname()==q.GetNetname()and v.m_Uuid.AsString()!=q.m_Uuid.AsString());ids={t.m_Uuid.AsString()for t in b1.GetTracks()if t.GetNetname()==q.GetNetname()and t.m_Uuid.AsString()in added};assert ids;tree=parse(without_generated_fills(a.board.read_text()));tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ids)];cut=a.out/'actual-input-graph-cut.kicad_pcb';cut.write_text(dump_board(tree))
 for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(e),cut.with_suffix(e))
 cb=pcbnew.LoadBoard(str(cut));pcbnew.ZONE_FILLER(cb).Fill(cb.Zones());pcbnew.SaveBoard(str(cut),cb);rb=pcbnew.LoadBoard(str(cut));rb.BuildConnectivity();cp={v.m_Uuid.AsString():v for v in rb.GetPads()};assert target.m_Uuid.AsString()not in group(rb,cp[q.m_Uuid.AsString()]),'Physical actual input cut not detected';cutrow=dict(owner=[r,pn],actual_endpoint=[target.GetParentFootprint().GetReference(),target.GetNumber()],retired_actual_Cu_UUIDs=sorted(ids),fresh_native_reload_detected_break=True,board_sha256=sha(cut))
assert all(sha(Path(v))==h for v,h in frozen.items());result=dict(passed=True,input_sha256=frozen,all_parts=len(f1),all_native_pad_identities=len(p1),exact_two_allowed_owner_poses={r:[*mm(f1[r].GetPosition()),f1[r].GetOrientationDegrees(),b1.GetLayerName(f1[r].GetLayer())]for r in sorted(allowed)},all_Manufacturer_lands_parts_pin_nets_preserved=True,all_prior_Source_clusters_preserved=groups,exact_added_Cu=len(added),exact_retired_Cu=len(retired),all_unrelated_Cu_preserved=True,actual_receiving_Source_endpoints=owners,actual_eight_private_control_and_LED_endpoints=private,new_drill_land_checks=drills,persisted_functional_input_cut=cutrow,remote_MC_RAILS_input_distribution_unrouted=True,strict_loaded_reference_power_and_timing_proofs_separate=True,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2));print('PASS',a.cut,groups,len(drills),flush=True)

