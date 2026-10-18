"""Conservative physical support test for corrected integer intended outlines."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from inventory import sha
H=Path(__file__).resolve().parent
for name in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/name))
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
R=H/'REG-two-native-intents-literal-gain-correction-r302';B=H/'R54-native-wider-IO3-monitor-joint-audit-r214';O=H/'REG-physical-support-inside-corrected-native-intents-r304';IDS={'d8d8bdad-3845-5659-b172-4d0e231cdadc','ed7b6af5-93e5-5f20-8977-d10ca721564d'}
def write(path,obj):path.write_text(json.dumps(obj,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();rr=json.loads((R/'receipt.json').read_text());assert sha(R/'model.pkl')==rr['model_SHA256'];g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());_,_,_,_,bc=pickle.loads((B/'model.pkl').read_bytes());rows=[];zm={q['uuid']:q for q in z}
 for uid in IDS:
  q=zm[uid];old=set_precision(q['shape'],0);outline=set_precision(q['zone_outline_shape'],0);excess=old.difference(outline);new=old.intersection(outline);assert new.difference(old).area<1e-12;q['shape']=new;rows.append({'owned_UUID':uid,'physical_before_SHA256':P.digest(old),'native_intended_SHA256':P.digest(outline),'physical_after_SHA256':P.digest(new),'physical_unsupported_outside_native_intended_mm2':excess.area,'physical_unsupported_bounds_mm':list(excess.bounds) if not excess.is_empty else [],'only_removed_actual_planning_support_mm2':old.difference(new).area,'never_added_Cu_mm2':new.difference(old).area});print('R304',uid,'outside intent',excess.area,flush=True)
 candidate=dict(c);candidate['zones']=[]
 for q in c['zones']:
  if q['uuid'] not in IDS:candidate['zones'].append(q);continue
  nq=copy.deepcopy(q);owned=zm[q['uuid']];nq['fills'][owned['layer']]=G.records(owned['shape']);candidate['zones'].append(nq)
 oldgroups=pickle.loads((B/'groups.pkl').read_bytes());newgroups={};tests=[]
 for net,ref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  old=oldgroups[net];new=F.graph(candidate,net);newgroups[net]=new;root=lambda groups:next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));a,bb=root(old),root(new);missing=F.discrete_keys(a)-F.discrete_keys(bb);contactbad=losses(old,new);a_refs={outer:unary_union([q['shape'] for q in a if q['kind']=='fill' and q['layer']==inner]) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};b_refs={outer:unary_union([q['shape'] for q in bb if q['kind']=='fill' and q['layer']==inner]) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};refbad,proof=REF.audit(bc,a_refs,b_refs,net);tests.append({'net':net,'old_contact_losses':contactbad,'prior_source_keys_lost':[list(x) for x in sorted(missing)],'strict_old_ref_losses':refbad,'full_formula_proof':proof});write(O/'contact-reference-checkpoint.json',tests);print('R304',net,'contacts',len(contactbad),'source',len(missing),'refs',len(refbad),flush=True)
 write(O/'only-two-physical-support-clip-ledger.json',rows);(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,candidate),protocol=5));(O/'only-two-owned-replacements.pkl').write_bytes(pickle.dumps([zm[uid] for uid in sorted(IDS)],protocol=5));(O/'ground-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));ok=not any(q['old_contact_losses'] or q['prior_source_keys_lost'] or q['strict_old_ref_losses'] for q in tests)
 rec=copy.deepcopy(rr);rec.update({'verdict':'PHYSICAL_INSIDE_INTENDED_OLD_CONTACT_REF_SUPPORT_PASS_NATIVE_GATES_OPEN' if ok else 'PHYSICAL_INSIDE_INTENDED_SUPPORT_REJECTED_REAL_REFERENCE_REPAIR_REQUIRED','parent_R302_receipt_SHA256':sha(R/'receipt.json'),'parent_R302_model_SHA256':sha(R/'model.pkl'),'model_SHA256':sha(O/'model.pkl'),'owned_replacements_SHA256':sha(O/'only-two-owned-replacements.pkl'),'only_two_physical_role_support_ledger_SHA256':sha(O/'only-two-physical-support-clip-ledger.json'),'new_fresh_ground_tests':tests,'corrected_generated_precision_binding_requires_successor':True,'native_jobs':0,'board_written':False,'adopted':False});write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'PASS':ok,'tests':[{'net':q['net'],'refs':len(q['strict_old_ref_losses'])} for q in tests]}),flush=True)
if __name__=='__main__':main()
