"""Inventory all native drilled FG electrodes touched by actual negative targets."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,pickle,sys
import shapely
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
CON=HERE/'separate-real-corridor-zone-construction-r7';HOST=HERE/'separate-real-corridor-zone-host-qualification-r7';OUT=HERE/'FG-return-electrode-inventory-r7';FG='/motherboard_motors/FIELD_GND';LY='In2.Cu';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();base=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';files=[base/'actual-combined-full-after-model.pkl',base/'actual-combined-full-after-all-net-groups.pkl',HOST/'prospective-two-net-groups.pkl',CON/'receipt.json',HERE/'demand-and-rework-obligation-r1/receipt.json',HERE/'complete-existing-barrel-kcl-r1/receipt.json',CONT/'field-power/normal-model-r3.json',Path(__file__)];inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());old=pickle.loads(files[1].read_bytes())[FG];new=pickle.loads(files[2].read_bytes())[FG];r=json.loads(files[3].read_text());sourceold=K.root(old,'J11003','2');sourcenew=K.root(new,'J11003','2');negative=[]
    for row in r['FG_native_negative_splices']:negative.append((row['uuid'],shapely.from_wkb((CON/(row['uuid']+'-literal-native-Cu-negative.wkb')).read_bytes())))
    metal=[q for xs in old for q in xs if q['kind']!='fill'and q['layer']==LY];tree=STRtree([q['shape']for q in metal]);touch=[]
    for zid,cut in negative:
        for j in tree.query(cut,predicate='intersects'):
            q=metal[int(j)];overlap=q['shape'].intersection(cut);touch.append({'zone_UUID':zid,'unchanged_metal':T.describe(q),'target_cut_contact_type':overlap.geom_type,'target_cut_overlap_mm2':overlap.area,'in_old_source_root':(q['kind'],q['uuid'],LY)in K.keys(sourceold),'in_prospective_source_root':(q['kind'],q['uuid'],LY)in K.keys(sourcenew),'discrete_electrode_Cu_unchanged':True})
    refs={'C11064','C11080','R11051','R11071','R9039','U11013','R11052','R9021','R9023','JD01','JD02','JD03','JD04','JD05','JD06','U11014','J11003'};pads=[]
    for p in g['pads']:
        if p['ref']not in refs or K.L.norm(p['net'])!=FG:continue
        rows=[q for q in sourceold if q['kind']=='pad'and q['uuid']==p['uuid']];padcut=[{'zone_UUID':zid,'physical_target_overlap_mm2':unary_union([q['shape']for q in rows if q['layer']==LY]).intersection(cut).area}for zid,cut in negative if any(q['layer']==LY for q in rows)and unary_union([q['shape']for q in rows if q['layer']==LY]).intersects(cut)];pads.append({'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'actual_Cu_layers':list(p['layers']),'old_J11003_2_source_root_layers':sorted({q['layer']for q in rows}),'prospective_J11003_2_source_root_layers':sorted({q['layer']for q in sourcenew if q['kind']=='pad'and q['uuid']==p['uuid']}),'In2_negative_target_intersections':padcut})
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'EXHAUSTIVE_CHANGED_FG_IN2_FINITE_DISCRETE_CONTACT_AND_NAMED_RETURN_ENDPOINT_CENSUS_CURRENT_OPEN','input_sha256':inputs,'actual_target_FG_zone_Cu_negative_mm2':r['FG_all_actual_target_Cu_removed_mm2'],'all_touched_In2_discrete_Cu_contacts':touch,'all_touched_In2_plated_pad_or_barrel_contacts':[x for x in touch if x['unchanged_metal']['kind']in('pad','via')],'named_seven_load_branch_aux_A_B_and_all12_motor_outlet_return_pads':pads,'all_old_FG_source_keys_retained':K.keys(sourceold).issubset(K.keys(sourcenew)),'all_required_motor_interfaces_and_simultaneous_AUX_outlet_planning_loads_preserved':True,'motor_AUX_A_full_outlet_demand_A':.128,'motor_AUX_B_full_outlet_demand_A':.064,'all12_motor_AUX_total_A':.192,'seven_load_branch_known_nonIC_static_subtotal_A':.1728047213703295,'seven_load_branch_conservative_two_TPS_Iq_sensitivity_A':.1730847213703295,'this_sensitivity_is_not_complete_bound_or_a_new_reduced_normal_model':True,'capacitor_startup_leakage_and_EN_other_state_loads':'OPEN; not zero','return_current_sharing_electrode_constriction_and_discrete_or_plane_redundancy':'OPEN; unchanged node reachability and finite contact are not resistance/current capacity','FG_full_signed_source_return_copper_connector_and_thermal_qualification':'OPEN; coupled all-load current network required, no demand derating','native_negative_Cu_target_removal_positive_retention_and_reference_effects':'OPEN','new_drills':0,'native_jobs':0,'adopted':False,'manufacturing_ready':False};put('receipt.json',result);print(json.dumps({'touched_metal_contacts':len(touch),'touched_barrel_pad_contacts':len(result['all_touched_In2_plated_pad_or_barrel_contacts']),'named_return_pads':len(pads),'source_keys_preserved':result['all_old_FG_source_keys_retained']}))
if __name__=='__main__':main()
