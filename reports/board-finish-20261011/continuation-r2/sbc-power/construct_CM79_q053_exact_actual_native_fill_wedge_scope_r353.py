"""Actual named native-fill negative scope includes all literal boundary lines."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r350/exact-expanded-sparse-constructor.py'
s=p.read_text(encoding='utf-8').replace('r350','r353').replace('R350','R353')
needle="originalSubtract=IM.subtract"
assert needle in s
replacement="""scopeAuthority=H/'sbc-power/CM79-R350-original-record47-exact-actual-negative-scope-failure-attribution-r352/receipt.json';assert sha(scopeAuthority)=='6689ee1688f5b7b0edd9cdcbcb602bc46b20f638570279bab80dca84acfbaa31';scopeProof=json.loads(scopeAuthority.read_text());assert scopeProof['strict_outside_whole_actual_bound_scope']['empty']and scopeProof['outside_prior_declared_corridor']['empty'];wholeNativeNegative=Path(fillSplice['additional_negative_beyond_normalcut']['file']);assert sha(wholeNativeNegative)==fillSplice['additional_negative_beyond_normalcut']['sha256'];fillWedges.append(zero(__import__('shapely',fromlist=['from_wkb']).from_wkb(wholeNativeNegative.read_bytes())));put(O/'native-current-record47-explicit-whole-actual-wedge-including-lines-authority.json',{'R349_receipt_sha256':sha(fillSpliceDir/'receipt.json'),'R352_scope_proof_sha256':sha(scopeAuthority),'whole_actual_negative_file':str(wholeNativeNegative.resolve()),'whole_actual_negative_sha256':sha(wholeNativeNegative),'no_zero_area_or_small_polygon_waiver':True,'no_source_or_native_outline_settings_coordinate_change':True});originalSubtract=IM.subtract"""
s=s.replace(needle,replacement)
s=s.replace("'R346_raw_fill_gain_and_scope_FAILURE_retained':True", "'R346_raw_fill_gain_and_scope_FAILURE_retained':True,'R350_named_triangle_scope_FAIL_and_R352_actual_whole_negative_scope_retained':True")
EXACT_EXPANDED_SOURCE=s
exec(compile(s,str(__file__),'exec'))
