"""Continue lazy annulus routing on actual corrected coupled source coordinates."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'repair_fbg_lazy_existing_returns_r10.py';o=H/'repair_logic_lazy_existing_returns_r12.py';assert not o.exists()
s=p.read_text();a=s.index(" assert sha(mp)==r['model_sha256']");e=s.index(' assert not OUT.exists()',a)
s=s[:a]+''' assert sha(mp)==r['model_sha256'] and r['actual_C_R102_R10_composed'] is True
 assert r['R106_model_sha256']=='3f9086799fb85283714126d51b1e7cc8dc477ffe8a3ed0b1c06edd91071dcf39'
 assert r['R10_proposed_zones_sha256']=='71b394897846e693fcb4abdbc41c71b5c93ec50c6e31c6ef206890b6662bc5fb'
 assert r['all_other_R106_h_and_owned_planes_exact'] and r['R10_source_spine_exact']
 assert all(not q['prior_actual_source_pad_losses']for q in r['actual_source_retention'])
''' +s[e:]
changes={"OUT=H/'fbg-lazy-existing-return-restoration-r10'":"OUT=H/'logic-lazy-existing-return-restoration-r12'","[('/motherboard_do/FIELD_B_0V','J11005')]":"[('/LOGIC_GND','J11001')]","'controller-fbg-existing-return-r10/'":"'controller-logic-existing-return-r12/'",'Field B existing-annulus return continuation R10':'Logic existing-annulus return continuation R12','FBG_LAZY_PATH':'LOGIC_LAZY_PATH','FBG_RETURN_R10_FROZEN':'LOGIC_RETURN_R12_FROZEN'}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
compile(s,str(o),'exec');o.write_text(s)
(H/'logic-lazy-existing-returns-r12-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'actual_corrected_R102_via_stub_C_CORE91_ROOT4_R10_coordinates_used':True,'only_LG_bank_source_J11001_2_selected_with_same_full_guard_source_projection_and_bank_proof':True,'foreign_new_planes_actual_discrete_rule_areas_C_reference_masks_hard':True,'all_mutual_native_current_gates_open':True,'native_jobs':0,'board_written':False},indent=1)+'\n')
print(json.dumps({'script':str(o),'sha256':sha(o)}))
