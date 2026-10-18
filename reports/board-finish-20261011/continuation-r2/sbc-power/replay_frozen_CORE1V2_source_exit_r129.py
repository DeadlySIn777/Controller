"""Replay frozen R125 physical candidate with strict extra owned-wall reserve.

The diagnosed out-of-scope strips are explicitly removed from the new 1V2
proposal. The bounded CORE notch is then accepted only after exact source
retention. Existing native outlines, discrete copper and source are untouched.
"""
from pathlib import Path
import copy,hashlib,json,pickle,sys,uuid
from shapely import from_wkb,set_precision
from shapely.geometry import Point,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import owned_analytic_track_guards_r75 as AT
import owned_native_pad_guards_r98 as AP
import io3_contact_restore_r2 as Q
O=H/'sbc-power/frozen-regional-source-exit-replay-r129'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(f,r):Path(f).write_text(json.dumps(r,indent=1)+'\n')
def polys(s):return [s] if s.geom_type=='Polygon' else [x for x in getattr(s,'geoms',[]) if x.geom_type=='Polygon']
def exact(model,net,ref,pin):
 Q.NET=net;gs,parts,assign=Q.groups(model,return_details=True)
 i=next(i for i,xs in enumerate(gs) if any((r['ref'],r['pad'])==(ref,pin) for r in xs))
 return {r['uuid'] for r in gs[i]},i,parts,assign
