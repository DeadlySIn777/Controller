"""Conditional local trace arithmetic only; no whole PDN/current rating.

Duplicate coincident CORE5 source records are one physical copper capsule.
No independent doubled width, equal-share pin current or qualified copper,
plating or temperature is credited.
"""
import hashlib,json,pickle,math
from pathlib import Path
H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/literal-T4-R7-local-trace-conditional-resistance-r260'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();p4=H/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r256/proposed-discrete.pkl';p7=H/'sbc-power/R7-NW-fullwidth-two-B-trunk-detour-nominations-r259/first-nominee-discrete.pkl';d4=pickle.loads(p4.read_bytes());d7=pickle.loads(p7.read_bytes());length=lambda ts:sum(math.dist(t['a'],t['b'])for t in ts)
 l4=length([t for t in d4['tracks']if t['net']=='/LOGIC_GND']);l5=length([t for t in d4['tracks']if t['net']!='/LOGIC_GND']);l7=length([t for t in d7['tracks']if t['net']=='/LOGIC_GND']);l12=length([t for t in d7['tracks']if t['net']=='/CORE_1V2']);old12=.7+math.hypot(.4,.4)
 rows=[]
 for cu in(35,25):
  for temp in(60,100,125):
   rho=1.7241e-8*(1+.00393*(temp-20));rs=rho/(cu*1e-6);barrel=rho*(.255e-3)/(math.pi*((.1e-3+.020e-3)**2-(.1e-3)**2));rows.append({'conditional_Cu_um':cu,'conditional_copper_temperature_C':temp,'sheet_ohm_per_square':rs,'T4_new_0p20mm_trace_R_ohm':rs*l4/.2,'T4_0p8A_alllocalized_at_this_pin_local_trace_drop_mV_STRESS_ONLY':.8*rs*l4/.2*1000,'R7_new_0p20mm_trace_R_ohm':rs*l7/.2,'R7_0p8A_alllocalized_at_this_pin_local_trace_drop_mV_STRESS_ONLY':.8*rs*l7/.2*1000,'R7_conditional_F_to_In1_0p255mm_20um_plating_barrel_R_ohm':barrel,'R7_conditional_trace_plus_barrel_drop_mV_at0p8A':.8*(rs*l7/.2+barrel)*1000,'T4_CORE5_original_one_physical_1p25mm_trunk_R_ohm':rs*13.1/1.25,'T4_CORE5_new_1p25mm_trunk_R_ohm':rs*l5/1.25,'T4_CORE5_incremental_local_R_ohm':rs*(l5-13.1)/1.25,'T4_CORE5_if_full7p882034293398381A_used_this_local_piece_delta_drop_mV_BOUND_ONLY':7.882034293398381*rs*(l5-13.1)/1.25*1000,'R7_CORE1V2_old_two_series_1p25mm_legs_R_ohm':rs*old12/1.25,'R7_CORE1V2_new_two_series_1p25mm_legs_R_ohm':rs*l12/1.25,'R7_CORE1V2_full0p8A_local_delta_drop_mV':.8*rs*(l12-old12)/1.25*1000})
 result={'verdict':'CONDITIONAL_LOCAL_TRACE_ARITHMETIC_NOT_FULL_SOURCE_PIN_LOAD_MESH_CURRENT_THERMAL_OR_TRANSIENT_PROOF','T4_delta_sha256':sha(p4),'R7_first_nominee_delta_sha256':sha(p7),'exact_lengths_mm':{'T4_ground_0p20':l4,'T4_CORE5_new_1p25':l5,'T4_CORE5_old_1p25_one_physical_coincident_trunk':13.1,'R7_ground_0p20':l7,'R7_CORE1V2_new_1p25':l12,'R7_CORE1V2_old_1p25_series':old12},'conditional_cases':rows,'full_current_0p8A_CORE_2A_IO3_7p882034293398381A_CORE5_not_reduced':True,'no_equal_sharing_or_two_duplicate_track_current_credit':True,'three_dimensional_local_spreading_actual_endpoints_return_mesh_complete_upstream_currents_and_local_cap_ESL_effectiveC':'OPEN','the_prior_single_real_A1_series_case_still_exceeds35mV_budget':True,'ordinary_native_DRC_actual_copper_plating_temperature_and_current_ratings':'OPEN','native_jobs':0,'board_written':False,'script_sha256':sha(__file__)};f=O/'receipt.json';f.write_text(json.dumps(result,indent=1)+'\n');print('R260_COMPLETE',sha(f),flush=True)
if __name__=='__main__':main()
