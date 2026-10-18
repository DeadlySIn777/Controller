"""Bound side-contact search; native In3 LG retreat is a held later gate."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;source=H/'screen_CORE5_actual_side_annular_In3_LGIn4_transport_r294.py';target=H/'screen_CORE5_scoped_LG_retreat_side_In3_LGIn4_transport_r295.py';assert not target.exists()
s=source.read_text(encoding='utf-8').replace('r294','r295').replace('R294','R295')
old="region=box(10,145,215,228);roi=region.buffer(3);domain=h['domains_normalized'];"
new="region=box(10,145,215,228);roi=region.buffer(3);full_reference=reference;reference=reference.intersection(roi);targets=[(v,a)for v,a in targets if roi.covers(Point(v['x'],v['y']))];domain=h['domains_normalized'];"
assert s.count(old)==1;s=s.replace(old,new)
old="for z in native['zones']:\n  for s in L.poly(N.O.polys(z['fills'].get('In3.Cu',[]))):"
new="for z in native['zones']:\n  # Only original native LG In3 may undergo its normal automatic clearance\n  # retreat. Exact per-record old source/contact/reference gates remain OPEN.\n  # No original outline or filled polygon is edited or fabricated by this screen.\n  if L.norm(z['net'])==LG:continue\n  for s in L.poly(N.O.polys(z['fills'].get('In3.Cu',[]))):"
assert s.count(old)==1;s=s.replace(old,new)
old="results.append(row);put('per-actual-source-barrel-full-current-In3-LGIn4-tests.json',results);print('R295_TARGET',target['uuid'],row['start_free'],row['target_free'],len(faces),bool(row['route']),flush=True)"
new=old+"\n  if accepted:break"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'target_count':len(targets),'proposal_count'", "'target_count':len(targets),'tested_target_count':len(results),'proposal_count'")
s=s.replace("'actual_foreign_planes_discrete_and_holes_hard':True", "'field_and_owned_planes_discrete_and_holes_hard':True,'original_native_LG_In3_automatic_retreat_only_pending_literal_source_contact_old_reference_proof':True,'original_native_LG_In1_In4_and_all_field_planes_not_carved':True,'source_clip_margin_mm':3,'source_clip_bound_exceeds_entire1p25body_radius':True")
compile(s,str(target),'exec');target.write_text(s,encoding='utf-8')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();receipt=H/'CORE5-scoped-LG-native-retreat-side-screen-derivation-r295.json';assert not receipt.exists();receipt.write_text(json.dumps({'source_file':str(source),'source_sha256':sha(source),'derived_file':str(target),'derived_sha256':sha(target),'exact_middle_withdrawn_actual_source_graph_and_annular_contacts_retained':True,'original_LG_In3_normal_clearance_retreat_pending_full_source_contact_reference_native':True,'native_LG_In1_In4_and_all_field_planes_hard':True,'source_region_margin3mm_greater_than_body_radius':True,'first_actual_proposal_ends_screen':True,'native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print('R295_SCRIPT_FROZEN',sha(target),flush=True)
