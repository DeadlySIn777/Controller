"""Derive a new pinned R42+DI6 binder without rewriting R62 authority."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'bind_di15_safe_root_r22_di6_r62.py'; raw=src.read_bytes(); s=raw.decode().replace('\r\n','\n')
start=s.index(" path=HERE.parent/'safe-logic-five-and-fag-margin-r22/model.pkl'")
end=s.index(" rp=HERE/'di6-reference-corrected-full-audit-r11.json'",start)
header=""" path=HERE.parent/'logic-two-reference-safe-return-restoration-r42/model.pkl';raw=A.read(path);assert C.sha(raw)=='a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba';old,h,binding,zones,before=pickle.loads(raw);h=copy.deepcopy(h);zones=copy.deepcopy(zones);assert before is not None
 receiptpath=path.with_name('receipt.json');receipt=json.loads(A.read(receiptpath));assert C.sha(A.read(receiptpath))=='c3662517d5484fd59d111be0e65881564de9700a64c80419ce0e55a9235b4e28';assert receipt['model_sha256']==C.sha(raw) and receipt['new_zone_shapes']==2 and receipt['new_holes']==0 and receipt['old_Cu_deleted']==0 and receipt['old_native_zone_outlines_changed']==0
 snap=path.with_name('proposed-zones.pkl');assert C.sha(A.read(snap))==receipt['proposed_zones_sha256']=='6dade25d3aced12036dcd56ef8bbec590f5bd721ec47bd83435cd3ad2186b114'
 independentpath=HERE.parent/'logic-two-independent-full-r43/receipt.json';independent=json.loads(A.read(independentpath));assert C.sha(A.read(independentpath))=='c0688d943d936947bb21ce60b7afc57574e5c4220db00ff7349b6b4821a0f0b3';assert independent['model_sha256']==C.sha(raw) and independent['added_zones_sha256']==receipt['proposed_zones_sha256'] and independent['all_original_Cu_holes_source_poses_native_outlines_unchanged_to_parent'];assert independent['verdict']=='PASS_TWO_NEW_LOGIC_PIECES_FULL_OLD_ZONE_NET_CONTACT_SOURCE_REFERENCE_HOST_GEOMETRY_NATIVE_CURRENT_OPEN'
 assert all(not q['old_discrete_contact_losses'] for q in independent['affected_net_contacts']);assert all(independent[k]==0 for k in ('physical_error_count','foreign_new_zone_error_count','foreign_hole_error_count','native_no_zone_area_error_count'));assert independent['all_old_zone_bearing_net_count']==76
 A.read(independentpath.with_name('reference-checkpoint.json'));A.read(independentpath.with_name('contact-checkpoint.json'))
"""
s=s[:start]+header+s[end:]
s=s.replace('corrected ROOT R22','checked ROOT R42').replace('safe-root-r22-DI6-bind-r62','safe-root-r42-DI6-bind-r118').replace('current-safe-root-r22-DI6-r62','current-safe-root-r42-DI6-r118').replace('DI15_R62','DI15_R118').replace('ROOT_safe_R22','ROOT_checked_R42').replace('SAFE_ROOT_R22','CHECKED_ROOT_R42')
dst=H/'bind_di15_checked_root_r42_di6_r118.py';assert not dst.exists();dst.write_text(s,newline='\n')
report={'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'change':'R42 model/receipt and independent R43 exact host authority replace R22 header; exact native-bound eleven DI6 chunks and incremental drill/fill/source predicates unchanged','model_only':True,'native_jobs':0}
out=H/'prepare-safe-r42-DI6-bind-r118.json';assert not out.exists();out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report))
