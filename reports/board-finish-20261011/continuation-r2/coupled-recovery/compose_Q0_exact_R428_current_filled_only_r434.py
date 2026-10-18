"""Sparse diagnostic actual-fill composition, immutable original record arrays.

Generated physical/intended q roles stay exact and explicitly UNQUALIFIED for
these new cuts. This stage provides no native emitter/current acceptance.
"""
from pathlib import Path
import sys,pickle,copy,json,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely import affinity,set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def records(sh):return[[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in K.RF.parts(sh)]
start=time.monotonic();out=H/'Q0-exact-R428-current-filled-only-r434';assert not out.exists();out.mkdir();pd=H/'Q0-R426-exact-native-owned-operation-r428';rp=pd/'receipt.json';assert sha(rp)=='f0b31e152b7f13c0a00401149176fb5dff69c4743121654439ca39a82dfeb27c';r=json.loads(rp.read_bytes());packetpath=Path(r['exact_packet_file']);assert sha(packetpath)==r['exact_packet_sha256']=='c884f640a6b722b977a8e8256c8f0463b3450c979e064ad9e40bc21fbef041b9';op=pickle.loads(packetpath.read_bytes());model=Path(r['input_current_model_file']);assert sha(model)==r['input_current_model_sha256'];g,h0,b,q,before=pickle.loads(model.read_bytes());h=copy.deepcopy(h0);nt=op['tracks'];nv=op['vias'];removed=set(op['exact_deleted_track_UUIDs']);h['tracks']=[t for t in h['tracks']if t['uuid']not in removed]+copy.deepcopy(nt);h['vias']+=copy.deepcopy(nv);sv=next(v for v in h['vias']if v['uuid']==op['original_SENSE_via_UUID']);assert sv['flashed']==['F.Cu','B.Cu'];sv['flashed']=['F.Cu','In2.Cu','B.Cu'];sv['prospective_additional_natural_annulus']='In2.Cu; native attestation mandatory, flags untouched';newpads=[];padids={p['uuid']for p in h['pads']if p['ref']=='R10016'}
for p in h['pads']:
 if p['uuid']not in padids:continue
 assert p['smd']and not p.get('hole');p['x']=round(p['x']-.5,9);p['y']=round(p['y']-.5,9)
 p['layers']={layer:records(affinity.translate(unary_union(K.L.poly(rs)),xoff=-.5,yoff=-.5))for layer,rs in p['layers'].items()};newpads.append(p)
fp=next(f for f in h['footprints']if f['ref']=='R10016');assert fp['uuid']==op['R10016_FP_UUID'];fp['x']=229.86;fp['y']=166.662;fp['courtyard']={layer:records(affinity.translate(unary_union(K.L.poly(rs)),xoff=-.5,yoff=-.5))for layer,rs in fp['courtyard'].items()};put(out/'exact-translated-host-FP-and-pad-schema.json',{'FP':fp,'pads':newpads,'exact_native_FP_after_sha256':op['exact_FP_after_sha256'],'all_local_native_AST_preserved':True});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6;zones=[];ledger=[];failures=[];affected={K.L.norm(t['net'])for t in nt+nv};extraann={**sv,'flashed':['In2.Cu']};zoneby={z['uuid']:z for z in before['zones']}
for z0 in before['zones']:
 z=copy.deepcopy(z0);net=K.L.norm(z['net']);local=float(z['clearance_mm']);maskby={};cutrows={}
 for layer in z['fills']:
  masks=[];cr=[]
  for item in nt+nv+[extraann]:
   via='d'in item;same=K.L.norm(item['net'])==net
   if item is extraann and layer!='In2.Cu':continue
   if not via and(item['layer']!=layer or same):continue
   req=max(local,gap(item['net'],net))+.025
   rad=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req
   cut=K.Z.bounded_disk(item,rad)if via else K.Z.bounded_buffer(LineString([item['a'],item['b']]),rad);masks.append(cut);cr.append({'UUID':item['uuid'],'kind':'new_via'if via else'new_track','raw_net':item['net'],'radius_mm':rad,'same_net_own_drill_only':bool(same),'cutter_WKB_sha256':K.C.sha(cut.wkb),'existing_SENSE_added_layer_only':item is extraann})
  for pad in newpads:
   if net==K.L.norm(pad['net'])or layer not in pad['layers']:continue
   sh=unary_union(K.L.poly(pad['layers'][layer]));cut=K.Z.bounded_buffer(sh,max(local,gap(pad['net'],net))+.025);masks.append(cut);cr.append({'UUID':pad['uuid'],'kind':'translated_SMD_pad','raw_net':pad['net'],'cutter_WKB_sha256':K.C.sha(cut.wkb)})
  mask=unary_union(masks);maskby[layer]=mask;cutrows[layer]=cr;rs=z0['fills'][layer];pieces=K.L.poly(rs);assert len(rs)==len(pieces);afterrecords=[];steps=[]
  for i,(rec,old)in enumerate(zip(rs,pieces)):
   if not mask.intersects(old):afterrecords.append(copy.deepcopy(rec));continue
   p0=set_precision(old,0);assert p0.wkb==old.wkb;remaining=p0.difference(mask);reserves=[]
   for iteration in range(16):
    arr=records(remaining);actual=unary_union(K.L.poly(arr));gain=actual.difference(p0)
    if gain.is_empty:break
    stem=z['uuid']+'-'+layer+'-'+str(i)+'-'+str(iteration);gp=out/(stem+'-raw-gain.wkb');gp.write_bytes(gain.wkb);reserve=set_precision(K.Z.bounded_buffer(gain,.0001),0);cp=out/(stem+'-explicit-100nm-negative-reserve.wkb');cp.write_bytes(reserve.wkb);remaining=actual.difference(reserve).intersection(p0);reserves.append({'raw_gain_file':str(gp),'raw_gain_sha256':sha(gp),'negative_cutter_file':str(cp),'negative_cutter_sha256':sha(cp),'reserve_mm':.0001,'no_original_coordinate_snap_no_area_waiver':True})
   arr=records(remaining);actual=unary_union(K.L.poly(arr));gain=actual.difference(p0);assert actual.is_valid
   if not gain.is_empty:
    gp=out/(z['uuid']+'-'+layer+'-'+str(i)+'-unresolved-literal-gain.wkb');gp.write_bytes(gain.wkb);failures.append({'UUID':z['uuid'],'layer':layer,'record':i,'gain_file':str(gp),'gain_sha256':sha(gp)})
   affected.add(net);afterrecords.extend(arr);steps.append({'record':i,'before_WKB_sha256':K.C.sha(p0.wkb),'after_WKB_sha256':K.C.sha(actual.wkb),'strict_no_reclaimed_Cu':gain.is_empty,'exact_scope_only_new_Cu_drill_pad_cuts_plus_declared_local_negative_reserves':True,'actual_removed_mm2':p0.difference(actual).area,'actual_split_piece_count':len(arr),'local_reserves':reserves})
  if steps:z['fills'][layer]=afterrecords;ledger.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'exact_local_clearance_mm':local,'before_record_count':len(rs),'after_record_count':len(afterrecords),'cuts':cutrows[layer],'actual_record_steps':steps})
 zones.append(z)
