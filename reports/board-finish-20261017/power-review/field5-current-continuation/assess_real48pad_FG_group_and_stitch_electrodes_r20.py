"""Measure actual floating48-pad ground Cu and real bridge electrodes.

Hypothetical floor coverage is diagnostic only. The group is not made rooted
until a physical Cu bridge passes source/contact/clearance/current gates.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,pickle,sys
import shapely
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';CENSUS=HERE/'new-F-power-return-floor-census-r19';OUT=HERE/'actual48-FG-floor-and-bridge-electrodes-r20';FG='/motherboard_motors/FIELD_GND'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sm(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
    assert not OUT.exists();OUT.mkdir();gp=ACTUAL/'actual-combined-full-after-all-net-groups.pkl';cg=CENSUS/'receipt.json';groups=pickle.loads(gp.read_bytes())[FG];source=K.root(groups,'J11003','2');floating=next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],q['pin'])==('JD02','A13')for q in xs));assert floating is not source;spads=sorted({q['ref']+'.'+q['pin']for q in source if q['kind']=='pad'});fpads=sorted({q['ref']+'.'+q['pin']for q in floating if q['kind']=='pad'});assert len(fpads)==48;sf=unary_union([q['shape']for q in source if q['kind']=='fill'and q['layer']=='In1.Cu']);ff=unary_union([q['shape']for q in floating if q['kind']=='fill'and q['layer']=='In1.Cu']);(OUT/'actual-rooted-In1-floor.wkb').write_bytes(sf.wkb);(OUT/'actual-floating48-In1-floor.wkb').write_bytes(ff.wkb);c=json.loads(cg.read_text());coverage=[];files=[gp,cg,Path(__file__)]
    for row in c['rows']:
        if row['scope']!='new_positive_Cu_only_excluding_existing_field_source_Cu':continue
        p=Path(row['WKB']);files.append(p);missing=shapely.from_wkb(p.read_bytes());guard=row['source_FG_In1_floor_inward_guard_mm'];floating_floor=ff if guard==0 else ff.buffer(-guard,quad_segs=128);recovered=missing.intersection(floating_floor);residual=missing.difference(floating_floor);name='hypothetical-root-after-real-bridge-'+str(round(guard*1000))+'um-uncovered.wkb';(OUT/name).write_bytes(residual.wkb);coverage.append({'guard_mm':guard,'currently_missing_new_power_Cu':sm(missing),'lies_in_actual_floating48_In1_Cu':sm(recovered),'still_outside_rooted_and_floating48_Cu':sm(residual),'hypothetical_source_join_not_accepted':True})
    candidates=[];layer_summary=[]
    for layer in K.LAYERS:
        aa=[q for q in source if q['layer']==layer];bb=[q for q in floating if q['layer']==layer]
        if not aa or not bb:continue
        tree=STRtree([q['shape']for q in aa]);ij,dist=tree.query_nearest([q['shape']for q in bb],all_matches=False,return_distance=True);layer=[]
        for fi,si,d in zip(ij[0],ij[1],dist):
            a=aa[int(si)];b=bb[int(fi)];p1,p2=nearest_points(a['shape'],b['shape']);layer.append({'layer':layer,'actual_Cu_edge_gap_mm':float(d),'rooted_electrode':T.describe(a),'floating48_electrode':T.describe(b),'nearest_real_Cu_points_mm':[list(p1.coords)[0],list(p2.coords)[0]],'rooted_record_bounds':list(a['shape'].bounds),'floating_record_bounds':list(b['shape'].bounds)})
        layer.sort(key=lambda r:(r['actual_Cu_edge_gap_mm'],r['rooted_electrode']['uuid'],r['floating48_electrode']['uuid']));candidates.extend(layer[:40]);layer_summary.append({'layer':layer,'best_real_Cu_electrodes':layer[:4]});(OUT/(layer.replace('.','-')+'-rooted-all-physical-Cu.wkb')).write_bytes(unary_union([q['shape']for q in aa]).wkb);(OUT/(layer.replace('.','-')+'-floating48-all-physical-Cu.wkb')).write_bytes(unary_union([q['shape']for q in bb]).wkb)
    r={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL48PAD_GROUND_GROUP_GEOMETRY_AND_RETURN_FLOOR_OBLIGATION_MEASURED_NO_VIRTUAL_JOIN','input_sha256':{str(p):sha(p)for p in files},'rooted_source_pad_nodes':spads,'actual_floating48_pad_nodes':fpads,'hypothetical_power_reference_floor_recovery_if_real_group_connection_is_built':coverage,'nearest_actual_source_and_group_Cu_electrodes':candidates,'layer_summary':layer_summary,'physical_bridge_new_foreign_clearance_old_source_contacts_references_current_material_thermal_and_native_after':'OPEN; no bridge or virtual ground union adopted','full_simultaneous_ground_return_envelope_A':4.58442937244,'branch_KCL_all48load_demand_and_current_sharing':'OPEN; no demand assigned zero or reduced','native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'rooted_pads':len(spads),'floating_pads':len(fpads),'coverage':[{'guard_mm':q['guard_mm'],'missing_mm2':q['currently_missing_new_power_Cu']['area_mm2'],'actual_float_Cu_overlap_mm2':q['lies_in_actual_floating48_In1_Cu']['area_mm2'],'residual_mm2':q['still_outside_rooted_and_floating48_Cu']['area_mm2']}for q in coverage],'nearest_per_layer':[{'layer':q['layer'],'nearest':q['best_real_Cu_electrodes'][0]}for q in layer_summary]}),flush=True)
if __name__=='__main__':main()
