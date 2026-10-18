"""Direct wide real-Cu bridge screen for the native floating48 ground group."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,pickle,sys,re
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';PRE=HERE/'actual48-FG-floor-and-bridge-electrodes-r21';OUT=HERE/'actual-FG-In1-wide-bridge-screen-r22';FG='/motherboard_motors/FIELD_GND';LY='In1.Cu'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();model=ACTUAL/'actual-combined-full-after-model.pkl';p=PRE/'receipt.json';g=pickle.loads(model.read_bytes());pre=json.loads(p.read_text());port=next(q for q in pre['layer_summary']if q['layer']==LY)['best_real_Cu_electrodes'][0];points=[[round(x,6),round(y,6)]for x,y in port['nearest_real_Cu_points_mm']];axis=LineString(points);rec,trees=K.F.build(g,layers={LY});domain=g['domains_normalized'][FG];vias={v['uuid']:v for v in g['vias']};rows=[]
    for width in(.8,1.,1.5,2.):
        body=axis.buffer((width/2+1e-8)/math.cos(math.pi/512),quad_segs=128);errors=[];near=[]
        for j in trees[LY].query(body.buffer(2)):
            q=rec[LY][int(j)];net=K.L.norm(q['net'])
            if net==FG:continue
            gap=.15 if q['domain']==domain else.6
            if q['kind']=='fill':gap=max(gap,float(next(z for z in g['zones']if z['uuid']==q['uuid'])['clearance_mm']))
            reservation=.005 if q['kind']=='pad'or(q['kind']=='track'and q['source'].get('m')is not None)else 0
            if q['kind']=='via':v=vias[q['uuid']];d=body.distance(Point(v['x'],v['y']))-v['d']/2
            elif q['kind']=='track'and q['source'].get('m')is None:t=q['source'];d=body.distance(LineString([t['a'],t['b']]))-t['w']/2
            else:d=body.distance(q['shape'])-reservation
            row=T.describe(q)|{'net':net,'guaranteed_gap_mm':d,'native_required_mm':gap,'engineering_guard_mm':.025,'source_record':q.get('source')}
            if d<gap+.2:near.append(row)
            if d<gap+.025:errors.append(row)
        holes=[]
        for v in g['vias']:
            if K.L.norm(v['net'])==FG and LY in v['flashed']:continue
            d=body.distance(Point(v['x'],v['y']))-v['drill']/2
            if d<.3:holes.append({'uuid':v['uuid'],'net':K.L.norm(v['net']),'guaranteed_hole_gap_mm':d,'required_plus_guard_mm':.3})
        for pad in g['pads']:
            if K.L.norm(pad['net'])==FG:continue
            for sh in K.L.poly(pad.get('hole')or[]):
                d=body.distance(sh)-.005
                if d<.3:holes.append({'uuid':pad['uuid'],'ref':pad['ref'],'pin':pad['num'],'net':K.L.norm(pad['net']),'native_pad_hole_upper_reservation_mm':.005,'guaranteed_hole_gap_mm':d,'required_plus_guard_mm':.3})
        rules=[]
        for r in g['rule_areas']:
            if LY in r['layers']and r['no_tracks']and any(body.distance(sh)<.025 for sh in K.L.poly(r['outline'])):rules.append({'uuid':r['uuid'],'name':r['name']})
        rows.append({'width_mm':width,'axis_length_mm':axis.length,'native_1nm_endpoints':points,'actual_Cu_errors':errors,'all_drill_errors':holes,'native_rule_errors':rules,'nearby_actual_Cu':near,'passes_fixed_native_Cu_holes_and_native_rules':not errors and not holes and not rules});print(json.dumps({'width':width,'Cu_errors':[{k:v for k,v in q.items()if k in('kind','uuid','net','ref','pin')}for q in errors],'hole_errors':holes,'rule_errors':rules}),flush=True)
    files=[model,p,Path(__file__)];r={'utc':datetime.now(timezone.utc).isoformat(),'status':'WIDE_REAL_FG_In1_BRIDGE_DIRECT_GAP_FIXED_CU_SCREEN_NO_ADOPTION','input_sha256':{str(q):sha(q)for q in files},'real_electrode_pair':port,'rows':rows,'full_simultaneous_return_current_A':4.58442937244,'source_existing_floor_contact_current_material_thermal_and_custom_DRC_rules':'OPEN; no spec weakened','native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
