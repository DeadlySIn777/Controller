"""Keep exact R100 feed size but isolate immutable native-fill provenance effects."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'materialize_CORE_wide_immutable_R214_incremental_r107.py';s=base.read_text();changes=[]
for a,b in [("CORE-wider-new-only-legal-envelope-proposal-r106';assert sha(packet/'receipt.json')=='74bb46a6fd31e60c8461f7f8c2ecf58cfc32a259abf3616466888f24400f4b39'","CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';assert sha(packet/'receipt.json')=='77e2d358f3a177854b3b2aaa4863430e36967e4eb06520f91a501742f054e4cd'"),("digest(core['shape'])=='fc29d425b54f78f8fcfd04273ccb26698013a914cfa718e7ba7a110cafc5b853'","digest(core['shape'])=='4b5675bccc5a299d38f996843162681d4f227b6c194ae3d65194d4b00a823e74'"),("CORE-wide-immutable-R214-materialized-source-proposal-r107","CORE-narrow-immutable-R214-materialized-source-proposal-r109")]:
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b})
s=s.replace('R107_','R109_');out=H/'materialize_CORE_narrow_immutable_R214_incremental_r109.py';assert not out.exists();compile(s,str(out),'exec');out.write_text(s);(H/'CORE-narrow-immutable-R214-r109-derivation.json').write_text(json.dumps({'base_sha256':sha(base),'new_sha256':sha(out),'changes':changes,'same_R100_route_size_but_immutable_positive_head_nativefilled_Cu_only_added_primitive_cuts':True,'wider_R107_IO3_source_loss_not_waived':True},indent=1)+'\n');print('R109_DERIVED',sha(out),flush=True)
