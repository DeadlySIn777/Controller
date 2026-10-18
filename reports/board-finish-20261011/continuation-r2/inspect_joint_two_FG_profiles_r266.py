"""Read the actual saved profile schema before exact native serialization."""
import pickle,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';assert hashlib.sha256(p.read_bytes()).hexdigest()=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440';q=pickle.loads(p.read_bytes())[3];rows=[{k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}for z in q if z['uuid']in{'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}];assert len(rows)==2;out=H/'joint-two-FG-profile-schema-r266.json';assert not out.exists();out.write_text(json.dumps(rows,indent=1)+'\n');print(json.dumps(rows,indent=1),flush=True)
