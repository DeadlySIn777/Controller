"""Independent source-bound conditional DC and explicit local cap/return ledger.

No numerical estimate here is a physical current, thermal, SI or native gate.
"""
import hashlib,json,pickle,sys,math,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
from verify_source import parse,child,children,atom
import contact_layout as C
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/CORE-R100-source-bound-conditional-DC-cap-return-review-r231'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin)for q in xs))
def main():
 assert not O.exists();O.mkdir();base=H/'CORE-In2-owned-notch-materialized-source-proposal-r100';assert sha(base/'model.pkl')=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';assert sha(base/'receipt.json')=='cdb3c648f30dfd0ec60d921169637c180b90769d70ef141fc19d143fb0b18258';g,h,b,z,c=pickle.loads((base/'model.pkl').read_bytes());PS.restore_bound_generated_precision_states(b,z)
 pack=H/'CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';assert sha(pack/'receipt.json')=='77e2d358f3a177854b3b2aaa4863430e36967e4eb06520f91a501742f054e4cd';route=pickle.loads((pack/'proposed-route-and-zone.pkl').read_bytes())[0];axis=LineString(route['source_to_main_points']);assert route['core_width_mm']==1.;assert abs(axis.length-68.92214006026306)<.001
 q=next(q for q in z if q['uuid']=='b0453302-df03-561f-9bc4-0560bc66658a');assert q['layer']=='In2.Cu'and q['net']=='/CORE_1V2';d=pickle.loads((base/'proposed-discrete.pkl').read_bytes());assert len(d['vias'])==2 and not d['tracks'];viaids={v['uuid']for v in d['vias']};assert all(v['d']==.5 and v['drill']==.2 for v in d['vias']);assert len(viaids)==2
 nf=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(nf)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';src=parse(nf.read_text());parts={atom(x,'ref'):x for x in children(child(src,'components'),'comp')};nets=children(child(src,'nets'),'net');pins={};rail=[]
 for net in nets:
  for n in children(net,'node'):
   node={k:atom(n,k)for k in('ref','pin','pinfunction','pintype')};node['raw_net']=atom(net,'name');pins.setdefault(node['ref'],[]).append(node)
   if atom(net,'name')=='/CORE_1V2':rail.append(node)
 groups=pickle.loads((base/'groups.pkl').read_bytes());core=root(groups['/CORE_1V2'],'L2001','2');lg=root(groups['/LOGIC_GND'],'J11001','2');corekeys={(x['kind'],x['uuid'],x['layer'])for x in core if x['kind']!='fill'};lgkeys={(x['kind'],x['uuid'],x['layer'])for x in lg if x['kind']!='fill'};corepads={x['uuid']for x in core if x['kind']=='pad'};lgpads={x['uuid']for x in lg if x['kind']=='pad'}
 circuit={}
 for ref in sorted(set(n['ref']for n in rail)|{'U2001','L2001','R2001','R2002','R2003','R2004','C2001','C2002','C2003','U1001'}):
  if ref not in parts:continue
  p=parts[ref];circuit[ref]={'value':atom(p,'value'),'footprint':atom(p,'footprint'),'fields':{atom(f,'name'):f[2]if len(f)>2 else''for f in children(child(p,'fields')or[],'field')},'exact_fresh_source_pin_rows':pins.get(ref,[])}
 caprows=[]
 for ref in sorted(set(n['ref']for n in rail if n['ref'].startswith('C'))):
  ps=[p for p in h['pads']if p['ref']==ref];supply=[p for p in ps if p['net']=='/CORE_1V2'];ground=[p for p in ps if p['net']=='/LOGIC_GND'];caprows.append({'ref':ref,'actual_value':atom(parts[ref],'value'),'physical_pads':[{'pin':p['num'],'UUID':p['uuid'],'raw_net':p['net'],'at':[p['x'],p['y']],'layers':list(p['layers']),'actual_CORE_source_pad_member':p['uuid']in corepads,'actual_J1_ground_source_pad_member':p['uuid']in lgpads}for p in ps],'all_actual_supply_pins_source_connected':bool(supply)and all(p['uuid']in corepads for p in supply),'all_actual_ground_pins_source_connected':bool(ground)and all(p['uuid']in lgpads for p in ground),'DC_continuity_does_not_qualify_local_inductance_or_effective_capacitance':True})
 portrows=[]
 groundvias=[v for v in h['vias']if v['net']=='/LOGIC_GND'and any(('via',v['uuid'],l)in lgkeys for l in('In1.Cu','In4.Cu'))]
 for v in d['vias']:
  cp=Point(v['x'],v['y']);ann=cp.buffer(.25,quad_segs=128).difference(cp.buffer(.1,quad_segs=128));oldsource=unary_union([r['shape']for r in core if r['kind']=='fill'and r['layer']=='In3.Cu']);landing=ann.intersection(oldsource).area;near=sorted([(math.dist([v['x'],v['y']],[a['x'],a['y']]),a)for a in groundvias],key=lambda r:r[0])[:3]
  portrows.append({'new_CORE_port':v,'actual_native_original_CORE_In3_finite_annular_overlap_mm2':landing,'prospective_source_layer_keys':[l for l in v['flashed']if('via',v['uuid'],l)in corekeys],'nearest_actual_J1_source_ground_barrels':[{'distance_mm':di,'UUID':a['uuid'],'at':[a['x'],a['y']],'d':a['d'],'drill':a['drill'],'actual_or_prospective_flashes':a['flashed'],'original198b_record':next((r for r in g['vias']if r['uuid']==a['uuid']),None),'actual_J1_source_layer_keys':[l for l in a['flashed']if('via',a['uuid'],l)in lgkeys]}for di,a in near],'fresh_native_all6_source_and_return_loop_gate':'OPEN'})
 # Geometric adjacent-plane coverage is reported honestly; it is not a DC
 # return-resistance solve and does not credit another power domain as ground.
 envelope=axis.buffer(.5,quad_segs=128);refrows=[]
 for layer in('In1.Cu','In4.Cu'):
  shapes=[r['shape']for r in lg if r['kind']=='fill'and r['layer']==layer and r['shape'].intersects(envelope)];ground=unary_union(shapes);gap=envelope.difference(ground);f=O/(layer+'-uniform-core-without-J1-ground-shadow.wkb');f.write_bytes(gap.wkb);refrows.append({'reference_layer':layer,'actual_J1_source_fill_coverage_mm2':envelope.intersection(ground).area,'uniform_feed_body_without_that_reference_mm2':gap.area,'missing_WKB_sha256':sha(f),'low_impedance_return_current_mesh_not_qualified':True})
 # Exact geometrical conductor path is a minimum-width construction witness.
 # Uniform-rectangle + hollow-barrel numbers are conditional bounds, not a
 # claim that source/pad spreading or the actual return contributes zero.
 I=.8;rho20=1.7241e-8;alpha=.00393;L=axis.length*1e-3;w=route['core_width_mm']*1e-3;cases=[]
 for copper_um,temp in((35,20),(35,60),(35,100),(25,100),(25,125)):
  rho=rho20*(1+alpha*(temp-20));R=rho*L/(w*copper_um*1e-6);t=.020e-3;dd=.2e-3;barrel_area=math.pi*((dd/2+t)**2-(dd/2)**2);rv=rho*.255e-3/barrel_area;rvfull=rho*1.53e-3/barrel_area;cases.append({'conditional_sheet_copper_um':copper_um,'conditional_copper_temperature_C':temp,'conditional_rho_ohm_m':rho,'uniform_1mm_core_R_ohm':R,'full_0p8A_sheet_drop_V':I*R,'full_0p8A_sheet_heat_W':I*I*R,'conditional_20um_finished_0p2mm_barrel_area_m2':barrel_area,'actual_new_In2_In3_center_spacing_mm':.255,'two_used_layer_barrels_R_ohm':2*rv,'conditional_two_full_1p53mm_barrels_R_ohm':2*rvfull,'sheet_plus_two_short_barrels_drop_V':I*(R+2*rv),'nominal_1p2V_minus_that_supply_drop_V':1.2-I*(R+2*rv),'return_and_spreading_and_source_ripple_not_zero_ASSUMPTIONS_OPEN':True})
 primary={'Efinix_T20':{'url':'https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf','revision':'DST20-v6.0 November2025','pages':[52,53,56,57],'package_and_grade_source':'actual T20F256I4','VCC_and_PLL_recommended_at_device_pins_relative_to_local_GND_V':[1.15,1.2,1.25],'user_mode_current_requires_actual_power_estimator_not_typical_leakage_derating':True},'TI_TPS62901':{'url':'https://www.ti.com/lit/ds/symlink/tps62901.pdf','revision':'SLVSFS7A January2024','pages':[5,19,23,39,41],'layout_obligations':'Short low impedance switching loops; close input/output capacitors; quiet short VOS/FB at output capacitor; full distributed output capacitance and stability remain separate.'}}
 put(O/'actual-source-circuit-pin-and-value-ledger.json',circuit);put(O/'exact-local-CORE-capacitor-source-return-membership.json',caprows);put(O/'actual-CORE-and-J1-return-port-rows.json',portrows);put(O/'uniform-body-reference-coverage.json',refrows);put(O/'conditional-DC-cases.json',cases)
 put(O/'receipt.json',{'verdict':'INDEPENDENT_SOURCE_PIN_CAP_RETURN_LEDGER_AND_CONDITIONAL_DC_ONLY_FULL_RATING_OPEN','exact_ROOT_R100_model_sha256':sha(base/'model.pkl'),'exact_R100_source_contact_receipt_sha256':sha(base/'receipt.json'),'exact_source_sha256':sha(nf),'route_length_mm':axis.length,'minimum_constructor_core_mm':route['core_width_mm'],'full_CORE1V2_A_retained':I,'full_IO3_A_retained':2.,'exact_source_device':'T20F256I4','actual_regulator':'TPS62901RPJR','rail_pin_count':len(rail),'capacitor_count':len(caprows),'all_listed_cap_supply_and_ground_source_connected':all(r['all_actual_supply_pins_source_connected']and r['all_actual_ground_pins_source_connected']for r in caprows),'conditional_DC_cases':cases,'actual_new_port_source_and_return_rows_sha256':sha(O/'actual-CORE-and-J1-return-port-rows.json'),'source_circuit_values_and_mode_REQUIRE_REVIEW_sha256':sha(O/'actual-source-circuit-pin-and-value-ledger.json'),'uniform_body_ground_coverage_sha256':sha(O/'uniform-body-reference-coverage.json'),'primary_manufacturer_contracts':primary,'capacitor_effective_C_ESR_ESL_local_loop_source_accurate_mode_feedback_regulator_corners_return_sheet_current_sharing_barrel_plating_thermal_native_flash_DRC':'OPEN','no_equal_current_sharing_fixed_via_ampacity_or_source_rating_assumption':True,'no_original_source_geometry_rule_or_reference_gate_mutation':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R231_COMPLETE',sha(O/'receipt.json'),'caps',len(caprows),'allcapnodes',all(r['all_actual_supply_pins_source_connected']and r['all_actual_ground_pins_source_connected']for r in caprows),flush=True);print('R231_MODE_FB',{r:circuit[r]for r in('R2001','R2003','R2004')if r in circuit},flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
