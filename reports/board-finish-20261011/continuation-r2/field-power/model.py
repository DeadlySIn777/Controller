"""Source-bound signed field-power planning ledger, not physical rating evidence."""
import hashlib, json, math, re
from pathlib import Path
from inventory import HERE,BASE,NET,PARSER,BOARD,load,sha

VMAX={'FIELD_A_24V_PROTECTED':30.,'FIELD_B_24V_PROTECTED':30.,'FIELD_5V':5.1,'FIELD_B_5V_PRE':5.1,'DOA_FIELD_3V3':3.366,'DOB_FIELD_3V3':3.366,'AUX_24V_A':30.,'AUX_24V_B':30.,'AUX_5V_A':5.1,'AUX_5V_B':5.1,'PRB0_24V':30.,'PRB1_24V':30.,'SENS24_G0':30.,'SENS24_G1':30.,'SENS24_G2':30.,'SAFE_24V':30.,'ARM_LAMP':30.}
SUFFIX=lambda n:n.replace('{slash}','/').rsplit('/',1)[-1]
def ohms(value):
 # Tolerance text must not become fractional resistance digits. Scientific
 # notation is used by the preserved 1e+06R AUX24 divider values.
 value=value.upper().strip()
 m=re.match(r'CRCW\d{4}(\d+)([KMR])(\d+)',value)
 if m:return (float(m[1])+float('0.'+m[3]))*{'R':1,'K':1000,'M':1000000}[m[2]]
 value=re.sub(r'\s*\d+(?:\.\d+)?%.*$','',value).strip()
 m=re.fullmatch(r'([\d.]+(?:E[+-]?\d+)?)([KMR]?)',value)
 if m:
  num,unit=m.groups();return float(num)*{'':1,'R':1,'K':1000,'M':1000000}[unit]
 m=re.fullmatch(r'(\d+)([KMR])(\d+)',value)
 if m:return (float(m[1])+float('0.'+m[3]))*{'R':1,'K':1000,'M':1000000}[m[2]]
 raise ValueError('Unresolved resistance '+value)
def resistor_feeds(parts,pins,nets,rail):
 rows=[]
 for n,nodes in nets.items():
  if SUFFIX(n)!=rail:continue
  for node in nodes:
   ref=node['ref']
   if not ref.startswith('R'):continue
   other=[x for x in pins[ref] if x['pin']!=node['pin']]
   assert len(other)==1
   r=ohms(parts[ref]['value']);bound=VMAX[rail]/(r*.975)
   rows.append({'ref':ref,'source_pin':node['pin'],'other_pin':other[0]['pin'],'other_net':other[0]['net'],'ohm':r,'current_upper_a':bound,'basis':'Vmax/Rmin, zero-drop bound, Rmin=.975R (1% initial +100ppm/K*150K); normal other-node potentials within0..source. No assumed LED VF or logicVOL reduces this bound.'})
 return rows
def buck_ports(iout,vin=18.,vout=5.1,eff=.8,bias_vin=.00005):
 if not (iout>=0 and vin>0 and vout>0 and 0<eff<=1 and bias_vin>=0):raise ValueError('Invalid buck policy')
 # Bias reservation already includes VIN/EN/BIAS and switching loss estimate once.
 iin=vout*iout/(vin*eff)+bias_vin
 return {'IN_load_a':iin,'OUT_injection_a':iout,'GND_injection_a':iin-iout,'GND_current_into_IC_a':iout-iin,'input_power_w':vin*iin,'output_power_w':vout*iout,'total_loss_reservation_w':vin*iin-vout*iout,'vin_v':vin,'vout_v':vout,'efficiency_planning_estimate':eff,'additional_input_bias_reservation_a':bias_vin}
