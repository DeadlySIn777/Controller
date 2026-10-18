"""Freeze completed R609 physical proof after receipt-only Path/list failure."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
O=H/'original-IO3-TMR-R587-fresh-native-completed-proof-r613'
A=H/'original-IO3-TMR-R587-fresh-native-all-drill-source-contact-r609'
N=H/'original-IO3-TMR-outline-only-native-API-selected-FA-IO3-r587'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
assert not O.exists();O.mkdir()
helper=H/'audit_R587_fresh_native_all_drill_TMR_source_contact_r609.py'
put(A/'failure.json',{'status':'RECEIPT_SERIALIZATION_FAILURE_AFTER_COMPLETED_FRESH_NATIVE_GRAPH_AND_ALL_SOURCE_CONTACT_NOZONE_OUTPUTS','helper_SHA256':sha(helper),'failure':'inputfiles appended variable source, the completed source-result list, rather than a helper Path; AttributeError list.resolve. All comparison and graph files were written before this error; no geometry/native/model mutation.'})
assert sha(N/'receipt.json')=='3e311f29e40798b65f2e6ee08d79c304f1021f5bc11da0c5657992e0fa63f8a5'
receipt=read(N/'receipt.json');fill=read(N/'scoped-fill/receipt.json');api=read(N/'native-outline-API.json');expected=read(N/'exact-native-outline-shadow-expected.json')
assert fill['candidate_sha256']==api['candidate_sha256']==expected['candidate_sha256']=='73ddd001ae470e124c9cfb9f48ee8b5e4272403253463806ee04809fbb06fceb'
assert sha(N/'scoped-fill/geometry.json')==fill['geometry_sha256']=='ea90a5639bebaec4cc8afe28b2052e3eb5c1294c5a51f1a9acd56a8fd20fe170'
assert sha(N/'scoped-fill/actual-via-flashes.json')==fill['actual_via_flashes_sha256']=='cc0c4bdc24d1c4242c015bfac82e16f98452b8515be6b7042b622426e5de6ca5'
assert not api['errors']and not fill['all_discrete_post_fill_errors']and fill['filler_ok']
sources=read(A/'actual-native-selected-source-and-host-delta.json');contacts=read(A/'all-selected-host-prior-native-physical-relationships.json');direct=read(A/'all-selected-host-before-direct-fill-contacts.json');nozone=read(A/'native-filled-and-intended-TMR-nozone-errors.json');ann=read(A/'existing498-real-all-layer-annular-contacts.json');rings=read(A/'native-intended-TMR-rule-ring-binding.json');pads=read(A/'exact-native-physical-pad-bindings.json')
assert len(rings)==28 and not nozone and not read(A/'native-direct-contact-disagreements.json')
assert not any(x['losses']for x in contacts)
for s in sources:
 assert not s['R515_host_prior_source_keys_lost']and not s['R155_prior_source_keys_lost']and not s['actual_native_R218_prior_source_keys_lost']
assert sources[0]['R14045_exact_eight_keys_rooted']and sources[0]['existing498_actual_In2_source_fill_annulus']['finite_overlap_nonempty']
assert all(x['retained_direct_any_same_net_native_fill_touch']for x in direct)
count={label:sum(x['baseline']==label for x in direct)for label in ('R515_host_before','R218_actual_native_before')}
assert count['R515_host_before']==605
prior=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r563/fresh-native-selected-all-drilled-groups.pkl';assert sha(prior)=='714aa0188e069e636559be9a4f49c6017d5a57fe7037808af1e42622c1a45b3b'
files=[Path(__file__),helper,H/'audit_R587_fresh_native_all_drill_TMR_source_contact_r607.py',H/'audit_native_TMR_R218_resolved_r563.py',N/'receipt.json',N/'scoped-fill/receipt.json',N/'scoped-fill/geometry.json',N/'scoped-fill/actual-via-flashes.json',N/'native-outline-API.json',N/'exact-native-outline-shadow-expected.json',N/'copy/board.kicad_pcb',N/'copy/board.kicad_dru',prior]+sorted(A.glob('*.json'))+[A/'fresh-native-selected-all-drilled-groups.pkl']
put(O/'receipt.json',{'status':'R587_ACTUAL_CPP_SELECTED_FA_IO3_ALL_DRILL_SOURCE_CONTACT_AND_TMR_BOTH_ROLE_PASS_FULL_BOARD_CURRENT_DRC_OPEN','candidate_SHA256':fill['candidate_sha256'],'native_geometry_SHA256':fill['geometry_sha256'],'actual_via_flashes_SHA256':fill['actual_via_flashes_sha256'],'actual_selected_zone_count':len(fill['selected_zone_UUIDs']),'actual_native_pad_bindings':len(pads),'sources':sources,'all_old_physical_group_losses':0,'prior_R515_R155_and_actual_R218_source_key_losses':0,'host_BEFORE605_direct_contact_count':count['R515_host_before'],'actual_R218_BEFORE_direct_contact_count':count['R218_actual_native_before'],'all_direct_contact_losses':0,'existing498_finite_annular_contacts':ann,'API_all28_outer_hole_rings_and_native_profiles_exact':True,'raw_native_AREA_AST_API_model_exact_three_integer_vertices_and_layers':read(A/'actual-native-area-exact-closed-shape-schema-and-raw-AST-binding.json'),'native_physical_and_intended_nozone_errors':nozone,'actual_groups_file':str((A/'fresh-native-selected-all-drilled-groups.pkl').resolve()),'actual_groups_SHA256':sha(A/'fresh-native-selected-all-drilled-groups.pkl'),'proof_mode':'Fresh K.physical graph built from the NEW R587 CPP export and all drills; preserved R218 graph used only as BEFORE comparator. R609 failed only after freezing all independent source/contact/nozone proof outputs.','raw_R563_original5492_boundary_FAIL_preserved':True,'raw_R575_R577_virtual_clip_failures_NOT_USED':True,'all8_R567_zone_overlap_errors_and_inherited_current_reference_CORE_ROOT42_FAIL_OPEN_preserved':True,'unselected_nets_full_board_DRC_reference_current_thermal_SI':'OPEN_NO_SELECTED_CREDIT','inputs_SHA256':{str(p.resolve()):sha(p)for p in files},'native_jobs':0,'board_or_model_written':False,'adopted':False})
print('R613',sha(O/'receipt.json'),'direct',count,'nozone',len(nozone),flush=True)
