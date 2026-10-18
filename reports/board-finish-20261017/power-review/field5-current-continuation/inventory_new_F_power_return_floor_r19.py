"""Exact source-rooted return-floor coverage, separate from old-reference retention."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,pickle,sys
from shapely.geometry import LineString
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';HOST=HERE/'strict-FG-F-source-negative-r15';OUT=HERE/'new-F-power-return-floor-census-r19';FG='/motherboard_motors/FIELD_GND';NET='/motherboard_power_entry/FIELD_5V'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sm(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
    assert not OUT.exists();OUT.mkdir();files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',HOST/'strict-power-only-target-model.pkl',HOST/'receipt.json',HERE/'power-only-FG-F-effects-host-r12/native-quantized-power-track-operations.json',Path(__file__)];inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());old=pickle.loads(files[1].read_bytes());h=pickle.loads(files[2].read_bytes());newfg=K.root(K.physical(h,FG,K.hole_context(h))[1],'J11003','2');oldfg=K.root(old[FG],'J11003','2');oldfield=K.root(old[NET],'L11003','2');tracks=json.loads(files[4].read_text());points=[tracks[0]['a']]+[t['b']for t in tracks];holes=unary_union(K.hole_context(h)[0]);body=LineString(points).buffer(.25,quad_segs=128).difference(holes);oldCu=unary_union([q['shape']for q in oldfield if q['layer']=='F.Cu']);newCu=body.difference(oldCu);oldfloor=unary_union([q['shape']for q in oldfg if q['kind']=='fill'and q['layer']=='In1.Cu']);newfloor=unary_union([q['shape']for q in newfg if q['kind']=='fill'and q['layer']=='In1.Cu']);rows=[]
    for guard in(0,.075):
        floor=newfloor if guard==0 else newfloor.buffer(-guard,quad_segs=128)
        for name,shape in(('entire_new_track_drilled_body',body),('new_positive_Cu_only_excluding_existing_field_source_Cu',newCu)):
            miss=shape.difference(floor);filename=name+'-'+str(round(guard*1000))+'um-missing.wkb';(OUT/filename).write_bytes(miss.wkb);rows.append({'scope':name,'source_FG_In1_floor_inward_guard_mm':guard,'scope_Cu':sm(shape),'uncovered_Cu':sm(miss),'missing_positive_area_components':[sm(p)for p in RF.parts(miss)],'exact_empty_gate':miss.is_empty,'WKB':str(OUT/filename)})
    r={'utc':datetime.now(timezone.utc).isoformat(),'status':'NEW_POWER_TRACE_RETURN_FLOOR_CENSUS_RAW_SCOPES_NOT_A_CURRENT_OR_REFERENCE_PASS','input_sha256':inputs,'old_source_FG_In1_floor_lost':sm(oldfloor.difference(newfloor)),'old_source_FG_In1_floor_gained':sm(newfloor.difference(oldfloor)),'rows':rows,'entire_body_includes_existing_owned_source_pad_and_target_via_apertures':True,'positive_only_scope_does_not_auto_waive_any_raw_missing_body':True,'same_current_all12_outlet_and_other_full_planning_loads_preserved':True,'full_signed_FG_return_geometric_path_impedance_spreading_and_electrothermal':'OPEN; projected floor coverage alone is not current capacity','FA38retirement_existing_port_In3_replacement_and_its_FG_ground_Cu_effects':'PENDING coupled rebind; no new drill assumed','actual_native_positive_negative_minwidth_source_contacts_old_and_new_reference_DRC_SI':'OPEN','adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'old_FG_In1_source_floor_lost_mm2':r['old_source_FG_In1_floor_lost']['area_mm2'],'rows':[{k:v for k,v in x.items()if k in('scope','source_FG_In1_floor_inward_guard_mm','uncovered_Cu','exact_empty_gate')}for x in rows]}),flush=True)
if __name__=='__main__':main()
