"""Complete the omitted global In4 leg; retain the three exact R250 solves."""
import hashlib,json,pickle,sys,math,traceback
from pathlib import Path
from shapely.geometry import Point
import shapely
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import solve_CORE_R112_literal_ground_loop_r250 as S
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/CORE-R112-global-ground-loop-leg-r251'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();old=H/'sbc-power/CORE-R112-literal-four-leg-ground-loop-r250';assert sha(old/'receipt.json')=='8855d5c95f55b9de27a14f9b976c0443188c2c9d61427a7e826c3c13f12ab3f0';mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes());vs={v['uuid']:v for v in h['vias']};source=vs['07ec511d-7db2-4d0a-b3e6-724f14592d86'];cross=vs['009de6d1-a266-4015-9fa1-fd0e2e809155'];target=vs['2712cb19-4473-49e1-832c-7afe543955d9'];base=H/'sbc-power/CORE-R112-exact-ground-cross-layer-topology-r249';shape=S.pieces(shapely.from_wkb((base/'In4.Cu-exact-drilled-source-ground-union.wkb').read_bytes()))[1];assert abs(shape.area-8487.939611536442)<1e-8
 def ann(v):return Point(v['x'],v['y']).buffer(v['d']/2-.00000002,quad_segs=128).difference(GP.bounded_disk(v,v['drill']/2+.00000002))
 sa=ann(cross).intersection(shape);ta=ann(target).intersection(shape);f=O/'global-In4-exact-physical-sheet.wkb';f.write_bytes(shape.wkb);rows=[]
 for step in(.1,.075):
  r=S.solve(shape,sa,ta,step);rows.append(r);put(O/'checkpoint.json',rows);print('R251_GLOBAL_IN4',json.dumps(r),flush=True)
 prior=json.loads((old/'checkpoint.json').read_text());roles=['regulator_GND4_to_actual_07ec','source_ground_actual_07ec_to_actual_009d','FPGA_actual_2712_to_GND_A1'];fixed=[next(r for r in reversed(prior)if r['role']==role and r['conservative_contained_path'])for role in roles];success=[r for r in rows if r['conservative_contained_path']];cases=[];feedp=H/'sbc-power/CORE-R112-wide-actual-annular-contained-sheet-r247/receipt.json';assert sha(feedp)=='6604bebdb45eda2e89bacde9bf3b5f53f3588743dfbb3fadfc072b2962c1238c';feed=json.loads(feedp.read_text())
 if success:
  total=sum(r['effective_sheet_squares']for r in fixed)+success[-1]['effective_sheet_squares']
  for cu in(35,25):
   for temp in(60,100,125):
    rho=1.7241e-8*(1+.00393*(temp-20));rs=total*rho/(cu*1e-6);barrels=[]
    for v,length in((source,.255),(cross,.765),(target,1.020)):
     d=v['drill']*1e-3;t=.020e-3;rr=rho*(length*1e-3)/(math.pi*((d/2+t)**2-(d/2)**2));barrels.append({'UUID':v['uuid'],'used_length_mm_CONDITIONAL_stack':length,'conditional_finished_plating_um':20,'R_ohm':rr})
    drop=.8*(rs+sum(r['R_ohm']for r in barrels));fd=next(r['sheet_plus_two_used_barrels_drop_V']for r in feed['conditional_supply_cases']if r['conditional_Cu_um']==cu and r['conditional_copper_temperature_C']==temp);cases.append({'conditional_Cu_um':cu,'conditional_temperature_C':temp,'four_actual_return_sheet_squares':total,'three_actual_return_barrel_rows':barrels,'return_sheet_R_ohm':rs,'full_0p8A_this_single_pin_return_drop_V':drop,'new_feed_plus_literal_return_drop_V':fd+drop,'remaining_low1p185V_to_local1p15V_budget_V':.035-fd-drop,'all_shared_logic_loads_other_pin_allocations_source_old_In3_VOS_remote_return_capacitor_effectiveC_ESL_and_transients_still_unqualified':True})
 put(O/'receipt.json',{'verdict':'LITERAL_FULL_GLOBAL_IN4_RETURN_AND_THREE_SAVED_LEGS_CONDITIONAL_SINGLE_PIN_NUMERICS'if success else'LITERAL_GLOBAL_IN4_EXACT_CONNECTED_FACE_HAS_NO_CONTAINED_PATH_AT_DECLARED_GRID_RESOLUTIONS','exact_R112_model_sha256':sha(mp),'exact_global_In4_physical_WKB_sha256':sha(f),'global_In4_rows':rows,'three_saved_exact_R250_leg_rows':fixed,'unchanged_R250_receipt_sha256':sha(old/'receipt.json'),'conditional_full_loop_cases':cases,'no_original_two_unrooted_FPGA_GND_R7_T4_hidden':True,'full_0p8A_CORE_2A_IO3_retained':True,'literal_series_route_is_one_current_stress_CASE_no_equal_pin_layer_barrel_sharing_or_physical_rating_claim':True,'other_parallel_real_ground_paths_not_credited_in_this_series_case':True,'grid_convergence_and_fixed_terminal_equipotential_and_plating_tolerance_full_shared_ground_current_native_thermal':'OPEN','source_supply_VOS_and_all31_FPGAGND_actual_low_voltage_potential_full_capacitor_transient_loop':'OPEN','no_reference_readiness_gate_changed':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R251_COMPLETE',sha(O/'receipt.json'),'cases',len(cases),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
