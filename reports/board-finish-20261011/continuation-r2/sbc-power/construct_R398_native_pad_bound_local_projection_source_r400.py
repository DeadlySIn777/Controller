"""Sparse diagnostic with real native pads and per-record native-aperture projection."""
import sys,json,pickle,hashlib,time,copy,traceback,collections
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as PS
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
N=H/'sbc-power/CM79-R397-exact-five-tracks-three-ordinary-vias-R7035-real-pose-r398'
P=H/'sbc-power/CM79-R398-native-R7035-real-pose-three-via-mask-readonly-r399'
O=H/'sbc-power/CM79-R398-actual-native-pad-local-aperture-fresh-source-r400'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'WKB_sha256':hashlib.sha256(s.wkb).hexdigest()}
def signature(c,net):return pickle.dumps({k:[x for x in c[k]if L.norm(x['net'])==net]for k in('tracks','vias','pads','zones')},protocol=5)
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';assert sha(P/'receipt.json')=='dd0d9da0656cd5b5d6d3d4462ba55d8bfc4755a41dd8004b59ee25dd8227a450';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());pack=pickle.loads((N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl').read_bytes());api=json.loads((P/'actual-native-API.json').read_text());roleBytes={(r['uuid'],k):r[k].wkb for r in q for k in('shape','zone_outline_shape')};put(O/'original-mixed-precision-WKB-restoration.json',PS.restore_bound_field_current_precision_states(b,q));nt=copy.deepcopy(pack['tracks']);nv=copy.deepcopy(pack['vias']);actual={p['uuid']:p for p in api['native_pads']};own=set(actual);oldPads={p['uuid']:p for p in h['pads']if p['uuid']in own};assert set(oldPads)==own;newPads={}
 for uid,a in actual.items():
  old=oldPads[uid];assert(a['ref'],a['num'],a['net'])==(old['ref'],str(old['num']),old['net']);newPads[uid]={**copy.deepcopy(old),'x':a['x'],'y':a['y'],'layers':a['layers'],'hole':a['hole'],'native_outside_layers':a['outside_layers'],'native_absolute_pad_angle_deg':a['absolute_pad_angle_deg'],'native_actual_pose_mask_API_sha256':sha(P/'actual-native-API.json'),'native_inside_outside_error_IU':1}
 for v in nv:
  av=next(x for x in api['new_native_vias']if x['uuid']==v['uuid']);v['flashed']=av['actual_flashed_layers'];v['native_beforefill_mask_API_sha256']=sha(P/'actual-native-API.json');v['fresh_afterfill_flashes_and_SOURCE']='OPEN'
 hh=copy.deepcopy(h);hh['tracks']+=nt;hh['vias']+=nv;hh['pads']=[newPads.get(p['uuid'],p)for p in hh['pads']];fp=next(f for f in hh['footprints']if f['ref']=='R7035');fp['x'],fp['y']=pack['target_root_mm_deg'][:2];from nominate_R371_coupled_R7036_minimal_rigid_pad_poses_r391 import moved
 mm=moved(pack['R7035_source_scope'],pack['model_rigid_pose_degrees_dx_dy']);fp['courtyard']['F']=IM.records(mm['court']);fp['native_owned_rigid_pose_mm_deg']=pack['target_root_mm_deg'];fp['native_owned_pose_API_sha256']=sha(P/'actual-native-API.json');cc={**c,'tracks':c['tracks']+nt,'vias':c['vias']+nv,'pads':[newPads.get(p['uuid'],p)for p in c['pads']],'zones':[]};dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;native=A.C.inventory((H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb').read_bytes());ledger=[];cutops=[];affected=set(L.norm(t['net'])for t in nt+nv)
 for old in c['zones']:
  z={**old,'fills':{}};local=float(z['clearance_mm'])
  for layer,rs in old['fills'].items():
   existing=L.poly(rs);cuts=[];ops=[]
   for item in nt+nv:
    via='d'in item;same=L.norm(item['net'])==L.norm(z['net'])
    if not via and(item['layer']!=layer or same):continue
    clear=max(local,gap(item['net'],z['net']));radius=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+clear)if via else item['w']/2+clear;cut=Z.bounded_disk(item,radius)if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
    if any(cut.intersects(sh)for sh in existing):cuts.append(cut);ops.append({'new_UUID':item['uuid'],'kind':'via'if via else'track','raw_net':item['net'],'native_local_clearance_mm':local,'physical_native_radius_mm':radius,'planner25um_extra_not_used_as_actual_native_fill':True,'same_net_drill_only':bool(via and same),'cutter':ds(cut)})
   for item in newPads.values():
    if L.norm(item['net'])==L.norm(z['net']):continue
    for sh in L.poly(item['native_outside_layers'].get(layer,[])):
     cut=Z.bounded_buffer(sh,max(local,gap(item['net'],z['net'])))
     if any(cut.intersects(ss)for ss in existing):cuts.append(cut);ops.append({'new_UUID':item['uuid'],'kind':'native_actual_moved_pad_outside_1nm','raw_net':item['net'],'native_local_clearance_mm':local,'cutter':ds(cut)})
   if cuts:
    assert old['uuid']in native[3],('foreign_owned_role_cut_prohibited',old['uuid']);z['fills'][layer],recordLedger=IM.subtract(rs,cuts,O,old['uuid']+'-'+layer.replace('.','_'));affected.add(L.norm(z['net']));ledger.append({'zone_UUID':old['uuid'],'raw_net':old['net'],'layer':layer,'unchanged_original_native_outline_settings_UUID':True,'per_record':recordLedger,'exact_declared_new_physical_Cu_and_hole_operations':ops});cutops.extend({'zone_UUID':old['uuid'],'layer':layer,'shape':cut}for cut in cuts)
   else:z['fills'][layer]=copy.deepcopy(rs)
  cc['zones'].append(z)
 put(O/'explicit-local-original-native-plane-hole-pad-track-impact.json',ledger);assert all(r[k].wkb==roleBytes[r['uuid'],k]for r in q for k in('shape','zone_outline_shape'));(O/'model.pkl').write_bytes(pickle.dumps((g,hh,b,q,cc),protocol=5));put(O/'host-phase.json',{'phase':'FRESH_CHANGED_SOURCE_GRAPHS_START','actual_native_PAD_API_sha256':sha(P/'actual-native-API.json'),'model_sha256':sha(O/'model.pkl')});print('R400_MODEL',sha(O/'model.pkl'),'affected',sorted(affected),flush=True)
 cached=pickle.loads((H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354/actual-drilled-after-groups.pkl').read_bytes());cached.update(pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes()));enc=L.norm(pack['R7035_source_scope']['source_pin_nets']['2']);beforeCtx=K.hole_context(c);_,cached[enc]=K.physical(c,enc,beforeCtx);ctx=K.hole_context(cc);fresh={};sourceRows={};roots=K.ROOTS+[('/mc_local_power/CORE_5V','R11022','2'),('/motherboard_motors/AUX_5V_B','U11014','6')];roots+=[(enc,'R7035','2')];allBefore,allTrees=F.build(c);newHoleShapes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in nv];otherIdentity=[]
 for net,ref,pin in roots:
  if net in affected:
   _,xs=K.physical(cc,net,ctx);fresh[net]=xs;before=cached[net];proof,loss=K.contact_losses(before,xs);old=K.root(before,ref,pin);now=K.root(xs,ref,pin);missing=sorted(K.keys(old)-K.keys(now));sourceRows[net]={'source':ref+'.'+pin,'before_source_key_count':len(K.keys(old)),'after_source_key_count':len(K.keys(now)),'all_old_source_keys_lost':[list(k)for k in missing],'old_group_relationship_rows':proof,'old_group_relationship_losses':loss};print('R400_SOURCE',net,len(missing),len(loss),flush=True)
  else:
   assert signature(c,net)==signature(cc,net);hits=[]
   for layer in K.LAYERS:
    for nh in newHoleShapes:
     for j in allTrees[layer].query(nh,predicate='intersects'):
      rr=allBefore[layer][int(j)]
      if L.norm(rr['net'])==net and not nh.intersection(rr['shape']).is_empty:hits.append({'UUID':rr['uuid'],'layer':layer})
   assert not hits,(net,hits);fresh[net]=cached[net];otherIdentity.append({'net':net,'source':ref+'.'+pin,'native_Cu_pad_source_role_fills_metadata_exact':True,'every_new_hole_disjoint_all_native_Cu':True,'actual_SOURCE_graph_and_all_layer_keys_mathematically_identical':True})
 put(O/'fresh-all-changed-source-oldgroups-and-pad-layer-keys.json',sourceRows);put(O/'other-source-bank-new-hole-disjoint-full-physics-identity.json',otherIdentity);(O/'fresh-actual-drilled-all-source-groups.pkl').write_bytes(pickle.dumps(fresh,protocol=5));oldRoot=K.root(cached['/LOGIC_GND'],'J11001','2');newRoot=K.root(fresh['/LOGIC_GND'],'J11001','2');oldRefs=K.source_refs(oldRoot);newRefs=K.source_refs(newRoot);newBodyRows=[];sig=Point(81,28.8);sigCap=sig.buffer(.525,quad_segs=128);ioCap=Point(80.65,24.5).buffer(.575,quad_segs=128);jd=next(p for p in c['pads']if p['uuid']==pack['exact_JD12_B3_UUID']);jdCap=unary_union(L.poly(jd['layers']['In3.Cu'])).buffer(.275,quad_segs=128)
 for t in nt:
  net=L.norm(t['net']);actual=unary_union([rr['shape']for xs in fresh[net]for rr in xs if rr['kind']=='track'and rr['uuid']==t['uuid']and rr['layer']==t['layer']]);guard=ioCap if net=='/IO_3V3'else unary_union([sigCap,jdCap])if t['layer']=='In3.Cu'else sigCap;lost=actual.difference(guard).difference(newRefs[t['layer']]);fn=O/(t['uuid']+'-fresh-actual-body-exact-terminal-reference-gap.wkb');fn.write_bytes(lost.wkb);newBodyRows.append({'UUID':t['uuid'],'layer':t['layer'],'actual_body':ds(actual),'exact_inner_guard_reference_gap':ds(lost),'gap_file':str(fn.resolve())})
 for p in actual.values()if False else newPads.values():
  sh=unary_union(L.poly(p['native_outside_layers']['F.Cu']));lost=sh.difference(newRefs['F.Cu']);newBodyRows.append({'UUID':p['uuid'],'kind':'native_moved_SMD_OUTSIDE_1nm_FULL_BODY','whole_actual_J1_In1_reference_gap':ds(lost)})
 put(O/'all-five-new-body-and-two-native-full-SMD-source-reference-proof.json',newBodyRows);oldLoss=[];maskHits=[]
 for layer,rlayer in K.MAP.items():
  ref=oldRefs[layer]
  for rr in allBefore[layer]:
   if rr['kind']=='fill'or rr['uuid']in own or dom.get(L.norm(rr['net']))!=dom.get('/LOGIC_GND'):continue
   supported=rr['shape'].difference(unary_union([hs for hs in beforeCtx[0]if hs.intersects(rr['shape'])])).intersection(ref)
   if supported.is_empty:continue
   lost=supported.difference(newRefs[layer])
   if not lost.is_empty:oldLoss.append({'UUID':rr['uuid'],'kind':rr['kind'],'layer':layer,'actual_raw_before_supported_loss':ds(lost)})
   for op in cutops:
    if op['layer']==rlayer:
     hit=supported.intersection(op['shape'])
     if not hit.is_empty:maskHits.append({'UUID':rr['uuid'],'layer':layer,'declared_cut_zone_UUID':op['zone_UUID'],'actual_before_supported_mask_hit':ds(hit)})
 put(O/'raw-all-existing-body-reference-losses-no-waiver.json',oldLoss);put(O/'literal-old-supported-body-mask-vs-every-declared-local-cut-hits.json',maskHits);portRows=[]
 for v in nv:
  if L.norm(v['net'])!='/LOGIC_GND':continue
  ov={}
  for ly in('In1.Cu','In4.Cu'):
   ann=unary_union([rr['shape']for rr in newRoot if rr['kind']=='via'and rr['uuid']==v['uuid']and rr['layer']==ly]);actualFill=unary_union([rr['shape']for rr in newRoot if rr['kind']=='fill'and rr['layer']==ly]);ov[ly]=ann.intersection(actualFill).area
  portRows.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'fresh_actual_source_connected_two_plane_annulus_overlap_mm2':ov,'both_positive':all(x>0 for x in ov.values())})
 put(O/'fresh-both-new-LG-return-actual-J1-source-annuli.json',portRows);put(O/'receipt.json',{'verdict':'ACTUAL_NATIVE_PAD_BOUND_SPARSE_LOCAL_NATIVE_APERTURE_SOURCE_DIAGNOSTIC','parent_R371_model_sha256':sha(D/'model.pkl'),'model_sha256':sha(O/'model.pkl'),'R398_packet_sha256':sha(N/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl'),'R399_actual_native_API_sha256':sha(P/'actual-native-API.json'),'fresh_changed_source_net_count':len(sourceRows),'source_key_loss_count':sum(len(x['all_old_source_keys_lost'])for x in sourceRows.values()),'old_source_group_relationship_loss_count':sum(len(x['old_group_relationship_losses'])for x in sourceRows.values()),'other_source_exact_newhole_disjoint_bank_count':len(otherIdentity),'new_body_reference_FAIL_count':sum(not x.get('exact_inner_guard_reference_gap',x.get('whole_actual_J1_In1_reference_gap'))['EMPTY']for x in newBodyRows),'raw_old_body_reference_loss_count':len(oldLoss),'literal_old_body_mask_vs_local_cut_hit_count':len(maskHits),'new_LG_actual_two_source_plane_annulus_FAIL_count':sum(not x['both_positive']for x in portRows),'original_all_other_FP_Cu_footprints_native_source_rules_and_generated_role_WKB_exact':True,'actual_local_native_normal_antipads_projection_not_native_fill_or_minwidth_credit':True,'complete_native_afterfill_allmasks_current_loop_capacity_SI_thermal':'OPEN','all_inherited_CORE14_CORE93_and_other_FAIL_flags':'RETAINED','adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R400',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
