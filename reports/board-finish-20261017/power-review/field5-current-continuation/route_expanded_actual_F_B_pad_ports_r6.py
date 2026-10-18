"""Reuse frozen expanded free Cu geometry with actual source-pad anchors."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
import hashlib,importlib.util,json,pickle,sys
import shapely
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];PRE=HERE/'parallel-F-B-actual-source-pad-probe-r5';OUT=HERE/'parallel-expanded-actual-pad-port-r6';hp=HERE/'probe_parallel_existing_barrel_corridors_r2.py';sp=importlib.util.spec_from_file_location('corridor',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H);K=H.K;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):return[s]if s.geom_type=='Polygon'else list(s.geoms)
def main():
    assert not OUT.exists();OUT.mkdir();model=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-combined-full-after-model.pkl';g=pickle.loads(model.read_bytes());target=(278.687,149.387);rows=[];files=[model,PRE/'receipt.json',hp,Path(__file__)]
    for layer,ref,pin in(('F.Cu','L11003','2'),('B.Cu','C11081','1')):
        p=PRE/(layer.replace('.','-')+'-free-centerline-area.wkb');files.append(p);free=shapely.from_wkb(p.read_bytes());pad=next(q for q in g['pads']if(q['ref'],q['num'])==(ref,pin));source=unary_union(K.L.poly(pad['layers'][layer]));start=tuple(source.centroid.coords)[0];startparts=[q for q in parts(free)if q.covers(Point(start))];endparts=[q for q in parts(free)if q.covers(Point(target))];shared=[q for q in startparts if q.covers(Point(target))];r={'layer':layer,'source_terminal':ref+'.'+pin,'source_mm':list(start),'target_existing_barrel':'0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3','target_mm':target,'trace_width_mm':.5,'source_centerline_free':bool(startparts),'target_centerline_free':bool(endparts),'same_continuous_free_centerline_component':bool(shared),'source_component_bounds':[list(q.bounds)for q in startparts],'target_component_bounds':[list(q.bounds)for q in endparts],'only_FG_fill_cuts_allowed_other_actual_native_Cu_hard':True,'new_holes':0}
        if shared:
            rr=H.route(shared[0],start,target,.05);r.update(rr)
            if'path_mm'in rr:
                axis=LineString(rr['path_mm']);r['rectangular_track_squares_length_over_width']=axis.length/.5;r['source_real_pad_finite_attachment_mm2']=axis.buffer(.25,quad_segs=128).intersection(source).area;r['native_source_old_contacts_FG_return_reference_material_thermal_barrel_KCL_and_voltage_budget']='OPEN';(OUT/(layer.replace('.','-')+'-candidate-body.wkb')).write_bytes(axis.buffer(.25,quad_segs=128).wkb)
        else:r['status']='REAL_PAD_PORT_NOT_CONNECTED_AT_HALF_MM_WITH_ALL_NON_FG_CU_FIXED'
        rows.append(r);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(r),flush=True)
    result={'status':'EXPANDED_PHYSICAL_HALF_MM_PATH_SEARCH_REAL_SOURCE_PAD_PORTS','input_sha256':{str(p):sha(p)for p in files},'rows':rows,'no_full_board_route_impossibility_claim':True,'native_after_current_and_return':'OPEN','adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
