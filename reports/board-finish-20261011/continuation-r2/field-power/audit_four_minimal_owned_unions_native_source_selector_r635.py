"""Correct only the frozen audit's U11018 output-pin selector; no geometry edits."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
old=H/'audit_four_minimal_owned_unions_actual_contacts_reference_r633.py'
failed=H/'four-minimal-owned-unions-actual-all-drill-source-contact-reference-r633/failure.json'
assert not failed.exists()
failed.write_text(json.dumps({'status':'FAILED_SOURCE_SELECTOR_AFTER_FOUR_FRESH_ACTUAL_GRAPH_BUILDS','helper_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'incorrect_requested_source':'U11018.8','frozen_native_source_output':'U11018.1','native_pin_function':'OUT_1','native_pin_type':'power_out','no_geometry_or_source_or_native_stage_changed':True,'completed_output_file':'exact-minimal-owned-role-original-identity-and-negative-only-proof.json'},indent=1)+'\n',encoding='utf-8')
s=old.read_text(encoding='utf-8').replace('r633','r635').replace('R633','R635')
wrong="('/motherboard_do/DOB_FIELD_3V3','U11018','8')"
assert s.count(wrong)==1
s=s.replace(wrong,"('/motherboard_do/DOB_FIELD_3V3','U11018','1')")
anchor=' sources=[]\n'
assert s.count(anchor)==1
proof=''' sources=[]
 from inventory import PARSER
 from export_ab_native import load_parser
 source=H/'combined-power-source-r3-hierarchy/source-export/fresh.net'
 assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 nl=load_parser(PARSER)['read_netlist'](source)
 assert nl['node_net'][('U11018','1')]=='/motherboard_do/DOB_FIELD_3V3'
 assert nl['node_net'][('L11003','2')]=='/motherboard_power_entry/FIELD_5V'
 put(OUT/'native-authoritative-added-source-selectors.json',{'fresh_source_SHA256':sha(source),'U11018.1':{'net':nl['node_net'][('U11018','1')],'pin_function':'OUT_1','pin_type':'power_out'},'L11003.2':{'net':nl['node_net'][('L11003','2')]},'failed_prior_helper_SHA256':sha(H/'audit_four_minimal_owned_unions_actual_contacts_reference_r633.py'),'failed_receipt_SHA256':sha(H/'four-minimal-owned-unions-actual-all-drill-source-contact-reference-r633/failure.json'),'all_physical_and_source_geometry_unchanged':True})
 checkpoint=OUT/'fresh-four-actual-graphs-checkpoint.pkl';checkpoint.write_bytes(pickle.dumps(now,protocol=5))
 put(OUT/'fresh-four-actual-graphs-checkpoint-receipt.json',{'current_model_SHA256':sha(M),'before_group_SHA256':sha(gf),'fresh_four_graph_checkpoint_SHA256':sha(checkpoint),'changed_nets':sorted(changed),'remaining_contact_source_reference_checks':'OPEN'})
'''
s=s.replace(anchor,proof)
exec(compile(s,str(Path(__file__)),'exec'))
