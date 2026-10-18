"""Matched old/new sheet screen at the unchanged genuine finite electrodes."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,time
import shapely
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FIELD=ROOT/'reports/board-finish-20261011/continuation-r2/field-power';HOST=HERE/'separate-real-corridor-zone-host-qualification-r7';BASE=HERE/'actual-native-sheet-two-level-r1';OUT=HERE/'prospective-real-corridor-two-level-current-r7'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic();helper=FIELD/'solve_FIELD5_actual_finite_annular_sheet_r551.py';files=[HOST/'receipt.json',HOST/'prospective-source-rooted-In2-sheet.wkb',BASE/'receipt.json',BASE/'actual-e19f-In2-source-contact.wkb',BASE/'actual-0901-In2-target-contact.wkb',FIELD/'normal-model-r3.json',helper,Path(__file__)];inputs={str(p):sha(p)for p in files};h=json.loads(files[0].read_text());assert 'PASS'in h['status'];sheet,source,target=[shapely.from_wkb(p.read_bytes())for p in(files[1],files[3],files[4])];old=json.loads(files[2].read_text());plan=json.loads(files[5].read_text());normal=plan['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'];stress=plan['routing_local_targets_a']['FIELD5V_after_A_prereg'];assert stress==.36
    spec=importlib.util.spec_from_file_location('frozen_r551',helper);solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver);rows=[];electric=[];comparison=[]
    for step in(.025,.0125):
        put('status.json',{'phase':'MATCHED_PROSPECTIVE_CONTAINED_SHEET_SOLVE','step_mm':step,'numeric_threads':2,'affinity':list(range(16,28)),'native_jobs':0});r=solver.solve(sheet,source,target,step);rows.append(r);put('checkpoint.json',rows);print(json.dumps(r),flush=True);assert r['status']=='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED'
        oldrow=next(x for x in old['mesh_rows']if x['step_mm']==step and x.get('boundary_case')=='whole_actual_In2_e19f_finite_source_to_0901_finite_target')
        oldsq=oldrow['effective_sheet_squares'];newsq=r['effective_sheet_squares'];comparison.append({'step_mm':step,'actual_R299_squares':oldsq,'prospective_widened_squares':newsq,'prospective_change_fraction':newsq/oldsq-1,'same_actual_annular_electrodes_unchanged':True})
        for thick,temp in((35,60),(25,125)):
            rho=1.724e-8*(1+.00393*(temp-20));R=newsq*rho/(thick*1e-6)
            for current in(normal,stress):electric.append({'step_mm':step,'conditional_Cu_um':thick,'conditional_uniform_Cu_C':temp,'current_A':current,'sheet_R_ohm':R,'sheet_drop_V':R*current,'sheet_Joule_W':R*current*current,'peak_mesh_edge_A_per_mm':current*r['unit_current_peak_mesh_edge_A_per_mm']})
        put('comparison-checkpoint.json',comparison)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'PROSPECTIVE_PHYSICAL_WIDENING_MATCHED_TWO_LEVEL_DC_SCREEN_NATIVE_FIELD5_AND_FG_CURRENT_GATES_OPEN','input_sha256':inputs,'mesh_rows':rows,'matched_comparison':comparison,'conditional_electrical':electric,'normal_all12_and_other_planning_current_A':normal,'unchanged_routing_stress_A':stress,'two_level_refinement_change':rows[1]['effective_sheet_squares']/rows[0]['effective_sheet_squares']-1,'all_fixed_source_and_target_real_electrodes_retained':True,'upstream_F_four_shared_barrel_terms_local_fanout_return_feedback_switching_startup_ripple_and_real_material_temperature_plating':'OPEN','FG_signed_return_capacity_and_thermal_effects_of_all_five_negative_Cu_targets':'OPEN','actual_native_positive_retention_and_negative_target_removal':'OPEN; prospective host Cu is not native AFTER','full_current_capacity_and_terminal_voltage_spec_margin':'OPEN; no qualified FIELD5 minimum voltage budget exists','native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};put('receipt.json',result);put('status.json',{'phase':'COMPLETE_CONDITIONAL_ONLY_NATIVE_AND_BOTH_RAIL_CURRENT_OPEN'});print(json.dumps({'comparison':comparison,'seconds':result['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
