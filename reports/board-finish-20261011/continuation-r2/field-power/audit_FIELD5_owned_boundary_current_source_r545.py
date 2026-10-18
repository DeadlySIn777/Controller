"""Fresh changed nets and exhaustive exact unchanged-net identity on R543.

All cached counts are literal. Unchanged nets are proved by exact full Cu,
hole, pad and per-net fill identity; no fictitious 81 recomputed graphs.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib,time,collections,re
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl';P=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl';G=H/'FA-IO3-TMR-current-R515-complete-delta-direct-contact-r517/actual-drilled-current-groups.pkl';D=H.parent/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru';O=H/'FIELD5-R543-full-exact-net-source-contact-reference-geometry-r545'
FG='/motherboard_motors/FIELD_GND';NET='/motherboard_power_entry/FIELD_5V';FID='e2fe644a-2849-5c69-8ebb-d1e94909cd4c';OLD='61cb8179-7754-5031-bbea-0da464bf816f'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def sm(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'WKB_SHA256':dg(s)}
def fill_identity(group,layers):return sorted((r['uuid'],r['layer'],dg(r['shape']))for r in group if r['kind']=='fill'and r['layer']in layers)
def main():
 assert not O.exists();O.mkdir();st=time.monotonic();assert sha(M)=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416';assert sha(P)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862';assert sha(G)=='800faccdde6591605693b1159fe49f273bee7d2d67fed48fe71b8f0b6685c028'
 g,h,b,q,c=pickle.loads(M.read_bytes());pg,ph,pb,pq,pc=pickle.loads(P.read_bytes());MS.restore_bound_field_current_precision_states(b,q);MS.restore_bound_field_current_precision_states(pb,pq);assert g==pg and h==ph and{k:v for k,v in c.items()if k!='zones'}=={k:v for k,v in pc.items()if k!='zones'}
 packet=pickle.loads((M.parent/'only-one-positive-one-owned-boundary-negative-and-preview-withdrawal.pkl').read_bytes());newq=packet['only_new_positive_q'];UID=newq['uuid'];assert newq==next(z for z in q if z['uuid']==UID);changed={FG,NET}
 nets={L.norm(x['net'])for kind in('pads','vias','tracks','zones')for x in c[kind]};oldnets={L.norm(x['net'])for kind in('pads','vias','tracks','zones')for x in pc[kind]};assert nets==oldnets;exact=[]
 for net in sorted(nets-changed):
  assert[z for z in c['zones']if L.norm(z['net'])==net]==[z for z in pc['zones']if L.norm(z['net'])==net];exact.append({'net':net,'all_native_discrete_pad_hole_and_current_fill_arrays_exact':True,'no_new_holes_or_foreign_fill_projection':True,'physical_graph_identical_by_exact_records':True})
 for z in q:
  if z['uuid']in(UID,FID):continue
  prior=next(x for x in pq if x['uuid']==z['uuid']);assert z==prior
 old=pickle.loads(G.read_bytes());cached_count=len(old);now=dict(old);ctx=K.hole_context(c)
 for net in sorted(changed):
  if net not in old:_,old[net]=K.physical(pc,net,ctx)
  _,now[net]=K.physical(c,net,ctx);print('R545 fresh',net,'groups',len(now[net]),flush=True)
 relations=[];losses=[]
 for net in sorted(old):
  _,bad=K.contact_losses(old[net],now[net]);relations.append({'net':net,'before_groups':len(old[net]),'after_groups':len(now[net]),'losses':bad,'fresh_actual_graph':net in changed,'exact_unchanged_reuse':net not in changed});losses.extend({'net':net,**r}for r in bad)
 sources=[]
 for net,ref,pin in[K.ROOTS[0],*K.ROOTS[1:],(NET,'L11003','2')]:
  a=K.root(old[net],ref,pin);n=K.root(now[net],ref,pin);lost=K.keys(a)-K.keys(n);sources.append({'net':net,'source':ref+'.'+pin,'prior_source_keys_lost':[list(x)for x in sorted(lost)],'before_named_source_pads':len({r['uuid']for r in a if r['kind']=='pad'and str(r['pin'])}),'after_named_source_pads':len({r['uuid']for r in n if r['kind']=='pad'and str(r['pin'])})})
 root=K.root(now[NET],'L11003','2');present={(r['ref'],str(r['pin']))for r in root if r['kind']=='pad'};need=[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')];missing=[x for x in need if x not in present];put(O/'all-prior-contact-relations.json',relations);put(O/'all-ten-source-key-deltas.json',sources);put(O/'exhaustive-unchanged-per-net-physical-record-identity.json',exact);print('R545 source/contact',len(losses),sum(len(r['prior_source_keys_lost'])for r in sources),'targets missing',missing,flush=True)
 direct=[];directbad=[];finalfill=collections.defaultdict(list)
 for xs in now[FG]:
  for r in xs:
   if r['kind']=='fill':finalfill[r['uuid'],r['layer']].append(r['shape'])
 for layer in K.LAYERS:
  metal=[r for xs in old[FG]for r in xs if r['layer']==layer and r['kind']!='fill'];tree=STRtree([r['shape']for r in metal])
  for fill in[r for xs in old[FG]for r in xs if r['kind']=='fill'and r['layer']==layer and r['uuid']==FID]:
   for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
    r=metal[int(j)]
    if r['shape'].distance(fill['shape'])>.000002:continue
    good=any(sh.distance(r['shape'])<=.000002 for sh in finalfill[FID,layer]);row={'net':FG,'zone_UID':FID,'layer':layer,'old_fill_piece_SHA256':dg(fill['shape']),'native_metal_key':[r['kind'],r['uuid'],layer],'direct_same_zone_contact_retained':good};direct.append(row)
    if not good:directbad.append(row)
 put(O/'all-owned-FG-old-direct-native-layer-contacts.json',direct)
 # The deliberate owned FIELD5 layer redesign retains all physical native
 # keys/source relationships; no claim of unchanged removed In4 fill contact.
 ownmoves=[];rkeys=K.keys(root)
 for xs in old[NET]:
  for f in xs:
   if f['kind']!='fill'or f['uuid']!=OLD:continue
   for r in xs:
    if r['kind']=='fill'or r['layer']!=f['layer']or r['shape'].distance(f['shape'])>.000002:continue
    ownmoves.append({'withdrawn_owned_preview_zone':OLD,'old_layer':f['layer'],'retained_native_key':[r['kind'],r['uuid'],r['layer']],'actual_L11003_2_source_rooted_after':(r['kind'],r['uuid'],r['layer'])in rkeys,'explicit_plane_layer_change_not_faked_unchanged_direct_layer_contact':True})
 put(O/'only-owned-FIELD5-preview-layer-contact-change-ledger.json',ownmoves)
 # Stable exact physical constituent order, not a ground shadow expansion.
 refs=[];refbad=[];newrefs_by={}
 for net,ref,pin in K.ROOTS[:3]:
  ar=K.root(old[net],ref,pin);nr=K.root(now[net],ref,pin);same=fill_identity(ar,('In1.Cu','In4.Cu'))==fill_identity(nr,('In1.Cu','In4.Cu'));before_ref=K.source_refs(ar);after_ref=before_ref if same else K.source_refs(nr);newrefs_by[net]=after_ref;bad,proof=RF.audit(pc,before_ref,after_ref,net,());refbad.extend({'bank':net,**r}for r in bad);dc=[]
  for z in pq:
   if z['layer']not in K.MAP or h['domains_normalized'][L.norm(z['net'])]!=h['domains_normalized'][net]:continue
   gap=lit(z['shape']).intersection(before_ref[z['layer']]).difference(after_ref[z['layer']]);row={'UID':z['uuid'],'layer':z['layer'],'raw_net':z['net'],'formula':'actual_before_DC_body_intersect_before_source_supported_reference_minus_after_source_reference','actual_before_supported_reference_delta':sm(gap)};dc.append(row)
   if not gap.is_empty:refbad.append({'bank':net,**row})
  refs.append({'net':net,'all_source_In1_In4_physical_fill_constituent_UUID_layer_WKBs_exact':same,'no_nonexistent_before_shadow_created':True,'strict_RF_old_track_losses':bad,'strict_RF_proof':proof,'all_prior_DC_actual_supported_reference_deltas':dc});print('R545 refs',net,'exact',same,'bad',len(bad),flush=True)
 put(O/'three-bank-strict-old-track-and-supported-DC-reference-deltas.json',refs)
 records,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda n:.15 if dom[L.norm(n)]==dom[NET]else .6;checks=[];errors=[];body=lit(newq['shape'])
 for j in trees['In2.Cu'].query(body.buffer(.8),predicate='intersects'):
  r=records['In2.Cu'][int(j)]
  if L.norm(r['net'])==NET:continue
  if r['kind']=='via':v=r['source'];distance=Point(v['x'],v['y']).distance(body)-v['d']/2
  elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];distance=LineString([t['a'],t['b']]).distance(body)-t['w']/2
  else:distance=lit(r['shape']).distance(body)
  row={'kind':'new_positive_to_actual_true_'+r['kind'],'UID':r['uuid'],'raw_net':r['net'],'actual_gap_mm':distance,'required_mm':gap(r['net'])+.025};checks.append(row)
  if distance<row['required_mm']:errors.append(row)
 for z in c['zones']:
  if L.norm(z['net'])==NET or'In2.Cu'not in z['fills']:continue
  sh=unary_union(L.poly(z['fills']['In2.Cu']));distance=sh.distance(body)
  if sh.is_empty or distance>.8:continue
  req=max(float(z['clearance_mm']),gap(z['net']),.15)+.025;row={'kind':'new_positive_to_current_foreign_fill','UID':z['uuid'],'raw_net':z['net'],'actual_gap_mm':distance,'required_mm':req};checks.append(row)
  if distance<req:errors.append(row)
 for z in q:
  if z['layer']!='In2.Cu'or L.norm(z['net'])==NET:continue
  for role in('shape','zone_outline_shape'):
   distance=lit(z[role]).distance(body)
   if distance>.8:continue
   req=max(float(z['clearance_mm']),gap(z['net']),.15)+.025;row={'kind':'new_positive_to_owned_foreign_'+role,'UID':z['uuid'],'raw_net':z['net'],'actual_gap_mm':distance,'required_mm':req};checks.append(row)
   if distance<req:errors.append(row)
 put(O/'all-new-positive-true-cap-foreign-fill-peer-role-checks.json',checks);put(O/'new-true-geometry-errors.json',errors);print('R545 truegeometry',len(checks),len(errors),flush=True)
 text=D.read_text(encoding='utf-8');rules=[]
 for name,cond,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',text):
  if'zone'not in what.split():continue
  names=re.findall(r"A.intersectsArea\('([^']+)'\)",cond);assert len(names)==1;area=next(a for a in h['rule_areas']if a.get('name')==names[0]);rules.append((name,area,re.findall(r"A.NetName != '([^']+)'",cond)))
 rules.extend((a.get('name',a['uuid']),a,[])for a in h['rule_areas']if a.get('no_zones'));nozone=[];count=0
 for z in q:
  for name,area,exempt in rules:
   if z['layer']not in area['layers']or z['net']in exempt:continue
   ar=unary_union(L.poly(area['outline']))
   for role in('shape','zone_outline_shape'):
    count+=1;hit=lit(z[role]).intersection(ar)
    if not hit.is_empty:nozone.append({'UID':z['uuid'],'role':role,'rule':name,'raw_net':z['net'],**sm(hit)})
 put(O/'all-generated-both-role-native-nozone-errors.json',nozone)
 ref=newrefs_by[FG]['In2.Cu'];rawgap=body.difference(ref);physicalbody=body.difference(unary_union([ctx[0][int(j)]for j in ctx[1].query(body,predicate='intersects')]));physicalgap=physicalbody.difference(ref);(O/'new-FIELD5-raw-DC-body-source-ground-reference-gap.wkb').write_bytes(rawgap.wkb);(O/'new-FIELD5-actual-drilled-DC-body-source-ground-reference-gap.wkb').write_bytes(physicalgap.wkb)
 (O/'actual-drilled-current-groups.pkl').write_bytes(pickle.dumps(now,protocol=5));bad=losses or directbad or refbad or errors or nozone or missing or any(r['prior_source_keys_lost']for r in sources)or any(not r['actual_L11003_2_source_rooted_after']for r in ownmoves)
 put(O/'receipt.json',{'status':'FIELD5_SOURCE_LAYER_CAUSE_REPAIR_HOST_CONTACT_SOURCE_OLDREF_TRUE_GEOMETRY_NOZONE_PASS_CURRENT_NEW_RETURN_NATIVE_OPEN'if not bad else'FIELD5_SOURCE_LAYER_REDESIGN_HOST_REPAIR_REQUIRED','model_SHA256':sha(M),'exact_before_R515_SHA256':sha(P),'cached_baseline_physical_graph_net_count':cached_count,'fresh_changed_net_count':2,'complete_compared_graph_net_count':len(old),'exhaustive_actual_net_count':len(nets),'unchanged_nets_certified_by_exact_full_native_discrete_hole_fill_identity':len(exact),'old_physical_relationship_losses':losses,'direct_old_owned_FG_native_contact_count':len(direct),'direct_old_owned_FG_native_contact_losses':directbad,'all_ten_prior_source_key_loss_count':sum(len(r['prior_source_keys_lost'])for r in sources),'FIELD5_nine_target_pads_missing':missing,'IO3_current_all_original_arrays_exact':True,'old_reference_delta_losses':refbad,'new_true_geometry_check_count':len(checks),'new_true_geometry_errors':errors,'all_generated_both_role_nozone_check_count':count,'native_nozone_errors':nozone,'new_FIELD5_DC_raw_full_body_ground_reference_gap':sm(rawgap),'new_FIELD5_DC_actual_drilled_body_ground_reference_gap':sm(physicalgap),'DC_power_classification_not_a_fabricated_MAP_or_loop_qualification':True,'full_FIELD5_A':.341130981,'FIELD5_reservation_A':.36,'FAG_full_signed_source_return_A':4.58442937244,'positive_sheet_barrel_drop_FAG_current_redistribution_loop_thermal_CPP_fill_DRC':'OPEN','old_R15528refs_CORE_ROOT42_planner_FAIL_OPEN_R525_537_539_541_FAILURES_retained':True,'native_jobs':0,'adopted':False,'actual_current_groups_SHA256':sha(O/'actual-drilled-current-groups.pkl'),'elapsed_seconds':time.monotonic()-st});print('R545',sha(O/'receipt.json'),'PASS',not bad,'newDCgap',physicalgap.area,flush=True)
if __name__=='__main__':main()
