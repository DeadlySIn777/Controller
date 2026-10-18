"""Conditional real F.Cu source component before the e19f plane transfer."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,pickle,sys,time
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2';FIELD=CONT/'field-power'
for p in(CONT/'coupled-recovery',FIELD,CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
OUT=HERE/'actual-F-source-component-two-level-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic();helper=FIELD/'solve_FIELD5_actual_finite_annular_sheet_r551.py'
    files=[ACTUAL/'actual-combined-full-after-all-net-groups.pkl',HERE/'actual-source-paths-r1/source-path-receipt.json',FIELD/'normal-model-r3.json',helper,Path(__file__)]
    inputs={str(p):sha(p)for p in files};groups=pickle.loads(files[0].read_bytes());root=K.root(groups['/motherboard_power_entry/FIELD_5V'],'L11003','2')
    source=unary_union([q['shape']for q in root if q['kind']=='pad'and(q['ref'],q['pin'],q['layer'])==('L11003','2','F.Cu')]);target=unary_union([q['shape']for q in root if q['kind']=='via'and q['uuid']=='e19f5a4a-8797-4ce8-a00d-4c884cc46739'and q['layer']=='F.Cu'])
    allF=unary_union([q['shape']for q in root if q['layer']=='F.Cu']);parts=[allF]if allF.geom_type=='Polygon'else list(allF.geoms);sheet=unary_union([p for p in parts if p.intersection(source).area>1e-10]);source=source.intersection(sheet);target=target.intersection(sheet)
    assert source.area>1 and target.area>.1
    for name,s in [('actual-F-source-component',sheet),('actual-L11003-2-source-contact',source),('actual-e19f-F-target-contact',target)]:(OUT/(name+'.wkb')).write_bytes(s.wkb)
    spec=importlib.util.spec_from_file_location('frozen_r551',helper);solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)
    plan=json.loads(files[2].read_text());normal=plan['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'];stress=plan['routing_local_targets_a']['FIELD5V_after_A_prereg'];rows=[];electrical=[]
    for step in(.025,.0125):
        row=solver.solve(sheet,source,target,step);rows.append(row);put('checkpoint.json',rows);print(json.dumps(row),flush=True);assert row['status']=='CONDITIONAL_CONTAINED_ACTUAL_SHEET_SOLVED'
        for thickness,temp in((35,60),(25,125)):
            rho=1.724e-8*(1+.00393*(temp-20));R=row['effective_sheet_squares']*rho/(thickness*1e-6)
            for current in(normal,stress):electrical.append({'step_mm':step,'conditional_Cu_um':thickness,'conditional_uniform_temperature_C':temp,'source_to_e19f_current_concentration_A':current,'R_ohm':R,'drop_V':current*R,'Joule_W':current*current*R,'current_is_stress_boundary_not_physical_sharing_claim':True})
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_F_SOURCE_COMPONENT_CONDITIONAL_DC_SCREEN_COMPLETE_FULL_NETWORK_CURRENT_GATE_OPEN','input_sha256':inputs,'actual_F_source_component_area_mm2':sheet.area,'actual_L11003_2_source_contact_mm2':source.area,'actual_e19f_target_annulus_mm2':target.area,'actual_source_root':'L11003.2','actual_target':'e19f5a4a-8797-4ce8-a00d-4c884cc46739 F.Cu','rows':rows,'two_level_relative_change':rows[1]['effective_sheet_squares']/rows[0]['effective_sheet_squares']-1,'conditional_electrical_cases':electrical,'planar_native_component_includes_actual_pads_tracks_via_annuli_and_fill':True,'barrels_other_planar_components_return_regulation_ripple_transient_and_capacitance_excluded':True,'F_injection_to_other_vias_and_loads_not_solved':True,'no_equal_current_sharing_or_lower_load_limit_assumed':True,'two_levels_do_not_prove_continuum_convergence_or_thermal_capacity':True,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result)

if __name__=='__main__':main()
