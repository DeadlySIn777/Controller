"""Prove untouched-net physical identity and recompute the affected old refs."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
F,L,RF=K.F,K.L,K.RF
OUT=H/'U10003-R196-unchanged-net-physical-identity-and-strict-oldrefs-r199'
FG='/motherboard_motors/FIELD_GND';FLT='/motherboard_do/DOA_FLT_N_FIELD';CLK='/motherboard_do/DOA_SCLK_FIELD';affected={FG,FLT,CLK}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def main():
 assert not OUT.exists();OUT.mkdir();bp=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';proof=H/'U10003-compliant-clock-fault-ground-independent-drilled-source-geometry-r197/receipt.json'
 assert sha(bp)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'and sha(mp)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5'and sha(proof)=='ae56bcd589964506e95f251d8a2be9c0f9563db32f28923ffbbf9829f71b580d'
 p=json.loads(proof.read_bytes());assert p['geometry_source_contact_scope_pass']
 g,h0,b0,q0,before=pickle.loads(bp.read_bytes());ng,h,b,q,after=pickle.loads(mp.read_bytes());assert ng==g
 for name in h0:
  if name not in('tracks','vias'):assert h[name]==h0[name],('unchanged_header',name)
 oldv={v['uuid']:v for v in h0['vias']};assert all(next(v for v in h['vias']if v['uuid']==u)==v for u,v in oldv.items())
 for kind in('tracks','vias'):
  a=[x for x in h0[kind]if L.norm(x['net'])not in affected];bb=[x for x in h[kind]if L.norm(x['net'])not in affected];assert a==bb,kind
 oldq={x['uuid']:x for x in q0};newq={x['uuid']:x for x in q}
 for uid,x in oldq.items():
  if L.norm(x['net'])in affected:continue
  y=newq[uid];assert all(x[r].wkb==y[r].wkb for r in('shape','zone_outline_shape'));assert {k:v for k,v in x.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in y.items()if k not in('shape','zone_outline_shape')}
 oldz={x['uuid']:x for x in before['zones']};newz={x['uuid']:x for x in after['zones']}
 for uid,x in oldz.items():
  if L.norm(x['net'])not in affected:assert newz[uid]==x,('unchanged_actual_filled_records',uid)
 assert all(L.norm(z['net'])==FG for uid,z in newz.items()if uid not in oldz)
 records,trees=F.build(before);hole_contacts=[];newvia=[v for v in h['vias']if v['uuid']not in oldv]
 for v in newvia:
  hole=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
  for layer in h['copper_layers']:
   for j in trees[layer].query(hole,predicate='intersects'):
    r=records[layer][int(j)]
    if L.norm(r['net'])in affected:continue
    witness=r['shape'].intersection(hole)
    if not witness.is_empty:hole_contacts.append({'new_hole':v['uuid'],'old_kind':r['kind'],'old_UUID':r['uuid'],'net':r['net'],'layer':layer,'literal_overlap_area_mm2':witness.area})
 print('R199_UNCHANGED_METADATA_FILL_NEW_HOLES',len(hole_contacts),flush=True);put(OUT/'new-drill-intersections-with-untouched-net-Cu.json',hole_contacts)
 contexts=[K.hole_context(x)for x in(before,after)];_,og=K.physical(before,FG,contexts[0]);_,ag=K.physical(after,FG,contexts[1]);oldroot=K.root(og,'J11003','2');newroot=K.root(ag,'J11003','2');oldrefs=K.source_refs(oldroot);newrefs=K.source_refs(newroot);receipt=json.loads(mp.with_name('receipt.json').read_bytes());removed=receipt['seven_exact_original_track_replacements']
 rows,stats=RF.audit(h0,oldrefs,newrefs,FG,removed);direct=[];oldtracks={t['uuid']:t for t in h0['tracks']}
 for row in rows:
  t=oldtracks[row['uuid']];body=K.A.shape({'kind':'segment',**t})if not t.get('m')else L.body(t);loss=body.intersection(oldrefs[t['layer']]).difference(newrefs[t['layer']]);row['original_direct_formula_loss_mm2']=loss.area;row['original_direct_formula_empty']=loss.is_empty
  if not loss.is_empty:direct.append(row);(OUT/(row['uuid']+'-direct-old-reference-loss.wkb')).write_bytes(loss.wkb)
 put(OUT/'strict-affected-ground-old-reference-raw-rows.json',rows);put(OUT/'strict-affected-ground-old-reference-direct-rows.json',direct)
 untouched=sorted({L.norm(x['net'])for kind in('tracks','vias','pads','zones')for x in before.get(kind,[])if L.norm(x['net'])not in affected});ok=not hole_contacts and not direct
 result={'verdict':'UNCHANGED_OTHER_NET_PHYSICS_AND_AFFECTED_OLD_REFERENCE_SCOPE_PASS_NEW_BODY_NATIVE_CURRENT_OPEN'if ok else'FAIL_UNTOUCHED_NET_DRILL_OR_STRICT_OLD_REFERENCE','model_sha256':sha(mp),'base_sha256':sha(bp),'scoped_three_net_geometry_contact_source_receipt_sha256':sha(proof),'untouched_net_count':len(untouched),'all_untouched_original_Cu_FP_masks_actual_fill_arrays_and_generated_WKB_exact':True,'new_drill_intersections_with_untouched_Cu':hole_contacts,'untouched_physical_graphs_identical_by_exact_Cu_metadata_and_hole_disjointness':not hole_contacts,'actual_old_ground_source_reference_raw_delta_rows':len(rows),'actual_original_direct_old_reference_loss_rows':len(direct),'old_reference_stats':stats,'new_body_reference_raw_and_drilled_failures_retained':True,'native_fullactualsourceflash_connectivity_current_thermal_electrical_SI_and_manufacturing':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False};put(OUT/'receipt.json',result);print('R199_COMPLETE',ok,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
