"""Minimal coupled locked-native G0_FAULT reroute for a .925 DIC pair.

Every original endpoint/interior contact and locked property is explicit.
Only two original .20 F tracks plus unaccepted NEW DIC target/transport
items are owned. Exact current fills are subtracted conservatively; no
old cache healing, reference waiver, native job or adoption is claimed.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math,copy
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import construct_DIC_three_track_coupled_r164 as B
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def serial(p):return [round(x,6)for x in p]

def main():
 st=time.monotonic();out=H/'DIC-exact-retired-cutter-two-locked-G0-FAULT-policy-route-r554';assert not out.exists();out.mkdir()
 mp=H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/exact-retired-NEW55ab-only-cache-restoration-INTERMEDIATE_NOT_ADOPTED.pkl';assert sha(mp)=='fe1e8dfb04083ffb2084f37da0702280a654011cc090f3bd7b4bc9de93e7af85'
 bf=H/'Q0-R526-full-current-contacts-source-reference-r528/actual-before-and-after-source-banks.pkl';assert sha(bf)=='9b48079a0eb2b1a592dca1fc195ffe70b350e9ff9a110f069178a9f207db0a17'
 cp=H/'DIC-original-target-and-native-same-net-ports-r546/census-components-only-NOT_ACCEPTED_MODEL.pkl';assert sha(cp)=='da79618735b2406b246a4d53135202eed29780cf31475890a46592fa17f4ab64'
 sp=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sp)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 source=sp.read_bytes();inv=K.C.inventory(source);identity=K.A.N.SourceNets(source);g,h0,b,q,c=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);cc=pickle.loads(cp.read_bytes());rrp=H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/receipt.json';assert sha(rrp)=='0fb06aad596ba3efad377852b8ee38ddd26f95530a629434ceb443254e440e4e';rreceipt=json.loads(rrp.read_bytes());rgp=Path(rreceipt['actual_J1_groups_file']);assert sha(rgp)==rreceipt['actual_J1_groups_SHA256'];root=K.root(pickle.loads(rgp.read_bytes()),'J11001','2');baselineRoot=pickle.loads(bf.read_bytes())['after']['/LOGIC_GND'];NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';FAULT='/motherboard_io_control/DI_SENSOR_G0_FAULT';LG='/LOGIC_GND';old={z['uuid']:z for z in c['zones']};dom=h['domains_normalized'];refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}
 native_removed={'2baae30c-8553-42e8-95d4-0fb985c24070','3eb0b0e1-5064-4fc4-9191-b1b9d35840f4'};original=[t for t in h['tracks']if t['uuid']in native_removed];assert len(original)==2
 nativechunks={u:inv[3][u]for u in native_removed};assert all(source.count(ch)==1 and b'(locked yes)'in ch for ch in nativechunks.values());assert all(K.L.norm(t['net'])==FAULT and t['layer']=='F.Cu'and t['w']==.2 for t in original)
 oldgroups=K.physical(c,FAULT,K.hole_context(c))[1];ownedgroup=next(xs for xs in oldgroups if any(r['uuid']in native_removed for r in xs));oldbody=unary_union([r['shape']for r in ownedgroup if r['uuid']in native_removed]);obligations=[]
 for r in ownedgroup:
  if r['uuid']in native_removed or r['layer']!='F.Cu':continue
  hit=oldbody.intersection(r['shape'])
  if not hit.is_empty:obligations.append({'kind':r['kind'],'UUID':r['uuid'],'layer':r['layer'],'raw_net':r['net'],'ref':r.get('ref'),'pin':r.get('pin'),'actual_old_shared_contact':info(hit),'exact_remaining_body':info(r['shape'])})
 put(out/'exact-native-locked-two-track-and-shared-contact-authority.json',{'raw_net':identity.raw(FAULT),'source_SHA256':sha(sp),'exact_deleted_chunks':{u:ch.decode()for u,ch in nativechunks.items()},'native_definitions':original,'all_original_group_keys':[list(k)for k in sorted(K.keys(ownedgroup))],'all_surviving_F_shared_contact_obligations':obligations,'original_endpoints_mm':[[129.25,89.65],[130.75,89.45]],'internal_deleted_only_node_mm':[130.549999,89.65]})
 newtarget=[t for t in h['tracks']if K.L.norm(t['net'])==NET and(t['layer']=='In2.Cu'or t['uuid']=='d6b8c2fd-6f95-59ce-aba3-a2baec2d0177')];assert len(newtarget)==8;new_withdrawn={t['uuid']for t in newtarget};assert new_withdrawn.isdisjoint(inv[3]);h['tracks']=[t for t in h['tracks']if t['uuid']not in native_removed|new_withdrawn]
 assert not any(v['uuid']=='55ab5777-4032-59ab-94d1-d5a4478c7a72'for v in h['vias']);sig={'uuid':'55ab5777-4032-59ab-94d1-d5a4478c7a72','net':identity.raw(NET),'x':130.782294,'y':90.235607,'d':.5,'drill':.2,'flashed':list(K.LAYERS)};oldsig=dict(sig);h['vias'].append(sig);sig['x']=130.822162;sig['y']=90.130643;ret=next(v for v in h['vias']if v['uuid']=='9ef5dbc8-049b-5a46-b319-e13870c3e4c4');assert .90<=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']])<=1;src=next(v for v in h['vias']if v['uuid']=='7a5d26bb-831f-5d1a-9459-60db126ea224')
 moves=json.loads((H/'DIC-three-return-saved-window-correction-r366/selected-minimal-ground-return-relocations.json').read_bytes());moved=[]
 for r in moves:
  v=next(v for v in h['vias']if v['uuid']==r['old_return_UUID']);v['x'],v['y']=r['new_xy_mm'];moved.append(v)
 cuts={ly:[]for ly in refs};cutledger=[]
 for rec in root:
  if rec['kind']!='fill'or rec['layer']not in refs:continue
  ly=rec['layer'];local=float(old[rec['uuid']]['clearance_mm']);svrad=max(.1+.275,.25+max(local,.15)+.025)
  for v,rad in [(sig,svrad)]+[(v,v['drill']/2)for v in moved]:
   if Point(v['x'],v['y']).distance(rec['shape'])>rad:continue
   cut=rec['shape'].intersection(K.Z.bounded_disk(v,rad));cuts[ly].append(cut);cutledger.append({'zone_UUID':rec['uuid'],'layer':ly,'new_changed_via_UUID':v['uuid'],'source_local_clearance_mm':local,'cut_radius_mm':rad,'removed_from_actual_current_source_Cu':info(cut)})
 finalrefs={ly:sh.difference(unary_union(cuts[ly]))for ly,sh in refs.items()};put(out/'exact-current-reference-only-negative-cut-ledger.json',cutledger);pairproof=[]
 for sv,rv in((sig,ret),(src,moved[0]),(next(v for v in h['vias']if v['uuid']=='1f815e33-e973-46e2-833e-96fee8d37fcf'),moved[1])):
  pp=Point(rv['x'],rv['y']);ann=pp.buffer(rv['d']/2,quad_segs=128).difference(pp.buffer(rv['drill']/2,quad_segs=128));aa={ly:ann.buffer(-.025,quad_segs=128).intersection(sh).area for ly,sh in finalrefs.items()};dist=math.dist([sv['x'],sv['y']],[rv['x'],rv['y']]);pairproof.append({'signal_UUID':sv['uuid'],'signal_xy_mm':[sv['x'],sv['y']],'return_UUID':rv['uuid'],'return_xy_mm':[rv['x'],rv['y']],'spacing_mm':dist,'hard_window_mm':[.90,1.0],'nominal_after_all_changed_holes_actual_source_annular_interior_mm2':aa,'exact_original_CMD_diameter_drill_masks_unchanged':sv['uuid']=='1f815e33-e973-46e2-833e-96fee8d37fcf','final_fresh_source_graph_NATIVE_all6_current_SI':'OPEN'})
 assert all(.90<=r['spacing_mm']<=1 and all(v>.005 for v in r['nominal_after_all_changed_holes_actual_source_annular_interior_mm2'].values())for r in pairproof)
 record={'pairs':pairproof,'routes':[],'errors':[]};nt=[];chunks={};cur={'zones':q,'after':c};win=box(121,86,137,103);preGP=H/'CORE-R250-vs-actual-R214-independent-r252/actual-drilled-groups.pkl';assert sha(preGP)=='d79902573902eb14a85e42f97bcdae4928a1f9df4cd8c0ef9f35005c03d16f7e';preRoot=K.root(pickle.loads(preGP.read_bytes())['/LOGIC_GND'],'J11001','2');preRef=unary_union([r['shape']for r in preRoot if r['kind']=='fill'and r['layer']=='In1.Cu']);srcOwn=K.Z.bounded_disk(src,.525).intersection(preRef);assert K.C.sha(srcOwn.wkb)=='f349215378bb280b1038ba1ef2ca09138201b4102b2670b6c4e5324fdd399ae1';targetOwn=K.Z.bounded_disk(sig,.525).intersection(refs['In1.Cu']);own=unary_union([srcOwn,targetOwn]);put(out/'two-exact-before-source-clipped-own-aperture-authorities.json',{'source_UUID':src['uuid'],'source_pre_DIC_actual_root_groups_SHA256':sha(preGP),'source_exact_clipped_own_credit':info(srcOwn),'target_UUID':sig['uuid'],'target_exact_retired_cutter_replayed_before_source_ROOT_SHA256':sha(rgp),'target_exact_clipped_own_credit':info(targetOwn),'both_radius_mm':.525,'every_non_source_void_denied':True,'full_final_pair_source_NATIVE_SI':'OPEN'})
 def route(net,ly,a,bp,scope,region):
  free=B.physical_centres(h,cur,net,ly,region).intersection(finalrefs['In1.Cu'].union(scope).intersection(region.buffer(1)).buffer(-.105,quad_segs=128));parts=[s for s in K.RF.parts(free)if s.covers(Point(a))and s.covers(Point(bp))];row={'raw_net':identity.raw(net),'layer':ly,'requested_endpoints_mm':[a,bp],'same_fullwidth_physical_reference_component':bool(parts)};record['routes'].append(row);print('R550_ROUTE',net,ly,len(parts),flush=True)
  if not parts:return False
  path,search=T.route(parts[0],tuple(a),tuple(bp));path=[serial(p)for p in path];body=unary_union([K.A.shape({'kind':'segment','a':a,'b':b,'w':.2})for a,b in zip(path,path[1:])]);gap=body.difference(finalrefs['In1.Cu'].union(scope));row.update({'points_mm':path,'width_mm':.2,'length_mm':LineString(path).length,'actual_fullbody_reference_gap':info(gap),'search':search,'used_signal_own_scope_only_when_NET_DIC':net==NET})
  if not gap.is_empty:return False
  for a,bp in zip(path,path[1:]):
   uid,ch=identity.serial_segment(net,ly,a,bp,.2)
   if net==FAULT:ch=ch.replace(b'(width 0.2)',b'(width 0.2) (locked yes)');assert b'(locked yes)'in ch
   assert uid not in inv[3]and uid not in chunks
   t={'uuid':uid,'net':identity.raw(net),'layer':ly,'a':a,'b':bp,'w':.2};t.update({'locked':True}if net==FAULT else{});nt.append(t);chunks[uid]=ch;h['tracks'].append(t)
  return True
 positive=route(FAULT,'F.Cu',[130.75,89.45],[129.25,89.65],Point(),box(128.9,88.9,131.5,90.9))
 if positive:
  newfault=unary_union([K.A.shape({'kind':'segment',**t})for t in nt]);shared=[]
  for ob in obligations:
   remaining=unary_union([r['shape']for r in ownedgroup if r['uuid']==ob['UUID']and r['layer']=='F.Cu']);hit=newfault.intersection(remaining);shared.append({**ob,'new_locked_replacement_finite_shared_contact':info(hit),'retained':not hit.is_empty})
  record['all_native_shared_contact_proof']=shared;positive=all(r['retained']for r in shared)
 if positive:
  # Fixed target pad centreline attachment chosen from its real body, never
  # an invented off-pad target; geometric route selects the same conductor.
  free=B.physical_centres(h,cur,NET,'F.Cu',win).intersection(finalrefs['In1.Cu'].union(own).intersection(win.buffer(1)).buffer(-.105,quad_segs=128));parts=[s for s in K.RF.parts(free)if s.covers(Point(sig['x'],sig['y']))and not s.intersection(cc['target_F_component'].buffer(-.105,quad_segs=128)).is_empty]
  if parts:
   attachment=serial(nearest_points(Point(sig['x'],sig['y']),parts[0].intersection(cc['target_F_component'].buffer(-.105,quad_segs=128)))[1].coords[0]);positive=route(NET,'F.Cu',[sig['x'],sig['y']],attachment,own,win)
  else:record['errors'].append('no_real_target_pad_F_reference_component');positive=False
 if positive:positive=route(NET,'In2.Cu',[src['x'],src['y']],[sig['x'],sig['y']],own,win)
 identity.assert_chunks(chunks);referrors=[];records,trees=K.F.build({**h0,'zones':[]});outmap={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'}
 for ly,inner in outmap.items():
  oldRef=unary_union([r['shape']for r in baselineRoot if r['kind']=='fill'and r['layer']==inner]);delta=oldRef.difference(finalrefs[inner])
  for j in trees[ly].query(delta.envelope,predicate='intersects')if not delta.is_empty else[]:
   r=records[ly][int(j)]
   if r['kind']!='track'or r['uuid']in native_removed|new_withdrawn or K.L.norm(r['net'])==LG or dom.get(K.L.norm(r['net']))!=dom[LG]:continue
   loss=r['shape'].intersection(oldRef).difference(finalrefs[inner])
   if not loss.is_empty:referrors.append({'UUID':r['uuid'],'raw_net':r['net'],'layer':ly,'native_original':r['uuid']in inv[3],'loss':info(loss)})
 record['strict_all_retained_current_reference_losses']=referrors;constructive=positive;positive=positive and not referrors;record['constructor_routes_positive_before_raw_old_reference_expression_gate']=constructive
 put(out/'constructor-operation-and-exact-local-physical-reference-results.json',record)
 if constructive:
  # This is an explicit operation nomination, not a projected/accepted
  # current model: owned roles/fills and all-net physical source/contact
  # replay are separate mandatory independent stages.
  packet={'input_current_model_SHA256':sha(mp),'native_source_SHA256':sha(sp),'only_exact_native_deletes':nativechunks,'only_unaccepted_NEW_track_withdrawals':new_withdrawn,'old_NEW_target_and_return_via_definitions':[oldsig]+[v for v in h0['vias']if v['uuid']in{r['old_return_UUID']for r in moves}],'changed_only_NEW_via_definitions':[sig]+moved,'new_locked_fault_and_DIC_tracks':nt,'exact_new_track_chunks':chunks,'current_role_and_actual_filled_projection':'OPEN; exact scoped negative-only replay required','all_native_LOCK_contact_source_reference_and_current':'OPEN','pairs':pairproof,'raw_current_old_reference_expression_failures':referrors,'exact_R552_retirement_source_cache_replay_receipt_SHA256':sha(rrp),'all_original_native_via_masks_flags_and_CMD_physical_definition_unchanged':True}
  pf=out/'exact-coupled-operation-NOT_ACCEPTED_MODEL.pkl';pf.write_bytes(pickle.dumps(packet,protocol=5))
 receipt={'verdict':'CONCRETE_EXACT_RETIRED_CUTTER_POLICY_DIC_LOCKED_FAULT_OPERATION_RAW_GATES_OPEN_OR_FAIL'if constructive else'EXACT_RETIRED_CUTTER_DIC_LOCKED_FAULT_OPERATION_INCOMPLETE','input_current_model_sha256':sha(mp),'source_native_parent_sha256':sha(sp),'source_banks_sha256':sha(bf),'only_original_native_deletes':sorted(native_removed),'only_unaccepted_new_tracks_replaced':sorted(new_withdrawn),'new_track_count':len(nt),'strict_retained_reference_losses':referrors,'constructor_local_result':record,'pair_window_mm':[.90,1.0],'chain':['F.Cu','In2.Cu','F.Cu'],'max_layer_legs':3,'original_source_F_segment_and_source_SIG_unchanged':True,'all_original_source_locked_replacements_locked_yes':True,'new_own_apertures_clipped_actual_before_source_not_generic_disks':True,'exact_R552_source_cache_retirement_replay_receipt_SHA256':sha(rrp),'full_raw_old_reference_gate_PASS':not referrors,'constructor_routes_positive':constructive,'no_ordinary_window_exception_sameplane_label_or_generic_aperture_credit':True,'all_allnet_contact_source_direct_trueCu_exactnewOwnScope_current_NATIVE_SI':'OPEN','all_inherited_raw_failures_preserved':True,'native_jobs':0,'adopted':False,'source_board_project_or_current_model_written':False,'input_SHA256':{str(f.resolve()):sha(f)for f in(Path(__file__),mp,bf,cp,sp,rrp,rgp,preGP)},'output_SHA256':{str(f.resolve()):sha(f)for f in out.iterdir()if f.is_file()},'elapsed_seconds':time.monotonic()-st};put(out/'receipt.json',receipt);print('R550_COMPLETE',sha(out/'receipt.json'),receipt['verdict'],flush=True)
if __name__=='__main__':main()
