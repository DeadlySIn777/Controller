"""Two sparse diagnostic stages on exact R250, inherited failure retained.

Only new discrete primitives cut current native/owned filled records. Native
coordinates are never snapped; generated roles replay their bound operation
metadata. No global projection, whole stale overlay or native job is used.
"""
import copy,hashlib,json,pickle,sys,time,traceback,collections
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import physical_reference_losses_r3_zero_r208 as RF
O=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r261'
ROOTS=K.ROOTS+[('/mc_local_power/CORE_5V','R11022','2'),('/motherboard_motors/AUX_5V_B','U11014','6')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1,allow_nan=False)+'\n')
def records(s):return [[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in RF.parts(s)]
def zero(s):
 n=set_precision(s,0);assert n.wkb==s.wkb;return n
def cutters(items,removedbody,net,layer,local,h,outline=False):
 result=[];dom=h['domains_normalized'];gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6
 for x in items:
  via='d'in x;same=L.norm(x['net'])==L.norm(net)
  if via:
   if same:
    if outline:continue
    radius=x['drill']/2+.00000002;sh=Z.bounded_disk(x,radius);kind='new_same_net_physical_drill_only'
   else:
    radius=max(x['drill']/2+.275,x['d']/2+max(local,gap(x['net'],net))+.025)+.0001;sh=Z.bounded_disk(x,radius);kind='new_foreign_ordinary_Cu_hole_antipad'
  else:
   if x['layer']!=layer or same:continue
   body=Z.bounded_buffer(LineString([x['a'],x['b']]),x['w']/2);owned=removedbody.get((L.norm(x['net']),layer));novel=body.difference(owned)if owned is not None else body
   if novel.is_empty:continue
   radius=max(local,gap(x['net'],net))+.025+.0001;sh=Z.bounded_buffer(novel,radius);kind='new_track_only_novel_Cu_clearance'
  result.append({'new_UUID':x['uuid'],'kind':kind,'same_net':same,'radius_or_novel_body_clearance_mm':radius,'cut_WKB_sha256':dig(sh),'shape':zero(sh)})
 return result
def construct(stage,model,d,bound):
 P=O/stage;P.mkdir();g,h0,b0,q0,before=model;h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);put(P/'generated-operation-metadata-replay.json',PS.restore_bound_generated_precision_states(b,q));rm=set(d['removed_original_track_UUIDs']);old=[t for t in h['tracks']if t['uuid']in rm];assert len(old)==len(rm);h['tracks']=[t for t in h['tracks']if t['uuid']not in rm]+d['tracks'];h['vias']+=d['vias'];items=d['tracks']+d['vias'];oldbody={}
 for net,layer in {(L.norm(t['net']),t['layer'])for t in old}:oldbody[net,layer]=unary_union([Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)for t in old if(L.norm(t['net']),t['layer'])==(net,layer)])
 qmap={z['uuid']:z for z in q};roleledger=[];fail=[]
 for z in q:
  for role in('shape','zone_outline_shape'):
   oldsh=z[role];cc=cutters(items,oldbody,z['net'],z['layer'],float(z['clearance_mm']),h,role=='zone_outline_shape');active=[x for x in cc if x['shape'].intersects(oldsh)]
   if not active:continue
   cut=unary_union([x['shape']for x in active]);remaining=oldsh.difference(cut);gain=remaining.difference(oldsh)
   row={'UUID':z['uuid'],'role':role,'before_WKB_sha256':dig(oldsh),'after_WKB_sha256':dig(remaining),'operation_grid_mm':get_precision(remaining),'remove_only':gain.is_empty,'cuts':[{k:v for k,v in x.items()if k!='shape'}for x in active]};roleledger.append(row)
   if not gain.is_empty:fail.append({'kind':'generated_role_positive_gain','row':row,'gain_mm2':gain.area})
   z[role]=remaining
 for z in q:
  for role in('shape','zone_outline_shape'):
   restored=set_precision(z[role],1e-6,mode='pointwise')
   if restored.wkb!=z[role].wkb:fail.append({'kind':'new_generated_role_not_exact_canonical_nm','UUID':z['uuid'],'role':role})
 b['generated_precision_state_ledger']=[{'new_generated_UUID':z['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':dig(z[role])}for z in q for role in('shape','zone_outline_shape')];b['restored_generated_grid_UUIDs']=sorted(qmap);b['T4_R7_sparse_exploratory_diagnostic_delta']={'exact_root_R250_model_sha256':bound['root_model_sha256'],'stage':stage,'prior_stages_preserved':True,'inherited_new_CORE_fullbody_93p041959_mm2_FAIL_retained':True,'full_current_native_thermal_manufacturing':'OPEN'}
 out=[];filledledger=[];affected={L.norm(x['net'])for x in items}
 for z in before['zones']:
  nz=copy.deepcopy(z)
  for layer,rs in z['fills'].items():
   cc=cutters(items,oldbody,z['net'],layer,float(z['clearance_mm']),h);polys=L.poly(rs);assert len(polys)==len(rs);nr=[];steps=[];changed=False
   for i,(rec,p)in enumerate(zip(rs,polys)):
    active=[x for x in cc if x['shape'].intersects(p)]
    if not active:nr.append(copy.deepcopy(rec));continue
    changed=True;cut=unary_union([x['shape']for x in active]);raw=zero(p).difference(cut);extra=[]
    # Preserve literal positive-operation residues as failures; no hidden
    # snap, area threshold or unauthorized correction is performed.
    serialized=records(raw);rebuilt=unary_union(L.poly(serialized));gain=rebuilt.difference(p);withdrawal=p.difference(rebuilt).difference(cut);samepoly=rebuilt.equals(unary_union(RF.parts(raw)))
    row={'record':i,'before_WKB_sha256':dig(p),'after_WKB_sha256':dig(rebuilt),'strict_no_new_filled_Cu':gain.is_empty,'strict_withdrawal_within_exact_new_primitive_masks':withdrawal.is_empty,'serialized_exact_polygonal_remaining':samepoly,'cuts':[{k:v for k,v in x.items()if k!='shape'}for x in active]};steps.append(row)
    for role,sh in [('rawremaining',raw),('gain',gain),('extra-withdrawal',withdrawal)]:f=P/(z['uuid']+'-'+layer+'-'+str(i)+'-'+role+'.wkb');f.write_bytes(sh.wkb)
    if not(gain.is_empty and withdrawal.is_empty and samepoly):fail.append({'kind':'filled_record_exact_scope_or_gain_failure','UUID':z['uuid'],'layer':layer,**row})
    if rebuilt.equals(p):nr.append(copy.deepcopy(rec))
    else:nr.extend(serialized)
   if changed:
    a=unary_union(polys);n=unary_union(L.poly(nr));gained=n.difference(a);fullcut=unary_union([x['shape']for x in cc]);extra=a.difference(n).difference(fullcut);row={'UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'before_WKB_sha256':dig(a),'after_WKB_sha256':dig(n),'strict_no_reclaimed_Cu':gained.is_empty,'strict_only_new_primitive_withdrawal':extra.is_empty,'removed_mm2':a.difference(n).area,'record_operations':steps};filledledger.append(row);affected.add(L.norm(z['net']));nz['fills'][layer]=nr
    if not gained.is_empty or not extra.is_empty:fail.append({'kind':'whole_filled_scope_failure',**row})
  out.append(nz)
 after={**before,'tracks':h['tracks'],'vias':h['vias'],'zones':out};put(P/'exact-generated-role-new-antipad-ledger.json',roleledger);put(P/'exact-current-filled-record-new-primitive-ledger.json',filledledger);put(P/'strict-construction-failures.json',fail);put(P/'sparse-operation.json',{'removed_original_tracks':old,'new_tracks':d['tracks'],'new_vias':d['vias'],'no_footprint_pad_source_native_zone_definition_or_rule_changes':True,'source_binding':bound})
 if not fail:(P/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,after),protocol=5))
 put(P/'construction-receipt.json',{'verdict':'SPARSE_DIAGNOSTIC_CONSTRUCTOR_PASS_INHERITED_FAILURE_RETAINED'if not fail else'SPARSE_DIAGNOSTIC_STRICT_CONSTRUCTOR_FAIL_NO_MODEL_PROMOTION','source_binding':bound,'stage':stage,'strict_failures':fail,'model_sha256':sha(P/'model.pkl')if not fail else None,'only_new_primitives_no_global_projection':True,'native_coordinates_never_snapped':True,'inherited_new_CORE_wholebody_reference_gap_mm2':93.04195929171794,'inherited_new_CORE_reference_full_current_and_native_gates':'FAIL_OR_OPEN_RETAINED','native_jobs':0,'board_written':False,'adopted':False})
 print('R261_CONSTRUCT',stage,len(fail),len(filledledger),len(roleledger),flush=True)
 return P,(g,h,b,q,after),affected,rm,oldbody,fail
