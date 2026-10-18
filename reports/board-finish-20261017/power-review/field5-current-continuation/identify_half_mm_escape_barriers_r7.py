"""Exact foreign-object witnesses at nearest enclosed-source escape bridges."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,math,pickle
import shapely
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];PRE=HERE/'parallel-F-B-actual-source-pad-probe-r5';OUT=HERE/'half-mm-enclosed-source-escape-barriers-r7';hp=HERE/'probe_parallel_existing_barrel_corridors_r2.py';sp=importlib.util.spec_from_file_location('corridor',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H);K=H.K;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):return[s]if s.geom_type=='Polygon'else list(s.geoms)
def main():
    assert not OUT.exists();OUT.mkdir();model=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-combined-full-after-model.pkl';g=pickle.loads(model.read_bytes());rec,trees=K.F.build(g,layers={'F.Cu','B.Cu'});domain=g['domains_normalized'][H.T.NET];via={v['uuid']:v for v in g['vias']};rows=[];files=[model,PRE/'receipt.json',HERE/'parallel-expanded-actual-pad-port-r6/receipt.json',hp,Path(__file__)]
    for layer,ref,pin in(('F.Cu','L11003','2'),('B.Cu','C11081','1')):
        fp=PRE/(layer.replace('.','-')+'-free-centerline-area.wkb');files.append(fp);free=shapely.from_wkb(fp.read_bytes());pad=next(q for q in g['pads']if(q['ref'],q['num'])==(ref,pin));source=unary_union(K.L.poly(pad['layers'][layer]));start=source.centroid;target=Point(278.687,149.387);a=next(p for p in parts(free)if p.covers(start));b=next(p for p in parts(free)if p.covers(target));pa,pb=nearest_points(a,b);axis=LineString([pa,pb]);body=axis.buffer(.25,quad_segs=128);blocks=[]
        for j in trees[layer].query(body.buffer(1)):
            q=rec[layer][int(j)];net=K.L.norm(q['net'])
            if net==H.T.NET or(q['kind']=='fill'and net=='/motherboard_motors/FIELD_GND'):continue
            sh=q['shape'];reservation=.005 if q['kind']=='pad'or(q['kind']=='track'and q['source'].get('m')is not None)else 0
            if q['kind']=='via':v=via[q['uuid']];d=body.distance(Point(v['x'],v['y']))-v['d']/2
            elif q['kind']=='track'and q['source'].get('m')is None:t=q['source'];d=body.distance(LineString([t['a'],t['b']]))-t['w']/2
            else:d=body.distance(sh)-reservation
            req=.15 if q['domain']==domain else.6
            if q['kind']=='fill':req=max(req,float(next(z for z in g['zones']if z['uuid']==q['uuid'])['clearance_mm']))
            if d<req+.025:blocks.append(H.T.describe(q)|{'net':net,'required_native_gap_mm':req,'native_shape_reservation_mm':reservation,'guaranteed_body_gap_mm':d,'engineering_guard_mm':.025,'native_source_record':q.get('source')})
        other=[]
        for v in g['vias']:
            if v['uuid']in(H.T.T1,H.T.T2)or(K.L.norm(v['net'])==H.T.NET and layer in v['flashed']):continue
            d=body.distance(Point(v['x'],v['y']))-v['drill']/2
            if d<.3:other.append({'kind':'drill','uuid':v['uuid'],'net':K.L.norm(v['net']),'body_gap_mm':d,'required_plus_guard_mm':.3})
        r={'layer':layer,'source_terminal':ref+'.'+pin,'source_free_component':{'area_mm2':a.area,'bounds':list(a.bounds),'distance_to_frozen_ROI_boundary_mm':a.distance(box(250,120,350,210).boundary)},'target_free_component':{'area_mm2':b.area,'bounds':list(b.bounds)},'nearest_centerline_bridge_mm':[list(pa.coords)[0],list(pb.coords)[0]],'bridge_length_mm':axis.length,'bridge_fixed_Cu_violations':blocks,'bridge_drill_violations':other,'interpretation':'This is one shortest inter-component bridge witness, not a globally minimal foreign-reroute set. Every all-fixed 0.5mm route must leave the enclosed source component; some hard native Cu/drill/rule boundary therefore needs a real escape edit or taper.','no_new_copper_or_foreign_reroute_frozen':True};rows.append(r);(OUT/(layer.replace('.','-')+'-source-free-component.wkb')).write_bytes(a.wkb);(OUT/(layer.replace('.','-')+'-target-free-component.wkb')).write_bytes(b.wkb);print(json.dumps({'layer':layer,'bridge_mm':axis.length,'blocking_native_Cu':[{k:v for k,v in q.items()if k in('kind','uuid','net','ref','pin')}for q in blocks],'blocking_drills':other}),flush=True)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_NATIVE_FIXED_CU_ESCAPE_OBSTACLES_IDENTIFIED_FOR_SUBSTANTIVE_HALF_MM_PARALLEL_PATH','input_sha256':{str(p):sha(p)for p in files},'rows':rows,'all_power_limits_and_simultaneous_loads_preserved':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
