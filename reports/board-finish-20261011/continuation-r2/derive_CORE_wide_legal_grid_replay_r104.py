"""Bind the cached generated legal-region precision; retain strict predicates."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'widen_CORE_owned_In2_plane_envelope_r103.py';s=base.read_text();changes=[]
for a,b in [("legal=from_wkb((base/'In2.Cu-legal.wkb').read_bytes());replays=[]", "legal=from_wkb((base/'In2.Cu-legal.wkb').read_bytes());legal_WKB=legal.wkb;legal=set_precision(legal,1e-6,mode='pointwise');assert legal.wkb==legal_WKB;replays=[]"),("CORE-wider-owned-FAG-In2-notch-feed-proposal-r103","CORE-wider-owned-FAG-In2-notch-feed-proposal-r104"),("'R103_CORE_NEW_ENVELOPE_ONLY'","'R104_CORE_NEW_ENVELOPE_ONLY'")]:
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b})
compile(s,'widen_CORE_owned_In2_plane_envelope_r104.py','exec');out=H/'widen_CORE_owned_In2_plane_envelope_r104.py';assert not out.exists();out.write_text(s)
(H/'CORE-wider-envelope-r104-derivation.json').write_text(json.dumps({'base_sha256':sha(base),'derived_sha256':sha(out),'changes':changes,'only_documented_generated_legal_and_NEW_plane_WKB_exact_precision_tags':'1nm pointwise','strict_original_route_subset_and_exactlegal_coverage_predicates_retained':True,'no_native_precision_edit':True},indent=1)+'\n');print('R104_DERIVED',sha(out),flush=True)