after={**before,'tracks':h['tracks'],'vias':h['vias'],'pads':h['pads'],'footprints':h['footprints'],'zones':zones};put(out/'exact-new-primitive-only-filled-record-cut-ledger.json',ledger);put(out/'raw-literal-no-gain-failures.json',failures);put(out/'affected-native-physical-net-list.json',sorted(affected));mp=out/'model.pkl'
if not failures:mp.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5))
result={'verdict':'EXACT_SPARSE_ACTUAL_FILL_DIAGNOSTIC_COMPOSITION_SOURCE_CONTACT_REFERENCE_OPEN'if not failures else'STRICT_LITERAL_FILL_GAIN_FAIL_NO_MODEL','source_R428_receipt_sha256':sha(rp),'source_packet_sha256':sha(packetpath),'base_model_file':str(model),'base_model_sha256':sha(model),'model_file':str(mp)if not failures else None,'model_sha256':sha(mp)if not failures else None,'new_tracks':len(nt),'new_vias':len(nv),'original_track_deletes':len(removed),'FP_translations':1,'exact_native_old_SENSE_flags_and_required_F_B_retained_New_In2_prospective':True,'g_b_q_all_physical_intended_geometry_profile_metadata_exact_R155':True,'generated_q_foreign_primitive_antipad_and_own_drill_role_replay':'OPEN; actual-filled-only diagnostic stage, not emitter/native/current acceptance','every_unaffected_original_filled_record_array_exact':True,'literal_no_new_or_reclaimed_filled_Cu':not failures,'full_ALL_native_contacts_nine_sources_ZERO_incremental_reference_new_body_true_Cu_and_current_native':'OPEN','all_raw_R155_R368_28_R7_CORE_ROOT42_planner_and_native_failures_preserved':True,'source_or_board_written':False,'native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'model_sha256':result['model_sha256'],'affected_nets':len(affected),'fill_steps':sum(len(x['actual_record_steps'])for x in ledger),'strict_gains':len(failures)}),flush=True)
