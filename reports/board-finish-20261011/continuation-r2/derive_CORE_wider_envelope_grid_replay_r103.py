"""Restore only the documented newly generated plane's nm tags before overlay."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'widen_CORE_owned_In2_plane_envelope_r102.py';s=base.read_text();changes=[]
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b})
rep("legal=from_wkb((base/'In2.Cu-legal.wkb').read_bytes());points", "legal=from_wkb((base/'In2.Cu-legal.wkb').read_bytes());replays=[]\n for role in('shape','zone_outline_shape'):\n  old=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==old;replays.append({'only_documented_NEW_CORE_UUID':q['uuid'],'role':role,'WKB_unchanged':True,'grid_mm':1e-6,'WKB_sha256':digest(q[role])})\n points")
rep("physical=native.difference(ownholes);assert native.is_valid", "native=set_precision(unary_union([q['zone_outline_shape'],native]),1e-6);assert legal.covers(native),'expanded original-route union escaped unchanged legal region';physical=native.difference(ownholes);assert native.is_valid")
rep("CORE-wider-owned-FAG-In2-notch-feed-proposal-r102", "CORE-wider-owned-FAG-In2-notch-feed-proposal-r103")
rep("'new_affected_FAG_return_notch_all77_source_native_guard_body_reference_full_current_mesh':'OPEN'", "'new_affected_FAG_return_notch_all77_source_native_guard_body_reference_full_current_mesh':'OPEN','only_generated_old_plane_tags_replayed_WKB_exact':replays,'failed_R102_overlay_without_tag_replay_rejected_before_model':True")
rep("'R102_CORE_NEW_ENVELOPE_ONLY'", "'R103_CORE_NEW_ENVELOPE_ONLY'")
compile(s,'widen_CORE_owned_In2_plane_envelope_r103.py','exec');out=H/'widen_CORE_owned_In2_plane_envelope_r103.py';assert not out.exists();out.write_text(s)
(H/'CORE-wider-envelope-r103-derivation.json').write_text(json.dumps({'base_sha256':sha(base),'derived_sha256':sha(out),'changes':changes,'no_native_or_unowned_coordinate_precision_change':True,'prior_constructive_route_reused_not_stale_whole_model':True},indent=1)+'\n');print('R103_DERIVED',sha(out),flush=True)
