"""Derive a preserved exploratory planner with exact own-cut provenance.

The outward projection polygon is used only to nominate a route across the
new signal's own transition. Final analytic-disk strips stay explicitly open.
No neighbouring old reference void is healed by this nomination operation.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
src=HERE/'construct_di6_reference_paths_r9.py';dst=HERE/'construct_di6_reference_paths_r10.py'
assert not dst.exists();text=src.read_text()
text=text.replace("out=HERE/'di6-reference-path-correction-r9.json'","out=HERE/'di6-reference-path-correction-r10.json'")
text=text.replace("actualref=refs[layer].intersection(win.buffer(1));allowed=actualref.union(unary_union(voids)).buffer(-.105)","actualref=refs[layer].intersection(win.buffer(1));owncut=Point(signal['x'],signal['y']).buffer(.525/math.cos(math.pi/512),quad_segs=128);old_reference_only_owncut=cp['oldrefs'][layer].intersection(owncut);allowed=actualref.union(old_reference_only_owncut).union(unary_union(voids)).buffer(-.105)")
text=text.replace("'reference_circle_boundary_artifacts_not_waived':True","'reference_circle_boundary_artifacts_not_waived':True,'nomination_only_own_outward_projection_strip':{'exact_new_signal_UUID':signal['uuid'],'analytic_radius_mm':.525,'bounded_projection_circumradius_mm':.525/math.cos(math.pi/512),'former_rooted_reference_intersection_only':True,'actual_analytic_disk_reference_gaps_must_remain_OPEN':True}")
text=text.replace("'R8_receipt_sha256':", "'preserved_R9_planner_sha256':C.sha(A.read(HERE/'construct_di6_reference_paths_r9.py')),'preserved_R9_report_sha256':C.sha(A.read(HERE/'di6-reference-path-correction-r9.json')),'R8_receipt_sha256':")
assert text!=src.read_text();dst.write_text(text)
print(dst)