def audit(P,base,model,d,groups,affected,removed,oldbody):
 g,h0,b0,q0,before=base;ng,h,b,q,after=model;items=d['tracks']+d['vias'];newctx=K.hole_context(after);newholes=[Z.bounded_disk(v,v['drill']/2)for v in d['vias']];nets=set(groups);nets|={L.norm(z['net'])for z in before['zones']}|affected;newgroups={};contacts=[];bad=[];direct=[];directbad=[];changed={(r['UUID'],r['layer'])for r in json.loads((P/'exact-current-filled-record-new-primitive-ledger.json').read_text())}
 for net in sorted(nets):
  old=groups.get(net)
  if old is None:_,old=K.physical(before,net,K.hole_context(before))
  disjoint=all(not sh.intersects(r['shape'])for xs in old for r in xs for sh in newholes)
  if net not in affected and disjoint:new=old
  else:_,new=K.physical(after,net,newctx)
  newgroups[net]=new;rows,loss=K.contact_losses(old,new,removed);contacts.append({'net':net,'old_layer_relationship_losses':loss,'unchanged_geometry_new_holes_disjoint_reuse':net not in affected and disjoint});bad.extend({'net':net,**r}for r in loss)
  if net in affected:
   final=collections.defaultdict(list)
   for xs in new:
    for r in xs:
     if r['kind']=='fill':final[r['uuid'],r['layer']].append(r['shape'])
   for l in K.LAYERS:
    metal=[r for xs in old for r in xs if r['layer']==l and r['kind']!='fill'and r['uuid']not in removed];tree=STRtree([r['shape']for r in metal])
    for fill in(r for xs in old for r in xs if r['kind']=='fill'and r['layer']==l and(r['uuid'],l)in changed):
     for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
      r=metal[int(j)]
      if r['shape'].distance(fill['shape'])>.000002:continue
      hit=any(s.distance(r['shape'])<=.000002 for s in final[fill['uuid'],l]);row={'net':net,'UUID':fill['uuid'],'layer':l,'old_physical_layer_key':[r['kind'],r['uuid'],l],'same_zone_direct_actual_contact_retained':hit};direct.append(row)
      if not hit:directbad.append(row)
  put(P/'all-current-77-contact-progress.json',contacts);print('R261_CONTACT',P.name,net,len(loss),flush=True)
 sources=[];refs=[]
 for net,ref,pin in ROOTS:
  old=K.root(groups[net],ref,pin);new=K.root(newgroups[net],ref,pin);lost=sorted(k for k in K.keys(old)-K.keys(new)if not(k[0]=='track'and k[1]in removed));sources.append({'net':net,'source':ref+'.'+pin,'lost_retained_old_layer_keys':[list(k)for k in lost]})
  if ref in('J11001','J11003','J11005'):
   loss,proof=RF.audit(before,K.source_refs(old),K.source_refs(new),net,removed);refs.append({'ground':net,'strict_ZERO_old_signal_and_all_power_reference_losses':loss,'proof':proof})
 lg=K.root(newgroups['/LOGIC_GND'],'J11001','2');sr=K.source_refs(lg);bodyrefs=[]
 for t in d['tracks']:
  body=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);gap=body.difference(sr[t['layer']]);f=P/(t['uuid']+'-newfullbody-source-reference-gap.wkb');f.write_bytes(gap.wkb);bodyrefs.append({'UUID':t['uuid'],'net':t['net'],'layer':t['layer'],'actual_source_reference_gap_mm2':gap.area,'gap_empty':gap.is_empty,'gap_sha256':sha(f)})
 groundpads={pin:any(r['kind']=='pad'and(r['ref'],r['pin'])==('U1001',pin)for r in lg)for pin in('T1','T4','R7')};core=next(z for z in q if z['uuid']=='b0453302-df03-561f-9bc4-0560bc66658a');cg=core['shape'].difference(sr['In2.Cu']);(P/'inherited-new-CORE-fullbody-source-reference-gap.wkb').write_bytes(cg.wkb)
 rec,trees=F.build({**h,'zones':[]});filled={l:[]for l in K.LAYERS}
 for z in after['zones']:
  for l,rs in z['fills'].items():filled[l].extend({'UUID':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':sh}for sh in L.poly(rs))
 ft={l:STRtree([r['shape']for r in rows])for l,rows in filled.items()};dom=h['domains_normalized'];domain_gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6;checks=[];errors=[];planner=[];inherited=[]
 for x in items:
  via='d'in x;axis=Point(x['x'],x['y'])if via else LineString([x['a'],x['b']]);radius=x['d']/2 if via else x['w']/2;body=Z.bounded_buffer(axis,radius);old=oldbody.get((L.norm(x['net']),x.get('layer')));nov=body.difference(old)if old is not None else body
  for l in K.LAYERS if via else[x['layer']]:
   targets=[r for j in trees[l].query(body.buffer(.8),predicate='intersects')for r in[rec[l][int(j)]]]+[{'uuid':r['UUID'],'net':r['net'],'kind':'fill','shape':r['shape'],'local':r['local']}for j in ft[l].query(body.buffer(.8),predicate='intersects')for r in[filled[l][int(j)]]]
   for r in targets:
    if L.norm(r['net'])==L.norm(x['net']):continue
    bga=via and r['kind']=='pad'and r.get('ref')=='U1001';native=.125 if bga else max(domain_gap(x['net'],r['net']),r.get('local',0));req=native+.025
    if r['kind']=='track'and not r['source'].get('m'):t=r['source'];target=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);gap=axis.distance(LineString([t['a'],t['b']]))-radius-t['w']/2
    elif r['kind']=='via':v=r['source'];target=Z.bounded_disk(v,v['d']/2);gap=axis.distance(Point(v['x'],v['y']))-radius-v['d']/2
    else:target=r['shape'];gap=axis.distance(target)-radius
    novgap=nov.distance(target)if not nov.is_empty else float('inf');row={'new_UUID':x['uuid'],'other_UUID':r['uuid'],'kind':r['kind'],'layer':l,'actual_true_gap_mm':gap,'native_requirement_mm':native,'planner_requirement_mm':req,'U1001_existing_native_pad_via_predicate':bga,'novel_body_gap_mm':novgap,'unchanged_old_anchor_only':not via and gap<req and novgap>=req};checks.append(row)
    if gap<native and(via or novgap<native):errors.append(row)
    if gap<req and(via or novgap<req):planner.append(row)
    if row['unchanged_old_anchor_only']:inherited.append(row)
 smds=[(p,sh)for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree([sh for p,sh in smds]);holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ap=[]
 for v in d['vias']:
  p=Point(v['x'],v['y']);near=smds[int(st.nearest(p))];sm=p.distance(near[1])-v['drill']/2-.005;dr=min((p.distance(sh)-v['drill']/2-.005,uid)for uid,sh in holes if uid!=v['uuid']);pitch=min((p.distance(Point(w['x'],w['y'])),w['uuid'])for w in h['vias']if w['uuid']!=v['uuid']);row={'UUID':v['uuid'],'guarded_SMD_mm':sm,'nearest_SMD_UUID':near[0]['uuid'],'guarded_every_drill':dr,'ordinary_pitch':pitch};ap.append(row)
  if sm<.275 or dr[0]<.275 or pitch[0]<.815:errors.append({'kind':'ordinary_SMD_every_drill_pitch','row':row})
 put(P/'all-current-77-layer-contact-losses.json',bad);put(P/'all-old-direct-fill-layer-contact-losses.json',directbad);put(P/'nine-actual-source-banks.json',sources);put(P/'three-bank-strict-ZERO-old-references.json',refs);put(P/'new-fullbody-source-references.json',bodyrefs);put(P/'actual-native-effective-true-copper-checks.json',checks);put(P/'actual-native-effective-true-copper-errors.json',errors);put(P/'separate-extra-planner-reserve-failures.json',planner);put(P/'unchanged-original-anchor-deficits.json',inherited);put(P/'ordinary-SMD-drill-pitch.json',ap);(P/'actual-drilled-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5))
 incremental=not(bad or directbad or errors or any(r['lost_retained_old_layer_keys']for r in sources)or any(r['strict_ZERO_old_signal_and_all_power_reference_losses']for r in refs))
 result={'verdict':'DIAGNOSTIC_INCREMENTAL_CONTACT_SOURCE_REFERENCE_NATIVE_EFFECTIVE_PASS_INHERITED_CORE_BODY_AND_FULL_CURRENT_FAIL_OPEN_RETAINED'if incremental else'DIAGNOSTIC_INCREMENTAL_FAILURE_VISIBLE_NO_PROMOTION','all_current_net_count':len(nets),'actual_drilled_layer_contact_loss_count':len(bad),'direct_fill_contact_loss_count':len(directbad),'nine_source_layer_key_loss_count':sum(len(r['lost_retained_old_layer_keys'])for r in sources),'strict_ZERO_old_signal_and_PDN_reference_loss_count':sum(len(r['strict_ZERO_old_signal_and_all_power_reference_losses'])for r in refs),'new_native_effective_geometry_error_count':len(errors),'separate_extra_planner_deficit_count':len(planner),'full_planner_PASS':not planner,'new_track_fullbody_source_reference_gaps':bodyrefs,'actual_ground_source_membership':groundpads,'inherited_CORE_fullbody_source_reference_gap_mm2':cg.area,'inherited_CORE_wholebody_gate':'FAIL_RETAINED'if not cg.is_empty else'NO_GAP_IN_THIS_DIAGNOSTIC_SCOPE_FULL_CURRENT_STILL_OPEN','full_current_rail_return_pin_load_mesh_decoupling_fault_transient_thermal_and_actual_native':'OPEN_RETAINED','model_sha256':sha(P/'model.pkl')if(P/'model.pkl').exists()else None,'native_jobs':0,'board_written':False,'adopted':False};put(P/'receipt.json',result);print('R261_AUDIT',P.name,incremental,len(errors),len(bad),len(directbad),len(planner),cg.area,sha(P/'receipt.json'),flush=True)
 return newgroups,result
def main():
 assert not O.exists();O.mkdir();mp=H/'coupled-recovery/CORE-R112-per-polygon-immutable-owned-construction-r250/model.pkl';assert sha(mp)=='96d3f55a95b770a2a7f46e3b25274723946fe1572c6c82d81b7355b660360868';rp=H/'coupled-recovery/CORE-R250-vs-actual-R214-independent-r252/receipt.json';assert sha(rp)=='db5c57276f9dfc385b8a195daa178d36af296a3be24b226370c936d2442df560';r=json.loads(rp.read_text());assert not r['true_all6_geometry_errors']and not r['all77_actual_drilled_contact_losses']and not r['direct_actual_original_layer_fill_contact_losses']and r['nine_prior_source_bank_layer_key_loss_count']==r['three_bank_strict_ZERO_retained_reference_loss_count']==0;model=pickle.loads(mp.read_bytes());gp=rp.parent/'actual-drilled-groups.pkl';assert sha(gp)==r['output_files_sha256'][str(gp.resolve())];groups=pickle.loads(gp.read_bytes());bound={'root_model_sha256':sha(mp),'independent_incremental_receipt_sha256':sha(rp),'overall_root_verdict':r['verdict'],'root_failed_CORE_body_gap_mm2':r['new_CORE_fullbody_actual_J1_reference']['actual_J1_In1_full_reference_gap_mm2']};put(O/'exact-diagnostic-authority-binding.json',bound)
 for stage,dp in[('T4-only',H/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r256/proposed-discrete.pkl'),('T4-plus-R7',H/'sbc-power/R7-NW-fullwidth-two-B-trunk-detour-nominations-r259/first-nominee-discrete.pkl')]:
  d=pickle.loads(dp.read_bytes());source={**bound,'discrete_delta_path':str(dp.resolve()),'discrete_delta_sha256':sha(dp)};P,current,affected,rm,oldbody,fail=construct(stage,model,d,source)
  if fail:print('R261_STOP_STRICT_CONSTRUCTION_FAILURE',stage,flush=True);break
  groups,result=audit(P,model,current,d,groups,affected,rm,oldbody);model=current
  if result['verdict'].startswith('DIAGNOSTIC_INCREMENTAL_FAILURE'):print('R261_STOP_INCREMENTAL_FAILURE',stage,flush=True);break
 print('R261_COMPLETE',flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
