"""Use the native reference property for FP UUID; model FP records omit UUID."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/freeze_R371_R7035_exact_source_native_Cu_reference_scope_r380.py'
failed=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r380/failure.json'
assert not failed.exists();failed.write_text(json.dumps({'failure':"KeyError: model footprint record has no 'uuid'; before native/model/source changes",'script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_jobs':0},indent=1)+'\n',encoding='utf-8')
s=p.read_text(encoding='utf-8').replace('r380','r381').replace('R380','R381')
s=s.replace('import json,pickle,hashlib,sys,time','import json,pickle,hashlib,sys,time,re')
s=s.replace("chunk=iv[3][fp['uuid']]", "fps=[(u,ch)for u,ch in iv[3].items()if A.C.pcbtext.chunk_kind(ch)=='footprint'and re.search(rb'\\(property\\s+\"Reference\"\\s+\"R7035\"',ch)];assert len(fps)==1;fpuid,chunk=fps[0]")
s=s.replace("fp['uuid']",'fpuid').replace("'UUID':f['uuid']", "'UUID':f.get('uuid')")
s=s.replace("'footprint':fp,'pads':pads", "'footprint':fp,'FP_UUID':fpuid,'pads':pads")
s=s.replace("atom(comp,'value'),pins,fp,flush=True", "atom(comp,'value'),pins,[fp['x'],fp['y']],fp['side'],flush=True")
exec(compile(s,str(__file__),'exec'))
