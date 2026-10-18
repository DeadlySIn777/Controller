"""Independent drill-envelope check of the frozen numerical cell sets.

The original solver's additional inset is 0.000002 mm (2 nm), not 2 um.
Retain its exact raster, then test accepted complete square cells against true
nominal circular via drills and a 5 um outward native pad-hole envelope.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,pickle,sys,time
import numpy as np
import shapely
from shapely.geometry import Point
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
OUT=HERE/'independent-accepted-cell-drill-envelope-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
OLD=CONT/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
NEW=HERE/'actual-native-sheet-two-level-r1';MATCH=HERE/'old-In4-vs-new-In2-matched-electrodes-r1';TRACE=HERE/'actual-source-paths-r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def read(p):return shapely.from_wkb(p.read_bytes())

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    files=[ACTUAL/'actual-combined-full-after-model.pkl',OLD/'actual-full-R157-before-model.pkl',NEW/'receipt.json',MATCH/'receipt.json',Path(__file__)]
    model_new,model_old=[pickle.loads(p.read_bytes())for p in files[:2]];newreceipt=json.loads(files[2].read_text());matchreceipt=json.loads(files[3].read_text())
    cases=[('old_In4',model_old,MATCH/'actual-old-drilled-In4-sheet.wkb',MATCH/'exact-common-real-source-electrode.wkb',matchreceipt,'old_In4_exact_common_finite_electrodes'),('new_In2',model_new,NEW/'actual-full-source-rooted-In2-sheet.wkb',MATCH/'exact-common-real-source-electrode.wkb',matchreceipt,'new_In2_exact_common_finite_electrodes'),('regional_new_In2',model_new,TRACE/'actual-native-source-contained-physical-sheet.wkb',TRACE/'actual-native-upstream-source-all-contacts.wkb',newreceipt,'regional_actual_upstream_all_contacts')]
    files += [p for _,_,a,b,*_ in cases for p in(a,b)]
    inputs={str(p):sha(p)for p in files};rows=[]
    for name,g,path,srcpath,receipt,case in cases:
        sheet=read(path);source=read(srcpath)
        for step in(.025,.0125):
            inset=sheet.buffer(-step/math.sqrt(2)-.000002);x0,y0,x1,y1=inset.bounds;xx=np.arange(math.floor(x0/step)*step+step/2,x1,step);yy=np.arange(math.floor(y0/step)*step+step/2,y1,step);X,Y=np.meshgrid(xx,yy);mask=shapely.contains_xy(inset,X,Y);lab,_=label(mask,np.array([[0,1,0],[1,1,1],[0,1,0]]));sm=mask&shapely.contains_xy(source.buffer(-step/math.sqrt(2)-.000002),X,Y);ids=set(lab[sm])-{0};mask &=np.isin(lab,list(ids));del X,Y,lab,sm
            expected=next(r['contained_cells']for r in receipt['mesh_rows']if r['boundary_case']==case and r['step_mm']==step);assert int(mask.sum())==expected
            collisions=[];minimum=None;near_vias=0;near_padholes=0
            def local_cells(bounds,margin):
                a,b,c,d=bounds;xs=np.flatnonzero((xx>=a-step/2-margin)&(xx<=c+step/2+margin));ys=np.flatnonzero((yy>=b-step/2-margin)&(yy<=d+step/2+margin))
                if not len(xs)or not len(ys):return np.array([]),np.array([])
                vy,vx=np.nonzero(mask[np.ix_(ys,xs)]);return xx[xs[vx]],yy[ys[vy]]
            for v in g['vias']:
                r=v['drill']/2;hx,hy=v['x'],v['y'];cx,cy=local_cells((hx-r,hy-r,hx+r,hy+r),.025)
                if not len(cx):continue
                near_vias+=1;d=np.hypot(np.maximum(np.abs(cx-hx)-step/2,0),np.maximum(np.abs(cy-hy)-step/2,0))-r;m=float(d.min());minimum=m if minimum is None else min(minimum,m)
                if m< -1e-10:collisions.append({'kind':'true_nominal_via_circle','uuid':v['uuid'],'minimum_square_edge_gap_mm':m})
            for p in g['pads']:
                for hole in K.L.poly(p.get('hole')or[]):
                    upper=hole.buffer(.005,quad_segs=128);cx,cy=local_cells(upper.bounds,0)
                    if not len(cx):continue
                    near_padholes+=1;cells=shapely.box(cx-step/2,cy-step/2,cx+step/2,cy+step/2);hits=shapely.intersects(cells,upper)
                    if bool(hits.any()):collisions.append({'kind':'native_pad_hole_plus_5um_envelope','uuid':p['uuid'],'ref':p['ref'],'pin':p['num'],'square_intersections':int(hits.sum())})
            row={'sheet':name,'step_mm':step,'exact_frozen_contained_cell_count':expected,'exact_solver_raster_reconstructed':True,'true_nominal_via_circle_neighborhoods_checked':near_vias,'native_pad_hole_plus_5um_neighborhoods_checked':near_padholes,'minimum_complete_square_edge_to_true_via_drill_gap_mm':minimum,'collisions':collisions,'pass':not collisions};rows.append(row);put('checkpoint.json',rows);print(json.dumps(row),flush=True)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ALL_FROZEN_NUMERICAL_SQUARES_PASS_SEPARATE_NOMINAL_DRILL_ENVELOPES'if all(r['pass']for r in rows)else'RAW_DRILL_ENVELOPE_CONTROL_FAIL_NO_PHYSICAL_CELL_PROMOTION','input_sha256':inputs,'rows':rows,'original_solver_additional_inset_mm':.000002,'original_solver_additional_inset_nm':2,'native_pad_hole_outward_approximation_reservation_mm':.005,'actual_fabrication_registration_plating_temperature_and_thermal_capacity_qualified':False,'new_solver_jobs':0,'native_jobs':0,'board_written':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result)

if __name__=='__main__':main()
