"""Separate physical-source routes from explicit unclosed fullbody refs."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM51_polygon_routed_ordinary_ground_fanouts_r276.py').read_text()
s=s.replace('CM51-exact-polygon-routed-ordinary-ground-fanout-nominations-r276','CM51-physical-routed-ordinary-ground-fullbody-reference-FAIL-retained-r277')
s=s.replace('CM51-ordinary-inward-first-ground-fanout-nominations-r275/partial-only-nominated-discrete.pkl','CM51-exact-polygon-routed-ordinary-ground-fanout-nominations-r276/only-nominated-discrete.pkl')
s=s.replace('.intersection(sourcecentre).difference(unary_union(tc))','.difference(unary_union(tc))')
s=s.replace("if errors:continue\n    v=", "if any(e['kind']!='actual_drilled_fullbody_reference'for e in errors):continue\n    v=")
s=s.replace("'full_analytic_later_joint_rebind_required':True", "'full_analytic_later_joint_rebind_required':True,'fullbody_reference_FAIL_retained':bool(errors)")
s=s.replace('CM51_ALL_ORDINARY_POLYGON_ROUTE_NOMINEES_CURRENT_HEAD_CONSTRUCTION_AND_SOURCE_PROOF_OPEN','CM51_ALL_PHYSICAL_ORDINARY_SOURCE_ROUTE_NOMINEES_NEW_REFERENCE_FAILS_RETAINED_FULL_PROOF_OPEN')
s=s.replace("'CM_signed_return_A':3.5593046439628484", "'new_fullbody_reference_filter_disabled_for_diagnostic_only':True,'every_new_nonempty_reference_gap_is_unclosed_FAIL_no_waiver':True,'CM_signed_return_A':3.5593046439628484")
s=s.replace('R276','R277')
exec(compile(s,str(__file__),'exec'))
