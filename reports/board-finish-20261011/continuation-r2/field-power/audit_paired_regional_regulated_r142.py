"""Paired full regional projection, all-zone-net contacts and source references."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
from audit_field_io3_crossings_r15e import losses
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'));sys.path.insert(0,str(H.parent/'coupled-recovery'))
import regional_guarded_declared_projection_r140 as P
import physical_reference_losses_r1 as REF
from regulated_outer_joins_r51 import PORTS
O=H/'paired-regional-six-regulated-full-contact-audit-r142'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();oldp=H.parent/'safe-logic-five-and-fag-margin-r22';newp=H/'safe-root22-regulated-source-contact-audit-r130';assert sha(oldp/'model.pkl')=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a' and sha(newp/'model.pkl')=='c9454c9ab38a87c23eb16c33c05cda5f10237627c4986ab1e052296859ad342b';heads=[];primitive_rows=[];baseline_reprojection=[]
 for label,base in [('ROOT_R22',oldp),('REG_R130',newp)]:
  g,h,b,z,global_saved=pickle.loads((base/'model.pkl').read_bytes());print('R142 full regional',label,flush=True);after,cuts=P.projected(g,h,z);oldcuts=json.loads((base/'receipt.json').read_text())['full_projection_retreats'] if label=='ROOT_R22' else json.loads((base/'oldfill-retreats.json').read_text());om={(q['zone_uuid'],q['layer']):q for q in oldcuts};cm={(q['zone_uuid'],q['layer']):q for q in cuts};allkeys=set(om)|set(cm)
  for key in sorted(allkeys):
   aa=om.get(key,{}).get('cutters',[]);bb=cm.get(key,{}).get('cutters',[]);primitive_rows.append({'label':label,'original_zone_UUID':key[0],'layer':key[1],'every_relevant_outward_cutter_row_unchanged':aa==bb})
  (O/(label+'-regional-model.pkl')).write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));write(O/(label+'-regional-retreats.json'),cuts);heads.append((g,h,b,z,after));write(O/'cutter-primitive-checkpoint.json',primitive_rows)
  oldzones={q['uuid']:q for q in global_saved['zones']}
  for q in after['zones']:
   if q['uuid'] not in oldzones:continue
   for l,records in q['fills'].items():
    aa=unary_union(C.poly(oldzones[q['uuid']]['fills'].get(l,[])));bb=unary_union(C.poly(records));lost=aa.difference(bb).area;added=bb.difference(aa).area
    if lost or added:baseline_reprojection.append({'label':label,'zone_uuid':q['uuid'],'layer':l,'global_to_regional_removed_mm2':lost,'global_to_regional_added_mm2':added,'old_sha256':P.digest(aa),'regional_sha256':P.digest(bb)})
 before,after=heads[0][4],heads[1][4];nets=sorted({C.norm(q['net']) for q in before['zones']}|{C.norm(q['net']) for q in after['zones']});assert len(nets)==76;oldgroups={};newgroups={};rows=[]
 for net in nets:
  aa=F.graph(before,net);bb=F.graph(after,net);oldgroups[net]=aa;newgroups[net]=bb;bad=losses(aa,bb);rows.append({'net':net,'regional_R22_old_discrete_losses':bad,'old_groups':len(aa),'new_groups':len(bb)});print('R142 contact',net,'loss',len(bad),flush=True);write(O/'contact-checkpoint.json',rows)
 sources=[];refs=[];reg=[]
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));aa,bb=root(oldgroups[net]),root(newgroups[net]);lost=F.discrete_keys(aa)-F.discrete_keys(bb);sources.append({'net':net,'actual_external_source':ref+'.2','regional_baseline_source_keys_lost':[list(k) for k in sorted(lost)],'old_source_named_physical_pads':len({q['uuid'] for q in aa if q['kind']=='pad' and q['pin']}),'new_source_named_physical_pads':len({q['uuid'] for q in bb if q['kind']=='pad' and q['pin']})});oldref={out:unary_union([q['shape'] for q in aa if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newref={out:unary_union([q['shape'] for q in bb if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,diag=REF.audit(before,oldref,newref,net);refs.append({'ground':net,'regional_baseline_retained_outer_reference_losses':bad,'proof':diag});print('R142 source-ref',net,len(lost),len(bad),flush=True)
 for bank,net,ref,pin,policy in PORTS:
  gs=newgroups.get(net)
  if gs is None:gs=F.graph(after,net);newgroups[net]=gs
  root=next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));ri=next(i for i,xs in enumerate(gs) if xs is root);unroot=[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)];reg.append({'bank':bank,'actual_regulator_source':ref+'.'+pin,'all_named_loads_source_rooted':not unroot,'remaining_named_groups':unroot,'full_current_routing_reservation_A':policy})
 write(O/'contact-rows.json',rows);write(O/'source-rows.json',sources);write(O/'reference-rows.json',refs);write(O/'regulated-rows.json',reg);write(O/'cutter-primitive-rows.json',primitive_rows);write(O/'global-to-regional-reprojection.json',baseline_reprojection);(O/'ROOT_R22-regional-groups.pkl').write_bytes(pickle.dumps(oldgroups,protocol=5));(O/'REG_R130-regional-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));ok=all(q['every_relevant_outward_cutter_row_unchanged'] for q in primitive_rows) and not any(q['regional_R22_old_discrete_losses'] for q in rows) and not any(q['regional_baseline_source_keys_lost'] for q in sources) and not any(q['regional_baseline_retained_outer_reference_losses'] for q in refs);write(O/'receipt.json',{'verdict':'PAIRED_FULL_REGIONAL_CONTACT_SOURCE_REFERENCE_PASS' if ok else 'PAIRED_FULL_REGIONAL_REPAIR_REQUIRED','ROOT_R22_global_model_sha256':sha(oldp/'model.pkl'),'REG_R130_global_model_sha256':sha(newp/'model.pkl'),'ROOT_R22_regional_model_sha256':sha(O/'ROOT_R22-regional-model.pkl'),'REG_R130_regional_model_sha256':sha(O/'REG_R130-regional-model.pkl'),'ROOT_R22_regional_groups_sha256':sha(O/'ROOT_R22-regional-groups.pkl'),'REG_R130_regional_groups_sha256':sha(O/'REG_R130-regional-groups.pkl'),'all76_zone_nets_checked':len(nets),'relevant_cutter_primitive_rows':len(primitive_rows),'cutter_primitives_and_required_guards_unchanged':all(q['every_relevant_outward_cutter_row_unchanged'] for q in primitive_rows),'source_rows_sha256':sha(O/'source-rows.json'),'contact_rows_sha256':sha(O/'contact-rows.json'),'reference_rows_sha256':sha(O/'reference-rows.json'),'regulated_rows_sha256':sha(O/'regulated-rows.json'),'global_to_regional_reprojection_sha256':sha(O/'global-to-regional-reprojection.json'),'projector_file_sha256':sha(H/'regional_guarded_declared_projection_r140.py'),'global_failed_reference_results_preserved_not_waived':True,'root_independent_final_native_current_fault_barrel_drop_thermal_GATES':'OPEN','board_written':False,'native_jobs':0});print('R142 complete',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
