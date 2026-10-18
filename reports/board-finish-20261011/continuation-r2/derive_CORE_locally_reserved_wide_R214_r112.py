"""Apply the locally reserved widening to the exact immutable native baseline."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'materialize_CORE_wide_immutable_R214_incremental_r107.py';s=base.read_text();changes=[]
for a,b in [("CORE-wider-new-only-legal-envelope-proposal-r106';assert sha(packet/'receipt.json')=='74bb46a6fd31e60c8461f7f8c2ecf58cfc32a259abf3616466888f24400f4b39'","CORE-wide-local-IO3-branch-reservation-proposal-r111';assert sha(packet/'receipt.json')=='7ee4c5126cdaeb45db8f26524ec34d459cdcfe5baf54ec20d9c8b67230ebc24c'"),("digest(core['shape'])=='fc29d425b54f78f8fcfd04273ccb26698013a914cfa718e7ba7a110cafc5b853'","digest(core['shape'])=='d7e6b486a7bc3410a82b432cf541acc713eb6f5de15f8adf814427bcc438c8d9'"),("CORE-wide-immutable-R214-materialized-source-proposal-r107","CORE-wide-reserved-IO3-immutable-R214-materialized-r112")]:
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b})
s=s.replace('R107_','R112_');out=H/'materialize_CORE_wide_reserved_IO3_R214_r112.py';assert not out.exists();compile(s,str(out),'exec');out.write_text(s);(H/'CORE-wide-local-IO3-R214-r112-derivation.json').write_text(json.dumps({'base_sha256':sha(base),'new_sha256':sha(out),'changes':changes,'only_new_widening_changed_local_IO3_via57bd_reservation':True,'all_old_source_reference_and_native_actual_Cu_guards_unmodified':True,'R107_source_loss_and_original_R224_reference_failure_remain_rejected':True},indent=1)+'\n');print('R112_DERIVED',sha(out),flush=True)