def ldo_ports(iout,ground=.001):return {'IN_load_a':iout+ground,'OUT_injection_a':iout,'GND_injection_a':ground}
def ipc_width(a):return (215.3*a*a/(10*(.035/.0254)))**(1/1.15)*.0254 if a else 0.
def main():
 paths=[NET,PARSER,BOARD,HERE/'inventory.json',BASE/'power-audit/field-load-trace/receipt.json',BASE/'power-audit/constraint-snapshot/0-field_pdn_spec.json',Path('reports/motherboard-do-20260930/sources/tps274c65.txt'),Path('reports/motherboard-power-entry-20260930/sources/tps7a16.txt'),Path('reports/processor-hardware-20260929/source/research/field-power/lmr36506.txt'),Path('reports/motherboard-safety-sensor-20260930/sources/iso7760.txt'),Path('reports/motherboard-operator-20260930/sources/iso7720.txt')]
 before={str(p.resolve()):sha(p) for p in paths};parts,pins,nets=load()
 feeds={r:resistor_feeds(parts,pins,nets,r) for r in VMAX}
 q={
  'A3V3':{'U10003_ISO7762_VCC2_100Mbps_max':.026,'U10004_VDD_row_max':.0016,'U10009_VDD_row_max':.0016,'U14028_ISO7720_VCC1_max_DC_AC_rows':.0042,'U22001_TPS3700_VDD_reservation':.000015,'U22002_ISO7720_VCC1_max_DC_AC_rows':.0042,'additional_leak_switching_margin':.001},
  'B3V3':{'U10016_ISO7762_VCC2_100Mbps_max':.026,'U10017_VDD_row_max':.0016,'U10022_VDD_row_max':.0016,'U19008_LTC2962_VCC_max':.00021,'U19009_U19011_LVC_unloaded_plus_switching_reservation':.001,'U19017_ISO7720_VCC2_100Mbps_max':.0117,'U19019_ISO7760_VCC1_max_DC_AC_rows':.0114,'U19025_ISO1540_VCC2_LOW_max':.0067,'U19026_ADS1115_operating_fulltemp_max':.0003,'U19027_TMUX1511_VDD_max':.00007,'U22003_ISO7720_VCC1_max_DC_AC_rows':.0042,'additional_leak_switching_margin':.001},
  'FIELD5V':{'U11013_U11014_TPS2553_input_max_rows':.00028,'U11025_U11026_LVC_unloaded_plus_switching_reservation':.001,'U9003_U9004_LTC2962_VCC_max':.00042,'U9007_ISO7720_VCC1_max_DC_AC_rows':.0042,'additional_leak_switching_margin':.001}}
 a3=math.fsum(q['A3V3'].values())+math.fsum(v['current_upper_a'] for v in feeds['DOA_FIELD_3V3'])
 b3=math.fsum(q['B3V3'].values())+math.fsum(v['current_upper_a'] for v in feeds['DOB_FIELD_3V3'])
 # These finite budgets are routing targets, not replacements for device limits.
 a_ldo=ldo_ports(.050);b_ldo=ldo_ports(.120)
 fa5=.192+math.fsum(q['FIELD5V'].values())+math.fsum(v['current_upper_a'] for v in feeds['FIELD_5V'])+math.fsum(v['current_upper_a'] for v in feeds['AUX_5V_A']+feeds['AUX_5V_B'])
 fb5=math.fsum(v['current_upper_a'] for v in feeds['FIELD_B_5V_PRE'])
 a_buck=buck_ports(.360);b_buck=buck_ports(.130)
 # Full branch terms supplied independently by root will be appended in a separate
 # receipt; no zero is substituted for missing branch/entry consumption.
 branches={'FA_EXTERNAL24_NORMAL_A':4.+.148+.074+.100+.100,'FB_EXTERNAL24_NORMAL_A':4.+.200+.200+.200+6*.00275+.050}
 result={'schema':'root106-signed-field-normal-planning-v2','candidate_sha256':before[str(BOARD.resolve())],'source_export_sha256':before[str(NET.resolve())],
  'scope':'Planning row-envelope and explicit reservations, not a guaranteed arbitrary-mode/temperature or transient maximum. All16DO(.5Aeach),12motoraux,3sensor(.2Aeach),2probe(.1Aeach),6wetting(.00275Aeach),.05AONlamp preserved simultaneously; no concurrency exclusion.',
  'bounds_and_conditions':{'input_voltage_v':[18,30],'field5_planning_v':[4.9,5.1],'LDO3V3_max_v':3.366,'resistor_combined_error':.025,'LDO_ground_current_reservation_a':.001,'LDO_ground_basis':'TPS7A16 table gives15uA max at10uA output; loaded100mA ground5uA is typical only.1mA is explicit planning margin, not a guaranteed new component bound.','buck_efficiency_basis':'TI LMR36506 RevC §7.3.10 uses.8 as conservative normal light-load estimate; not guaranteed full-corner efficiency. Bias reservation50uA covers listed nonswitchingVIN/EN/BIAS rows once; switching/load losses already represented by.8.','isolator_basis':'Largest listed DC/1/10/100Mbps same-side maxima;100Mbps cases atCL15pF. This preserves8.333MHzSPI and does not interpolate a lower current. Mixed-state/load/capacitance actual dynamic guarantee remains open.','TPS274_basis':'VS2.5mA externalVDD/all-diagnostics/SCLKoff row;VDD1.6mA maximum of separate externalVDD SCLK/ADC rows. SimultaneousSCLK+allADCdiagnostics not guaranteed by those rows.'},
  'component_current_terms':q,'resistor_source_upper_bounds':feeds,'normal_contract_external24_terms_a':branches,
  'computed_local_output_envelopes_a':{'DOA3V3':a3,'DOB3V3':b3,'FIELD5V_original_without_A_LDO':fa5,'FIELD5V_A_prereg_revision':fa5+a_ldo['IN_load_a'],'FIELD_B5V_PRE_with_120mA_B_reservation':fb5+b_ldo['IN_load_a']},
  'routing_local_targets_a':{'DOA3V3':.050,'DOB3V3_complete_required':.120,'FIELD5V_after_A_prereg':.360,'FIELD_B5V_PRE_complete':.130},
  'signed_regulator_ports':{'U11009':a_buck,'U11017_A_prereg_revision':a_ldo,'U19028':b_buck,'U11018_complete_B_budget':b_ldo},
  'B_LDO_capacity_screen':{'existing_device_output_rating_a':.100,'computed_envelope_a':b3,'conservative_envelope_exceeds_existing_rating':b3>.100,'not_an_observed_overload':True,'recommended_source_change':'Split dedicated DO3V3(U10016/17/22 and owned decoupling/pullups) from retained safety/diagnostic3V3; add an exact reviewed TPS7A1633 with own input/output bypass/bleed fed by existingFIELD_B5V_PRE. Eachsource keeps60V input rating. Root review required before stagingB.'},
  'A_LDO_correction':{'feed_IN_EN_C11074_from':'FIELD_5V','unchanged_output_rating_a':.100,'routing_output_target_a':.050,'old_direct30V_loss_w':(30-3.234)*.050+30*.001,'new5V_loss_w':(5.1-3.234)*.050+5.1*.001,'native_source_export':'PENDING'},
  'proposed_trunk_capacity_policy':{r:{'copper_capacity_target_a':6.5,'minimum_existing_width_fit_mm_raw':ipc_width(6.5),'ordinary_0p6_0p3_vias_min_at_assumed_point5A':math.ceil(6.5/.5),'unchanged_per_net_drop_budget_v':.48,'unchanged_rise_policy_c':10.} for r in ['FA','FAG','FB','FBG']},
  'actual_limits_unchanged':{'DO_channel_a':.5,'DO_quad_a':2.,'TPS26630_3kohm_nominal_A':6.,'TPS26630_3kohm_table_A':[5.58,6.42],'source_continuous_board_rating':'NOT_QUALIFIED','maximum_simultaneous_fault_current':'NOT_BOUNDED_BY_DC_THRESHOLD'},
  'real_external_power_roots':{'FA_POSITIVE':['J11003','1'],'FA_RETURN':['J11003','2'],'FB_POSITIVE':['J11005','1'],'FB_RETURN':['J11005','2']},'shutdown_contacts_are_not_power_roots':['J11004','J11006'],
  'legacy_policy_retained_as_history':{'FA_FAG_design_a':4.58,'FB_FBG_design_a':4.82,'claimed_FA_limit_a':5.08,'claimed_FB_limit_a':5.32},
  'necessary_planner_change':'Groundnet route sizing must use signed multiport injections and absolute downstream cut currents, not all-positive converterGND=VINplusloadOUT. Preserve local converter return circulatingcurrent and branch paths. Existing installedfield_current_guard intentionally rejects negativeclusters and cannot consume this signedledger without separatelyreviewed solver changes.',
  'unresolved_branch_inputs':'Root MAX17612/TPS1H000/TPS26624/entry consumption receipts pending; no missing value becomeszero.',
  'inputs_before':before,'inputs_after':{p:sha(p) for p in before},'native_jobs':0,'board_or_original_source_edits':0,'applicable_routes_emitted':False,'full_rail_qualified':False,'manufacturing_ready':False}
 assert result['inputs_before']==result['inputs_after']
 assert fa5+a_ldo['IN_load_a']<.360
 assert fb5+b_ldo['IN_load_a']<.130
 assert a3<.050
 assert all(math.isclose(p['IN_load_a']-p['OUT_injection_a'],p['GND_injection_a'],abs_tol=1e-12) for p in result['signed_regulator_ports'].values())
 (HERE/'normal-model-r1.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'outputs':result['computed_local_output_envelopes_a'],'B_LDO_over_envelope':b3>.1,'signed_buck_GND':{r:result['signed_regulator_ports'][r]['GND_injection_a'] for r in ['U11009','U19028']},'inputs_unchanged':True}))
if __name__=='__main__':main()
