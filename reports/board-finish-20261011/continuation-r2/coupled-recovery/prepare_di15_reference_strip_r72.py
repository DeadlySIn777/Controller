"""Create corrected R72 with the exact R66 old-domain-boundary detour."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;source=HERE/'construct_di15_In1_reference_strip_r64.py';raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='8dc6559e1d042e6c0aaea740b80e88b1d8c324faa60e2dee919a179308c48278';s=raw.decode()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("directory=HERE/'di15-In1-reference-strip-r64'","directory=HERE/'di15-In1-reference-strip-r72'")
replace("pathfile=HERE/'di15-neighbor-void-detour-r58.json'","pathfile=HERE/'di15-original-boundary-detour-r66.json'")
replace("4f64d84d0aa6a7577fcf341e8a101c05bdada00b46926b98e4dab7f43ba543c4","8acc0b87389d630e23e9f34306292fe2e8c9c3ed4c4c9403572d03f337a19e30")
replace("'controller/DI15/reference-r64/'","'controller/DI15/reference-r72/'")
replace("'DI15 ordinary In2 adjacent source reference R64'","'DI15 ordinary In2 adjacent source reference R72'")
replace('"""Corrected R64: actual safe R22 + R58 neighbouring-void detour.','"""Corrected R72: exact safe R22 + R66 unchanged-native-boundary detour.')
target=HERE/'construct_di15_In1_reference_strip_r72.py';assert not target.exists();target.write_text(s,newline='\n');print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'created':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
