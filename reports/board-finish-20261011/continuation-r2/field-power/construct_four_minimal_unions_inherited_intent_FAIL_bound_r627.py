"""Preserve the exact pre-existing B3 role excess as an explicit raw FAIL."""
from pathlib import Path
import ast
H=Path(__file__).resolve().parent
p=H/'construct_four_unions_complete_named_record_edge_scopes_r625.py'
t=ast.parse(p.read_text(encoding='utf-8'));t.body.pop();ns={'__file__':str(p)};exec(compile(t,str(p),'exec'),ns);s=ns['s']
s=s.replace('R543-four-unions-complete-named-generated-record-edge-scopes-r625','R543-four-minimal-unions-inherited-B3-intent-FAIL-bound-r627')
old="assert outside_intent.is_empty,('physical outside native intention',i,ds(outside_intent))"
new="before_outside=unary_union([zero(a['shape'])for a in members]).difference(unary_union([zero(a['zone_outline_shape'])for a in members]));novel=outside_intent.difference(before_outside);assert novel.is_empty and outside_intent.wkb==before_outside.wkb,('novel or altered physical outside native intention',i,ds(novel));put(OUT/f'cluster-{i}-inherited-physical-outside-intended-FAIL-ledger.json',{'raw_before':ds(before_outside),'raw_after':ds(outside_intent),'exact_same_WKB':True,'raw_FULL_FAIL_preserved':not outside_intent.is_empty,'novel_role_excess_EMPTY':True,'no_clipping_or_waiver':True})"
assert old in s;s=s.replace(old,new)
s=s.replace("'physical_within_intended':True", "'new_physical_outside_intended_EMPTY':True,'inherited_physical_outside_intended_FAIL':ds(outside_intent)")
s=s.replace("'status':'FOUR_MINIMAL_SAME_NINE_SETTINGS_OWNED_UNIONS_NEGATIVE_ONLY_CONSTRUCTED_SOURCE_REFERENCE_NATIVE_OPEN'", "'status':'FOUR_MINIMAL_UNIONS_DIAGNOSTIC_INHERITED_B3_PHYSICAL_OUTSIDE_INTENT_FAIL_BOUND_SOURCE_REFERENCE_NATIVE_OPEN'")
s=s.replace("print('R625'","print('R627'")
exec(compile(s,str(Path(__file__)),'exec'))
