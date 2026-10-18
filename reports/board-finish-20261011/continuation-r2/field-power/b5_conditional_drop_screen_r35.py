"""Conditional DC copper sensitivity; explicitly excludes full mesh certification."""
import json,math
from pathlib import Path
from inventory import sha
P=Path(__file__).resolve().parent;OUT=P/'b5-conditional-drop-screen-r35'
def main():
 assert not OUT.exists();OUT.mkdir();bp=P/'b5-source-rooted-feeds-r4';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'receipt.json')=='6de12c1e964abfcc1855e4449016301dcc0c3265ae7d7a7623c8107647e59c6f';rs=[]
 for q in br['rows']:
  bridge=q.get('inner_source_bridge_route');bridge=bridge if bridge and not bridge.get('source_escape_initialization') else None;stub=float(q['stub_length_mm']);line=0 if not bridge else float(bridge['length_mm'])/float(bridge['minimum_core_width_mm']);rs.append({'target_pads':q['physical_pads'],'via_UUID':q['via']['uuid'] if 'via' in q else q.get('via_UUID'),'bridge_length_mm':0 if not bridge else bridge['length_mm'],'bridge_min_core_mm':None if not bridge else bridge['minimum_core_width_mm'],'bridge_squares':line,'outer_stub_length_mm':stub,'outer_stub_width_mm':.25,'stub_squares':stub/.25})
 rho20=1.724e-8;alpha=.00393;cases=[];I=br['routing_policy_A']
 for thick in(35.,25.):
  for temp in(20.,60.,105.):
   sheet=rho20*(1+alpha*(temp-20))/(thick*1e-6);bridgeR=sheet*sum(q['bridge_squares'] for q in rs);stubR=sheet*sum(q['stub_squares'] for q in rs);cases.append({'copper_thickness_um':thick,'copper_temperature_C':temp,'sheet_resistance_ohm_per_square':sheet,'sum_all_bridge_line_core_R_ohm':bridgeR,'sum_all_stub_line_R_ohm':stubR,'sum_line_core_drop_at_full_014A_each_V':I*(bridgeR+stubR),'sum_line_core_loss_at_full_014A_each_W':I*I*(bridgeR+stubR),'not_actual_series_or_simultaneous_branch_current_allocation':True})
 barrel=[]
 for drill in(.2,.3):
  for plating in(20.,25.):
   for temp in(20.,60.,105.):
    R=rho20*(1+alpha*(temp-20))*.0016/(math.pi*drill*.001*plating*1e-6);barrel.append({'drill_mm':drill,'barrel_length_mm':1.6,'conditional_plating_um':plating,'temperature_C':temp,'ideal_cylindrical_barrel_R_ohm':R,'drop_at_full_014A_V':I*R,'loss_at_full_014A_W':I*I*R,'not_native_flash_or_actual_plating_proof':True})
 source=P/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';r={'verdict':'CONDITIONAL_LINE_AND_BARREL_SENSITIVITY_FULL_MESH_THERMAL_PENDING','full_normal_load_A':br['complete_B5_load_A'],'routing_reservation_A':I,'input_model_sha256':br['normal_model_r3_sha256'],'native_source_sha256':sha(source),'B5_r4_construction_receipt_sha256':sha(bp/'receipt.json'),'R25_contact_aperture_receipt_sha256':sha(P/'local-and-b5-return-audit-r25/receipt.json'),'native_outline_and_drilled_physical_Cu_recipe_sha256':sha(P/'additive-ground-b5-native-recipe-r27/receipt.json'),'source_root':'L19001.2','true_upstream_supply_root':'J11005.1 through U11006/U19028; not shutdown J11006','rows':rs,'line_cases':cases,'barrel_cases':barrel,'physical_cases_are_sensitivity_inputs_not_qualified_manufacture_limits':True,'full_014A_on_each_bridge_is_separate_conservative_line_screen_not_an_invented_total_load':True,'all_load_limits_and_concurrency_unchanged':True,'open_gates':['actual full signed pin current distribution and source-rooted return drop','finite sheet solution including annular contacts/local necks and all branch contacts','native actual F/In4 flash and filled physical Cu geometry','manufactured copper/plating/package solder limits','startup cap charging/partial power/fault recovery/short circuit transients','temperature rise and temperature-dependent regulator dropout at retained full load'],'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_sha256':sha(OUT/'receipt.json'),'line_cases':cases},indent=1))
if __name__=='__main__':main()
