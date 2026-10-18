"""Full old relationships, actual ground roots and strict prior refs vs R160."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
import physical_reference_losses_r2 as REF
O=H/'sbc-power/original-IO3-full-all76-incremental-audit-r180'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def main():
 assert len(sys.argv)==2 and not O.exists();O.mkdir();mp=Path(sys.argv[1]);bp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';assert sha(bp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
 old,h,b,z,new=pickle.loads(mp.read_bytes());bo,bh,bb,bz,before=pickle.loads(bp.read_bytes());assert old==bo and h==bh,'Only exact new IO3 geometry is authorized in this incremental composition'
 nets={C.norm(q['net']) for q in before['zones']};assert len(nets)==76
 text=Path(REF.__file__).read_text();assert 'if loss.area>1e-9:' in text;text=text.replace('if loss.area>1e-9:','if loss.area>0:').replace("'threshold_mm2':1e-9","'threshold_mm2':0")
 hf=O/'strict-positive-reference-helper.py';hf.write_text(text);ns={'__file__':str(hf.resolve()),'__name__':'strict_positive_reference_helper'};exec(compile(text,str(hf),'exec'),ns)
 rows=[];groups={};oldgroups={}
 for net in sorted(nets):
  a=F.graph(before,net);n=F.graph(new,net);bad=losses(a,n);oldgroups[net]=a;groups[net]=n;rows.append({'net':net,'before_groups':len(a),'after_groups':len(n),'old_discrete_contact_losses':bad});put(O/'contact-checkpoint.json',rows);print('R180_CONTACT',net,len(a),len(n),'losses',len(bad),flush=True)
 source=[];refs=[]
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  a=oldgroups[net];n=groups[net];ar=next(xs for xs in a if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));nr=next(xs for xs in n if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));lost=F.discrete_keys(ar)-F.discrete_keys(nr)
  source.append({'net':net,'source':ref+'.2','before_named_pads':sum(q['kind']=='pad' and bool(q['pin']) for q in ar),'after_named_pads':sum(q['kind']=='pad' and bool(q['pin']) for q in nr),'lost_prior_source_keys':[list(k) for k in sorted(lost)]})
  oldref={o:unary_union([q['shape'] for q in ar if q['kind']=='fill' and q['layer']==l]) for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};newref={o:unary_union([q['shape'] for q in nr if q['kind']=='fill' and q['layer']==l]) for o,l in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]}
  bad,proof=ns['audit'](before,oldref,newref,net);refs.append({'net':net,'retained_reference_losses':bad,'proof':proof});put(O/'reference-checkpoint.json',refs);print('R180_SOURCE_REF',net,len(lost),len(bad),flush=True)
 ok=not any(r['old_discrete_contact_losses'] for r in rows) and not any(r['lost_prior_source_keys'] for r in source) and not any(r['retained_reference_losses'] for r in refs)
 (O/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));put(O/'receipt.json',{'verdict':'PASS_INCREMENTAL_ALL76_OLD_CONTACT_SOURCE_STRICT_REFERENCE' if ok else 'FAIL_INCREMENTAL_ALL76_OLD_CONTACT_SOURCE_STRICT_REFERENCE','model_sha256':sha(mp),'parent_R160_model_sha256':sha(bp),'all76_rows':rows,'source_rows':source,'strict_reference_file':str((O/'reference-checkpoint.json').resolve()),'strict_reference_sha256':sha(O/'reference-checkpoint.json'),'new_feed_paired_return_current_original_IO3_branch_native_gates':'OPEN','no_original_discrete_source_native_definition_change':True,'no_area_waiver':True,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)});print('R180_COMPLETE',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