def froot(model,net,ref,pin):return next(xs for xs in F.graph(model,net) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,pin) for q in xs))
def padids(rows):return {q['uuid'] for q in rows if q['kind']=='pad' and q['pin']}
def main():
 assert not O.exists();O.mkdir()
 mp=H/'sbc-power/core1v2-extra-In4-source-guarded-input-r112/model.pkl'
 assert sha(mp)=='b58fed8889bb7fed0f5460e16680d7c56fc69b14e04b5f528c98e1fa6811c8b7'
 old,h,b,z,current=pickle.loads(mp.read_bytes());b=copy.deepcopy(b)
 cf=H/'sbc-power/major-rail-regional-logged-source-exit-r125/failed-scope-1/new-feed.wkb'
 sf=H/'sbc-power/major-rail-regional-logged-source-exit-r125/rejections.json'
 diag=json.loads(sf.read_bytes());assert diag[0]['reason']=='physical_carve_exceeds_exact_bounded_scope' and diag[0]['width']==1.0
 nominee=from_wkb(cf.read_bytes());assert not nominee.is_empty
 hard=copy.deepcopy(h);peers=[]
 for folder,qsha,rsha,dsha in [
  ('field-power/regulated-four-retained-hard-snapshot-r127','82ab625dbe9310aa1287321a1e96f814a3408dead04200a8c4340882edf1b589','66f83482cf96300b4fdfbeba537263c935fb46d61d791c29e7aee8df1706e85f','9651216efa39c190b8731162251cb4b68f6313f1b12c62f5eab45d2a452c891b'),
  ('logic-return-r18-snapshot-1','943d222e160f478d8cc351f63489b5b07a4ef380a326e81b8e6f2a6d13a05a42','26a948f505170aaa5b3ea6f86bfe2013465c7ed5493d98ba2f7469d7efb11eb3',None)]:
  qf=H/folder/'proposed-zones.pkl';rf=H/folder/'receipt.json';assert sha(qf)==qsha and sha(rf)==rsha
  qs=pickle.loads(qf.read_bytes());peers+=qs
  row={'zones_file':str(qf.resolve()),'zones_sha256':qsha,'receipt_file':str(rf.resolve()),'receipt_sha256':rsha,'source_contact_current_native_credit':False}
  if dsha:
   df=H/folder/'proposed-discrete.pkl';assert sha(df)==dsha
   ds=pickle.loads(df.read_bytes());row.update(discrete_file=str(df.resolve()),discrete_sha256=dsha)
   for key in ('vias','tracks'):
    by={q['uuid']:q for q in hard[key]}
    for q in ds[key]:
     if q['uuid'] in by:assert q==by[q['uuid']]
     else:hard[key].append(q)
  b.setdefault('source_exit_replay_hard_only_peer_proposals',[]).append(row)
 raw='/CORE_1V2';core_raw='/mc_local_power{slash}CORE_5V';core_net=C.norm(core_raw)
 wall_uid='c7e36847-4380-503d-80f2-836420105d9e';oldq=next(q for q in z if q['uuid']==wall_uid)
 before=oldq['shape'];outline=oldq.get('zone_outline_shape',before);escape=set_precision(box(233.212,91.61,239.212,97.61),1e-6)
 outside=set_precision(before,1e-6).difference(escape)
 required=.15+.025;carve_distance=required+.000020;reserve=.000050
 # An extra 50 nm belongs only to construction. The independent full .175
 # margin and exact scope checks remain unchanged.
 exclusion=GP.bounded_buffer(outside,carve_distance+reserve)
 clipped=set_precision(set_precision(nominee,1e-6).difference(exclusion),1e-6)
 uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-frozen-R125-core1v2-exact-source-exit-r129'))
 q={'uuid':uid,'net':raw,'layer':'In4.Cu','shape':clipped,'zone_outline_shape':clipped,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'native_outline_intentionally_preserves_frozen_physical_drill_holes':True,'label':'Frozen R125 source-exit candidate with strict extra construction reserve R129'}
 zz,vg=GP.normalize_owned_via_guards(hard,[q]);q=zz[0]
 zz,tg,_=AT.normalize_owned_track_guards(hard,[q]);q=zz[0]
 zz,pg,_=AP.normalize_owned_pad_guards(h,[q]);q=zz[0]
 cutter=GP.bounded_buffer(q['shape'],carve_distance)
 removed=before.intersection(cutter)
 after=set_precision(set_precision(before,1e-6).difference(cutter),1e-6)
 oa=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6)
 ledger={'old_new_owned_CORE_zone_UUID':wall_uid,'new_source_exit_zone_UUID':uid,'raw_net':core_raw,'layer':'In4.Cu','original_candidate_file':str(cf.resolve()),'original_candidate_sha256':sha(cf),'original_failed_diagnostic_sha256':sha(sf),'nominal_original_search_width_mm':1.0,'postclip_current_cross_section_requires_requalification':True,'declared_source_exit_scope_mm':list(escape.bounds),'full_required_Cu_gap_mm':required,'explicit_common_construction_reserve_mm':.000020,'additional_candidate_only_construction_reserve_mm':reserve,'candidate_removed_mm2':nominee.difference(q['shape']).area,'candidate_quantization_added_mm2':q['shape'].difference(nominee).area,'CORE_physical_removed_mm2':before.difference(after).area,'CORE_outline_removed_mm2':outline.difference(oa).area,'CORE_quantization_added_mm2':after.difference(before).area,'CORE_outline_quantization_added_mm2':oa.difference(outline).area,'outside_scope_physical_removed_mm2':removed.difference(escape).area,'outside_scope_outline_removed_mm2':outline.difference(oa).difference(escape).area,'original_native_zone_definitions_changed':0,'guards':{'via':vg,'track':tg,'native_pad':pg}}
 for label,shape in [('candidate-original-physical',nominee),('candidate-final-physical',q['shape']),('candidate-final-intended',q['zone_outline_shape']),('candidate-exclusion',exclusion),('CORE-physical-before',before),('CORE-physical-after',after),('CORE-outline-before',outline),('CORE-outline-after',oa),('exact-carve-cutter',cutter),('declared-source-exit-scope',escape)]:
  f=O/(label+'.wkb');f.write_bytes(shape.wkb);ledger.setdefault('geometry_files',{})[label]={'file':str(f.resolve()),'sha256':sha(f)}
 write(O/'exact-construction-ledger.json',ledger)
 assert not q['shape'].is_empty and not after.is_empty
 if not escape.covers(removed) or not escape.covers(outline.difference(oa)):
  write(O/'receipt.json',{'verdict':'FAIL_EXACT_SOURCE_EXIT_SCOPE_NO_SOURCE_ACCEPTANCE','ledger_sha256':sha(O/'exact-construction-ledger.json'),'outside_scope_physical_mm2':ledger['outside_scope_physical_removed_mm2'],'outside_scope_outline_mm2':ledger['outside_scope_outline_removed_mm2'],'native_jobs':0,'board_written':False});print('R129_EXACT_SCOPE_FAIL',ledger['outside_scope_physical_removed_mm2'],ledger['outside_scope_outline_removed_mm2'],flush=True);return
 print('R129_EXACT_SCOPE_PASS',ledger['CORE_physical_removed_mm2'],flush=True)
 newwall={**oldq,'shape':after,'zone_outline_shape':oa,'precarve_route_minimum_cross_section_and_current_must_be_requalified':True}
 proposed=[newwall if x['uuid']==wall_uid else x for x in z]+[q]
 selected={**h,'zones':[x for x in h['zones'] if x['net']==raw]}
 trial,retreat=GP.projected(old,selected,proposed)
 groups=F.graph(current,raw);prior=padids(next(xs for xs in groups if any(x['kind']=='pad' and (x['ref'],x['pin'])==('L2001','2') for x in xs)))
 target=padids(next(xs for xs in groups if any(x['kind']=='via' and x['uuid']=='13ace114-2da3-479c-9c70-bee7d15da004' for x in xs)))
 joined=padids(froot(trial,raw,'L2001','2'));write(O/'source-scope-checkpoint.json',{'1V2_prior_pad_keys':sorted(prior),'1V2_target_pad_keys':sorted(target),'joined_pad_keys':sorted(joined),'missing_target':sorted(target-joined),'missing_prior':sorted(prior-joined)})
 if not target<=joined or not prior<=joined:
  write(O/'receipt.json',{'verdict':'FAIL_1V2_FROZEN_CANDIDATE_SOURCE_JOIN','ledger_sha256':sha(O/'exact-construction-ledger.json'),'missing_target':sorted(target-joined),'missing_prior':sorted(prior-joined),'native_jobs':0,'board_written':False});print('R129_1V2_SOURCE_FAIL',len(target-joined),len(prior-joined),flush=True);return
 exact_joined,_,_,_=exact(trial,raw,'L2001','2');assert target<=exact_joined and prior<=exact_joined
 print('R129_1V2_EXACT_SOURCE_PASS',len(joined),flush=True)
 core_selected={**h,'zones':[x for x in h['zones'] if x['net']==core_raw]}
 core_before,_=GP.projected(old,core_selected,z);prior_core,_,_,_=exact(core_before,core_net,'R11022','2');assert len(prior_core)==8303
 core_after,_=GP.projected(old,core_selected,proposed);joined_core,root_index,parts,assign=exact(core_after,core_net,'R11022','2')
 lost=prior_core-joined_core;floating=[]
 for cq in proposed:
  if C.norm(cq['net'])!=core_net:continue
  for piece in polys(cq['shape']):
   hits={a for p,a in zip(parts[cq['layer']],assign[cq['layer']]) if p.intersection(piece).area>0}
   if hits!={root_index}:floating.append({'zone_UUID':cq['uuid'],'component_area_mm2':piece.area,'assigned_groups':list(hits)})
 write(O/'CORE-source-scope-checkpoint.json',{'prior_exact_CORE_keys':sorted(prior_core),'after_exact_CORE_keys':sorted(joined_core),'missing_CORE_keys':sorted(lost),'detached_proposed_CORE_components':floating})
 if lost or floating:
  write(O/'receipt.json',{'verdict':'FAIL_EXACT_CORE_SOURCE_RETENTION_AFTER_BOUNDED_EXIT','ledger_sha256':sha(O/'exact-construction-ledger.json'),'lost_exact_CORE_keys':sorted(lost),'detached_CORE_components':floating,'native_jobs':0,'board_written':False});print('R129_CORE_SOURCE_FAIL',len(lost),len(floating),flush=True);return
 snap=O/'accepted-source-scope';snap.mkdir();(snap/'proposed-zones.pkl').write_bytes(pickle.dumps(proposed,protocol=5));(snap/'new-feed-zones.pkl').write_bytes(pickle.dumps([q],protocol=5))
 b['CORE1V2_frozen_source_exit_exact_contact_ledger']={'file':str((O/'exact-construction-ledger.json').resolve()),'sha256':sha(O/'exact-construction-ledger.json'),'required_native_original_F_In3_and_added_In4_flash':True}
 write(snap/'receipt.json',{'verdict':'PASS_EXACT_SCOPED_1V2_JOIN_AND_ALL_8303_CORE_SOURCE_KEYS_NATIVE_FOREIGN_CURRENT_OPEN','base_model_sha256':sha(mp),'proposed_zones_sha256':sha(snap/'proposed-zones.pkl'),'new_feed_zones_sha256':sha(snap/'new-feed-zones.pkl'),'construction_ledger_sha256':sha(O/'exact-construction-ledger.json'),'source_rooted_1V2_named_pads':len(joined),'all_prior_CORE_keys_source_retained':len(prior_core),'all_remaining_CORE_components_source_rooted':True,'original_source_F_In3_added_In4_flash_native_required':True,'full_FOREIGN_contact_reference_current_and_native_gates':'OPEN','native_jobs':0,'board_written':False})
 print('R129_SCOPED_SOURCE_ACCEPTED',sha(snap/'receipt.json'),flush=True)
 final,retreat=GP.projected(old,h,proposed)
 for raw_net,scope in [(raw,trial),(core_raw,core_after)]:
  scope_fills={x['uuid']:(x['net'],x['fills']) for x in scope['zones'] if x['net']==raw_net}
  final_fills={x['uuid']:(x['net'],x['fills']) for x in final['zones'] if x['net']==raw_net};assert scope_fills==final_fills
 assert target<=padids(froot(final,raw,'L2001','2')) and prior_core<=exact(final,core_net,'R11022','2')[0]
 mf=O/'model.pkl';mf.write_bytes(pickle.dumps((old,h,b,proposed,final),protocol=5));write(O/'receipt.json',{'verdict':'PASS_FULL_PROJECTOR_SCOPED_1V2_CORE_RETENTION_FOREIGN_CURRENT_NATIVE_OPEN','model_sha256':sha(mf),'baseline_model_sha256':sha(mp),'scope_receipt_sha256':sha(snap/'receipt.json'),'construction_ledger_sha256':sha(O/'exact-construction-ledger.json'),'full_projector_selected_source_fills_exact_equal':True,'full_fitted_CORE1V2_A':.8,'full_fitted_CORE_5V_A':7.882034293398381,'native_jobs':0,'board_written':False,'full_foreign_retained_contacts_outer_reference_current_native_DRC':'OPEN'})
 print('R129_FULL_MODEL_FROZEN',sha(mf),flush=True)
if __name__=='__main__':main()
