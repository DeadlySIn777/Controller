"""Derive one explicit owned-only field-return notch proposal, with all gates open."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'probe_CORE_two_new_ordinary_port_layer_feeds_r94.py';s=base.read_text();changes=[]
def rep(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b})
rep("CORE-native-IO3-antipad-external-port-nominees-r93';assert sha(ports/'receipt.json')=='a206d92084e3f64d92d17c1ebb841e9cc9600d9dd6c9961e5ab4c97ac891dc06'", "CORE-partial-annular-native-IO3-antipad-port-nominees-r95';assert sha(ports/'receipt.json')=='a4eb4c826f82ede130116afbe5def91c505e8003f3196d0600a4b32f5fb8cfb7'")
rep('assert len(main_ports)==len(source_ports)==1','assert len(main_ports)==2 and len(source_ports)==3')
rep("assert {q['uuid']for q in pair}=={'04d05723-e107-55db-ab38-b494ef73fd44','ba6844fd-46da-52c3-a576-bf0dae97cc04'}", "assert pair[1]['uuid']=='0c3c4802-aa2d-55ad-a84b-6e2acf573601';owned_field_barrier='e2fe644a-2849-5c69-8ebb-d1e94909cd4c'")
rep("CORE-two-new-ordinary-port-layer-feed-proposals-r94';assert", "CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';assert")
rep("for layer in ('In2.Cu','F.Cu','B.Cu','In4.Cu','In3.Cu','In1.Cu'):", "assert len([q for q in z if q['uuid']==owned_field_barrier and q['layer']=='In2.Cu'and q['net']=='/motherboard_motors{slash}FIELD_GND'])==1\n for layer in ('In2.Cu',):")
rep("q['uuid']==cuttable.get(layer)or not search.intersects", "q['uuid']==cuttable.get(layer)or q['uuid']==owned_field_barrier or not search.intersects")
rep("'only_new_owned_LG_bounded_notch_proposed':cuttable.get(layer)", "'only_new_owned_LG_bounded_notch_proposed':cuttable.get(layer),'only_new_owned_FAG_In2_bounded_notch_proposed':owned_field_barrier,'FAG_unmodified_required_Cu_gap_with_constructor_margin_mm':.625100")
rep("'controller-core-two-new-ordinary-feed-r94/'", "'controller-core-owned-FAG-In2-notch-feed-r98/'")
rep("'actual_all6_new_ordinary_native_antipads_all77_contacts_direct_original_fill_contacts_source_no_loss_reference_current_drop_cap_loops_stability_thermal_native_DRC':'OPEN'", "'actual_all6_new_ordinary_native_antipads_all77_contacts_direct_original_fill_contacts_source_no_loss_reference_current_drop_cap_loops_stability_thermal_native_DRC':'OPEN','one_only_OWNED_NEW_FAG_In2_notch_scope':owned_field_barrier,'FAG_J3_2_all_prior_source_contacts_four_distinct_TPS26624_RTN_obligations_input_4_58442937244A_and_full_current_mesh_after_actual_cut_REQUIRED':True,'no_old_native_FAG_outline_settings_or_fills_credited_changed_by_this_nomination':True")
rep("'R94_FINITE_FEED_PROPOSAL'", "'R98_BOUNDED_NEW_FAG_IN2_NOTCH_FEED_PROPOSAL'")
compile(s,'probe_CORE_owned_FAG_In2_notch_feed_r98.py','exec');out=H/'probe_CORE_owned_FAG_In2_notch_feed_r98.py';assert not out.exists();out.write_text(s)
(H/'CORE-owned-FAG-In2-notch-feed-r98-derivation.json').write_text(json.dumps({'base_script_sha256':sha(base),'new_script_sha256':sha(out),'changes':changes,'separator_diagnosis_receipt_sha256':sha(H/'CORE-exact-remaining-port-face-separators-r97/receipt.json'),'ordinary_via_sizes_AND_foreign_gap_NOT_reduced':True,'only_owned_new_FAG_In2_e2fe_bounded_notch_plan_ALLOWED_NOT_YET_IMPLEMENTED_OR_ACCEPTED':True,'all_old_SOURCE_no_loss_reference_physical_guard_full_current_after_cut_native_GATES_OPEN':True},indent=1)+'\n');print('R98_DERIVED',sha(out),flush=True)
