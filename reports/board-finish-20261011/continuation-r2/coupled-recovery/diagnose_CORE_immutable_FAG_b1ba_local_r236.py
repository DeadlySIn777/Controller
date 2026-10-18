"""Exact one-body source-boundary cause diagnosis; no global projection."""
import sys,json,pickle,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in (H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import contact_layout as L
import physical_reference_losses_r3_zero_r208 as RF
import restore_SAFE_generated_precision_states_r168 as PS
from shapely.geometry import Point,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
C=A.C;O=H/'CORE-immutable-FAG-b1ba-exact-local-causal-r236'
GROUND='/motherboard_motors/FIELD_GND';UID='b1ba0f9c-e401-4123-9c8a-b90704d7a13f'
def put(p,r):p.write_text(json.dumps(r,indent=1,allow_nan=False)+'\n')
def blob(name,shape):
 p=O/name;p.write_bytes(shape.wkb)
 return {'file':str(p),'WKB_sha256':C.sha(p.read_bytes()),'area_mm2':shape.area,'bounds_mm':list(shape.bounds)if not shape.is_empty else[],'empty':shape.is_empty}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir()
 for module in(K,A,L,RF,PS):A.read(module.__file__)
 base=H.parent/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';br=A.read(base);assert C.sha(br)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h0,b0,q0,before=pickle.loads(br);PS.restore_bound_generated_precision_states(b0,q0);by0={q['uuid']:q for q in q0};oldctx=K.hole_context(before);_,oldgroups=K.physical(before,GROUND,oldctx);oldroot=K.root(oldgroups,'J11003','2');oldref=K.source_refs(oldroot)['F.Cu'];t=next(t for t in before['tracks']if t['uuid']==UID);assert t['net']=='/motherboard_power_entry/FA_SHDN_CONTACT'and t['layer']=='F.Cu';body=A.shape({'kind':'segment',**t});bounds=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2);nativeids={z['uuid']for z in h0['zones']};by_native={z['uuid']:z for z in h0['zones']};rows=[]
 for revision,folder,cp,receiptpin,modelpin,modelkey in [
  ('R109','CORE-R109-vs-actual-R214-independent-r232','CORE-narrow-immutable-R214-materialized-source-proposal-r109','313ff6a4fad8cc0fe4c0ebfd214638a57ec97f9a776a62adfcb85b975659edb9','fcd5182a7f2d415195508bda0297b9da9eed8cf118b0d78d1d52f942c844a773','R109_model_sha256'),
  ('R112','CORE-R112-vs-actual-R214-independent-r234','CORE-wide-reserved-IO3-immutable-R214-materialized-r112','bf1431fb2cf38d66e76727b2c9093b335ab49b22f9012065d9bffe9e6703b254','6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e','R112_model_sha256')]:
  ap=H/folder/'receipt.json';ar=A.read(ap);audit=json.loads(ar)
  if receiptpin:assert C.sha(ar)==receiptpin
  assert audit['original_R214_model_sha256']==C.sha(br)and audit[modelkey]==modelpin
  assert audit['native_jobs']==0 and audit['adopted'] is False
  mr=A.read(H.parent/cp/'model.pkl');assert C.sha(mr)==modelpin;ng,h,b,q,after=pickle.loads(mr);assert ng==g and h['tracks']==h0['tracks'] and h['pads']==h0['pads'];PS.restore_bound_generated_precision_states(b,q);by={z['uuid']:z for z in q};core=by['b0453302-df03-561f-9bc4-0560bc66658a'];nv=[v for v in h['vias']if v['uuid']not in{v['uuid']for v in h0['vias']}];assert len(nv)==2
  gp=ap.parent/'actual-drilled-groups.pkl';gr=A.read(gp);assert C.sha(gr)==audit['output_files_sha256'][str(gp)];newroot=K.root(pickle.loads(gr)[GROUND],'J11003','2');newref=K.source_refs(newroot)['F.Cu'];bank=next(r for r in json.loads(A.read(ap.parent/'three-bank-ZERO-signal-and-all104PDN-reference.json'))if r['ground']==GROUND);delta=oldref.difference(newref);assert C.sha(delta.wkb)==bank['strict_zero_proof']['exact_delta_WKB_sha256']['F.Cu'];lost=next((r for r in bank['all_actual_retained_signal_AND_PDN_power_body_reference_losses']if r['uuid']==UID),None)
  if lost is None:
   rows.append({'revision':revision,'strict_receipt_sha256':C.sha(ar),'unchanged_exact_body_has_no_STRICT_loss':True,'no_waiver_or_shape_change':True});continue
  assert len(bank['all_actual_retained_signal_AND_PDN_power_body_reference_losses'])==1
  parts=RF.parts(delta);tree=STRtree(parts);ids=tree.query(bounds.buffer(1e-9),predicate='intersects');selected=unary_union([parts[int(i)]for i in ids]);assert C.sha(selected.wkb)==lost['exact_local_delta_WKB_sha256'];gap=body.intersection(selected);assert gap.area==lost['prior_source_reference_lost_mm2'];window=box(*gap.bounds).buffer(.000002,cap_style=3);gapinfo=blob(revision+'-exact-full-body-loss.wkb',gap);beforeinfo=blob(revision+'-immutable-R214-local-source-reference.wkb',oldref.intersection(window));afterinfo=blob(revision+'-actual-current-local-source-reference.wkb',newref.intersection(window));contributors=[]
  for z in (z for z in oldroot if z['kind']=='fill'and z['layer']=='In1.Cu'):
   hit=z['shape'].intersection(gap)
   if hit.is_empty:continue
   uid=z['uuid'];final=[r['shape']for r in newroot if r['kind']=='fill'and r['layer']=='In1.Cu'and r['uuid']==uid];newfill=unary_union(final);oldfill=z['shape'];entry={'zone_UUID':uid,'layer':'In1.Cu','native_original_zone':uid in nativeids,'exact_old_physical_source_piece_WKB_sha256':C.sha(oldfill.wkb),'exact_new_same_UUID_source_union_WKB_sha256':C.sha(newfill.wkb),'old_fill_body_gap_intersection':blob(revision+'-'+uid+'-old-fill-gap-hit.wkb',hit),'same_UUID_actual_fill_loss_at_gap':blob(revision+'-'+uid+'-same-fill-local-delta.wkb',oldfill.difference(newfill).intersection(window))}
   if uid in by0:
    entry['generated_role_evidence']={}
    for role in('shape','zone_outline_shape'):
     a,n=by0[uid][role],by[uid][role];entry['generated_role_evidence'][role]={'before_WKB_sha256':C.sha(a.wkb),'after_WKB_sha256':C.sha(n.wkb),'exact_WKB_unchanged':a.wkb==n.wkb,'full_role_only_removed_mm2':a.difference(n).area,'full_role_added_mm2':n.difference(a).area,'exact_local_role_delta_at_gap':blob(revision+'-'+uid+'-'+role+'-local-role-delta.wkb',a.difference(n).intersection(window))}
   if uid in by_native:
    entry['original_native_definition']={k:v for k,v in by_native[uid].items()if k not in('fills','rings','outline')};entry['native_definition_exact_current']=next(z for z in h['zones']if z['uuid']==uid)==by_native[uid]
   contributors.append(entry)
  native_local=[]
  for z in before['zones']:
   if z['uuid']not in nativeids or L.norm(z['net'])!=GROUND:continue
   sh=unary_union(L.poly(z['fills'].get('In1.Cu',[])))
   if sh.distance(gap)>.000010:continue
   post=next(r for r in after['zones']if r['uuid']==z['uuid']);pn=unary_union(L.poly(post['fills'].get('In1.Cu',[])));native_local.append({'UUID':z['uuid'],'original_native_definition_exact':next(r for r in h['zones']if r['uuid']==z['uuid'])==by_native[z['uuid']],'R214_filled_record_before_WKB_sha256':C.sha(sh.wkb),'current_after_WKB_sha256':C.sha(pn.wkb),'exact_native_local_delta':blob(revision+'-'+z['uuid']+'-local-native-fill-delta.wkb',sh.difference(pn).intersection(window)),'native_fill_gain_local':blob(revision+'-'+z['uuid']+'-local-native-fill-gain.wkb',pn.difference(sh).intersection(window))})
  rows.append({'revision':revision,'strict_receipt_sha256':C.sha(ar),'strict_failure_preserved':lost,'exact_loss':gapinfo,'exact_R214_source_boundary':beforeinfo,'exact_current_source_boundary':afterinfo,'actual_old_source_fill_contributors':contributors,'all_actual_near_original_native_FAG_In1_fills':native_local,'distance_to_new_CORE_body_mm':gap.distance(core['shape']),'distance_to_nearest_new_CORE_port_mm':min(gap.distance(Point(v['x'],v['y']))for v in nv),'scope_no_global_projection_no_tolerance_no_own_disk_credit':True});print('R236_EXACT_LOCAL_MATCH',revision,gap.area,len(contributors),flush=True)
 put(O/'exact-local-causal-rows.json',rows);put(O/'receipt.json',{'verdict':'EXACT_IMMUTABLE_BOUNDARY_ONE_BODY_CAUSAL_DIAGNOSTIC_NO_WAIVER','source_model_sha256':C.sha(br),'unchanged_track':t,'matched_revisions':rows,'no_global_projector':True,'no_reference_buffer_expansion_or_threshold':True,'original_STRICT_failures_unchanged':True,'native_jobs':0,'source_or_board_written':False,'adopted':False,'read_files_sha256':A.READS,'output_files_sha256':{str(p):C.sha(p.read_bytes())for p in O.iterdir()if p.is_file()and p.name!='receipt.json'},'elapsed_seconds':time.monotonic()-started});print(C.sha((O/'receipt.json').read_bytes()),flush=True)
if __name__=='__main__':main()
