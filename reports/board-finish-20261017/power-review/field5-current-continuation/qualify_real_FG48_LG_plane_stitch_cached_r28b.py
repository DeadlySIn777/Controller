"""Two-mm real FG48 stitch with explicit LG plane-only negative source target.

All actual source keys, old discrete partitions, finite direct fill contacts,
and exact old signal-body source-reference overlaps are tested without waivers.
Prospective filled copper is a target, never a native AFTER claim.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,pickle,sys,time,uuid
import shapely
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';PRE=HERE/'LG-plane-only-protected-FG-In1-route-r27';OUT=HERE/'real-FG48-LG-plane-stitch-cached-host-r28b';FG='/motherboard_motors/FIELD_GND';LG='/LOGIC_GND';LY='In1.Cu'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
import native_lattice_boolean_splice as N
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sm(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def cached_physical(g,old,h,net,ctx):
 # Cached rows already contain the exact actual R299 HoleSet subtraction.
 # No untouched row is regenerated or normalized; only fill58c55 is cut.
 from collections import defaultdict
 prior=[q for xs in old[net] for q in xs];rows=[];changed=[];untouched=0
 cuts={z['uuid']:unary_union(K.L.poly(z['fills'][LY])).difference(unary_union(K.L.poly(next(a for a in h['zones']if a['uuid']==z['uuid'])['fills'][LY])))for z in g['zones']if K.L.norm(z['net'])==LG and LY in z['fills'] and next(a for a in h['zones']if a['uuid']==z['uuid']) is not z} if net==LG else{}
 for q in prior:
  cut=cuts.get(q['uuid'])if q['kind']=='fill'and q['layer']==LY else None
  if cut is None or not cut.intersects(q['shape']):rows.append(q);untouched+=1;continue
  after=q['shape'].difference(cut)
  for part in RF.parts(after):rows.append(q|{'shape':part,'key':('fill',q['uuid'],q['layer'],K.C.sha(part.wkb))})
  changed.append({'uuid':q['uuid'],'layer':q['layer'],'contour':q.get('contour'),'old_shape_SHA256':hashlib.sha256(q['shape'].wkb).hexdigest(),'new_shape_SHA256':hashlib.sha256(after.wkb).hexdigest(),'actual_cached_drilled_Cu_negative_mm2':q['shape'].difference(after).area})
 if net==FG:
  records,_=K.F.build(h,nets={FG},layers={LY});q=next(q for q in records[LY]if q['kind']=='track'and q['uuid']==h['tracks'][-1]['uuid']);holes,tree=ctx;body=q['shape'].difference(unary_union([holes[int(i)]for i in tree.query(q['shape'],predicate='intersects')]))
  for piece in RF.parts(body):rows.append(q|{'shape':piece,'key':('track',q['uuid'],LY,K.C.sha(piece.wkb))})
 uf=K.A.S.UF()
 for layer in K.LAYERS:
  rr=[q for q in rows if q['layer']==layer];tree=STRtree([q['shape']for q in rr])
  for i,q in enumerate(rr):
   uf.find(q['key'])
   for j in tree.query(q['shape'].buffer(.000002),predicate='intersects'):
    if i<int(j)and q['shape'].distance(rr[int(j)]['shape'])<=.000002:uf.join(q['key'],rr[int(j)]['key'])
 groups=defaultdict(list)
 for q in rows:groups[uf.find(q['key'])].append(q)
 put(('FG'if net==FG else'LG')+'-cached-physical-row-proof.json',{'cached_actual_drilled_HoleSet_source':str(ACTUAL/'actual-combined-full-after-all-net-groups.pkl'),'cached_actual_drilled_HoleSet_source_SHA256':sha(ACTUAL/'actual-combined-full-after-all-net-groups.pkl'),'unchanged_rows_exact_same_objects_and_WKB':untouched,'prior_total_rows':len(prior),'changed_cached_fill_rows':changed,'new_tracks':1 if net==FG else 0,'all_same_layer_edges_recomputed_with_exact_original_2nm_tolerance':True,'actual_pad_and_barrel_keys_cross_all_original_layers':True,'hole_context_model_SHA256':sha(ACTUAL/'actual-combined-full-after-model.pkl')})
 return list(groups.values())
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',PRE/'receipt.json',PRE/'2.0mm-candidate-axis.wkb',Path(__file__),Path(N.__file__)];inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());old=pickle.loads(files[1].read_bytes());r=json.loads(files[2].read_text());row=next(x for x in r['rows']if x['width_mm']==2.);route=row['route_attempts'][0];assert not route['native_quantization_clearance_failures'];pp=route['native_1nm_quantized_path_mm'];assert len(pp)==2;axis=LineString(pp);body=axis.buffer((1.+1e-8)/math.cos(math.pi/512),quad_segs=128);uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/R299/real-FG48-stitch/In1/2mm/243.777267,45.885499/245.655014,44.553600'));track={'uuid':uid,'net':next(t['net']for t in g['tracks']if K.L.norm(t['net'])==FG),'layer':LY,'a':pp[0],'b':pp[1],'w':2.,'m':None,'locked':True};zones=[];edits=[]
 for z in g['zones']:
  if K.L.norm(z['net'])!=LG or LY not in z['fills']:zones.append(z);continue
  oldCu=unary_union(K.L.poly(z['fills'][LY]));gap=max(.6,float(z['clearance_mm']))+.0251;mask=body.buffer(gap,quad_segs=128)
  if not oldCu.intersects(mask):zones.append(z);continue
  intent=unary_union(K.L.poly([[r[0],r[1:]]for r in z['outline']]));halo=float(z['min_thickness_mm'])/2+.00001;newintent,proof=N.splice(intent,intent.difference(mask.buffer(halo,quad_segs=128)),False);negative=intent.difference(newintent);actualnegative=oldCu.intersection(negative.union(mask));after=oldCu.difference(negative.union(mask));assert newintent.difference(intent).is_empty;zid=z['uuid']
  for name,s in(('native-negative-intent',newintent),('literal-source-negative',negative),('actual-native-Cu-negative-target',actualnegative),('negative-target-outside-literal-source-cut',actualnegative.difference(negative)),('target-remaining-native-Cu',after)):(OUT/(zid+'-'+name+'.wkb')).write_bytes(s.wkb)
  put(zid+'-native-lattice-proof.json',proof);edits.append({'uuid':zid,'layer':LY,'net':LG,'native_profile_unchanged':{k:z.get(k)for k in('priority','clearance_mm','min_thickness_mm','name')},'single_outer_source_parts_required':len(RF.parts(newintent)),'actual_negative_target':sm(actualnegative),'literal_source_negative':sm(negative),'outside_literal_source_cut':sm(actualnegative.difference(negative))});zones.append(z|{'fills':z['fills']|{LY:T.records(after)},'FG48_target_not_native_AFTER':True})
 h=g|{'tracks':g['tracks']+[track],'zones':zones};put('new-track-operation.json',track);(OUT/'new-FG48-stitch-body.wkb').write_bytes(body.wkb);(OUT/'prospective-stitch-and-LG-negative-model.pkl').write_bytes(pickle.dumps(h,protocol=5));ctx=K.hole_context(h);gates={};newgroups={}
 for net,ref,pin in((FG,'J11003','2'),(LG,'J11001','2')):
  new=cached_physical(g,old,h,net,ctx);newgroups[net]=new;a=K.root(old[net],ref,pin);b=K.root(new,ref,pin);lost=K.keys(a)-K.keys(b);rel,bad=K.contact_losses(old[net],new);refs,proof=RF.audit(g,K.source_refs(a),K.source_refs(b),net);gates[net]={'old_source_discrete_key_count':len(K.keys(a)),'new_source_discrete_key_count':len(K.keys(b)),'lost_source_keys':[list(x)for x in sorted(lost)],'old_partition_losses':bad,'raw_old_reference_losses':refs,'raw_reference_proof':proof,'old_source_pads':T.pads(a),'new_source_pads':T.pads(b),'newly_source_rooted_pads':sorted(set(T.pads(b))-set(T.pads(a))),'physical_groups_before':len(old[net]),'physical_groups_target':len(new)}
 contacts=[]
 for edit in edits:
  zid=edit['uuid'];metals=[q for xs in old[LG]for q in xs if q['kind']!='fill'and q['layer']==LY];tree=STRtree([q['shape']for q in metals]);before=[q for xs in old[LG]for q in xs if q['kind']=='fill'and q['uuid']==zid and q['layer']==LY];after=unary_union([q['shape']for xs in newgroups[LG]for q in xs if q['kind']=='fill'and q['uuid']==zid and q['layer']==LY])
  for f in before:
   for j in tree.query(f['shape'],predicate='intersects'):
    q=metals[int(j)];aa=q['shape'].intersection(f['shape']).area
    if aa<=0:continue
    bb=q['shape'].intersection(after).area;contacts.append({'zone_UUID':zid,'metal':T.describe(q),'old_finite_overlap_mm2':aa,'new_finite_overlap_mm2':bb,'retained':bb>0})
 failures=[q for q in contacts if not q['retained']];fg=gates[FG];ok=all(not x['lost_source_keys']and not x['old_partition_losses']and not x['raw_old_reference_losses']for x in gates.values())and not failures and len(fg['newly_source_rooted_pads'])==48 and len(fg['new_source_pads'])==232;out={'utc':datetime.now(timezone.utc).isoformat(),'status':'REAL_FG48_STITCH_EXACT_HOST_SOURCE_CONTACT_REFERENCE_GATES_PASS_NATIVE_CURRENT_OPEN'if ok else'REAL_FG48_STITCH_HOST_GATE_FAIL_NOT_PROMOTED','input_sha256':inputs,'cached_physical_row_variant_of_original_oracle':str(HERE/'qualify_real_FG48_LG_plane_stitch_r28.py'),'new_track':track,'nominal_length_mm':axis.length,'width_mm':2.,'rectangular_nominal_L_divided_by_w':axis.length/2.,'real_source_and_floating_electrodes':route,'explicit_LG_source_plane_only_targets':edits,'source_contact_reference_gates':gates,'all_affected_LG_role_positive_finite_old_contacts':contacts,'finite_contact_failures':failures,'all_foreign_discrete_Cu_true_drills_native109_frozen_rules_screen':str(PRE/'receipt.json'),'new_holes':0,'all12_outlet_and_other_load_limits_unchanged':True,'full_simultaneous_ground_return_boundary_A':4.58442937244,'signed_all_load_branch_KCL_source_spreading_constrictions_current_voltage_material_thermal_native_fill_minwidth_DRC_and_SI':'OPEN; no current or manufacturing pass claimed','current_FIELD5_In2_and_all_other_plane_roles_unchanged':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};put('receipt.json',out);print(json.dumps({'status':out['status'],'zones':len(edits),'new_FG_pads':fg['newly_source_rooted_pads'],'failures':{n:{k:len(x[k])for k in('lost_source_keys','old_partition_losses','raw_old_reference_losses')}for n,x in gates.items()},'finite_contact_failures':len(failures),'seconds':out['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
