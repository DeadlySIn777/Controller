"""Bind explicit retired-via scope before full-native mask comparisons."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=H/'combined-R753-serialized-all-Cu-expected-r297/all-copper-expected.json';assert sha(old)=='00ebcd618cdcdc292a499e06dc172273bb0a531fce81364411886b25a7513f70';e=json.loads(old.read_bytes())
mask=Path(e['baseline_full_native_mask_file']);assert sha(mask)==e['baseline_full_native_mask_SHA256'];actual=json.loads(mask.read_bytes())['vias']
retired=set(actual)-set(e['copper']);assert not retired,'This exact staged scope authorizes no native-via UID retirement'
e['authorized_removed_actual_full_R157_via_UUIDs']=[];e['every_actual_full_R157_via_UID_retained_expected']=True
OUT=H/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300';assert not OUT.exists();OUT.mkdir();fp=OUT/'all-copper-expected.json';fp.write_text(json.dumps(e,indent=1,allow_nan=False)+'\n',encoding='utf-8')
r={'status':'ALL_ACTUAL_R157_NATIVE_VIA_UUIDS_EXPLICITLY_RETAINED_NO_RETIREMENT_EXEMPTIONS','original_expected_SHA256':sha(old),'supplemented_expected_SHA256':sha(fp),'actual_FULL_R157_via_count':len(actual),'authorized_removed_via_UUIDs':[],'adopted':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8');print(json.dumps(r),flush=True)
