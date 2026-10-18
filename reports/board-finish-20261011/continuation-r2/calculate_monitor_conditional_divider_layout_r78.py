"""Bound only the added divider conductor's conditional DC series effect, not board accuracy."""
import hashlib,json,math,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import verify_source as V
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';tree=V.parse(source.read_text())
components={V.atom(q,'ref'):q for q in V.child(tree,'components')[1:]};assert V.atom(components['R9025'],'value')=='355000R 0.01% 5ppm'and V.atom(components['R9026'],'value')=='10000R 0.01% 5ppm'and V.atom(components['U9003'],'value')=='LTC2962HUD#PBF'
uv=next(q for q in V.child(tree,'nets')[1:]if V.atom(q,'name')=='/motherboard_motor_power/MOTOR_PWR_FIELD_A_1_UV');nodes={(V.atom(q,'ref'),V.atom(q,'pin'))for q in uv if isinstance(q,list)and q and q[0]=='node'};assert nodes=={('R9025','2'),('R9026','1'),('U9003','14')}
delta=H/'field-monitor-R9026-rotation-source-termination-r66/owned-delta.pkl';assert sha(delta)=='2669504846249102a6afe479c78f627b7729d0992c48bc64f79a330f431149c5';d=pickle.loads(delta.read_bytes());assert len(d['tracks'])==5 and len(d['vias'])==1 and all(q['layer']=='F.Cu'and q['w']==.2 for q in d['tracks']);length=sum(math.dist(q['a'],q['b'])for q in d['tracks']);assert abs(length-5.620418716093677)<1e-12
native=H/'field-monitor-native-R9026-rotation-r68/receipt.json';assert sha(native)=='3fbf5fa8c80a3bb9e03328108b677777482ae884786aef4d5ea2c09612a0baa4';nr=json.loads(native.read_bytes());assert nr['verdict']=='PASS_NATIVE_SCOPED_R9026_ROTATION_ONLY_FULL_MONITOR_GATES_OPEN'
review=H.parent.parent/'motherboard-motor-power-20260930/sources/ltc2962-primary-review.json';primary=json.loads(review.read_bytes());assert primary['threshold_v']==[.4975,.5025]and primary['adj_input_bias_max_a_at_sense_0p5v']==15e-9
nominal_top=355000.;nominal_bottom=10000.;tolerance=.0001+.0005+.0004;rows=[]
# These are explicit sensitivity inputs; they are not manufactured stack/plating measurements.
rho20=1.724e-8;alpha=.00393;temperature=125.;rho=rho20*(1+alpha*(temperature-20.));barrel_length_m=.0016;plating_m=20e-6;hole_radius_m=.0001
barrel_cross_section=math.pi*((hole_radius_m+plating_m)**2-hole_radius_m**2);barrel_R=rho*barrel_length_m/barrel_cross_section
for copper_um in(20,25,30):
 trace_R=rho*(length*1e-3)/(.2e-3*copper_um*1e-6);added_R=trace_R+barrel_R
 # Both new UV and ground traces belong to the lower-divider branch; they carry divider current.
 ideal=.5*(1+nominal_top/nominal_bottom);with_series=.5*(1+nominal_top/(nominal_bottom+added_R));max_delta=0.;corners=[]
 for rt in(nominal_top*(1-tolerance),nominal_top*(1+tolerance)):
  for rb in(nominal_bottom*(1-tolerance),nominal_bottom*(1+tolerance)):
   for threshold in(.4975,.5025):
    for bias in(-15e-9,15e-9):
     a=threshold*(1+rt/rb)+bias*rt;b=threshold*(1+rt/(rb+added_R))+bias*rt;max_delta=max(max_delta,abs(b-a));corners.append(b)
 rows.append({'assumed_outer_copper_um':copper_um,'assumed_conductor_temperature_C':temperature,'new_trace_R_ohm':trace_R,'assumed_barrel_R_ohm':barrel_R,'new_branch_total_R_ohm':added_R,'nominal_ideal_static_rail_threshold_V':ideal,'nominal_with_added_series_V':with_series,'nominal_shift_V':with_series-ideal,'nominal_shift_ppm':1e6*(with_series-ideal)/ideal,'worst_same_component_corner_series_shift_abs_V':max_delta,'component_corner_static_threshold_with_series_V':[min(corners),max(corners)],'threshold_lower_resistor_current_max_A':.5025/(nominal_bottom*(1-tolerance)+added_R)})
out=H/'monitor-conditional-divider-layout-r78.json';assert not out.exists();out.write_text(json.dumps({'verdict':'SOURCE_BOUND_CONDITIONAL_DIVIDER_SERIES_SENSITIVITY_ONLY','source_sha256':sha(source),'actual_UV_nodes':sorted(nodes),'delta_sha256':sha(delta),'native_FP_rotation_receipt_sha256':sha(native),'new_lower_branch_trace_length_mm':length,'trace_width_mm':.2,'full_nominal_divider_values_ohm':{'upper':nominal_top,'lower':nominal_bottom},'copper_resistivity_20C_ohm_m':rho20,'temperature_coefficient_per_C':alpha,'assumed_board_thickness_mm':1.6,'assumed_barrel_plating_um':20,'saved_component_corner_resistor_fraction':tolerance,'primary_datasheet':{'url':primary['url'],'revision':'Rev 0','verified_2026_10_12_web_table_page3':'ADJ497.5-502.5mV, monitor input±15nA at0.5V','saved_review_sha256':sha(review)},'sensitivity_rows':rows,'full_board_local_R9026_ground_vs_U9003_GND_potential':'UNMEASURED_NOT_ASSUMED_ZERO','other_branch_plane_current_noise_contact_barrel_thickness_thermal_fault_startup_native_DRC':'OPEN','full_threshold_or_product_accuracy_qualified':False,'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n')
print('R78_CONDITIONAL_DIVIDER',round(rows[1]['nominal_shift_ppm'],6),'ppm_at_assumed25um125C','full_board_accuracy_OPEN',sha(out))
