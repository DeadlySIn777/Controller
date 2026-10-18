"""Pin actual immutable heads and expose every exact SAFE-root delta."""
from pathlib import Path
import pickle,json,hashlib
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/safe-joint-exact-delta-inspection-r146'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 specs=[('field-R111',H/'field-power/corrected-regulated-native-bound-search-base-r111/model.pkl','722fae195cecfcfa07729dd243c2d74a0a0088e672582363265a2c15553db4d8'),('root-safe-R22',H/'safe-logic-five-and-fag-margin-r22/model.pkl','014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a'),('CORE1V2-R135',H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl','729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca')]
 models={}
 for label,path,want in specs:assert sha(path)==want;models[label]=pickle.loads(path.read_bytes())
 base=models['field-R111'];bz={q['uuid']:q for q in base[3]};rows=[]
 for label,path,want in specs[1:]:
  m=models[label];zh={q['uuid']:q for q in m[3]};diff=[]
  for uid,q in zh.items():
   if uid not in bz:diff.append({'UUID':uid,'operation':'add','raw_net':q['net'],'layer':q['layer'],'physical_sha256':digest(q['shape']),'outline_sha256':digest(q.get('zone_outline_shape',q['shape']))});continue
   o=bz[uid];op=o.get('zone_outline_shape',o['shape']);np=q.get('zone_outline_shape',q['shape'])
   if not o['shape'].equals(q['shape']) or not op.equals(np):diff.append({'UUID':uid,'operation':'geometry_mutation','raw_net':q['net'],'layer':q['layer'],'physical_before_sha256':digest(o['shape']),'physical_after_sha256':digest(q['shape']),'physical_removed_mm2':o['shape'].difference(q['shape']).area,'physical_added_mm2':q['shape'].difference(o['shape']).area,'outline_before_sha256':digest(op),'outline_after_sha256':digest(np),'outline_removed_mm2':op.difference(np).area,'outline_added_mm2':np.difference(op).area})
  removed=sorted(set(bz)-set(zh));discrete={}
  for key in ('pads','tracks','vias','footprints'):
   old={q['uuid']:q for q in base[1][key]};new={q['uuid']:q for q in m[1][key]};discrete[key]={'added_UUIDs':sorted(set(new)-set(old)),'removed_UUIDs':sorted(set(old)-set(new)),'changed_UUIDs':[u for u in set(old)&set(new) if old[u]!=new[u]]}
  rows.append({'label':label,'model_file':str(path.resolve()),'model_sha256':want,'owned_zone_delta':diff,'removed_owned_zone_UUIDs':removed,'discrete_delta':discrete})
 result={'verdict':'EXACT_DELTA_INSPECTION_ONLY_NOT_COMPOSITION_OR_CONTACT_ACCEPTANCE','base_model_sha256':specs[0][2],'rows':rows,'native_jobs':0,'board_written':False}
 (O/'receipt.json').write_text(json.dumps(result,indent=1)+'\n')
 print('SAFE_EXACT_HEAD_DELTAS',[(r['label'],len(r['owned_zone_delta']),len(r['removed_owned_zone_UUIDs']),r['discrete_delta']) for r in rows]);print('ZONE_DELTAS',json.dumps(rows[0]['owned_zone_delta'],indent=1))
if __name__=='__main__':main()
