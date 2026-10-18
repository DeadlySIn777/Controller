"""Freeze exact topology, seven-pad demand and bounded rework obligations.

This does not accept a new current rating or a terminal-voltage budget.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,math,pickle,re,sys,time
import shapely
from shapely.geometry import Point,LineString
from shapely.ops import nearest_points
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2';FIELD=CONT/'field-power'
for p in(CONT/'coupled-recovery',FIELD,CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
OUT=HERE/'demand-and-rework-obligation-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
MATCH=HERE/'old-In4-vs-new-In2-matched-electrodes-r1';UPSTREAM=HERE/'actual-F-source-component-two-level-r1';PROBE=HERE/'parallel-fixed-native-copper-probe-r2'
NATIVE=CONT/'combined-R753-one-full-native-fill-cached-DRC-r299/copy'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def desc(q):return{k:q[k]for k in('kind','uuid','layer','ref','pin','contour')if k in q}

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    helper=HERE.parent/'audit_shutdown_header_correction.py';netfile=HERE.parent/'late-power-schematic-grid-r3/after.net'
    files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',FIELD/'normal-model-r3.json',FIELD/'model_r2.py',MATCH/'receipt.json',MATCH/'three-separate-vertical-transfer-terms.json',UPSTREAM/'receipt.json',HERE/'actual-source-paths-r1/source-path-receipt.json',HERE/'independent-accepted-cell-drill-envelope-r1/receipt.json',PROBE/'receipt.json',NATIVE/'board.kicad_pcb',NATIVE/'board.kicad_dru',helper,netfile,Path(__file__),Path(T.__file__),Path(K.__file__)]
    inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());groups=pickle.loads(files[1].read_bytes());plan=json.loads(files[2].read_text());match=json.loads(files[4].read_text());upstream=json.loads(files[6].read_text());trace=json.loads(files[7].read_text());control=json.loads(files[8].read_text());probe=json.loads(files[9].read_text())
    assert inputs[str(NATIVE/'board.kicad_pcb')]=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
    assert control['status']=='ALL_FROZEN_NUMERICAL_SQUARES_PASS_SEPARATE_NOMINAL_DRILL_ENVELOPES'
    root=K.root(groups[T.NET],'L11003','2');targets={('C11064','1'),('C11080','1'),('R11051','1'),('R11071','1'),('R9039','1'),('U11013','1'),('U11013','3')}
    assert set(trace['diagnostic_only_new_gain_removed']['0901_target_named_pads'])=={a+'.'+b for a,b in targets}
    contact_inventory={}
    for uid in(T.T2,T.T1):
        rows=[]
        for ly in K.LAYERS:
            via=next(q for q in root if q['kind']=='via'and q['uuid']==uid and q['layer']==ly);contacts=[]
            for q in root:
                if q['layer']!=ly or(q['kind']=='via'and q['uuid']==uid):continue
                a=via['shape'].intersection(q['shape']).area
                if a>1e-10:contacts.append(desc(q)|{'finite_Cu_overlap_mm2':a})
            rows.append({'layer':ly,'annulus_mm2':via['shape'].area,'actual_finite_contacts':contacts})
        contact_inventory[uid]=rows
    put('actual-all-layer-barrel-contact-inventory.json',contact_inventory)
    target_paths={};target_layers={}
    for ref,pin in sorted(targets):
        pads=[q for q in root if q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin)];layers=sorted({q['layer']for q in pads});assert len(layers)==1;ly=layers[0];target_layers[ref+'.'+pin]=ly
        target_paths[ref+'.'+pin]=T.finite_path([q for q in root if q['layer']==ly],lambda q:q['kind']=='via'and q['uuid']==T.T1,lambda q:q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin))
    put('seven-real-pad-planar-finite-contact-paths.json',{'layers':target_layers,'paths':target_paths})
    spec=importlib.util.spec_from_file_location('source_netlist',helper);N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N);tree=N.parse(netfile)
    netnodes={N.atom(n,'name'):[{k:N.atom(q,k)if N.children(q,k)else''for k in('ref','pin','pinfunction','pintype')}for q in N.children(n,'node')]for n in N.children(N.child(tree,'nets'),'net')}
    aux={name:nodes for name,nodes in netnodes.items()if name.replace('{slash}','/')in('/motherboard_motors/AUX_5V_A','/motherboard_motors/AUX_5V_B')};assert len(aux)==2
    auxA=next(v for k,v in aux.items()if k.endswith('AUX_5V_A'));auxB=next(v for k,v in aux.items()if k.endswith('AUX_5V_B'));outA=[n for n in auxA if n['ref'].startswith('JD')];outB=[n for n in auxB if n['ref'].startswith('JD')];assert len(outA)==8 and len(outB)==4
    assert 'fa5=.192+'in(FIELD/'model_r2.py').read_text()
    local=[q for q in plan['resistor_source_upper_bounds']['FIELD_5V']if q['ref']in{'R11051','R11071','R9039'}];downstream=plan['resistor_source_upper_bounds']['AUX_5V_A'];assert{q['ref']for q in downstream}=={'R11052','R9021','R9023'}
    base=.016*len(outA)+math.fsum(q['current_upper_a']for q in local+downstream);two_switch=plan['component_current_terms']['FIELD5V']['U11013_U11014_TPS2553_input_max_rows'];conservative=base+two_switch
    demand={'actual_seven_pads':[a+'.'+b for a,b in sorted(targets)],'actual_pad_layers':target_layers,'source_root':'L11003.2','switch_INPUT_and_ENABLE':'U11013.1 and U11013.3','switch_output':'U11013.6','actual_AUX5_A_nodes':auxA,'actual_AUX5_B_nodes':auxB,'external_all12_motor_aux5_contract_A':.192,'AUX5_A_eight_distinct_motor_outlet_planning_A':.016*len(outA),'AUX5_B_four_distinct_motor_outlet_planning_A':.016*len(outB),'per_outlet_load_contract_A':.016,'outlet_load_count_is_not_current_sharing_among_parallel_copper':True,'three_local_resistor_terms':local,'three_actual_downstream_AUX5_A_resistor_terms':downstream,'known_non_IC_planning_subtotal_A':base,'combined_two_TPS2553_existing_model_term_A':two_switch,'screen_assigning_entire_two_switch_term_to_seven_pad_branch_A':conservative,'entire_two_switch_assignment_is_a_sensitivity_not_revised_normal_model':True,'C11064_C11080_capacitor_DC_leak_EN_input_leak_and_local_mixed_mode_reservations':'NOT assigned zero; source/datasheet full-corner allocation remains open. Normal-model global additional leakage/switching reserve is retained.','two_100nF_capacitors_nominal_startup_current':'I = (C11064_effective + C11080_effective)*dV/dt; nominal sum 0.2uF is not a bound on mounted effective capacitance or ramp/inrush.','full_simultaneous_normal_FIELD5_planning_A':plan['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'],'unchanged_routing_stress_A':plan['routing_local_targets_a']['FIELD5V_after_A_prereg'],'all12_motors_and_other_fitted_loads_remain_simultaneous':True,'five_preexisting_unrooted_pads':trace['actual_FIELD5_unrooted_named_pad_groups'],'no_unrooted_load_is_assigned_zero':True}
    put('seven-pad-source-and-demand-ledger.json',demand)
    sensitivities=[]
    for material,temp in((35,60),(25,125)):
        oldcase=next(r for r in match['conditional_electrical_cases']if r['boundary_case']=='old_In4_exact_common_finite_electrodes'and r['step_mm']==.0125 and r['conditional_Cu_um']==material and r['conditional_uniform_copper_temperature_C']==temp and r['current_A']==.36)
        newcase=next(r for r in match['conditional_electrical_cases']if r['boundary_case']=='new_In2_exact_common_finite_electrodes'and r['step_mm']==.0125 and r['conditional_Cu_um']==material and r['conditional_uniform_copper_temperature_C']==temp and r['current_A']==.36)
        fcase=next(r for r in upstream['conditional_electrical_cases']if r['step_mm']==.0125 and r['conditional_Cu_um']==material and r['conditional_uniform_temperature_C']==temp and r['source_to_e19f_current_concentration_A']==.36)
        for current in(base,conservative,.36):
            sensitivities.append({'Cu_um':material,'uniform_temperature_C':temp,'concentrated_current_A':current,'old_plane_sheet_drop_V':current*oldcase['sheet_R_ohm'],'new_plane_sheet_drop_V':current*newcase['sheet_R_ohm'],'upstream_F_sheet_drop_V':current*fcase['R_ohm'],'new_plane_plus_F_drop_sensitivity_V':current*(newcase['sheet_R_ohm']+fcase['R_ohm']),'new_plane_plus_F_heat_sensitivity_W':current*current*(newcase['sheet_R_ohm']+fcase['R_ohm']),'planning_4p9V_minus_new_plane_plus_F_V':4.9-current*(newcase['sheet_R_ohm']+fcase['R_ohm']),'planning_4p9V_is_not_guaranteed_source_corner_and_result_not_terminal_voltage':True,'barrel_local_load_switch_return_connector_harness_ripple_transient_and_feedback_excluded':True})
    put('seven-pad-and-full-stress-voltage-sensitivities.json',sensitivities)
    # Rework witnesses identify the actual fixed copper between named free-space
    # components; these straight bridges are NOT candidate tracks.
    rec,trees=K.F.build(g,layers={'F.Cu','B.Cu','In2.Cu','In3.Cu'});source=Point(306.0565,157.958);target=Point(278.687,149.387);witness=[]
    for row in probe['rows']:
        ly=row['layer'];freepath=PROBE/(ly.replace('.','-')+'-free-centerline-area.wkb');inputs[str(freepath)]=sha(freepath);free=shapely.from_wkb(freepath.read_bytes());parts=[free]if free.geom_type=='Polygon'else list(free.geoms);src=next((p for p in parts if p.covers(source)),None);tgt=next((p for p in parts if p.covers(target)),None)
        assert src is not None and tgt is not None
        a,b=nearest_points(src,tgt);axis=LineString([a,b]);width=row['width_mm'];blockers=[]
        for j in trees[ly].query(axis.buffer(width/2+2)):
            q=rec[ly][int(j)]
            if K.L.norm(q['net'])==T.NET:continue
            gap=.15 if q['domain']==g['domains_normalized'][T.NET]else.6
            if q['kind']=='fill':gap=max(gap,float(next(z for z in g['zones']if z['uuid']==q['uuid'])['clearance_mm']))
            distance=axis.distance(q['shape']);required=width/2+gap+.025
            if distance<required:blockers.append(desc(q)|{'net':K.L.norm(q['net']),'axis_distance_mm':distance,'axis_required_gap_mm_including_width_and_guard':required,'native_Cu_intersection_area_mm2':axis.buffer(width/2).intersection(q['shape']).area})
        witness.append({'layer':ly,'width_mm':width,'same_continuous_free_component':src.equals(tgt),'source_component_area_mm2':src.area,'target_component_area_mm2':tgt.area,'nearest_direct_component_boundary_bridge_mm':[list(a.coords)[0],list(b.coords)[0]],'boundary_bridge_length_mm':a.distance(b),'actual_blockers':blockers,'this_bridge_is_not_a_route_and_not_globally_minimal_rework':True})
    put('fixed-copper-corridor-closure-witnesses.json',witness)
    board=(NATIVE/'board.kicad_pcb').read_bytes();nominal=float(re.search(rb'\(general\s*\(thickness\s+([0-9.]+)\)',board).group(1));vertical=json.loads((MATCH/'three-separate-vertical-transfer-terms.json').read_text());assert nominal==vertical['board_general_nominal_thickness_mm']==1.6
    obligations={'verdict':'REAL_SOURCE_ANCHORED_IN2_REPLACEMENT_EXISTS_BUT_CURRENT_AND_TERMINAL_VOLTAGE_QUALIFICATION_REMAIN_OPEN','historical_direct_In4_contact_loss_is_true':'Both old via-to-61cb8179 fill contacts are deliberately withdrawn. Current connectivity is a different real In2 current path, not identical retained In4 copper.','old_plane_contact_count_patch':'Do not add via-contained zones or inflate annuli; that does not supply an independent source-to-load conductor.','current_decision':'3.4991097 times matched sheet resistance cannot be accepted by contact preservation or small total Joule heat. No qualified AUX5_A terminal minimum/maximum, full converter corner, mounted Cu/plating and thermal environment, or complete shared source/return network budget is provided here.','needed_design_choice':'Establish complete unchanged terminal-voltage and thermal/current margin at all simultaneous loads using exact source/return/branch geometry, or create a wider/parallel physical corridor and requalify it. Keep current limits and fitted channels unchanged.','concrete_rework_scope':'Begin with L11003.2 source F fanout to e19f, the actual In2 gained branch to 0901, then the 0901 F/B load fanouts. A bounded no-cut additive search in x268..316/y138..184 has no 0.50mm F/In2/In3 or 0.35mm B source-to-target corridor with all native foreign copper fixed. Exact free-area and blocking-object witnesses are retained. Any wider solution needs explicit affected foreign conductor/ground/reference redesign, source-contact retention and a fresh native fill; no additive packet is safe to promote from this probe.','optional_resistance_regression_target':'A proposed engineering target may be <=87.8889368 matched sheet squares at the stated numerical boundary, to recover the old conditional plane resistance. This is not an inherited capacity rating, an approved voltage allowance or an instruction to restore the withdrawn In4 zone.','stackup':'Nominal native board 1.6mm versus declared Cu+dielectric+mask 1.55mm is unreconciled. Declared midplane distances used only as conditional sensitivities, not scaled or fabricator qualified.','vertical_terms':'Keep source e19f F-to-plane, target 0901 plane-to-F and target 0901 plane-to-B separate; target currents and other taps must satisfy actual KCL. Never add three full-current drops.','convergence':'Old matched plane changes -2.96%, new matched plane -4.02%; F source changes -18.50%. Two levels do not establish continuum convergence. F source needs further refinement before a precise end-to-end DC result.','new_composed_native_board':'All results bind genuine saved R299. Rebind to actual new composed native Cu/masks/contacts after its fill; no automatic geometric or current carryover.','missing_board_joins':'Five unrooted C9004/U9004 pads remain required unfinished board joins; their retained loads are not zero.','physical_qualification':'Ripple, inrush, capacitance/bias, feedback, protection fault/partial-power behavior, harness, measured temperature, plating and qualified manufacturing process remain open.'}
    put('actionable-rework-and-qualification-obligations.json',obligations)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'FIELD5_REPLACEMENT_REAL_PATH_PROVED_CONDITIONAL_NUMERICS_FROZEN_CURRENT_GATE_OPEN','input_sha256':inputs,'actual_saved_native_candidate_sha256':sha(NATIVE/'board.kicad_pcb'),'matched_old_new_sheet_fine_ratio':match['matched_electrode_comparisons'][1]['new_divided_by_old'],'known_non_IC_seven_pad_subtotal_A':base,'seven_pad_screen_with_entire_existing_two_switch_IC_term_A':conservative,'qualified_terminal_voltage_margin':False,'actual_all_layer_contacts_file':'actual-all-layer-barrel-contact-inventory.json','demand_file':'seven-pad-source-and-demand-ledger.json','sensitivity_file':'seven-pad-and-full-stress-voltage-sensitivities.json','rework_blocker_file':'fixed-copper-corridor-closure-witnesses.json','obligation_file':'actionable-rework-and-qualification-obligations.json','native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
