"""Withdraw two unaccepted reference-cutting additions and trim one owned margin."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for p in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/p))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import physical_reference_losses_r1 as REF
from audit_field_io3_crossings_r15e import losses
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def main():
 bp=H/'corrected-joint-ground-base-r11/model.pkl';mp=H/'logic-source-union-reuse-return-restoration-r18/model.pkl';nativebound=H/'field-power/corrected-regulated-native-bound-search-base-r111/model.pkl';out=H/'safe-logic-five-and-fag-margin-r22'
 assert sha(bp)=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8' and sha(mp)=='20ae7a0558877ba76300f2163b920c77fe96c5861a930fb7b22570f665ad37b8' and sha(nativebound)=='722fae195cecfcfa07729dd243c2d74a0a0088e672582363265a2c15553db4d8' and not out.exists()
 g,h,b,z,failed=pickle.loads(mp.read_bytes());_,bh,bb,bz,before=pickle.loads(bp.read_bytes());ng,nh,nb,nz,ncurrent=pickle.loads(nativebound.read_bytes());assert g==ng and h==bh==nh
 withdrawn={'1bd97ebc-5412-519e-9cd2-15f4ce38846d','87644989-0ce6-5fef-b623-b5205f619109'};adds=pickle.loads(mp.with_name('proposed-zones.pkl').read_bytes());assert withdrawn<={q['uuid']for q in adds}
 out.mkdir();(out/'withdrawn-unaccepted-logic-zones.pkl').write_bytes(pickle.dumps([q for q in adds if q['uuid']in withdrawn],protocol=5));final=[copy.deepcopy(q)for q in z if q['uuid']not in withdrawn]
 target=next(q for q in final if q['uuid'].startswith('d5e1a664-'));records,_=F.build({**h,'zones':[]});pad=next(q for q in records['In2.Cu']if q['kind']=='pad'and q['uuid'].startswith('600473a0-'))
 assert target['net']!=pad['net'];need=max(.6,float(target.get('clearance_mm',.15)))+.025;prior=copy.deepcopy(target);oldgap=target['shape'].distance(pad['shape']);assert oldgap<need and need-oldgap<.000006
 cutter=N.bounded_buffer(pad['shape'],need+.000020);target['shape']=set_precision(target['shape'].difference(cutter),1e-6);target['zone_outline_shape']=set_precision(prior.get('zone_outline_shape',prior['shape']).difference(cutter),1e-6);newgap=target['shape'].distance(pad['shape']);assert newgap>=need
 for key in ('shape','zone_outline_shape'):
  oldshape=prior.get(key,prior['shape']);assert target[key].difference(oldshape).area==0;(out/(target['uuid']+'-'+key+'-removed.wkb')).write_bytes(oldshape.difference(target[key]).wkb)
 ledger={'owned_new_zone_uuid':target['uuid'],'foreign_pad_uuid':pad['uuid'],'layer':'In2.Cu','old_gap_mm':oldgap,'required_mm':need,'extra_construction_guard_mm':.000020,'new_gap_mm':newgap,'original_native_or_old_Cu_changes':0,'before_physical_sha256':hashlib.sha256(prior['shape'].wkb).hexdigest(),'after_physical_sha256':hashlib.sha256(target['shape'].wkb).hexdigest(),'removed_area_mm2':prior['shape'].difference(target['shape']).area}
 write(out/'owned-margin-correction.json',ledger);(out/'owned-margin-replacement.pkl').write_bytes(pickle.dumps(target,protocol=5));print('R22_PROJECT_SAFE_FIVE_AND_ONE_MARGIN',flush=True)
 after,retreat=N.projected(g,h,final);groups={};sources=[];refs=[];contactrows=[]
 nets=sorted({C.norm(q['net'])for q in before['zones']}|{C.norm(q['net'])for q in after['zones']})
 for net in nets:
  a=F.graph(before,net);n=F.graph(after,net);bad=losses(a,n);groups[net]=n;contactrows.append({'net':net,'prior_R11_discrete_losses':bad});write(out/'contact-checkpoint.json',contactrows);print('R22_CONTACT',net,len(bad),flush=True)
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  root=lambda xs:next(q for q in xs if any(a['kind']=='pad'and(a['ref'],a['pin'])==(ref,'2')for a in q));a=root(F.graph(before,net));n=root(groups[net]);lost=F.discrete_keys(a)-F.discrete_keys(n);sources.append({'net':net,'actual_source':ref+'.2','prior_source_keys_lost':[list(k)for k in sorted(lost)],'source_rooted_named_pads':len({q['uuid']for q in n if q['kind']=='pad'and q['pin']})})
  oldref={o:unary_union([q['shape']for q in a if q['kind']=='fill'and q['layer']==l])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newref={o:unary_union([q['shape']for q in n if q['kind']=='fill'and q['layer']==l])for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,diag=REF.audit(before,oldref,newref,net);refs.append({'net':net,'retained_outer_reference_losses':bad,'proof':diag});write(out/'reference-checkpoint.json',refs);print('R22_SOURCE_REF',net,len(lost),len(bad),sources[-1]['source_rooted_named_pads'],flush=True)
 b=copy.deepcopy(nb);b['root_R22_owned_logic_subset']={'failed_R18_model_sha256':sha(mp),'R20_independent_failure_receipt_sha256':sha(H/'logic-seven-independent-incremental-r20/receipt.json'),'withdrawn_only_two_unaccepted_new_zone_UUIDs':sorted(withdrawn),'retained_five_new_logic_zone_UUIDs':[q['uuid']for q in adds if q['uuid']not in withdrawn],'margin_correction_sha256':sha(out/'owned-margin-correction.json'),'canonical_native_binding_parent_sha256':sha(nativebound)}
 model=out/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,final,after),protocol=5));(out/'proposed-zones.pkl').write_bytes(pickle.dumps([q for q in adds if q['uuid']not in withdrawn],protocol=5));(out/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));ok=not any(r['prior_R11_discrete_losses']for r in contactrows)and not any(r['prior_source_keys_lost']for r in sources)and not any(r['retained_outer_reference_losses']for r in refs)
 write(out/'receipt.json',{'verdict':'PASS_SAFE_FIVE_LOGIC_AND_EXPLICIT_FAG_MARGIN_HOST_SOURCE_REFERENCE_CONTACT_NATIVE_CURRENT_OPEN'if ok else'FAIL_SAFE_SUBSET_CONTACT_SOURCE_REFERENCE','model_sha256':sha(model),'proposed_zones_sha256':sha(out/'proposed-zones.pkl'),'baseline_model_sha256':sha(bp),'failed_R18_model_sha256':sha(mp),'withdrawn_new_UUIDs':sorted(withdrawn),'only_new_owned_shape_changes':True,'original_Cu_holes_source_poses_native_outlines_exact':True,'canonical_native_binding_R111':True,'actual_source_retention':sources,'old_contacts':contactrows,'reference_checkpoint_sha256':sha(out/'reference-checkpoint.json'),'owned_margin_correction':ledger,'bank_projection_operator':'UNCHANGED_GP58_FRESH_FULL_ALLNET','full_projection_retreats':retreat,'all_analytic_original198b_dc936_fullsource_current_mesh_native_DRC_gates':'OPEN','script_sha256':sha(__file__),'native_jobs':0,'board_written':False,'adopted':False})
 print('R22_COMPLETE',ok,sha(model),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
