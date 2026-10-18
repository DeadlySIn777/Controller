"""Metadata/ownership supplement. No new geometry or native board mutation."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in (H,ROOT,ROOT/'sbc-power',ROOT/'coupled-recovery'):sys.path.insert(0,str(d))
import ordinary_routes as O
from verify_source import parse,atom
R735=H/'FIELD-complete-exact-R157-native-definition-only-replay-r735'
OUT=H/'FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r739'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def artifact(p):return {'file':str(Path(p).resolve()),'SHA256':sha(p)}
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists();OUT.mkdir();start=time.monotonic()
    rf=R735/'complete-field-native-definition-only-replay.json';assert sha(rf)=='1b2a8afa77e9df103f0c8330911615fe29b8139ec1e2909f46f5472f3a5e6a79'
    r=json.loads(rf.read_bytes());rows=json.loads(Path(r['operations']['file']).read_bytes())
    base=Path(r['baseline_host_model']['file']);current=Path(r['current_field_host_model']['file']);native=Path(r['native_parent']['file'])
    assert sha(base)==r['baseline_host_model']['SHA256'] and sha(current)==r['current_field_host_model']['SHA256'] and sha(native)==r['native_parent']['SHA256']
    _,_,_,q0,_=pickle.loads(base.read_bytes());_,_,binding,qs,_=pickle.loads(current.read_bytes())
    old={q['uuid']:q for q in q0};new={q['uuid']:q for q in qs}
    sparse=[];renames=[]
    for uid in r['superseded_owned_roles']:
        sparse.append({'action':'retire-owned-role','UUID':uid,'before_physical_SHA256':hs(old[uid]['shape']),
            'before_intended_SHA256':hs(old[uid]['zone_outline_shape']),'role':old[uid],
            'NOTE':'Only for exact R155 field-first transition. Later peer scopes replay on mapped current role.'})
    for uid in r['shared_owned_role_changes']+r['current_union_roles']:
        q=new[uid];sparse.append({'action':'replace-owned-role' if uid in old else 'add-owned-role','UUID':uid,
            'before_physical_SHA256':hs(old[uid]['shape']) if uid in old else None,
            'before_intended_SHA256':hs(old[uid]['zone_outline_shape']) if uid in old else None,'role':q,
            'NOTE':'Exact field-first definition/physical authority; never replace later peer cuts by this whole role.'})
        for member in q.get('constituent_proposal_UUIDs',[]):
            if member in r['superseded_owned_roles']:renames.append({'prior_owned_UUID':member,'current_canonical_UUID':uid,'raw_net':q['net'],'layer':q['layer']})
    renames=[]
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
    assert {z['prior_owned_UUID'] for z in renames}==set(r['superseded_owned_roles'])
    rolefile=OUT/'only-exact-field-first-owned-role-delta-NOT_MODEL_OR_LATER_PEER_OVERLAY.pkl';rolefile.write_bytes(pickle.dumps(sparse,protocol=5))
    put(OUT/'retired-owned-role-to-current-canonical-role-sparse-peer-mask-mapping.json',renames)
    # Frozen R735 contains one metadata overstatement. Preserve it and explicitly correct its predicate.
    conflictfile=Path(r['ROOT_peer_overlap_conflicts']['file']);conf=json.loads(conflictfile.read_bytes());assert sha(conflictfile)==r['ROOT_peer_overlap_conflicts']['SHA256']
    profiles={p['uuid']:p['native_profile'] for p in conf['ROOT_positive_zone_identity']};corrected=[]
    for c in conf['conflicts']:
        q=new[c['FIELD_proposal_UUID']];fp={k:q[k] for k in profiles[c['ROOT_uuid']]};rp=profiles[c['ROOT_uuid']]
        differences={k:{'ROOT':rp[k],'FIELD':fp[k]} for k in rp if rp[k]!=fp[k]}
        assert differences=={'priority':{'ROOT':126,'FIELD':124}}
        corrected.append({**c,'exact_native_profile_differences':differences,
            'supersedes_R735_unconditional_native_equal_settings_same_net_overlap_requires_union_flag':True,
            'same_all_native_settings_and_raw_net_overlap':False,
            'native_equal_settings_same_net_overlap_requires_explicit_union_or_partition_before_DRC':False,
            'resolution_for_first_combined_diagnostic':'Retain exact separate ROOT126 and FIELD124 native definitions; no merge, partition or geometry withdrawal',
            'actual_native_interaction_source_contacts_reference_and_DRC':'OPEN; priority difference is no proof of these gates'})
    # Exact chunk-operation collision check against ROOT ordinary/FP and ROOT two zone additions.
    opfile=ROOT/'U10003-HOST-joint-exact-native-Cu-and-attested-pose-packet-r263/exact-native-discrete-and-pose-operation.json'
    assert sha(opfile)=='858e64a48c76714000ac4338e528915867d290358581943ce9a6f42d6afcf561'
    rops=json.loads(opfile.read_bytes());fieldids={v['uuid'] for v in rows};rootids={v['uuid'] for v in rops}
    assert not fieldids&rootids;assert not fieldids&set(profiles)
    raw=native.read_bytes();head,chunks,tail=O.C.pcbtext.split(raw);assert head+b''.join(chunks)+tail==raw
    inv={O.C.pcbtext.chunk_uuid(c):c for c in chunks if O.C.pcbtext.chunk_uuid(c)}
    preserved=[{'UUID':u,'exact_native_chunk_SHA256':hashlib.sha256(c).hexdigest(),'AST':parse(c.decode())}
        for u,c in inv.items() if u.startswith('dc1a')]
    assert len(preserved)==1 and preserved[0]['AST'][0]=='segment' and any(x=='locked' or isinstance(x,list) and x[0]=='locked' for x in preserved[0]['AST'][1:])
    assert preserved[0]['UUID'] not in fieldids and preserved[0]['UUID'] not in rootids
    # Inventory only: do not serialize a candidate or inject any stored filled polygons.
    simulated=dict(inv)
    for row in rows:
        uid=row['uuid'];action=row['action']
        if action in ('delete','replace'):
            before=Path(row['exact_before']['file']);assert sha(before)==row['exact_before']['SHA256'];assert simulated[uid]==before.read_bytes()
        if action=='delete':del simulated[uid]
        else:
            af=Path(row['after']['file']);assert sha(af)==row['after']['SHA256'];ch=af.read_bytes()
            if action=='add':assert uid not in simulated
            assert O.C.pcbtext.chunk_uuid(ch)==uid;simulated[uid]=ch
    for pe in conf['ROOT_positive_zone_identity']:
        uid=pe['uuid'];assert uid not in simulated;path=Path(pe['chunk']['file']);assert sha(path)==pe['chunk']['SHA256'];simulated[uid]=path.read_bytes()
    invariant=[u for u in inv if u not in fieldids];assert all(simulated[u]==inv[u] for u in invariant)
    put(OUT/'corrected-ROOT-FG-distinct-priority-native-interaction.json',{'source_R735_failure_scope':artifact(conflictfile),'corrected_interactions':corrected,
        'ROOT_positive_roles_byte_exact':conf['ROOT_positive_zone_identity'],'no_UUID_collision':True,'same_profile_merge_not_authorized_or_applied':True,
        'native_full_fill_source_reference_and_current_flags':'OPEN'})
    put(OUT/'first-combined-native-sparse-composition-order-and-conflicts.json',{
        'FIELD_exact_R157_recipe':artifact(rf),'FIELD_field_first_role_delta':artifact(rolefile),
        'retired_role_mask_mapping':artifact(OUT/'retired-owned-role-to-current-canonical-role-sparse-peer-mask-mapping.json'),
        'R737_flattened_constituent_assertion_failure_preserved':artifact(H/'FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r737/failure.json'),
        'R733_full_inventory_and_R687_complete_physical_header_identity_preserved':True,
        'ROOT_ordinary_scope':artifact(opfile),'ROOT_positive_zone_scope':artifact(OUT/'corrected-ROOT-FG-distinct-priority-native-interaction.json'),
        'exact_original_locked_CORE5_dc1a_retained':preserved,'unqualified_CORE_R353_R371_new_transport_and_middle_withdrawal_excluded':True,
        'required_order':['Apply FIELD exact R157 field-first native definitions including R573 original549 negative notches',
            'Apply ROOT exact R263 ordinary/pose and retain separate two exact ROOT priority126 FG native definitions',
            'Rebind Q0/DIC/DI6 and SBC R379/R398 only through exact sparse new/delete/mask operations; native original filled arrays remain CPP-derived',
            'Map retired FIELD roles to the current canonical owner before applying each later shared-negative mask and regenerate only affected owner native parts',
            'Independently check all raw nets/profiles/definition coordinates/source and new-new clearances before ONE all-net native fill'],
        'shared_role_conflicts_requiring_later_exact_negative_replay':['Q0 bde -> cf2a FIELD_GND In1 canonical union; Q0 e2fe -> current e2fe FIELD_GND In2',
            'Q0 FA7ef local SMD shielding -> current TMR-repaired FA7ef, preserving remote TMR notch',
            'ROOT/SBC original549 ordinary antipads -> native CPP fill, preserving R573 outline-only negative definition',
            'SBC R379 positive LG In4 priority127 remains independent; do not copy rejected R360 seven trace bodies or unqualified new CORE transport'],
        'same_native_UUID_collisions_FIELD_ROOT_ordinary_and_two_FG_zones':[],'literal_all_other_original_native_chunks_preserved':True,
        'FIELD_plus_two_ROOT_zone_definition_count':sum(O.C.pcbtext.chunk_kind(c)=='zone' for c in simulated.values()),
        'no_physical_geometry_native_mask_fill_array_rule_or_source_change_in_this_supplement':True,
        'all_raw_failures_and_current_native_thermal_FAB_gates':'HELD; diagnostic only'})
    put(OUT/'receipt.json',{'status':'EXACT_SPARSE_OWNERSHIP_RECONCILIATION_NO_GEOMETRY_CHANGE_NO_NATIVE_STAGE',
        'FIELD_recipe_SHA256':sha(rf),'field_first_role_delta_SHA256':sha(rolefile),
        'composition_contract_SHA256':sha(OUT/'first-combined-native-sparse-composition-order-and-conflicts.json'),
        'profile_interaction_correction_SHA256':sha(OUT/'corrected-ROOT-FG-distinct-priority-native-interaction.json'),
        'native_UUID_collisions':0,'ROOT_FG_native_overlap_pairs':len(corrected),'existing_locked_CORE5_middle_retained':True,
        'no_board_saved_no_filled_polygon_edit_no_launch':True,'adopted':False,'elapsed_seconds':time.monotonic()-start})
    print('R739_COMPLETE',sha(OUT/'receipt.json'),'contract',sha(OUT/'first-combined-native-sparse-composition-order-and-conflicts.json'),flush=True)
if __name__=='__main__':main()
