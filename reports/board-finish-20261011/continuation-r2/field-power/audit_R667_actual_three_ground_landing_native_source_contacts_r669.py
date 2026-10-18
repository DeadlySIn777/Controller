"""Fresh native three-ground comparison; no forced flags or host fill credit."""
import os, psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
 os.environ[n]='2'
p=psutil.Process(); p.cpu_affinity(list(range(16,28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,collections,math
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent; ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import audit_aux_exact_raw as A
M=ROOT/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
N=H/'R157-minimal-local-three-ground-landings-selected-native-r667'
B=H/'R157-actual-three-ground-native-all-drill-source-groups-r663'
P=H/'R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665'
OUT=H/'R667-actual-native-three-ground-local-landings-source-contact-reference-r669'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def countpad(rows):return len({r['uuid']for r in rows if r['kind']=='pad'and str(r['pin'])})
def shapeinfo(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}

def exact_reference_delta(before,oldrefs,newrefs,ground):
 """Every direct original supported body difference, including line witnesses."""
 delta={ly:oldrefs[ly].difference(newrefs[ly])for ly in oldrefs}
 rows=[]; candidates=0; checked=0
 for t in before['tracks']:
  ly=t['layer'];net=L.norm(t['net'])
  if ly not in K.MAP or net==ground or before['domains_normalized'].get(net)!=before['domains_normalized'][ground]:continue
  checked+=1
  if delta[ly].is_empty:continue
  if t.get('m')is not None:body=L.body(t);bounds=body.envelope
  else:body=None;bounds=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2)
  if not bounds.intersects(delta[ly]):continue
  candidates+=1
  if body is None:body=A.shape({'kind':'segment',**t})
  loss=body.intersection(oldrefs[ly]).difference(newrefs[ly])
  if not loss.is_empty:
   f=OUT/(ground.rsplit('/',1)[-1]+'-'+t['uuid']+'-strict-reference-loss.wkb');f.write_bytes(loss.wkb)
   rows.append({'track_UUID':t['uuid'],'raw_net':t['net'],'layer':ly,'actual_before_source_supported_reference_lost':shapeinfo(loss),'exact_loss_file':str(f.resolve()),'zero_area_line_witness_NOT_WAIVED':True})
 return rows,{'retained_eligible_track_count':checked,'exact_delta_bounds_candidate_count':candidates,'delta':{ly:shapeinfo(sh)for ly,sh in delta.items()},'actual_original_formula':'body.intersection(actual_before_source_fill).difference(actual_after_source_fill)','threshold':0,'no_buffer_expansion_no_line_or_area_waiver':True}

def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic()
 assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 assert sha(B/'receipt.json')=='33703477904ca3cc046c80e741f59897c68c04d2c6dd13d307792d006b1bb1cd'
 assert sha(B/'actual-R157-native-three-ground-all-drilled-groups.pkl')=='a24dcae5ae52ae71e548e7f75f2d1ec746324187cf1dc5ab67e01a4ef6f347b7'
 assert sha(P/'receipt.json')=='f804da80445f226e7e10cfd9660b35bf6ba7dd3b935b2dbb7a542c32769cbabd'
 sourcePCB=N/'copy/board.kicad_pcb';sourcebytes=sourcePCB.read_bytes();assert b'padstack'not in sourcebytes.lower();assert b'layer_shapes'not in sourcebytes.lower();assert b'custom_pad_primitives'not in sourcebytes.lower()
 nr=json.loads((N/'receipt.json').read_bytes());native=json.loads((N/'selected-ground-fill/receipt.json').read_bytes());api=json.loads((N/'native-23-local-zone-API.json').read_bytes());assert not api['errors']and not native['all_discrete_post_fill_errors'];assert sha(N/'selected-ground-fill/geometry.json')==native['actual_geometry_SHA256'];assert sha(N/'selected-ground-fill/actual-via-flashes.json')==native['actual_via_flashes_SHA256']
 g,h,b,q,c=pickle.loads(M.read_bytes());ng=json.loads((N/'selected-ground-fill/geometry.json').read_bytes());fl=json.loads((N/'selected-ground-fill/actual-via-flashes.json').read_bytes())['vias'];baseline=pickle.loads((B/'actual-R157-native-three-ground-all-drilled-groups.pkl').read_bytes());raws={p['net']for p in h['pads']if L.norm(p['net'])in {a[0]for a in K.ROOTS[:3]}}
 index=collections.defaultdict(list)
 for p in h['pads']:
  if p['net']in raws:index[p['ref'],str(p['num']),p['x'],p['y'],p['net']].append(p)
 replacements={};padledger=[]
 for p in ng['pads']:
  if p['net']not in raws:continue
  options=index[p['ref'],str(p['num']),*p['at'],p['net']];assert len(options)==1,(p['ref'],p['num'],p['at']);old=options[0];new={**old,'layers':{ly:O.polys(p['poly'])for ly in p['layers']}};replacements[old['uuid']]=new;padledger.append({'UUID':old['uuid'],'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'actual_native_at_mm':p['at'],'layers':p['layers'],'actual_native_005_ERROR_INSIDE_polygon':True,'single_shape_reuse_scope':'Exact unchanged source AST has no padstack or per-layer shape override declaration; ordinary common pad shape used only on native-reported member layers'})
 assert set(replacements)=={p['uuid']for p in h['pads']if p['net']in raws}
 vias=[{**v,'flashed':fl[v['uuid']],'mask_provenance':'R667 actual selected native FlashLayer, never forced'}for v in h['vias']];pads=[replacements.get(p['uuid'],p)for p in h['pads']];zones=[{**z,'fills':{ly:O.polys(rs)for ly,rs in z['fills'].items()}}for z in ng['zones']if z['net']in raws];candidate={**c,'pads':pads,'vias':vias,'zones':[z for z in c['zones']if z['net']not in raws]+zones};ctx=K.hole_context(candidate);assert len(ctx[0])==len(vias)+sum(len(L.poly(p.get('hole')or[]))for p in pads)
 proposal=pickle.loads((P/'only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl').read_bytes());assert len(proposal)==23;byvia={v['uuid']:v for v in vias};nativezones={z['uuid']:z for z in zones};apirows=json.loads((P/'native-exact-local-zone-chunk-rows.json').read_bytes());assert {r['uuid']for r in apirows}=={z['uuid']for z in proposal};originalrequired=json.loads((ROOT/'R155-known-reference-native-diagnostic-r157/measure/original-parent-retained-via-actual-flash-masks.json').read_bytes())['retained_original_via_masks']
 result={};source=[];contacts=[];contactbad=[];direct=[];directbad=[];sameoldzonebad=[];refs=[];landing=[];landingbad=[];sourcebody=[];sourcebodybad=[]
 for net,ref,pin in K.ROOTS[:3]:
  _,xs=K.physical(candidate,net,ctx);result[net]=xs;old=baseline[net];ar=K.root(xs,ref,pin);br=K.root(old,ref,pin);ak=K.keys(ar);bk=K.keys(br);rows,bad=K.contact_losses(old,xs);contacts.append({'net':net,'baseline':'ACTUAL R157 CPP all drills','actual_old_group_count':len(old),'actual_selected_new_group_count':len(xs),'all_relationship_rows':rows,'losses':bad});contactbad.extend({'net':net,**r}for r in bad)
  lost=sorted(bk-ak);source.append({'net':net,'external_source':ref+'.'+pin,'actual_before_source_named_pad_count':countpad(br),'actual_after_source_named_pad_count':countpad(ar),'actual_before_source_layer_key_count':len(bk),'actual_after_source_layer_key_count':len(ak),'all_prior_actual_source_keys_lost':[list(k)for k in lost],'mask_credit_only_actual_FlashLayer_PLUS_finite_source_group':True})
  for ly in K.LAYERS:
   oldbody=unary_union([r['shape']for r in br if r['kind']=='fill'and r['layer']==ly]);newbody=unary_union([r['shape']for r in ar if r['kind']=='fill'and r['layer']==ly]);bodylost=oldbody.difference(newbody);bodyadded=newbody.difference(oldbody);row={'net':net,'layer':ly,'all_actual_before_SOURCE_filled_Cu':shapeinfo(oldbody),'all_actual_after_SOURCE_filled_Cu':shapeinfo(newbody),'literal_actual_before_source_Cu_NOT_retained':shapeinfo(bodylost),'explicit_actual_source_Cu_added':shapeinfo(bodyadded),'current_capacity_not_inferred_from_fill_area':True};sourcebody.append(row)
   if not bodylost.is_empty:
    f=OUT/(net.rsplit('/',1)[-1]+'-'+ly+'-actual-source-filled-Cu-not-retained.wkb');f.write_bytes(bodylost.wkb);row['exact_loss_file']=str(f.resolve());sourcebodybad.append(row)
  fillby=collections.defaultdict(list)
  for gr in xs:
   for r in gr:
    if r['kind']=='fill':fillby[r['layer']].append(r)
  filltrees={ly:STRtree([r['shape']for r in rs])for ly,rs in fillby.items()}
  for ly in K.LAYERS:
   oldfill=[r for gr in old for r in gr if r['kind']=='fill'and r['layer']==ly];oldtree=STRtree([r['shape']for r in oldfill]);metal=collections.defaultdict(list)
   for gr in old:
    for r in gr:
     if r['kind']!='fill'and r['layer']==ly:metal[r['kind'],r['uuid'],ly].append(r['shape'])
   for key,ss in metal.items():
    body=unary_union(ss);hit=[oldfill[int(i)]for i in oldtree.query(body.buffer(.000002),predicate='intersects')if body.distance(oldfill[int(i)]['shape'])<=.000002]
    if not hit:continue
    nh=[fillby[ly][int(i)]for i in filltrees[ly].query(body.buffer(.000002),predicate='intersects')if body.distance(fillby[ly][int(i)]['shape'])<=.000002]if ly in filltrees else[];oldids={r['uuid']for r in hit};newids={r['uuid']for r in nh};missing=sorted(oldids-newids);row={'net':net,'old_actual_discrete_layer_key':list(key),'old_actual_CPP_touching_zone_UUIDs':sorted(oldids),'new_actual_CPP_touching_zone_UUIDs':sorted(newids),'retained_direct_ANY_same_raw_net_actual_fill_touch':bool(nh),'old_same_zone_direct_touches_not_retained':missing};direct.append(row)
    if not nh:directbad.append(row)
    if missing:sameoldzonebad.append(row)
  rb,rproof=exact_reference_delta(candidate,K.source_refs(br),K.source_refs(ar),net);refs.append({'net':net,'strict_old_routed_reference_losses':rb,'proof':rproof})
  for z in proposal:
   if L.norm(z['net'])!=net:continue
   v=byvia[z['existing_source_via_UUID']];ly=z['layer'];axis=Point(v['x'],v['y']);ann=axis.buffer(v['d']/2,quad_segs=128).difference(axis.buffer(v['drill']/2,quad_segs=128));allhole=unary_union([ctx[0][int(i)]for i in ctx[1].query(ann,predicate='intersects')]);ann=ann.difference(allhole);own=unary_union(L.poly(nativezones[z['uuid']]['fills'].get(ly,[]))).difference(allhole);sf=unary_union([r['shape']for r in ar if r['kind']=='fill'and r['layer']==ly]);ov=ann.intersection(own);sv=ann.intersection(sf);flash=ly in fl[v['uuid']];rk=('via',v['uuid'],ly)in ak;minimum=axis.distance(z['zone_outline_shape'].exterior)-v['drill']/2
   row={'landing_UUID':z['uuid'],'existing_via_UUID':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'tested_missing_layer':ly,'original_required_actual_mask':originalrequired[v['uuid']],'actual_after_FlashLayers':fl[v['uuid']],'ALL_original_required_layers_observed':set(originalrequired[v['uuid']])<=set(fl[v['uuid']]),'actual_missing_layer_FLASH_observed_not_forced':flash,'actual_missing_layer_via_key_external_source_rooted':rk,'finite_ALL_DRILLS_subtracted_annulus':shapeinfo(ann),'actual_own_new_CPP_landing_fill':shapeinfo(own),'finite_own_landing_annular_contact':shapeinfo(ov),'finite_actual_source_fill_annular_contact':shapeinfo(sv),'native_zone_min_thickness_mm':.15,'native_API_zone_nominal_outer_diameter_mm':.5,'native_via_nominal_diameter_mm':v['d'],'native_via_nominal_drill_mm':v['drill'],'nominal_barrel_radial_annular_width_mm':(v['d']-v['drill'])/2,'exact_256_edge_intended_min_radial_annular_width_mm':minimum,'polygon_chord_width_NOT_promoted_to_nominal_width':True,'native_min_feature_survival_evidence':'Actual CPP filled this exact .15-min intended disk and naturally flashes/contacts the plated barrel; physical nominal plating/current/thermal ratings remain OPEN','intended_own_via_centre_covered':z['zone_outline_shape'].covers(axis),'current_plating_SI_loop_thermal':'OPEN'};landing.append(row)
   if not row['ALL_original_required_layers_observed']or not flash or not rk or ov.is_empty or ov.area<=0 or sv.is_empty or sv.area<=0 or not row['intended_own_via_centre_covered']:landingbad.append(row)
  put(OUT/'checkpoint-source-census.json',source);put(OUT/'checkpoint-landing-proof.json',landing);print('R669',net,'sourcepads',countpad(ar),'contactloss',len(bad),'sourcekeyloss',len(lost),'ref_losses',len(rb),flush=True)
 put(OUT/'finite-contact-versus-literal-boundary-scope.json',{'actual_split_graph_and_direct_contact_distance_mm':.000002,'same_distance_nm':2,'literal_filled_Cu_and_routed_reference_comparisons_threshold':0,'line_witnesses_NOT_WAIVED':True,'native_padstack_layer_override_declarations_absent_exact_source_SHA256':sha(sourcePCB)})
 gp=OUT/'fresh-R667-actual-three-ground-all-drilled-groups.pkl';gp.write_bytes(pickle.dumps(result,protocol=5));put(OUT/'exact-actual-native-pad-bindings.json',padledger);put(OUT/'all-three-ground-old-physical-relationships.json',contacts);put(OUT/'all-three-actual-source-bank-keys.json',source);put(OUT/'all-old-direct-native-fill-contacts.json',direct);put(OUT/'old-ANY-same-net-direct-fill-contact-losses.json',directbad);put(OUT/'old-same-zone-direct-touch-differences-retained.json',sameoldzonebad);put(OUT/'all-three-strict-old-track-source-reference-deltas.json',refs);put(OUT/'all-23-actual-native-landing-flash-source-annulus-proof.json',landing);put(OUT/'all-six-layer-source-filled-copper-monotonicity-and-current-scope.json',sourcebody)
 failed=bool(contactbad or directbad or any(r['all_prior_actual_source_keys_lost']for r in source)or any(r['strict_old_routed_reference_losses']for r in refs)or landingbad or native['prior_R157_actual_selected_ground_flash_losses'])
 files=[Path(__file__),M,B/'receipt.json',B/'actual-R157-native-three-ground-all-drilled-groups.pkl',N/'receipt.json',N/'selected-ground-fill/receipt.json',N/'selected-ground-fill/geometry.json',N/'selected-ground-fill/actual-via-flashes.json',N/'native-23-local-zone-API.json',P/'receipt.json',P/'only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl',P/'native-exact-local-zone-chunk-rows.json']
 record={'status':'R667_ACTUAL_SELECTED_LANDING_FLASH_SOURCE_CONTACT_REFERENCE_PASS_OTHER_BOARD_CURRENT_OPEN'if not failed else'R667_ACTUAL_SELECTED_LANDING_SOURCE_CONTACT_REFERENCE_OR_FLASH_REPAIR_REQUIRED','actual_R157_before_receipt_SHA256':sha(B/'receipt.json'),'native_selected_receipt_SHA256':sha(N/'receipt.json'),'native_selected_actual_geometry_SHA256':native['actual_geometry_SHA256'],'native_all_discrete_post_fill_errors':native['all_discrete_post_fill_errors'],'original_Cu_holes_masks_flags_outlines_profiles_SOURCE_RULES_untouched':True,'natural_missing_layer_success_count':len(landing)-len(landingbad),'tested_layer_count':len(landing),'target_existing_barrel_count':len({r['existing_via_UUID']for r in landing}),'actual_prior_source_key_loss_count':sum(len(r['all_prior_actual_source_keys_lost'])for r in source),'actual_old_relationship_losses':contactbad,'actual_old_ANY_same_raw_direct_fill_touch_losses':directbad,'same_original_zone_direct_touch_differences_count':len(sameoldzonebad),'same_original_zone_differences_NOT_SILENTLY_ERASED':True,'strict_old_routed_source_reference_loss_count':sum(len(r['strict_old_routed_reference_losses'])for r in refs),'prior_R157_actual_ground_flash_losses':native['prior_R157_actual_selected_ground_flash_losses'],'failed_landing_proofs':landingbad,'all_source_census':source,'actual_all_six_layer_source_fill_monotonicity_raw_failures':sourcebodybad,'any_raw_source_fill_loss_keeps_current_delta_unqualified':True,'actual_groups_file':str(gp.resolve()),'actual_groups_SHA256':sha(gp),'actual_cpp_own_landing_nominal_minfeature_survival_not_current_capacity':True,'cached_eedf_zero_fills_NO_old_physical_contact_claim':True,'original_R15722_mask_FAILs_preserved_as_before_evidence':True,'all_other_native_held_source_TMR8zone_errors_reference_current_loop_plating_SI_thermal':'OPEN_OR_FAIL_UNCHANGED; no full-board adoption','native_jobs':0,'save_or_forced_FlashLayer_or_adoption':False,'input_SHA256':{str(f.resolve()):sha(f)for f in files},'output_SHA256':{str(f.resolve()):sha(f)for f in OUT.iterdir()if f.is_file()and f.name!='receipt.json'},'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',record);print('R669_COMPLETE',sha(OUT/'receipt.json'),record['status'],flush=True)
if __name__=='__main__':main()
