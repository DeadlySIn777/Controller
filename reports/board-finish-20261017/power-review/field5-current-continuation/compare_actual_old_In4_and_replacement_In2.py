"""Matched real-electrode DC screen of withdrawn In4 and replacement In2.

Never changes a board. Native finite contact apertures are solved separately,
then their exact intersections form identical electrodes for both sheets.
Three vertical transfer resistances are recorded separately with unknown
branch currents, so no invented load split or sum of three full currents occurs.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,math,pickle,sys,time
import shapely
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
FIELD=CONT/'field-power'
for p in (CONT/'coupled-recovery',FIELD,CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
OUT=HERE/'old-In4-vs-new-In2-matched-electrodes-r1'
OLD=FIELD/'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
NEW=HERE/'actual-native-sheet-two-level-r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(name,value):(OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def geometry(shape):return {'area_mm2':shape.area,'bounds':list(shape.bounds),'sha256':hashlib.sha256(shape.wkb).hexdigest()}
def rho(temp):return 1.724e-8*(1+.00393*(temp-20))

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    helper=FIELD/'solve_FIELD5_actual_finite_annular_sheet_r551.py'
    files=[OLD/'actual-full-R157-before-model.pkl',ACTUAL/'actual-combined-full-after-model.pkl',NEW/'receipt.json',helper,FIELD/'normal-model-r3.json',Path(K.__file__),Path(T.__file__),Path(__file__)]
    names=['actual-full-source-rooted-In2-sheet','actual-e19f-In2-source-contact','actual-0901-In2-target-contact']
    files += [NEW/(n+'.wkb')for n in names]
    inputs={str(p):sha(p)for p in files}
    old=pickle.loads(files[0].read_bytes());newmodel=pickle.loads(files[1].read_bytes())
    oldroot=K.root(K.physical(old,T.NET,K.hole_context(old))[1],'L11003','2')
    sheet_old=unary_union([q['shape']for q in oldroot if q['kind']=='fill'and q['uuid']=='61cb8179-7754-5031-bbea-0da464bf816f'and q['layer']=='In4.Cu'])
    sheet_new,source_new,target_new=[shapely.from_wkb((NEW/(n+'.wkb')).read_bytes())for n in names]
    assert sheet_old.area>90 and sheet_new.area>790
    via_binding={};old_contacts=[]
    for uid in(T.T2,T.T1):
        ov=next(v for v in old['vias']if v['uuid']==uid);nv=next(v for v in newmodel['vias']if v['uuid']==uid)
        checked=('uuid','net','x','y','d','drill','flashed')
        assert all(ov[k]==nv[k]for k in checked)
        assert set(ov['flashed'])==set(K.LAYERS)
        via_binding[uid]={k:ov[k]for k in checked};via_binding[uid]['unchanged_native_all6_flash']=True
        annulus=unary_union([q['shape']for q in oldroot if q['kind']=='via'and q['uuid']==uid and q['layer']=='In4.Cu'])
        old_contacts.append(annulus.intersection(sheet_old))
    source_old,target_old=old_contacts
    source_common=source_old.intersection(source_new);target_common=target_old.intersection(target_new)
    assert source_common.area>.15 and target_common.area>.06
    for shape in (sheet_old,sheet_new):
        assert source_common.difference(shape).area<1e-12 and target_common.difference(shape).area<1e-12
    shapes={'actual-old-drilled-In4-sheet':sheet_old,'actual-old-e19f-In4-source-contact':source_old,'actual-old-0901-In4-target-contact':target_old,'exact-common-real-source-electrode':source_common,'exact-common-real-target-electrode':target_common}
    for n,s in shapes.items():(OUT/(n+'.wkb')).write_bytes(s.wkb)
    source_path=T.finite_path(oldroot,lambda q:q['kind']=='pad'and(q['ref'],q['pin'])==('L11003','2'),lambda q:q['kind']=='via'and q['uuid']==T.T2 and q['layer']=='In4.Cu')
    sheet_path=T.finite_path(oldroot,lambda q:q['kind']=='via'and q['uuid']==T.T2 and q['layer']=='In4.Cu',lambda q:q['kind']=='via'and q['uuid']==T.T1 and q['layer']=='In4.Cu')
    binding={'unchanged_physical_vias':via_binding,'actual_old_sheet':geometry(sheet_old),'actual_new_sheet':geometry(sheet_new),'old_source':geometry(source_old),'new_source':geometry(source_new),'old_target':geometry(target_old),'new_target':geometry(target_new),'exact_common_source':geometry(source_common),'exact_common_target':geometry(target_common),'finite_old_converter_inductor_to_source_barrel_path':source_path,'finite_old_barrel_to_barrel_path':sheet_path,'source_anchor':'U11009.5 SW -> L11003.1 -> L11003.2 -> F source fanout -> e19f','new_source_path_receipt':str(HERE/'actual-source-paths-r1/source-path-receipt.json'),'identical_common_electrode_WKB_used_without_disks_or_load_sharing_assumptions':True}
    put('source-sheet-electrode-binding.json',binding)
    spec=importlib.util.spec_from_file_location('frozen_contained_r551',helper);solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
    cases=[('old_In4_actual_native_apertures',sheet_old,source_old,target_old),('old_In4_exact_common_finite_electrodes',sheet_old,source_common,target_common),('new_In2_exact_common_finite_electrodes',sheet_new,source_common,target_common)]
    plan=json.loads((FIELD/'normal-model-r3.json').read_text());normal=plan['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'];stress=plan['routing_local_targets_a']['FIELD5V_after_A_prereg'];assert stress==.36
    rows=[];electrical=[]
    for name,sheet,src,tgt in cases:
        for step in(.025,.0125):
            put('status.json',{'phase':'ACTUAL_NATIVE_MATCHED_SHEET_SOLVE','case':name,'step_mm':step,'completed':len(rows),'affinity':list(range(16,28)),'numeric_threads':2,'native_jobs':0})
            row=solver.solve(sheet,src,tgt,step);row['boundary_case']=name;rows.append(row);put('checkpoint.json',rows)
            print(json.dumps({'case':name,'step_mm':step,'status':row['status'],'squares':row.get('effective_sheet_squares'),'cells':row.get('contained_cells')}),flush=True)
            assert row['status']=='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED'
            for thickness,temp in((35,60),(25,125)):
                resistance=row['effective_sheet_squares']*rho(temp)/(thickness*1e-6)
                for current in(normal,stress):electrical.append({'boundary_case':name,'step_mm':step,'conditional_Cu_um':thickness,'conditional_uniform_copper_temperature_C':temp,'current_A':current,'sheet_R_ohm':resistance,'sheet_drop_V':current*resistance,'sheet_Joule_W':current*current*resistance,'peak_mesh_edge_A_per_mm':current*row['unit_current_peak_mesh_edge_A_per_mm'],'upstream_F_barrels_load_fanout_return_feedback_ripple_transients_excluded':True})
            put('conditional-electrical-cases.json',electrical)
    comparison=[]
    for step in(.025,.0125):
        rr={r['boundary_case']:r for r in rows if r['step_mm']==step}
        old_sq=rr['old_In4_exact_common_finite_electrodes']['effective_sheet_squares'];new_sq=rr['new_In2_exact_common_finite_electrodes']['effective_sheet_squares']
        comparison.append({'step_mm':step,'old_matched_squares':old_sq,'new_matched_squares':new_sq,'new_divided_by_old':new_sq/old_sq,'matched_electrode_both_sheets_same_rho_thickness_temperature_current':True})
    refinement=[]
    for name,*_ in cases:
        rr=[r for r in rows if r['boundary_case']==name]
        refinement.append({'boundary_case':name,'coarse_squares':rr[0]['effective_sheet_squares'],'fine_squares':rr[1]['effective_sheet_squares'],'fine_relative_change':rr[1]['effective_sheet_squares']/rr[0]['effective_sheet_squares']-1})
    # Native stackup is a provisional design declaration, not measured laminate.
    assert old['stackup']==newmodel['stackup']
    stack=newmodel['stackup'];ordered=('F.Cu','dielectric 1','In1.Cu','dielectric 2','In2.Cu','dielectric 3','In3.Cu','dielectric 4','In4.Cu','dielectric 5','B.Cu')
    depth={};pos=0
    for name in ordered:
        thick=stack[name]['thickness_mm']
        if name.endswith('.Cu'):depth[name]=pos+thick/2
        pos+=thick
    midplanes={name:value-depth['F.Cu']for name,value in depth.items()}
    transfers=[]
    for case,plane in(('old_In4','In4.Cu'),('new_In2','In2.Cu')):
        for term,start,end,current_symbol in(('source_e19f_F_to_plane','F.Cu',plane,'I_source_e19f'),('target_0901_plane_to_F',plane,'F.Cu','I_target_F'),('target_0901_plane_to_B',plane,'B.Cu','I_target_B')):
            length=abs(midplanes[end]-midplanes[start])
            for plating,temp in((25,60),(20,125)):
                drill_radius=.1e-3;t=plating*1e-6;area=math.pi*((drill_radius+t)**2-drill_radius**2)
                resistance=rho(temp)*(length*1e-3)/area
                transfers.append({'case':case,'term':term,'current_symbol':current_symbol,'midplane_segment_length_mm':length,'conditional_plating_um':plating,'conditional_uniform_temperature_C':temp,'R_ohm':resistance,'isolated_0_36A_term_drop_V':stress*resistance,'isolated_0_36A_is_sensitivity_only_not_sum_or_actual_branch_current':True})
    vertical={'declared_stackup':stack,'declared_outer_copper_surface_span_mm':pos,'declared_copper_midplanes_from_F_center_mm':midplanes,'board_general_nominal_thickness_mm':1.6,'declared_copper_plus_mask_span_mm':pos+stack['F.Mask']['thickness_mm']+stack['B.Mask']['thickness_mm'],'nominal_board_vs_stackup_discrepancy_mm':1.6-pos-stack['F.Mask']['thickness_mm']-stack['B.Mask']['thickness_mm'],'stackup_not_scaled_or_treated_as_fabricator_qualified':True,'three_separate_transfer_terms':transfers,'target_KCL':'I_target_F + I_target_B = I_target; actual split and other attached branches are unresolved','voltage_formula':'Upstream F source loss + R_source*I_source_e19f + R_sheet*I_sheet + R_target_F*I_target_F (F load) or R_target_B*I_target_B (B load) + load fanout and ground return. Shared barrel segment currents require a full network solution.','three_0_36A_terms_must_not_be_added_as_simultaneous_actual_drop':True,'electrothermal_and_plating_assumptions_qualified':False}
    put('three-separate-vertical-transfer-terms.json',vertical)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_WITHDRAWN_IN4_VERSUS_REPLACEMENT_IN2_MATCHED_ELECTRODE_DC_SCREEN_COMPLETE_CURRENT_GATE_OPEN','input_sha256':inputs,'source_sheet_binding':binding,'mesh_rows':rows,'matched_electrode_comparisons':comparison,'two_level_refinement':refinement,'conditional_electrical_cases':electrical,'vertical_transfer_file':'three-separate-vertical-transfer-terms.json','full_normal_all12_motor_and_other_planning_current_A':normal,'unchanged_routing_stress_A':stress,'load_split_does_not_reduce_or_redistribute_required_current':True,'same_material_current_temperature_for_both_sheets':True,'all6_real_via_layers_retained_no_geometry_reclassification':True,'current_capacity_material_plating_temperature_shared_barrel_upstream_return_ripple_transient_feedback_and_converter_full_corner_qualification':'OPEN','two_levels_do_not_establish_continuum_convergence_or_physical_current_capacity':True,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);put('status.json',{'phase':'COMPLETE_CURRENT_QUALIFICATION_OPEN','seconds':result['elapsed_seconds']});print(json.dumps({'status':result['status'],'matched':comparison,'refinement':refinement,'seconds':result['elapsed_seconds']}),flush=True)

if __name__=='__main__':main()
