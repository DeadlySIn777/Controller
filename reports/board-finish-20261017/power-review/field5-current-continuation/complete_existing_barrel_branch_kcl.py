"""Complete the requested three transfer sensitivities with an actual B tap.

e19f also has a real B-side monitor/cap branch. Its additional lower segment
cannot be silently omitted from a future complete network solution.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,pickle,sys
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
OUT=HERE/'complete-existing-barrel-kcl-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

def main():
    assert not OUT.exists();OUT.mkdir()
    files=[ACTUAL/'actual-combined-full-after-all-net-groups.pkl',HERE/'demand-and-rework-obligation-r1/actual-all-layer-barrel-contact-inventory.json',HERE/'old-In4-vs-new-In2-matched-electrodes-r1/three-separate-vertical-transfer-terms.json',CONT/'field-power/normal-model-r3.json',Path(__file__),Path(T.__file__),Path(K.__file__)]
    inputs={str(p):sha(p)for p in files};groups=pickle.loads(files[0].read_bytes());root=K.root(groups[T.NET],'L11003','2');vertical=json.loads(files[2].read_text());plan=json.loads(files[3].read_text());branches=[]
    for uid in(T.T2,T.T1):
        for ly in('F.Cu','B.Cu'):
            rows=[q for q in root if q['layer']==ly];cu=unary_union([q['shape']for q in rows]);parts=[cu]if cu.geom_type=='Polygon'else list(cu.geoms);via=next(q['shape']for q in rows if q['kind']=='via'and q['uuid']==uid);component=unary_union([p for p in parts if p.intersection(via).area>1e-10]);pads=sorted({(q['ref'],q['pin'])for q in rows if q['kind']=='pad'and q['shape'].intersection(component).area>1e-10});paths={}
            for ref,pin in pads:paths[ref+'.'+pin]=T.finite_path(rows,lambda q:q['kind']=='via'and q['uuid']==uid,lambda q:q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin))
            branches.append({'via':uid,'layer':ly,'physical_planar_component_area_mm2':component.area,'actual_named_pads':[a+'.'+b for a,b in pads],'finite_paths':paths})
    b=next(b for b in branches if b['via']==T.T2 and b['layer']=='B.Cu');assert b['actual_named_pads']==['C11081.1','R9029.1']
    r9029=next(q for q in plan['resistor_source_upper_bounds']['FIELD_5V']if q['ref']=='R9029')
    extra=[];mid=vertical['declared_copper_midplanes_from_F_center_mm']
    for case,plane in(('old_In4','In4.Cu'),('new_In2','In2.Cu')):
        length=mid['B.Cu']-mid[plane]
        for plating,temp in((25,60),(20,125)):
            area=math.pi*((.1e-3+plating*1e-6)**2-(.1e-3)**2);rho=1.724e-8*(1+.00393*(temp-20));R=rho*length*1e-3/area
            extra.append({'case':case,'term':'e19f_plane_to_existing_B_monitor_cap_branch','conditional_midplane_length_mm':length,'conditional_plating_um':plating,'conditional_uniform_temperature_C':temp,'R_ohm':R,'R9029_known_resistor_planning_A':r9029['current_upper_a'],'R9029_only_segment_drop_sensitivity_V':R*r9029['current_upper_a'],'C11081_leakage_inrush_and_other_physical_branches_not_assigned_zero':True})
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_ADDITIONAL_e19f_B_TAP_AND_FOUR_SEGMENT_KCL_OBLIGATION_FROZEN','input_sha256':inputs,'actual_planar_port_branches':branches,'existing_e19f_B_monitor_resistor_term':r9029,'three_original_transfer_sensitivities_retained':True,'additional_required_lower_e19f_B_segment':extra,'KCL_at_e19f_plane':'I_e19f_F_to_plane = I_e19f_into_plane_sheet + I_e19f_plane_to_B; include C11081 and R9029 at the B branch and all actual F-plane injections.','KCL_at_0901_plane':'I_plane_sheet_into_0901 = I_0901_plane_to_F + I_0901_plane_to_B','shared_current_and_voltage':'The source e19f F-to-plane resistance multiplies its actual combined sheet-plus-B current; the separate e19f plane-to-B resistance multiplies only its B branch current. Target F/B currents follow their actual loads. A future network must not use the same full 0.36A in all four segments.','no_complete_barrel_network_or_actual_current_capacity_claimed':True,'stackup_plating_temperature_and_thermal_assumptions_remain_unqualified':True,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);print(json.dumps({'status':result['status'],'e19f_B_pads':b['actual_named_pads'],'known_R9029_A':r9029['current_upper_a']}))

if __name__=='__main__':main()
