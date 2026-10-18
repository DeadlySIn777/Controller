"""Read-only attribution of saved model/native-view record differences."""
import hashlib,json,pickle,sys,collections
from pathlib import Path
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
bp=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';a=pickle.loads(bp.read_bytes());bb=pickle.loads(mp.read_bytes());scope={'/IO_3V3','/LOGIC_GND','/motherboard_do/DOA_FLT_N_FIELD','/motherboard_do/DOA_SDI_HOST','/motherboard_motors/FIELD_GND'};rows=[]
for kind in('tracks','vias','pads','zones'):
 old={x['uuid']:x for x in a[4][kind]if L.norm(x['net'])not in scope};new={x['uuid']:x for x in bb[4][kind]if L.norm(x['net'])not in scope};assert old.keys()==new.keys();diff=[];fields=collections.Counter()
 for uid,x in old.items():
  y=new[uid]
  if x==y:continue
  keys=sorted(k for k in x.keys()|y.keys()if x.get(k)!=y.get(k));fields.update(keys)
  if len(diff)<4:diff.append({'UUID':uid,'net':L.norm(x['net']),'different_fields':keys,'before':{k:x.get(k)for k in keys},'after':{k:y.get(k)for k in keys}})
 rows.append({'kind':kind,'count':len(old),'difference_fields':dict(fields),'first_four_samples':diff})
out=H/'R253-unselected-native-view-vs-model-schema-attribution-r259';assert not out.exists();out.mkdir();result={'base_sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'current_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'rows':rows,'geometry_or_source_modified':False};(out/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print(json.dumps(result,indent=1),flush=True)
