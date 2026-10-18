"""Clip real old In4 copper around all affected current source-reference floors.

Only a real source-to-target component may become a parallel-plane nominee.
Disconnected annular remnants are explicitly not promoted to zones.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,pickle,sys,time
import shapely
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
OUT=HERE/'reference-hard-real-In4-sheet-construction-r1'
TRIAGE=HERE/'old-In4-restoration-triage-r2'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def summary(s):return {'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    files=[TRIAGE/'receipt.json',TRIAGE/'old-exact-native-intent.wkb',TRIAGE/'old-exact-native-fill.wkb',ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',Path(__file__),Path(K.__file__),Path(RF.__file__)]
    inputs={str(p):sha(p)for p in files};control=json.loads(files[0].read_text());assert all(not r['source_keys_lost']for r in control['prospective_source_rows']);assert all(not r['old_relationship_losses']for r in control['prospective_partition_rows'])
    intent=shapely.from_wkb(files[1].read_bytes());native=shapely.from_wkb(files[2].read_bytes());g=pickle.loads(files[3].read_bytes());groups=pickle.loads(files[4].read_bytes());tracks={t['uuid']:t for t in g['tracks']};protected=[];floor_inventory=[]
    for entry in control['prospective_old_reference_rows']:
        net=entry['net'];root=K.root(groups[net],'J11001'if net=='/LOGIC_GND'else'J11003','2');floor=unary_union([q['shape']for q in root if q['kind']=='fill'and q['layer']=='In4.Cu']);guard=.625 if net=='/LOGIC_GND'else.275
        for loss in entry['strict_zero_reference_losses']:
            t=tracks[loss['uuid']];body=K.L.body(t);oldfloor=body.intersection(floor);assert not oldfloor.is_empty;mask=oldfloor.buffer(guard+.0001,quad_segs=128);protected.append(mask);floor_inventory.append({'track':t,'source_ground':net,'raw_full_restore_reference_loss_mm2':loss['prior_source_reference_lost_mm2'],'actual_existing_source_floor':summary(oldfloor),'required_guard_plus_0p1um_inward_reservation_mm':guard+.0001,'mask':summary(mask)})
    cutters=unary_union(protected);base=native.intersection(intent);floating=base.difference(cutters).buffer(-.000002,quad_segs=128);nominee=set_precision(floating,1e-6,mode='valid_output');assert nominee.difference(native).is_empty and nominee.difference(intent).is_empty;assert nominee.intersection(cutters).is_empty
    holes,tree=K.hole_context(g);physical=nominee.difference(unary_union([holes[int(i)]for i in tree.query(nominee,predicate='intersects')]));fieldroot=K.root(groups[T.NET],'L11003','2');source=unary_union([q['shape']for q in fieldroot if q['kind']=='via'and q['uuid']==T.T2 and q['layer']=='In4.Cu']);target=unary_union([q['shape']for q in fieldroot if q['kind']=='via'and q['uuid']==T.T1 and q['layer']=='In4.Cu']);parts=RF.parts(physical);connected=[p for p in parts if p.intersection(source).area>1e-10 and p.intersection(target).area>1e-10]
    components=[]
    for i,p in enumerate(parts):
        if p.area<.000001:continue
        components.append({'component':i,'physical':summary(p),'source_annular_overlap_mm2':p.intersection(source).area,'target_annular_overlap_mm2':p.intersection(target).area})
    for name,s in(('all-affected-current-source-reference-floor-guards',cutters),('reference-hard-real-old-In4-intent',nominee),('reference-hard-real-old-In4-physical',physical)):(OUT/(name+'.wkb')).write_bytes(s.wkb)
    put('all-raw-source-reference-floor-constraints.json',floor_inventory);put('all-substantial-candidate-components.json',components)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'REAL_REFERENCE_HARD_PARALLEL_In4_CANDIDATE_CONNECTED_HOST_GATES_PENDING'if connected else'REFERENCE_HARD_OLD_SHEET_DISCONNECTED_NO_ANNULAR_ZONE_PACKET','input_sha256':inputs,'old_real_native_sheet':summary(native),'all_affected_current_source_floor_guard_union':summary(cutters),'literal_inward_native_1nm_grid_nominee':summary(nominee),'physical_nominee':summary(physical),'exact_subset_of_old_real_native_and_intent':True,'disjoint_from_every_affected_old_source_floor_guard':True,'substantial_component_count':len(components),'continuous_source_to_target_component_count':len(connected),'components':components,'full_ground_cut_control_source_keys_and_old_partitions_zero_loss':True,'any_adopted_negative_cut_must_be_proved_subset_of_full_control_and_rebound_native':True,'native_new_field_layer_flashes_fill_old_contacts_full_source_current_reference_and_DRC':'OPEN; constructor only','isolated_annuli_will_not_be_promoted':True,'native_jobs':0,'board_written':False,'sparse_packet_frozen':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);print(json.dumps({'status':result['status'],'nominee_mm2':nominee.area,'physical_mm2':physical.area,'connected_components':len(connected),'substantial_components':components}),flush=True)

if __name__=='__main__':main()
