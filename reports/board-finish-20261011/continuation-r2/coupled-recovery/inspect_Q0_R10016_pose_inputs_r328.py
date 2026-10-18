from pathlib import Path
import sys,pickle,json,hashlib
H=Path(__file__).resolve().parent;P=H.parent
for p in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
model=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,current=pickle.loads(model.read_bytes());fp=next(f for f in h['footprints']if f['ref']=='R10016');pads=[p for p in h['pads']if p['ref']=='R10016'];out=H/'Q0-R10016-native-pose-inputs-r328';assert not out.exists();out.mkdir();r={'verdict':'EXACT_OLD_POSE_INPUTS_READ_ONLY','model_sha256':sha(model),'footprint':fp,'pads':pads,'board_or_model_written':False,'adopted':False};(out/'receipt.json').write_text(json.dumps(r,indent=1,allow_nan=False)+'\n');print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'footprint':{k:v for k,v in fp.items()if k!='courtyard'},'pads':[{k:v for k,v in p.items()if k not in('layers','hole')}for p in pads]}),flush=True)
