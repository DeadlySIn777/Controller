"""Independent native lands, Source endpoints and actual drill shapes for facing-health final donor."""
import sys,json,math,collections,shutil,argparse,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_populate_motherboard_pcb import pad_template
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lands(f):
 c=pcbnew.FOOTPRINT(f);c.SetPosition(pcbnew.VECTOR2I(0,0))
 if c.GetLayer()==pcbnew.B_Cu:c.Flip(c.GetPosition(),False)
 c.SetOrientationDegrees(0)
 return collections.Counter(pad_template(p)for p in c.Pads())
def group(b,p):return {p.m_Uuid.AsString()}|{q.m_Uuid.AsString()for q in b.GetConnectivity().GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T}
a=argparse.ArgumentParser();a.add_argument('--before',type=Path,required=True);a.add_argument('--board',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--cut',nargs=2);a.add_argument('--cap-cut',nargs=2);a.add_argument('--manifest',type=Path);a=a.parse_args();assert not a.out.exists();a.out.mkdir()
frozen={str(p):sha(p)for p in[a.before,a.board,Path(__file__),Path('hardware/motherboard/design.json')]};b0=pcbnew.LoadBoard(str(a.before));b=pcbnew.LoadBoard(str(a.board));b0.BuildConnectivity();b.BuildConnectivity();fs0={f.GetReference():f for f in b0.GetFootprints()};fs={f.GetReference():f for f in b.GetFootprints()};assert set(fs0)==set(fs);p0={p.m_Uuid.AsString():p for p in b0.GetPads()};ps={p.m_Uuid.AsString():p for p in b.GetPads()};assert set(ps)==set(p0)
allowed={'U11019','U11020','U11026','C11078','C11079','C11081'};moved={}
for r,f in fs0.items():
 g=fs[r];assert (f.GetFPID().GetLibNickname(),f.GetFPID().GetLibItemName(),f.GetValue())==(g.GetFPID().GetLibNickname(),g.GetFPID().GetLibItemName(),g.GetValue()),('PART',r)
 assert lands(f)==lands(g),('LAND',r);assert {(p.m_Uuid.AsString(),p.GetNumber(),p.GetNetname())for p in f.Pads()}=={(p.m_Uuid.AsString(),p.GetNumber(),p.GetNetname())for p in g.Pads()},('PIN',r)
 if (mm(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer())!=(mm(g.GetPosition()),g.GetOrientationDegrees(),g.GetLayer()):
  assert r in allowed,('UNEXPECTED_POSE',r);moved[r]=dict(before=[*mm(f.GetPosition()),f.GetOrientationDegrees(),b0.GetLayerName(f.GetLayer())],after=[*mm(g.GetPosition()),g.GetOrientationDegrees(),b.GetLayerName(g.GetLayer())])
 else:assert all(pad_identity(p)==pad_identity(ps[p.m_Uuid.AsString()])for p in f.Pads()),('UNMOVED_LAND',r)
prior=clusters_preserved(source_clusters(b0),b);pp={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};owners=[];private=[]
for r,c,s in [('U11019','C11078','C11029'),('U11020','C11079','C11029'),('U11025','C11080','C11055'),('U11026','C11081','C11055')]:
 for pin,rr,rp in [('5',c,'1'),('2',c,'2'),('5',s,'1'),('2',s,'2')]:
  assert pp[rr,rp].m_Uuid.AsString()in group(b,pp[r,pin]),(r,pin,rr,rp);owners.append(dict(owner=[r,pin],actual_endpoint=[rr,rp]))
for r in ['U11020','U11026']:
 for pin in ['1','3','4','6']:
  q=pp[r,pin];others=[p for p in b.GetPads()if p.GetNetname()==q.GetNetname()and p.m_Uuid.AsString()!=q.m_Uuid.AsString()];assert len(others)==1,(r,pin,len(others));p=others[0];assert p.m_Uuid.AsString()in group(b,q),(r,pin);private.append(dict(owner=[r,pin],actual_endpoint=[p.GetParentFootprint().GetReference(),p.GetNumber()]))
old={t.m_Uuid.AsString():identity(t)for t in b0.GetTracks()};new={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};changed={u for u in new if old.get(u)!=new[u]};ret=set(old)-set(new);mut={u for u in set(old)&set(new)if old[u]!=new[u]};assert all(old[u][1]==new[u][1]for u in mut),'Native net reassignment';drills=[]
for t in b.GetTracks():
 if t.m_Uuid.AsString()not in changed or not isinstance(t,pcbnew.PCB_VIA):continue
 shape=pcbnew.SHAPE_CIRCLE(t.GetPosition(),t.GetDrillValue()//2+pcbnew.FromMM(.15)+1);hits=[]
 for p in b.GetPads():
  if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
  for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
   if p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(shape,0):hits.append([p.GetParentFootprint().GetReference(),p.GetNumber(),b.GetLayerName(l)])
 assert not hits,('DRILL_REGISTRATION',t.m_Uuid.AsString(),hits);drills.append(dict(uuid=t.m_Uuid.AsString(),position_mm=mm(t.GetPosition()),native_shape_150um_registration=True))
cutrow=None
if a.cut or a.cap_cut:
 if a.cut:
  r,pin=a.cut;q=pp[r,pin];target=next(p for p in b.GetPads()if p.GetNetname()==q.GetNetname()and p.m_Uuid.AsString()!=q.m_Uuid.AsString());ids={t.m_Uuid.AsString()for t in b.GetTracks()if t.GetNetname()==q.GetNetname()};cutkind='actual_private_input'
 else:
  r,pin=a.cap_cut;q=pp[r,pin];assert a.manifest;frozen[str(a.manifest)]=sha(a.manifest);m=json.loads(a.manifest.read_text());row=next(v for v in m['owned_loops']if v['ref']==r);target=pp[row['owner'],'5'if pin=='1'else'2'];ids={t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedTracks(q)if t.GetNetname()==q.GetNetname()};assert ids;cutkind='actual_native_direct_cap_contacts_'+pin
 assert target.m_Uuid.AsString()in group(b,q);tree=parse(without_generated_fills(a.board.read_text()));tree=[v for v in tree if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ids)];out=a.out/'actual-saved-functional-cut.kicad_pcb';out.write_text(dump_board(tree))
 for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(e),out.with_suffix(e))
 cb=pcbnew.LoadBoard(str(out));pcbnew.ZONE_FILLER(cb).Fill(cb.Zones());pcbnew.SaveBoard(str(out),cb);cb=pcbnew.LoadBoard(str(out));cb.BuildConnectivity();cp={p.m_Uuid.AsString():p for p in cb.GetPads()};assert target.m_Uuid.AsString()not in group(cb,cp[q.m_Uuid.AsString()]),('ACTUAL_CUT_NOT_DETECTED',r,pin);cutrow=dict(kind=cutkind,from_endpoint=[r,pin],target_endpoint=[target.GetParentFootprint().GetReference(),target.GetNumber()],removed_UUIDs=sorted(ids),saved_native_cut_sha256=sha(out),fresh_reload_detected_break=True)
assert all(sha(Path(p))==h for p,h in frozen.items());res=dict(passed=True,input_hashes=frozen,board_sha256=sha(a.board),exact_manufacturer_lands_parts_pin_nets_preserved=len(fs),exact_native_pad_UUIDs_preserved=len(ps),allowed_pose_delta=moved,all_prior_Source_clusters=prior,actual_receiving_Source_endpoints=owners,actual_private_endpoints=private,exact_physical_Cu_delta_inventory=dict(new=sorted(set(new)-set(old)),retired=sorted(ret),modified=sorted(mut)),Cu_scope_authorization_is_separate_from_inventory=True,new_modified_native_drill_registration=drills,functional_cut=cutrow,reference_loaded_current_timing_and_remote_producer_proofs_separate=True,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(res,indent=2));print('PASS',len(fs),len(drills),cutrow,flush=True)



