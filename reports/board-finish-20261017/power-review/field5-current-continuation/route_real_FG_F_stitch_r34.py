"""Actual finite-FG-electrode wide detour; all foreign Cu/drills/rules hard."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,math,pickle,sys
import shapely
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';PRE=HERE/'actual48-FG-floor-and-bridge-electrodes-r21';OUT=HERE/'actual-wide-FG-F-stitch-route-r34';FG='/motherboard_motors/FIELD_GND';LY='F.Cu';hp=HERE/'probe_parallel_existing_barrel_corridors_r2.py';sp=importlib.util.spec_from_file_location('corridor',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H);K=H.K;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):return[s]if s.geom_type=='Polygon'else[p for p in s.geoms if p.geom_type=='Polygon']
def main():
    assert not OUT.exists();OUT.mkdir();model=ACTUAL/'actual-combined-full-after-model.pkl';src=PRE/'F-Cu-rooted-all-physical-Cu.wkb';flt=PRE/'F-Cu-floating48-all-physical-Cu.wkb';g=pickle.loads(model.read_bytes());source,floating=[shapely.from_wkb(p.read_bytes())for p in(src,flt)];domain=g['domains_normalized'][FG];roi=box(225,15,295,75);rec,trees=K.F.build(g,layers={LY});vias={v['uuid']:v for v in g['vias']};base=[];constraints=[]
    for j in trees[LY].query(roi.buffer(3)):
        q=rec[LY][int(j)];net=K.L.norm(q['net'])
        if net==FG:continue
        sh=q['shape'];gap=.15 if q['domain']==domain else.6
        if q['kind']=='fill':gap=max(gap,float(next(z for z in g['zones']if z['uuid']==q['uuid'])['clearance_mm']))
        if q['kind']=='via':v=vias[q['uuid']];sh=H.cover_circle(v['x'],v['y'],v['d']/2)
        if q['kind']=='pad'or(q['kind']=='track'and q['source'].get('m')is not None):sh=sh.buffer(.005,quad_segs=128)
        if q['kind']=='track'and q['source'].get('m')is None:t=q['source'];sh=LineString([t['a'],t['b']]).buffer((t['w']/2+1e-8)/math.cos(math.pi/512),quad_segs=128)
        base.append((sh,gap+.0251));constraints.append(Tdescribe(q)|{'net':net,'required_plus_guard_mm':gap+.0251})
    for v in g['vias']:
        if K.L.norm(v['net'])==FG and LY in v['flashed']:continue
        if Point(v['x'],v['y']).distance(roi)>3:continue
        base.append((H.cover_circle(v['x'],v['y'],v['drill']/2),.3001));constraints.append({'kind':'true_circular_drill','uuid':v['uuid'],'required_plus_guard_mm':.3001})
    for pad in g['pads']:
        if K.L.norm(pad['net'])==FG:continue
        for sh in K.L.poly(pad.get('hole')or[]):
            if sh.distance(roi)<3:base.append((sh.buffer(.005,quad_segs=128),.3001));constraints.append({'kind':'native_pad_hole_upper_reservation','uuid':pad['uuid'],'ref':pad['ref'],'pin':pad['num'],'required_plus_guard_mm':.3001})
    reserve,exempt=K.A.reservations();active_rules=[]
    for r in g['rule_areas']:
        if LY not in r['layers']:continue
        hard=r['no_tracks']or(r['name']in reserve and FG not in exempt.get(r['name'],set()))
        if hard:
            for sh in K.L.poly(r['outline']):
                if sh.distance(roi)<3:base.append((sh,.0251));active_rules.append({'uuid':r['uuid'],'name':r['name'],'native_no_tracks':r['no_tracks'],'frozen_reserved_rule':r['name']in reserve})
    rows=[]
    for width in(1.,.8,.5):
        blocked=unary_union([sh.intersection(roi.buffer(3)).buffer(width/2+gap,quad_segs=128)for sh,gap in base]);free=roi.intersection(unary_union(K.L.poly(g['outline'])).buffer(-.525-width/2)).difference(blocked);(OUT/(str(width)+'mm-free-centers.wkb')).write_bytes(free.wkb);candidates=[]
        for p in parts(free):
            a=p.intersection(source);b=p.intersection(floating)
            if a.area>1e-6 and b.area>1e-6:candidates.append((p,a,b))
        row={'width_mm':width,'same_free_component_touches_both_real_electrodes':bool(candidates),'source_free_electrode_area_mm2':free.intersection(source).area,'floating_free_electrode_area_mm2':free.intersection(floating).area,'native_actual109_and_frozen_reserved_rules_hard':True,'all_foreign_current_native_Cu_and_true_drills_hard':True,'new_holes':0}
        found=[]
        for part,a,b in candidates:
            aa=a.buffer(-.001);bb=b.buffer(-.001)
            if aa.is_empty or bb.is_empty:continue
            s,t=nearest_points(aa,bb);route=H.route(part,tuple(s.coords)[0],tuple(t.coords)[0],.025);found.append(route)
            if'path_mm'in route:
                pp=[[round(x,6),round(y,6)]for x,y in route['path_mm']];axis=LineString(pp);body=axis.buffer((width/2+1e-8)/math.cos(math.pi/512),quad_segs=128);check=[{'required_plus_guard_mm':gap,'body_gap_mm':body.distance(sh)}for sh,gap in base if body.distance(sh)<gap];route.update({'native_1nm_quantized_path_mm':pp,'native_quantization_clearance_failures':check,'real_rooted_electrode_overlap_mm2':body.intersection(source).area,'real_floating48_electrode_overlap_mm2':body.intersection(floating).area,'rectangular_nominal_L_over_w':axis.length/width});(OUT/(str(width)+'mm-candidate-axis.wkb')).write_bytes(axis.wkb)
        row['route_attempts']=found;rows.append(row);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'width':width,'shared_free_component':bool(candidates),'routes':[{k:v for k,v in r.items()if k in('status','length_mm','real_rooted_electrode_overlap_mm2','real_floating48_electrode_overlap_mm2','native_quantization_clearance_failures')}for r in found]}),flush=True)
    files=[model,src,flt,hp,Path(__file__),Path(K.A.__file__),Path(K.A.G.C06)/'alternate-r07/reserved-r07.json',Path(K.A.G.C06)/'alternate-r07/reserve/board.kicad_dru'];r={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_FINITE_ELECTRODE_FG_In1_WIDE_STITCH_FIXED_CU_ROUTE_SEARCH','input_sha256':{str(p):sha(p)for p in files},'ROI_mm':[225,15,295,75],'native_and_frozen_active_rules':active_rules,'rows':rows,'full_simultaneous_return_boundary_A':4.58442937244,'required_source_all232pad_closure_old_contact_floor_current_thermal_material_native_after':'OPEN; no virtual union or derating','native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
def Tdescribe(q):return H.T.describe(q)
if __name__=='__main__':main()
