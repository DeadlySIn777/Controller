"""Conditional actual-old-plus-new F sheet, genuine source and target electrodes.

This is not equal current sharing or a simple parallel-rectangle assumption.
Actual native source/spreading/load Cu participates in the planar F solve.
The In2 plane and vertical/return/load branch network remain separate/open.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,pickle,sys,time
import shapely
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';FIELD=CONT/'field-power';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';CAND=HERE/'F-parallel-offset-FA-landing-refined-r10';OUT=HERE/'conditional-new-F-real-source-target-two-level-r11'
for p in(CONT/'coupled-recovery',FIELD,CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic();helper=FIELD/'solve_FIELD5_actual_finite_annular_sheet_r551.py';files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',CAND/'receipt.json',CAND/'candidate-axis.wkb',FIELD/'normal-model-r3.json',helper,Path(__file__)];inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());groups=pickle.loads(files[1].read_bytes());root=K.root(groups[T.NET],'L11003','2');rr=json.loads(files[2].read_text());assert rr['trace_width_mm']==.5 and'path_mm'in rr;points=[[round(x,6),round(y,6)]for x,y in rr['path_mm']];axis=LineString(points);body=axis.buffer(.25,quad_segs=128);oldF=unary_union([q['shape']for q in root if q['layer']=='F.Cu']);holes=unary_union(K.hole_context(g)[0]+[Point(297.65,155.35).buffer(.1,quad_segs=128)]);raw=oldF.union(body).difference(holes);source=unary_union([q['shape']for q in root if q['kind']=='pad'and(q['ref'],q['pin'],q['layer'])==('L11003','2','F.Cu')]);target=unary_union([q['shape']for q in root if q['kind']=='via'and q['uuid']==T.T1 and q['layer']=='F.Cu']);parts=[raw]if raw.geom_type=='Polygon'else list(raw.geoms);sheet=unary_union([p for p in parts if p.intersection(source).area>1e-10]);source=source.intersection(sheet);target=target.intersection(sheet);assert source.area>1 and target.area>.1
    for name,s in(('native-old-plus-new-drilled-F-sheet',sheet),('native-L11003-2-source-electrode',source),('native-0901-F-target-electrode',target),('new-native-1nm-quantized-axis',axis)):(OUT/(name+'.wkb')).write_bytes(s.wkb)
    put('electrode-and-new-track-binding.json',{'actual_source_pad':'L11003.2 F.Cu','actual_target_via':T.T1+' F.Cu','source_area_mm2':source.area,'target_real_annulus_area_mm2':target.area,'nominal_new_width_mm':.5,'quantized_native_1nm_path_mm':points,'new_track_length_mm':axis.length,'old_F_component_and_new_positive_Cu_used_not_an_ideal_rectangle':True,'all_original_drilled_voids_and_one_conditional_FA_new_drill_subtracted':True,'new_FA_return_via_landing':'OPEN; any additional hole must be reapplied before final qualification'})
    spec=importlib.util.spec_from_file_location('frozen_solver_r551',helper);solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver);plan=json.loads(files[4].read_text());normal=plan['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'];stress=plan['routing_local_targets_a']['FIELD5V_after_A_prereg'];assert stress==.36;rows=[];electric=[]
    for step in(.025,.0125):
        put('status.json',{'phase':'CONDITIONAL_NEW_ACTUAL_F_SHEET_CONTAINED_MESH','step_mm':step,'affinity':list(range(16,28)),'numeric_threads':2});r=solver.solve(sheet,source,target,step);rows.append(r);put('checkpoint.json',rows);print(json.dumps(r),flush=True);assert r['status']=='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED'
        for thick,temp in((35,60),(25,125)):
            R=r['effective_sheet_squares']*1.724e-8*(1+.00393*(temp-20))/(thick*1e-6)
            for I in(normal,stress):electric.append({'step_mm':step,'conditional_Cu_um':thick,'conditional_uniform_Cu_C':temp,'source_to_target_boundary_current_A':I,'F_sheet_R_ohm':R,'F_sheet_drop_V':I*R,'F_sheet_Joule_W':I*I*R,'peak_mesh_edge_A_per_mm':I*r['unit_current_peak_mesh_edge_A_per_mm']})
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'CONDITIONAL_NEW_F_REAL_SOURCE_SPREADING_TO_REAL_0901_ANNULUS_DC_SCREEN_COMPLETE_ALL_PHYSICAL_CURRENT_NATIVE_GATES_OPEN','input_sha256':inputs,'rows':rows,'conditional_electrical':electric,'source':'Actual L11003.2 F pad; source spreading included in F planar sheet','target':'Actual0901 F annulus; target F fanout included where physically connected','normal_full_all12_and_other_planning_current_A':normal,'unchanged_stress_A':stress,'two_level_refinement_change':rows[1]['effective_sheet_squares']/rows[0]['effective_sheet_squares']-1,'no_equal_current_split_or_ideal_parallel307_and104_claim':True,'coupled_F_In2_barrel_shared_taps_full_signed_FG_return_load_network_feedback_switching_ripple_startup_capacitor_leakage_regulation':'OPEN','FA_new_via_and_paired_return_hole_copper_SMD_source_contact_reference_and_replacement_route':'OPEN','FG_F_negative_source_native_retention_full_current_and_thermal':'OPEN','terminal_minimum_voltage_budget_material_plating_temperature_continuum_mesh_convergence':'OPEN','native_fill_DRC_source_old_contact_reference_and_SI':'OPEN','adopted':False,'manufacturing_ready':False,'native_jobs':0,'elapsed_seconds':time.monotonic()-started};put('receipt.json',result);print(json.dumps({'status':result['status'],'fine_squares':rows[-1]['effective_sheet_squares'],'seconds':result['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
