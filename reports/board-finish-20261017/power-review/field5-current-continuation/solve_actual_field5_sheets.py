"""Two-level contained-cell FIELD5 screens on genuine full-native R299 copper.

The whole In2 case adds upstream sheet copper omitted by historical regional
R579. Source and target are genuine finite existing-barrel annular contacts.
This is conditional DC numerical evidence, not thermal or full-loop authority.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
import hashlib,importlib.util,json,pickle,sys,time,math
from datetime import datetime,timezone
import shapely
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
FIELD=CONT/'field-power'
for p in (CONT/'coupled-recovery',FIELD,CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
OUT=HERE/'actual-native-sheet-two-level-r1'
TRACE=HERE/'actual-source-paths-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def put(name,value):(OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def main():
    assert not OUT.exists();OUT.mkdir();start=time.monotonic()
    helper=FIELD/'solve_FIELD5_actual_finite_annular_sheet_r551.py'
    files=[helper,TRACE/'source-path-receipt.json',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',FIELD/'normal-model-r3.json',FIELD/'FIELD5-R543-same-real-annuli-contained-mesh-refinement-r579/receipt.json',Path(__file__)]
    inputs={str(p):sha(p)for p in files};trace=json.loads(files[1].read_text());assert trace['verdict']=='ACTUAL_NATIVE_IN2_REPLACEMENT_SOURCE_PATH_EXISTS_CURRENT_QUALIFICATION_OPEN'
    spec=importlib.util.spec_from_file_location('frozen_mesh_r551',helper);solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
    groups=pickle.loads(files[2].read_bytes());root=K.root(groups['/motherboard_power_entry/FIELD_5V'],'L11003','2')
    whole=unary_union([q['shape']for q in root if q['kind']=='fill'and q['layer']=='In2.Cu'])
    source=unary_union([q['shape']for q in root if q['kind']=='via'and q['uuid']=='e19f5a4a-8797-4ce8-a00d-4c884cc46739'and q['layer']=='In2.Cu']).intersection(whole)
    target=unary_union([q['shape']for q in root if q['kind']=='via'and q['uuid']=='0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3'and q['layer']=='In2.Cu']).intersection(whole)
    assert whole.area>790 and source.area>.16 and target.area>.06 and source.disjoint(target)
    for name,shape in [('actual-full-source-rooted-In2-sheet',whole),('actual-e19f-In2-source-contact',source),('actual-0901-In2-target-contact',target)]:
        p=OUT/(name+'.wkb');p.write_bytes(shape.wkb)
    names=['actual-native-source-contained-physical-sheet','actual-native-upstream-source-all-contacts','actual-native-upstream-source-goal-contact','actual-native-0901-finite-target-contact']
    regional=[]
    for name in names:
        p=TRACE/(name+'.wkb');inputs[str(p)]=sha(p);regional.append(shapely.from_wkb(p.read_bytes()))
    cases=[('regional_actual_upstream_all_contacts',regional[0],regional[1],regional[3]),('regional_actual_upstream_goal_contact',regional[0],regional[2],regional[3]),('whole_actual_In2_e19f_finite_source_to_0901_finite_target',whole,source,target)]
    plan=json.loads(files[3].read_text());normal=plan['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'];reserved=plan['routing_local_targets_a']['FIELD5V_after_A_prereg'];assert reserved==.36
    binding={'source_converter':'U11009.5 SW -> L11003.1 -> L11003.2 FIELD5V','whole_source_barrel':'e19f5a4a-8797-4ce8-a00d-4c884cc46739','target_barrel':'0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3','actual_In2_source_sheet_area_mm2':whole.area,'whole_source_finite_annular_overlap_mm2':source.area,'whole_target_finite_annular_overlap_mm2':target.area,'no_fabricated_electrode_disk_or_equal_current_sharing':True,'planning_full_simultaneous_FIELD5_A':normal,'unchanged_routing_stress_A':reserved,'all12_motor_aux5_and_all_other_planning_terms_retained':True,'the_0_36A_concentration_is_a_declared_numerical_stress_case_not_a_guaranteed_arbitrary_state_bound':True}
    put('actual-source-load-and-current-binding.json',binding);rows=[];electrical=[]
    for name,shape,src,tgt in cases:
        for step in(.025,.0125):
            put('status.json',{'phase':'CONTAINED_ACTUAL_NATIVE_DC_SHEET_SOLVE','case':name,'step_mm':step,'completed':len(rows),'affinity':list(range(16,28)),'numeric_threads':2,'native_jobs':0,'adopted':False})
            row=solver.solve(shape,src,tgt,step);row['boundary_case']=name;rows.append(row);put('checkpoint.json',rows)
            print(json.dumps({'case':name,'step_mm':step,'status':row['status'],'squares':row.get('effective_sheet_squares'),'cells':row.get('contained_cells')}),flush=True)
            if row['status']!='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED':continue
            for thickness,temp in((35,60),(25,125)):
                rho=1.724e-8*(1+.00393*(temp-20));resistance=row['effective_sheet_squares']*rho/(thickness*1e-6)
                for current in(normal,reserved):electrical.append({'boundary_case':name,'step_mm':step,'conditional_Cu_um':thickness,'conditional_uniform_copper_temperature_C':temp,'current_A':current,'sheet_R_ohm':resistance,'sheet_drop_V':current*resistance,'sheet_Joule_W':current*current*resistance,'peak_mesh_edge_A_per_mm':current*row['unit_current_peak_mesh_edge_A_per_mm'],'source_F_copper_barrels_load_fanout_return_feedback_ripple_and_transients_excluded':True})
            put('conditional-electrical-cases.json',electrical)
    comparisons=[]
    for name,*_ in cases:
        rr=[r for r in rows if r['boundary_case']==name and r['status']=='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED']
        if len(rr)==2:comparisons.append({'boundary_case':name,'coarse_step_mm':rr[0]['step_mm'],'fine_step_mm':rr[1]['step_mm'],'coarse_squares':rr[0]['effective_sheet_squares'],'fine_squares':rr[1]['effective_sheet_squares'],'fine_relative_change':rr[1]['effective_sheet_squares']/rr[0]['effective_sheet_squares']-1})
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_NATIVE_TWO_LEVEL_CONDITIONAL_DC_SOURCE_SHEET_SCREEN_COMPLETE_FULL_CURRENT_QUALIFICATION_OPEN','input_sha256':inputs,'source_current_binding':binding,'mesh_rows':rows,'conditional_electrical_cases':electrical,'two_level_comparisons':comparisons,'material_plating_temperature_and_converter_full_corner_assumptions_are_not_qualified':True,'two_levels_do_not_establish_complete_continuum_convergence_or_physical_current_capacity':True,'FIELD5_terminal_or_closed_loop_voltage_drop_budget_independently_qualified':False,'five_preexisting_unrooted_U9004_C9004_pads_remain_separate_uncompleted_board_joins':True,'no_annular_count_reclassification_or_via_contained_zone_added':True,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-start}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);put('status.json',{'phase':'COMPLETE_CONDITIONAL_CURRENT_GATE_OPEN','elapsed_seconds':time.monotonic()-start,'adopted':False});print(json.dumps({'status':result['status'],'seconds':result['elapsed_seconds'],'comparisons':comparisons}),flush=True)

if __name__=='__main__':main()
