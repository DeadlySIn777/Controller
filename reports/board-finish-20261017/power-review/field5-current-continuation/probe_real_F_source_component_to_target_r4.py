"""Search from any genuine upstream F source Cu, not just a trapped via center."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
import hashlib,importlib.util,json
import shapely
from shapely.geometry import Point
from shapely.ops import unary_union,nearest_points
HERE=Path(__file__).resolve().parent;OUT=HERE/'parallel-real-F-source-port-probe-r4';PRE=HERE/'parallel-F-B-explicit-FG-cut-probe-r3';SOURCE=HERE/'actual-F-source-component-two-level-r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();hp=HERE/'probe_parallel_existing_barrel_corridors_r2.py';sp=importlib.util.spec_from_file_location('frozen_corridor',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
def parts(s):return [s]if s.geom_type=='Polygon'else[p for p in s.geoms if p.geom_type=='Polygon']
def main():
    assert not OUT.exists();OUT.mkdir();files=[PRE/'F-Cu-free-centerline-area.wkb',SOURCE/'actual-F-source-component.wkb',SOURCE/'actual-L11003-2-source-contact.wkb',hp,Path(__file__)];free,source,terminal=[shapely.from_wkb(p.read_bytes())for p in files[:3]];target=(278.687,149.387);end=Point(target);rows=[];pp=parts(free);candidate=[]
    for i,p in enumerate(pp):
        contact=p.intersection(source);near=p.intersection(source.buffer(.20));r={'part':i,'centerline_area_mm2':p.area,'target_center_in_part':p.covers(end),'source_Cu_centerline_overlap_area_mm2':contact.area,'source_Cu_centerline_overlap_type':contact.geom_type,'source_electrode_body_reach_area_mm2':near.area,'L11003_2_contact_area_mm2':p.intersection(terminal).area};rows.append(r)
        if p.covers(end)and not contact.is_empty:candidate.append((p,contact))
    result={'status':'NO_HALF_MM_FREE_COMPONENT_JOINS_ANY_REAL_UPSTREAM_F_SOURCE_CU_TO_TARGET'if not candidate else'REAL_SOURCE_COMPONENT_PARALLEL_CORRIDOR_SEARCH','input_sha256':{str(p):sha(p)for p in files},'free_components':rows,'target':target,'all_existing_upstream_F_source_component_is_real_L11003_2_connected_Cu':True,'native_fill_and_current':'OPEN','adopted':False,'manufacturing_ready':False}
    for p,c in candidate:
        interior=c.buffer(-.0001);start=interior.representative_point()if not interior.is_empty else c.representative_point();row=H.route(p,tuple(start.coords)[0],target,.05);row['new_F_trace_width_mm']=.5;row['new_source_electrode_attachment_area_mm2']=start.buffer(.25,quad_segs=128).intersection(source).area;result.setdefault('route_rows',[]).append(row)
    (OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
