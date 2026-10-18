# Transparent derivative of probe_parallel_existing_barrel_corridors.py SHA256 416dfad7f2b71010c0d60266528d151dec660632a96e462cf0312573db681fa4
# Smaller 0.05 mm contained grid; widths 0.50/0.35 mm; existing same-net flashed via drill contacts remain allowed.
"""Bounded fixed-fill parallel-corridor search; no board or sparse packet.

Candidate tracks may join only the two existing FIELD5 barrels. All saved native
foreign copper stays fixed. A found path is a host geometry nominee, requiring
separate source-return/reference, native AFTER and complete current gates.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import hashlib,heapq,json,math,pickle,sys,time
import numpy as np
import shapely
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
OUT=HERE/'parallel-fixed-native-copper-probe-r2'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def cover_circle(x,y,r):return Point(x,y).buffer((r+1e-8)/math.cos(math.pi/512),quad_segs=128)

def route(free,start,end,step):
    x0,y0,x1,y1=free.bounds;xx=np.arange(math.ceil(x0/step)*step,x1,step);yy=np.arange(math.ceil(y0/step)*step,y1,step)
    X,Y=np.meshgrid(xx,yy);allowed=shapely.contains_xy(free.buffer(-step/math.sqrt(2)),X,Y);ny,nx=allowed.shape
    def anchors(point):
        ix=int(round((point[0]-xx[0])/step));iy=int(round((point[1]-yy[0])/step));found=[]
        for b in range(max(0,iy-3),min(ny,iy+4)):
            for a in range(max(0,ix-3),min(nx,ix+4)):
                q=(float(xx[a]),float(yy[b]))
                if allowed[b,a]and free.covers(LineString([point,q])):found.append((math.dist(point,q),b*nx+a))
        return sorted(found)[:8]
    starts=anchors(start);ends=anchors(end)
    if not starts or not ends:return {'status':'NO_CONTAINED_GRID_ENDPOINT_CONNECTION','start_anchor_count':len(starts),'end_anchor_count':len(ends)}
    endids={i:d for d,i in ends};dist={i:d for d,i in starts};previous={i:None for _,i in starts};queue=[]
    for d,i in starts:
        y,x=divmod(i,nx);heapq.heappush(queue,(d+math.dist((xx[x],yy[y]),end),d,i))
    goal=None;expanded=0
    while queue:
        _,d,i=heapq.heappop(queue)
        if d!=dist.get(i):continue
        expanded+=1
        if i in endids:goal=i;break
        y,x=divmod(i,nx)
        for dy,dx in((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            b=y+dy;a=x+dx
            if b<0 or b>=ny or a<0 or a>=nx or not allowed[b,a]:continue
            j=b*nx+a;nd=d+step*math.hypot(dy,dx)
            if nd<dist.get(j,float('inf')):
                dist[j]=nd;previous[j]=i;heapq.heappush(queue,(nd+math.dist((xx[a],yy[b]),end),nd,j))
    if goal is None:return {'status':'NO_FIXED_NATIVE_FILL_GRID_CORRIDOR','expanded':expanded,'grid_step_mm':step}
    points=[end];i=goal
    while i is not None:
        y,x=divmod(i,nx);points.append((float(xx[x]),float(yy[y])));i=previous[i]
    points.append(start);points.reverse();smooth=[points[0]];i=0
    while i<len(points)-1:
        j=len(points)-1
        while j>i+1 and not free.covers(LineString([points[i],points[j]])):j-=1
        smooth.append(points[j]);i=j
    assert free.covers(LineString(smooth))
    return {'status':'FIXED_NATIVE_FOREIGN_COPPER_GEOMETRY_CORRIDOR_NOMINEE','path_mm':[list(p)for p in smooth],'length_mm':LineString(smooth).length,'expanded':expanded,'grid_step_mm':step}

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    files=[ACTUAL/'actual-combined-full-after-model.pkl',HERE/'actual-source-paths-r1/source-path-receipt.json',Path(__file__),Path(K.__file__),Path(K.F.__file__),Path(K.L.__file__),HERE/'probe_parallel_existing_barrel_corridors.py']
    inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());net=T.NET;domain=g['domains_normalized'][net]
    rec,trees=K.F.build(g,layers={'F.Cu','B.Cu','In2.Cu','In3.Cu'})
    via={v['uuid']:v for v in g['vias']};start=(via[T.T2]['x'],via[T.T2]['y']);end=(via[T.T1]['x'],via[T.T1]['y'])
    roi=box(268,138,316,184);outline=unary_union(K.L.poly(g['outline']));results=[]
    for layer,width in(('F.Cu',.5),('B.Cu',.35),('In2.Cu',.5),('In3.Cu',.5)):
        put('status.json',{'phase':'HOST_FIXED_COPPER_CORRIDOR_PROBE','layer':layer,'width_mm':width,'native_jobs':0})
        candidates=[]
        for j in trees[layer].query(roi.buffer(3)):
            q=rec[layer][int(j)]
            if K.L.norm(q['net'])==net:continue
            body=q['shape'];uid=q['uuid']
            if q['kind']=='via':
                v=via[uid];body=cover_circle(v['x'],v['y'],v['d']/2)
            gap=.15 if q['domain']==domain else.6
            if q['kind']=='fill':gap=max(gap,float(next(z for z in g['zones']if z['uuid']==uid)['clearance_mm']))
            candidates.append({'kind':q['kind'],'uuid':uid,'net':K.L.norm(q['net']),'required_Cu_gap_mm':gap,'shape':body})
        for v in g['vias']:
            if v['uuid']in(T.T1,T.T2)or(K.L.norm(v['net'])==net and layer in v['flashed']):continue
            p=Point(v['x'],v['y'])
            if p.distance(roi)<2:candidates.append({'kind':'drill','uuid':v['uuid'],'net':K.L.norm(v['net']),'required_Cu_gap_mm':.275,'shape':cover_circle(v['x'],v['y'],v['drill']/2)})
        for p in g['pads']:
            for sh in K.L.poly(p.get('hole')or[]):
                if sh.distance(roi)<2:candidates.append({'kind':'pad_hole','uuid':p['uuid'],'ref':p['ref'],'pin':p['num'],'net':K.L.norm(p['net']),'required_Cu_gap_mm':.275,'shape':sh})
        for r in g['rule_areas']:
            if layer in r['layers']and r['no_tracks']:
                for sh in K.L.poly(r['outline']):
                    if sh.distance(roi)<2:candidates.append({'kind':'no_tracks_rule','uuid':r['uuid'],'net':'RULE','required_Cu_gap_mm':0,'shape':sh})
        blockers=unary_union([q['shape'].intersection(roi.buffer(3)).buffer(width/2+q['required_Cu_gap_mm']+.025,quad_segs=128)for q in candidates])
        free=roi.intersection(outline.buffer(-.525-width/2)).difference(blockers);(OUT/(layer.replace('.','-')+'-free-centerline-area.wkb')).write_bytes(free.wkb)
        result=route(free,start,end,.05);result.update({'layer':layer,'width_mm':width,'fixed_native_foreign_copper':True,'existing_source_barrel':T.T2,'existing_target_barrel':T.T1,'new_holes':0,'board_written':False})
        if 'path_mm'in result:
            axis=LineString(result['path_mm']);body=axis.buffer(width/2,quad_segs=128);checks=[]
            for q in candidates:
                d=body.distance(q['shape']);margin=d-q['required_Cu_gap_mm']
                if margin<.2:checks.append({k:v for k,v in q.items()if k!='shape'}|{'actual_body_distance_mm':d,'margin_mm':margin})
            checks.sort(key=lambda r:r['margin_mm']);assert all(c['margin_mm']>.0249 for c in checks)
            result['nearby_actual_geometry_constraints']=checks;result['minimum_near_constraint_margin_mm']=min((r['margin_mm']for r in checks),default=None)
            result['body_wkb_sha256']=hashlib.sha256(body.wkb).hexdigest();(OUT/(layer.replace('.','-')+'-candidate-track-body.wkb')).write_bytes(body.wkb)
            result['source_return_reference_native_after_full_current_and_thermal_gates']='OPEN; no corridor is promoted to a sparse packet or board'
            result['conditional_rectangular_track_squares_L_divided_by_w']=axis.length/width
        results.append(result);put('checkpoint.json',results);print(json.dumps({k:v for k,v in result.items()if k not in('path_mm','nearby_actual_geometry_constraints')}),flush=True)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'BOUNDED_FIXED_NATIVE_COPPER_PARALLEL_CORRIDOR_PROBE_NOT_ADOPTED','input_sha256':inputs,'unchanged_domains_gap_mm':{'same':.15,'different':.6},'additional_geometry_guard_mm':.025,'roi_mm':[268,138,316,184],'rows':results,'no_foreign_native_fill_cuts_proposed':True,'current_or_return_reference_pass_claimed':False,'native_jobs':0,'board_written':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);put('status.json',{'phase':'COMPLETE_HOST_GEOMETRY_ONLY','seconds':result['elapsed_seconds']})

if __name__=='__main__':main()
