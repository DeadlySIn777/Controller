"""Complete simultaneous normal planning ledger with explicit conditional bounds."""
import json,math
from inventory import HERE,BASE,NET,PARSER,BOARD,load,sha
from model import VMAX,resistor_feeds,buck_ports,ldo_ports,ipc_width,ohms,SUFFIX

BRANCH=BASE/'continuation-r2/branch-load-audit/passive-and-ic-screen-r1.json'
OTHER=BASE/'continuation-r2/branch-load-audit/additional-ic-conditions-r1.json'
def total(rows):return math.fsum(r['current_upper_a'] for r in rows)
def main():
 paths=[NET,PARSER,BOARD,BRANCH,OTHER,HERE/'normal-model-r1.json',HERE/'ab-prereg-split-source/receipt-r3.json',HERE/'ab-prereg-split-source/source-export/receipt-r2.json',HERE/'model.py',__file__]
 before={str(p):sha(p) for p in paths};parts,pins,nets=load()
 r=json.loads((HERE/'normal-model-r1.json').read_text(encoding='utf-8'));branch=json.loads(BRANCH.read_text(encoding='utf-8'));other=json.loads(OTHER.read_text(encoding='utf-8'))
 VMAX.update({n:30. for n in ['FA_RAW','FB_RAW','FA_IN','FB_IN']})
 feeds={n:resistor_feeds(parts,pins,nets,n) for n in VMAX}
 q=r['component_current_terms']
 a3=math.fsum(q['A3V3'].values())+total(feeds['DOA_FIELD_3V3'])
 b3=math.fsum(q['B3V3'].values())+total(feeds['DOB_FIELD_3V3'])
 doBrefs={'R10032','R10034'};doBq={'U10016_ISO7762_VCC2_100Mbps_max','U10017_VDD_row_max','U10022_VDD_row_max'}
 moved_current=math.fsum(q['B3V3'][k] for k in doBq)+total([x for x in feeds['DOB_FIELD_3V3'] if x['ref'] in doBrefs])
 new_bleed=3.366/(10000*.975)
 b_safe=b3-moved_current;b_do=moved_current+new_bleed+.001
 ldos={'U11017':ldo_ports(.050),'U11018':ldo_ports(.090),'U11038':ldo_ports(.040)}
 fa5=.192+math.fsum(q['FIELD5V'].values())+total(feeds['FIELD_5V'])+total(feeds['AUX_5V_A']+feeds['AUX_5V_B'])+ldos['U11017']['IN_load_a']
 fb5=total(feeds['FIELD_B_5V_PRE'])+ldos['U11018']['IN_load_a']+ldos['U11038']['IN_load_a']
 bucks={'U11009':buck_ports(.360),'U19028':buck_ports(.140)}
 # Replay exact nominal series/parallel branches with every resistor reduced by
 # the uniform planning error; parent receipt's initial-only screen is retained.
 passives=[]
 for row in branch['rows']:
  passives.append({**row,'domain':'FA' if row['name'].startswith('PRB') else 'FB','planning_upper_a':row['nominal_a']/.975,'planning_basis':'Uniform 2.5% minimum R envelope: source initial tolerance plus100ppm/K over150K. Identical scaling bounds these positive series/parallel input networks. ADC/LTC input current remains separate.'})
 pa=math.fsum(x['planning_upper_a'] for x in passives if x['domain']=='FA');pb=math.fsum(x['planning_upper_a'] for x in passives if x['domain']=='FB')
 # These upper bounds are distinct from the exact branch receipt, so no divider
 # or bleed is included a second time in the protected-output aggregate.
 fa_direct=[x for x in feeds['FIELD_A_24V_PROTECTED'] if x['ref'] not in {'R14058','R14064'}]
 fb_direct=[x for x in feeds['FIELD_B_24V_PROTECTED'] if x['ref'] not in {'R19021','R19028','R19034'}]
 extras={
  'FA':{'TPS274_VS_two_3mA_reservations':.006,'MAX17612_two_1p5mA_reservations':.003,'TPS26624_two_600uA_reservations':.0012,'probe_exact_passive_networks':pa,'AUX24_external_bleed_monitor_bounds':total(feeds['AUX_24V_A']+feeds['AUX_24V_B']),'other_direct_protected24_resistors':total(fa_direct),'aggregate_IC_input_TVS_FET_leak_dynamic_reservation':.005},
  'FB':{'TPS274_VS_two_3mA_reservations':.006,'MAX17612_three_1p5mA_reservations':.0045,'TPS1H000_two_8mA_reservations':.016,'sensor_SAFE_lamp_exact_passive_networks':pb,'other_direct_protected24_resistors':total(fb_direct),'aggregate_ADC_LTC_input_TVS_FET_leak_dynamic_reservation':.005}}
 external={'FA':{'eight_DO_channels':8*.5,'all12_motor_AUX24':.148+.074,'two_probes':2*.100},'FB':{'eight_DO_channels':8*.5,'three_sensor_branches':3*.200,'six_DI_wetting':6*.00275,'armed_lamp':.050}}
 protected={d:math.fsum(external[d].values())+math.fsum(extras[d].values())+bucks['U11009' if d=='FA' else 'U19028']['IN_load_a'] for d in ['FA','FB']}
 upstream={d:{'TPS26630_IQ_planning_a':.002,'raw_control_divider_upper_a':total(feeds[d+'_RAW']+feeds[d+'_IN']),'additional_gate_reverse_block_TVS_leak_reservation_a':.001} for d in ['FA','FB']}
 root={d:protected[d]+math.fsum(upstream[d].values()) for d in ['FA','FB']}
 device_ports={}
 for ref,current in [('U10004',.003),('U10009',.003),('U10017',.003),('U10022',.003)]:
  device_ports[ref]={'VS_pads':[x['pin'] for x in pins[ref] if x['pinfunction'].startswith('VS_')],'VDD_pads':[x['pin'] for x in pins[ref] if x['pinfunction'].startswith('VDD_')],'GND_pads':[x['pin'] for x in pins[ref] if 'GND' in x['pinfunction']],'VS_quiescent_reservation_a':current,'VDD_quiescent_row_envelope_a':.0016,'simultaneous_external_outputs_a':[.5]*4,'all_same_port_pads_must_be_contacted':True,'arbitrary_equal_split_of_parallel_pads':'FORBIDDEN_WITHOUT_PHYSICAL_CURRENT_SHARING_PROOF','device_GND_excludes_external_load_return':True}
 # Explicit sign convention: positive IN is drawn from supply; positive OUT
 # and GND are delivered to their nets. KCL: IN=OUT+GND. Bucks inject negative
 # GND current. This is real local circulating current, not a negative load.
 signed={**bucks,**ldos}
 raw_return_examples={d:{'external_return_and_local_loads_a':root[d]-bucks['U11009' if d=='FA' else 'U19028']['IN_load_a']+bucks['U11009' if d=='FA' else 'U19028']['OUT_injection_a'],'buck_GND_injection_a':bucks['U11009' if d=='FA' else 'U19028']['GND_injection_a'],'sum_external_source_return_a':root[d]} for d in ['FA','FB']}
 r.update(schema='root106-signed-field-normal-planning-v3',supersedes_model_sha256=sha(HERE/'normal-model-r1.json'),source_branch='ab-prereg-split-source, native exact14+4 PASS, no board integration',
  resistor_source_upper_bounds=feeds,exact_branch_passive_networks=passives,parent_conditional_IC_receipts={'branch':branch,'additional':other},
  computed_local_output_envelopes_a={'DOA3V3':a3,'DOB3V3_original_complete':b3,'DOB3V3_retained_safety_diagnostics':b_safe,'DOB_DO3V3_new_dedicated':b_do,'FIELD5V_after_A_prereg':fa5,'FIELD_B5V_PRE_after_split':fb5},
  routing_local_targets_a={'DOA3V3':.050,'DOB3V3_safety_diagnostics':.090,'DOB_DO3V3':.040,'FIELD5V_after_A_prereg':.360,'FIELD_B5V_PRE_after_split':.140},
  signed_regulator_ports=signed,TPS274_source_and_return_port_groups=device_ports,
  normal_external_output_contracts_a=external,normal_protected24_consumption_terms_a=extras,normal_protected24_trunk_envelopes_a=protected,
  upstream_entry_terms_a=upstream,real_connector_input_return_envelopes_a=root,signed_return_cut_examples=raw_return_examples,
  B_LDO_capacity_screen={'existing_device_rating_a':.100,'original_conservative_complete_envelope_a':b3,'original_envelope_exceeds_rating':b3>.100,'not_an_observed_overload':True,'corrected_unchanged_device_ratings_a':{'U11018':.100,'U11038':.100},'staged_native_split_pass':True,'PG_semantic_change':'FB_PGOOD = field-B entry good AND dedicated DO logic regulator good. Already existing physical path pulls B health/rearm latches down. Treat deliberate topology change in CLI/UI/diagnostics.'},
  pin_load_allocation={'B_DO_rail':{'IC_terms':{k:q['B3V3'][k] for k in doBq},'moved_pullups':[x for x in feeds['DOB_FIELD_3V3'] if x['ref'] in doBrefs],'new_R11088_bleed_a':new_bleed,'additional_leak_switching_reservation_a':.001},'B_retained_rail':{'IC_terms':{k:v for k,v in q['B3V3'].items() if k not in doBq},'retained_resistors':[x for x in feeds['DOB_FIELD_3V3'] if x['ref'] not in doBrefs]}},
  TPS26624_return_allocation={'total_IQ_reservation_each_a':.0006,'RTN_vs_GND_internal_split':'NOT_DATASHEET_BOUNDED; preserve both physical return ports/support island; aggregate current counted once','individual_port_routing_reservations_a':{'RTN':.001,'GND':.001},'external_load_return':'FIELD_GND; do not move AUX loads onto RTN'},
  branch_bound_status={'normal_rows_complete_and_nonzero_reservations':True,'normal_aggregate_dynamic_and_leak_margin_each_domain_a':.005,'full_arbitrary_mode_18_30V_temperature_guarantee':False,'conditional_row_envelopes_and_reserved_unknowns':'Explicit reservations support conservative routing planning; they cannot certify silicon corners, transient fault limits or manufacturing capacity.'},
  unresolved_branch_inputs='No missing normal branch is assigned zero. Exact guaranteed mixed-mode corner current, input-leak/TVS temperature bounds, internal RTN/GND split and converter full-corner efficiency remain unqualified; named reservations included.',
  normal_full_simultaneous_exceeds_6A_nominal_threshold=False,
  proposed_trunk_capacity_policy={d:{'copper_capacity_target_a':6.5,'minimum_existing_width_fit_mm_raw':ipc_width(6.5),'ordinary_0p6_0p3_vias_min_at_assumed_point5A':13,'per_net_drop_budget_v':.48,'rise_policy_c':10,'policy_status':'PROPOSED_COPPER_CAPACITY_NOT_DEVICE_RATING'} for d in ['FA','FAG','FB','FBG']},
  inputs_before=before,inputs_after={p:sha(p) for p in before},native_jobs=0)
 r['bounds_and_conditions']['resistor_parser_r2']='Exact ohmic/scientific and embedded-unit values; tolerance digits cannot enter nominal resistance. r1 historical nominal-parser errors corrected; input files preserved.'
 r['bounds_and_conditions']['TPS274_VS_planning_reservation_each_a']=.003
 r['bounds_and_conditions']['TPS26630_IQ_reservation_a']=.002
 r['bounds_and_conditions']['power_fault_scope']='6.5A copper policy does not bound startup cap charging, eFuse fault overshoot/delay, output inductive energy, connector/harness/fuse ratings or physical continuous duty.'
 assert a3<.05 and b_safe<.09 and b_do<.04 and fa5<.36 and fb5<.14
 assert all(math.isclose(p['IN_load_a'],p['OUT_injection_a']+p['GND_injection_a'],abs_tol=1e-12) for p in signed.values())
 assert all(v<5.58 for v in root.values())
 assert all(math.isclose(e['external_return_and_local_loads_a']+e['buck_GND_injection_a'],e['sum_external_source_return_a'],abs_tol=1e-12) for e in raw_return_examples.values())
 assert r['inputs_before']==r['inputs_after']
 (HERE/'normal-model-r2.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'local_outputs':r['computed_local_output_envelopes_a'],'protected_trunks':protected,'connector_supply_return':root,'signed_GND':{k:v['GND_injection_a'] for k,v in bucks.items()},'inputs_unchanged':True}))
if __name__=='__main__':main()
