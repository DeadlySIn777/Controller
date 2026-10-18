"""Bind individual actual source polygons behind the retained raw reference loss."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-old-antipad-individual-source-array-diagnosis-r210'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir()
 bp=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl'
 assert sha(bp)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'and sha(mp)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5'
 _,h0,_,_,before=pickle.loads(bp.read_bytes());_,h,_,_,after=pickle.loads(mp.read_bytes())
 uid='3aabe7ec-baf5-4304-ac89-079b0a62e545';t=next(x for x in h0['tracks']if x['uuid']==uid);assert t==next(x for x in h['tracks']if x['uuid']==uid)
 wp=H/'U10003-R196-unchanged-net-physical-identity-and-strict-oldrefs-r199'/f'{uid}-direct-old-reference-loss.wkb';w=from_wkb(wp.read_bytes());FG='/motherboard_motors/FIELD_GND'
 roots=[];rows=[]
 for label,m in [('before',before),('after',after)]:
  _,groups=K.physical(m,FG,K.hole_context(m));root=K.root(groups,'J11003','2');roots.append(root)
  for r in root:
   if r['kind']!='fill' or r['layer']!='In1.Cu' or not r['shape'].intersects(w.envelope.buffer(.00001)):continue
   p=OUT/(label+'-'+r['uuid']+'-'+str(len(rows))+'.wkb');p.write_bytes(r['shape'].wkb)
   rows.append({'side':label,'UUID':r['uuid'],'layer':r['layer'],'individual_actual_drilled_shape_WKB_sha256':sha(p),'file':str(p),'witness_overlap_empty':r['shape'].intersection(w).is_empty,'bounds_mm':list(r['shape'].bounds)})
 old=[r for r in roots[0]if r['kind']=='fill'and r['layer']=='In1.Cu'];new=[r for r in roots[1]if r['kind']=='fill'and r['layer']=='In1.Cu']
 identity=[]
 for row in rows:
  if row['side']=='before':identity.append({'before_WKB_sha256':row['individual_actual_drilled_shape_WKB_sha256'],'byte_identical_source_rooted_after_shape':any(hashlib.sha256(r['shape'].wkb).hexdigest()==row['individual_actual_drilled_shape_WKB_sha256']for r in new)})
 result={'verdict':'DIAGNOSTIC_INDIVIDUAL_ACTUAL_SOURCE_ARRAYS_NO_ACCEPTANCE','before_sha256':sha(bp),'after_sha256':sha(mp),'original_track':t,'raw_reference_loss_sha256':sha(wp),'raw_reference_loss_area_mm2':w.area,'raw_failure_preserved':True,'actual_individual_source_rows':rows,'exact_source_rooted_shape_identity':identity,'no_precision_area_or_reference_waiver':True,'native_jobs':0,'adopted':False}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R210_COMPLETE',len(rows),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
