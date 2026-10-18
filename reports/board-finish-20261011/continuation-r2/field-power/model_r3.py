"""Exact-source-bound current ledger after the qualified local input-cap choice."""
import copy,json,math
from inventory import HERE,BOARD,sha

def main():
 out=HERE/'normal-model-r3.json'
 if out.exists():raise ValueError('Frozen current ledger exists')
 old=HERE/'normal-model-r2.json';source=HERE/'combined-power-source-r2';cap=HERE/'new-local-bypass-r2.json'
 paths=[old,BOARD,cap,source/'receipt.json',source/'source-export/receipt.json',source/'source-export/fresh.net',HERE/'candidate-recipe-r1/receipt.json']
 before={str(p.resolve()):sha(p) for p in paths};r=copy.deepcopy(json.loads(old.read_text(encoding='utf-8')))
 export=json.loads((source/'source-export/receipt.json').read_text(encoding='utf-8'));assert export['verdict']=='PASS'
 r['schema']='root106-signed-field-normal-planning-v4-C95-combined-native-source'
 r['supersedes_model_sha256']=sha(old)
 r['source_export_sha256']=sha(source/'source-export/fresh.net')
 r['source_branch']='combined-power-source-r2: fresh native exact14 existing pad moves +6 new parts +L11001/C11061 Value/MPN only PASS; board adoption pending'
 r['source_binding']={'fresh_net_sha256':sha(source/'source-export/fresh.net'),'source_receipt_sha256':sha(source/'receipt.json'),'native_source_receipt_sha256':sha(source/'source-export/receipt.json'),'counts':export['counts'],'field_layout_recipe_sha256':sha(HERE/'candidate-recipe-r1/receipt.json')}
 c95_leak=.000010
 r['computed_local_output_envelopes_a']['FIELD_B5V_PRE_after_split']+=c95_leak
 r['C11095_local_bypass']={'MPN':'C1608X7R1H105K080AB','value':'1uF50VX7R0603','rail':'/motherboard_safety_sensor/FIELD_B_5V_PRE','ground':'/motherboard_do/FIELD_B_0V','DC_leak_reservation_a':c95_leak,'leak_is_reservation_not_measured_or_guaranteed_corner':True,'normal_capacitor_DC_load_not_C_dVdt':True,'startup_nominal_dVdt_factor_A_per_V_per_s':1e-6,'tolerance_positive_nominal_startup_factor_A_per_V_per_s':1.1e-6,'input_effective_screen_uF':.5508,'TI_input_minimum_uF':.1,'TI_recommended_input_uF':10.,'not_claimed_to_meet_10uF_recommendation':True,'effective_screen_basis':'1uF *.9 initial tolerance *.85 X7R temperature *.9 DC-bias planning floor *.8 explicit aging reservation. Primary reference curve interpolation at5.1V gives.9547206uF; neither curve nor arbitrary20% aging reservation is a guaranteed combined-corner manufacturer bound.','primary_cap_and_land_receipt_sha256':sha(cap),'local_input_return_loop_mm':4.574327131,'remote_C11076_preserved_as_nonlocal_corrected_B5PRE_cap':True,'assembly_note':'Native0603 lands fit stated body/terminal bounds but pad length/width exceed TDK reflow example ranges; paste/fillet review remains explicit.'}
 r['cap_and_dynamic_load_accounting']={'C11095_DC_reservation_in_B5PRE_a':c95_leak,'B5PRE_complete_DC_with_all_two_LDO_input_targets_a':r['computed_local_output_envelopes_a']['FIELD_B5V_PRE_after_split'],'B5PRE_routing_target_a':.140,'complete_DC_remaining_routing_margin_a':.140-r['computed_local_output_envelopes_a']['FIELD_B5V_PRE_after_split'],'routing_target_unchanged_and_buck_signed_accounting_unchanged':True,'each_input_cap_startup_current':'I=C_effective*dVIN/dt; no normal DC reservation proves simultaneous22uF LDO output+input-cap inrush or fault-current coordination.','each_LDO_output_cap_nominal_uF':{'U11017':22.,'U11018':22.,'U11038':22.},'all_output_caps_effective_and_stability_qualification':'Primary nominal source parts are preserved; mounted effective capacitance, ESR, loop parasitics and transient stability need qualified physical/corner evidence.'}
 r['source_specific_return_cut_contract']={
  'sign_convention':'Positive load GND current is delivered into the ground net; converter negative GND injection is withdrawn from it. Supply/OUT/GND satisfy IN=OUT+GND. Source connector return is the complete network sum, not an assumed current through every island or bridge.',
  'FA':{'real_external_source_pad':'J11003.2','connector_signed_return_a':r['real_connector_input_return_envelopes_a']['FA'],'all_positive_ground_terms_upper_a':r['signed_return_cut_examples']['FA']['external_return_and_local_loads_a'],'buck_negative_GND_a':r['signed_regulator_ports']['U11009']['GND_injection_a'],'DO_external_terminal_group':['JD09.A9','JD09.A10','JD09.A11','JD09.A12'],'DO_return_group_combined_a':4.,'DO_parallel_connector_pin_split':'Physical sharing must be solved; equal1A each is not assumed.','three_layer_r2_target_group0':'25 control/probe/driver-ground pads only; not the4A JD09 output-return island.'},
  'FB':{'real_external_source_pad':'J11005.2','connector_signed_return_a':r['real_connector_input_return_envelopes_a']['FB'],'all_positive_ground_terms_upper_a':r['signed_return_cut_examples']['FB']['external_return_and_local_loads_a'],'buck_negative_GND_a':r['signed_regulator_ports']['U19028']['GND_injection_a'],'DO_external_terminal_group':['JD09.B9','JD09.B10','JD09.B11','JD09.B12'],'DO_return_group_combined_a':4.,'DO_parallel_connector_pin_split':'Physical sharing must be solved; equal1A each is not assumed.','three_layer_r2_target_group0':'170 retained pads including4A DO/sensor/DI return. Use complete positive4.85896349563A as a conservative remote cut reservation if negative buck GND stays near source; do not use connector4.76859682896A blindly.'},
  'local_return_requirements':{'new_U11038_GND':'1mA LDO Iq plus localR11088.345230769mA bleed and cap transient; remote output-load return follows its actual devices. The .041A input target is not all injected into the new regulator ground pad.','U11018_GND':'1mA LDO Iq plus originalR11065.345230769mA bleed and cap transient; retained logic device currents are allocated at their actual GND ports.','U11017_GND':'1mA LDO Iq plus local output/passive bleed and cap transient; A domain VDD loads allocated at their real ground ports.','TPS274_VS_VDD_GND':'Every parallel physical port pad must connect. Total VS and VDD Iq are distinct from external0.5A output loads; parallel pad sharing is not inferred from pad count.','TPS26624_RTN_GND':'Total.600mA reservation counted once per device; unbounded internal return split is protected by1mA routing reservation for each physical port, preserving support graph.'},
 }
 r['PG_partial_power_startup_and_fault_analysis']={
  'FB_PGOOD_topology':'ExistingR22002 pulls up from retainedDOB_FIELD_3V3 through10k; sinks U11006.16/U22003.4/newU11038.3. It is not a24V pullup. NewPG explicitly makes dedicatedDO3V3 part of field-B health and retained latch/inhibit path.',
  'maximum_planning_pullup_current_a':3.366/(10000*.975),
  'TPS7A16_PG_bounds':'RecommendedPG0..5V/absolute5.5V;1mA sink condition; PG may be undefined belowVIN3V. Falling threshold83..93% of3.3V=2.739..3.069V.',
  'PG_is_not_READY':'TPS274 VDDUVLO rising2.8..2.98V permits PG release below the maximum READY threshold. Preserve hardware inhibit, SPI READY/POR/register initialization and deliberate rearm. Existing8.333MHz SPI/control rate remains unchanged.',
  'TPS274_partial_power':'VDD first withoutVS is not READY and output is disabled; VDD UVLO falling2.7..2.9V disables output/READY state, recovery includes POR. All unpowered interface states, alive-side injection and isolation-default behavior need the actual datasheet/physical power-sequence checks; no synthesized presence or forced ready signal.',
  'TPS7A16_reverse_power':'Input collapse with charged22uF output can violate VOUT-VIN .3V absolute condition or cause reverse current; input/output collapse and alive interface backfeed require fault/partial-power qualification. Do not assumePG alone handles this.',
  'timing':'No guaranteed PG maximum fall delay is provided by the rows screened;20ms system fault reaction is not proven by nominalPG threshold or aDC network.',
  'startup':'BothB LDOs plus existing/new input bypass and22uF outputs must be included in B5 .6A buck soft-start/capacitance/stability and eFuse coordination. The TPS7A16 current-limit row atVIN3V does not guarantee a5V fault corner.',
  'isolation_and_rearm':'Preserve all isolator boundaries, safety health latches, independently fitted12 motor enable/alarm and16DO .5A/channel. Neither split rail nor PG change grants automatic restart.',
 }
 r['power_corridor_plan']={
  'source_bound_candidate_recipe_sha256':sha(HERE/'candidate-recipe-r1/receipt.json'),
  'return_first':'Add exact source-PTH bridges to prospective model before using them as signal references. FBG target0 complete remote island; FAG target0 is a local-control island and JD09 group38 remains required.',
  'main_copper_policy_a':6.5,
  'current_sized_local_joins':'Use actual positive/signed cut load for each local group; do not put6.5A through each island. Preserve all untouched contacts and rule barriers. Targeted blocker rework may create a complete corridor when additive paths fail.',
  'capacity_evidence':'Native35um six-layer stackup is nominal evidence. Sheet/barrel solve must use exact polygon widths, length, current sharing and source/load contacts; PTH plating and temperature conditions remain unspecified. Merely summing width or vias is not qualification.',
  'routing_required':['FA/FB protected24 full simultaneous trunk and all device VS groups','FAG/FBG source-rooted full signed return','A5 full12 motor AUX5 and A LDO IN/EN/C74 source feed','B5PRE .140A complete buck-to-both-LDO and remoteC76/localC95 feed','DOB_DO3V3 .040A output with all ten moved VDD/pullup/cap pads','retained A/B3V3 isolated device groups and all required input/output/PG spines'],
 }
 r['applicable_routes_emitted']='Concrete14 pad net moves/5 field footprints/51 private copper retags/35 owned cuts/37 local fanout segments/six proposed source-rooted return polygons are staged. Supply/spine/all-return completion and physical/native gates remain open.'
 r['inputs_before']=before;r['inputs_after']={str(p.resolve()):sha(p) for p in paths};assert r['inputs_before']==r['inputs_after']
 for p in r['signed_regulator_ports'].values():assert math.isclose(p['IN_load_a'],p['OUT_injection_a']+p['GND_injection_a'],abs_tol=1e-12)
 assert r['computed_local_output_envelopes_a']['FIELD_B5V_PRE_after_split']<.140
 r['native_jobs']=0;r['board_or_original_source_edits']=False;r['full_rail_qualified']=False;r['manufacturing_ready']=False
 out.write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'model_sha256':sha(out),'B5PRE_complete_DC_a':r['computed_local_output_envelopes_a']['FIELD_B5V_PRE_after_split'],'connector_signed_a':r['real_connector_input_return_envelopes_a'],'inputs_unchanged':True}))

if __name__=='__main__':main()
