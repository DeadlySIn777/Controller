"""Conserved DC ground current scenarios from original full-load allocations.

Group allocations preserve uncertainty; they are not invented per-pad ratings.
"""
import json,hashlib,math
from pathlib import Path
import inspect_integrated_source as I
HERE=Path(__file__).resolve().parent
I.NET=HERE.parent/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    comps,pins=I.load();native=json.loads((HERE/'signed-return-inputs-r1.json').read_text());assert sha(I.NET)==native['sha256']
    def grounds(refs):return [{'ref':r,'pin':p,'net_raw':n} for r in sorted(set(refs)) for p,n in sorted(pins[r].items()) if n=='/LOGIC_GND']
    def nodes(net):return [{'ref':r,'pin':p,'net_raw':n} for r,ps in pins.items() for p,n in ps.items() if n==net]
    def ground_for_net(net,exclude=()):return grounds([r for r,ps in pins.items() if r not in exclude and any(n==net for n in ps.values()) and (r.startswith('U') or r.startswith('J'))])
    core='/mc_local_power{slash}CORE_5V';sbc='/motherboard_power_entry{slash}SBC_5V';motionnet='/motherboard_power_entry{slash}MOTION_5V_RAW'
    auxout=.287;auxinput=auxout*3.465/(4.75*.85);common=3.6+auxinput+.5+.05;nonSBC=2*3.465/(4.95*.85)+.8*1.25/(4.95*.85)+.7+.55+.341+.010;total=common+nonSBC
    motion=.8976+.4488+2*5.05/(330*.99)+1.05+.009;vin=17.7;eta=.85;coreinput=total*5.05/(vin*eta);motioninput=motion*5.05/(vin*eta);analoginput=7.5/(vin*.8);entry=coreinput+motioninput+analoginput
    groups=[]
    def add(label,current,endpoints,allocation,**extra):
        endpoints=list({(q['ref'],q['pin']):q for q in endpoints}.values())
        for q in endpoints:assert pins[q['ref']][q['pin']]=='/LOGIC_GND'
        groups.append({'label':label,'signed_total_a':current,'ground_node_candidates':endpoints,'within_group_distribution':allocation,**extra})
    simplex='nonnegative endpoint allocation with sum equal to signed group magnitude; solve stress cases at actual distinct physical pad groups; equal sharing is not a qualification'
    add('CM5 internal consumption plus AUX conversion cancellation',3.6+auxinput-auxout,grounds(['J15001','J15002']),simplex,internal_CM5_5V_a=3.6,exported_AUX_5V_equivalent_a=auxinput,exported_AUX_3V3_output_a=auxout,connector_current_and_sharing_qualification_open=True)
    add('AUX external SD and non-SD loads',auxout,ground_for_net('/motherboard_compute/SD_PORT_3V3')+ground_for_net('/motherboard_compute/CM_AUX_3V3',('J15001','J15002','U15012')),simplex,includes_SD_a=.250,nonSD_reservation_a=.037,unqualified_SD_part=True)
    add('USB full normal port allocation',.5,ground_for_net('/motherboard_compute/USB_SWITCHED_5V',('U15026',)),simplex,hardware_enforcement_and_device_scope_open=True)
    add('HDMI full normal port allocation',.05,ground_for_net('/motherboard_compute/HDMI_PORT_5V',('U15018',)),simplex,includes_IC_supply_current_scope_open=True)
    add('IO3 actual output load envelope',2.,ground_for_net('/IO_3V3',('U2002',)),simplex,physical_static_dynamic_full_load_qualification_open=True)
    add('IO3 buck ground cancellation',2*3.465/(4.95*.85)-2.,grounds(['U2002']),'single logical GND pin4; preserve each native physical pad identity',actual_output_a=2.,CORE5_input_screen_a=2*3.465/(4.95*.85))
    add('CORE1V2 actual FPGA output allocation',.8,ground_for_net('/CORE_1V2',('U2001',)),simplex,target_FPGA_power_report_open=True)
    add('CORE1V2 buck ground cancellation',.8*1.25/(4.95*.85)-.8,grounds(['U2001']),'single logical GND pin4; preserve each native physical pad identity',actual_output_a=.8,CORE5_input_screen_a=.8*1.25/(4.95*.85))
    add('ESP module full normal allowance',.7,grounds(['J16001','J16002']),simplex,includes_commodity_module_internal_conversion=True)
    add('Status complete allocation including LED sink returns',.55,grounds([r for r,c in comps.items() if c['sheet']=='/motherboard_status/' and not r.startswith('C')]),simplex,not_all_current_through_TLC_VCC_pin28=True,CORE5_supply_nodes=[q for q in nodes(core) if q['ref'].startswith(('R17','U17','D17'))],full_maximum_qualification_open=True)
    add('RS485 and CAN loaded primary source screen',.341,grounds(['U14812','U14813']),simplex,split_between_two_ICs_undocumented=True,isolated_secondary_ground_networks_excluded=True)
    add('Other CORE5 retained reservation',.010,grounds([r for r in comps if r.startswith('U')]),simplex,endpoint_current_scope_unresolved=True)
    add('CORE5 buck ground cancellation',coreinput-total,[q for q in grounds(['U11007']) if q['pin']!='17'],'power PGND1–4 and PGND_CONTROLLER_PAD share a bounded extracted total; AGND pin17 is not a high-current sharing endpoint',input_current_a=coreinput,output_current_a=total,power_ground_pins=['23','24','25','26','30'])
    motionrefs={q['ref'] for q in nodes(motionnet) if q['ref'].startswith(('U','J')) and q['ref']!='U11008'}
    motionrefs|={r for r,ps in pins.items() if r.startswith(('U','J')) and any(n.endswith('MOTION_5V') for n in ps.values())}
    add('Independent MOTION5 full normal allocation',motion,grounds(motionrefs),simplex,all12_fitted_interfaces_preserved=True,load_scope_reconstruction_not_target_physical_proof=True)
    add('MOTION5 buck ground cancellation',motioninput-motion,[q for q in grounds(['U11008']) if q['pin']!='17'],'power PGND1–4 and PGND_CONTROLLER_PAD share a bounded extracted total; AGND pin17 is not a high-current sharing endpoint',input_current_a=motioninput,output_current_a=motion,power_ground_pins=['23','24','25','26','30'])
    for r,w in [('U14601',1),('U14619',1),('U14701',1),('U14702',1),('U14703',3.5)]:add(r+' isolated converter primary return',w/(vin*.8),grounds([r]),'single −VIN pin1; output domains have separate isolated returns',output_capacity_screen_w=w,retained_supported_output_capacity_not_new_nameplate_load=True)
    add('Actual 24V source return',-entry,grounds(['J11001']),'single J11001.2 actual supply-return terminal',J11002_shutdown_contact_ground_is_not_second_supply_return=True)
    residual=sum(q['signed_total_a'] for q in groups);assert abs(residual)<1e-12,(residual,groups)
    result={'verdict':'CONSERVED_SIGNED_GROUP_SCENARIOS_REQUIRE_ENDPOINT_AND_PHYSICAL_QUALIFICATION','source':str(I.NET.resolve()),'source_sha256':sha(I.NET),'source_components':len(comps),'original_power_closure_audit':str((HERE.parents[2]/'motherboard-compute-20260930/power-closure-r01/audit.py').resolve()),'sign_convention':'positive injection from load/converter into LOGIC_GND; negative extraction toward source/converter. Buck GND injection is input current minus output current, conserving actual rail currents.','assumptions':{'CORE_and_MOTION_output_screen_v':5.05,'protected_input_v':vin,'buck_efficiency_screen':eta,'isolated_efficiency_screen':.8,'IO3_output_screen_v':3.465,'CORE1V2_output_screen_v':1.25,'conversion_efficiencies_guaranteed':False,'steady_state_DC_only':True,'startup_transient_fault_switching_current_excluded':True},'CORE5_output_a':total,'SBC_common_output_a':common,'CM5_plus_exported_AUX_5V_input_a':3.6+auxinput,'MOTION5_output_a':motion,'entry_return_a':entry,'entry_inverse_R_limit_screen_a':4.185/1.025,'entry_inverse_R_margin_screen_a':4.185/1.025-entry,'groups':groups,'signed_sum_a':residual,'native_physical_pad_UUID_mapping_required':True,'capacitor_DC_injection_zero_but_transient_obligations_retained':True,'missing_candidate_endpoints':[q['label'] for q in groups if not q['ground_node_candidates']],'all12_motor_and_retained_load_scope_preserved':True,'electrical_layout_qualification':False,'manufacturing_ready':False}
    path=HERE/'signed-return-scenarios-r1.json';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('SIGNED_RETURN',total,common,entry,residual,result['missing_candidate_endpoints'],sha(path))
if __name__=='__main__':main()
