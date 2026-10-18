"""Correct flattened-role metadata after preserving the R737 assertion failure."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
old=H/'freeze_FIELD_ROOT_priority_interaction_and_sparse_role_handoff_r737.py'
failed=H/'FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r737'
assert failed.exists() and not (failed/'failure.json').exists()
(failed/'failure.json').write_text(json.dumps({'status':'FAILED_BEFORE_EMISSION','assertion':'Flattened current constituent UUID list did not enumerate all historical canonical owners',
 'script_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'no_model_or_board_or_profile_correction_emitted':True},indent=1)+'\n',encoding='utf-8')
text=old.read_text(encoding='utf-8')
text=text.replace('FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r737','FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r739')
text=text.replace("    assert {z['prior_owned_UUID'] for z in renames}==set(r['superseded_owned_roles'])", """    renames=[]
    plans=H/'eight-native-overlap-plan-exact-R543-source-head-recensus-r601/four-current-scope-minimal-component-plans.json'
    planrows=json.loads(plans.read_bytes())
    for member in r['superseded_owned_roles']:
        prior=old[member]
        targets=[new[u] for u in r['current_union_roles'] if (new[u]['net'],new[u]['layer'])==(prior['net'],prior['layer'])]
        assert len(targets)==1
        current=targets[0]
        matches=[p for p in planrows if member in p['exact_R543_before_owned_UUIDs']]
        renames.append({'prior_owned_UUID':member,'current_canonical_UUID':current['uuid'],'raw_net':prior['net'],'layer':prior['layer'],
            'exact_R601_cluster_membership':bool(matches),'current_field_first_transition_binding':'Exact R735 native old-role retirement and current new-role assignment',
            'older_FIELD5_61cb_to_R543_source_repair_then_union_if_not_direct_member':not bool(matches),
            'no_geometric_or_constituent_identity_inferred_from_net_name_alone':True,'future_peer_negative_masks_need_fresh_exact_before_role_hashes':True})
    assert {z['prior_owned_UUID'] for z in renames}==set(r['superseded_owned_roles'])""")
text=text.replace("and 'locked' in preserved[0]['AST']", "and any(x=='locked' or isinstance(x,list) and x[0]=='locked' for x in preserved[0]['AST'][1:])")
text=text.replace("        'ROOT_ordinary_scope':artifact(opfile)","        'R737_flattened_constituent_assertion_failure_preserved':artifact(H/'FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r737/failure.json'),\n        'R733_full_inventory_and_R687_complete_physical_header_identity_preserved':True,\n        'ROOT_ordinary_scope':artifact(opfile)")
text=text.replace('R737_COMPLETE','R739_COMPLETE')
generated=H/'freeze_FIELD_ROOT_priority_interaction_and_sparse_role_handoff_r739.generated.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
exec(compile(text,str(generated),'exec'),{'__file__':str(generated),'__name__':'__main__'})
