"""Freeze exact .6 neck native successor; preserve original R166 recipe."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'emit_u10017_reference_safe_owned_recipe_r166.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u10017-reference-safe-native-owned-recipe-r166'","O=H/'SAFE-U10017-wider-native-owned-recipe-r183'")
s=s.replace("R=H/'u17-u10017-reference-safe-incremental-audit-r162';assert sha(R/'receipt.json')=='10bae09e7343683d918e333a19e43b90906b15fb794fcdd7be401ef7176b609a'","R=H/'SAFE-U10017-wider-full-branch-audit-r178';assert sha(R/'receipt.json')=='3f2884f06a786c35ad8c41a461228423cb1fba4046477a526937882bb8936d89';assert __import__('json').loads((R/'receipt.json').read_text(encoding='utf-8'))['verdict']=='SAFE_U10017_ONLY_WIDER_FULL_BRANCH_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS'")
s=s.replace("'incremental_R162_receipt_sha256'","'exact_full76_SAFE_R178_receipt_sha256'")
s=s.replace("'baseline_R142_IO3_split_and_precision_replay_OPEN':True","'supersedes_R166_only_by_frozen_R178_new_neck_width_and_native_proposal_geometry':True,'R166_old_neck_recipe_preserved':str((H/'u10017-reference-safe-native-owned-recipe-r166/receipt.json').resolve()),'full76_contacts_prior_sources_outer_references_R178_HOST_PASS':True,'failed_REG6_and_U17_NOT_INCLUDED':True,'full_branch_current_interval_A':[.26061632158690984,2.2686163215869097],'full9pad_current_receipt_sha256':sha(H.parent/'u10017-nine-pad-protected-bypass-current-bound-r48/receipt.json')")
old="covered=q.get('zone_outline_shape',q['shape']).covers(Point(xy));assert covered,(uid,'intended own source landing center absent');flashes.append"
new="covered=q.get('zone_outline_shape',q['shape']).covers(Point(xy));assert covered,(uid,'intended own source landing center absent');assert uid not in byid;flashes.append"
assert old in s;s=s.replace(old,new)
s=s.replace("'old_root_via_required_F_In1_retained':uid==source['uuid']","'NEW_owned_ordinary_barrel_absent_original_eedf':True,'new_barrel_owner':'ROOT_R9' if uid==source['uuid'] else 'FIELD_R178','all6_layer_ordinary_Cu_gate_required':True,'every_SMD_and_hole_drill_gap_required_mm':.275,'prior_root_owned_R9_required_F_In1_retained':uid==source['uuid']")
s=s.replace("'scope':'One exact U10017 protected F wall; bypass/new VDD and every retained outside source/contact mandatory'","'scope':'One exact original U10017 protected F wall; R178 widened bypass/new VDD and every retained outside source/contact mandatory'")
s=s.replace('R166', 'R183') if False else s
s=s.replace("print('R166'","print('R183'")
exec(compile(s,str(H/'emit_u10017_reference_safe_owned_recipe_r166.py'),'exec'))
