"""Locate actual source and old-copper blockers for two saved surface joins."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import collections,json,pickle,sys,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;O=N.O;sha=N.sha
OUT=H/'R157-two-no-via-signal-terminal-actual-source-and-Cu-blockers-r286'
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before();geo=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());fl=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias'];g,h,b,q,c=pickle.loads((H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl').read_bytes());lg=N.bound_R663_before_groups({'/LOGIC_GND'})[0]['/LOGIC_GND'];root=K.root(lg,'J11001','2');plane=K.source_refs(root)['F.Cu'];pairs=json.loads((H/'R157-actual-native-remaining-pad-joins-same-surface-census-r282/actual-short-common-surface-pad-group-pairs-not-routes.json').read_bytes());targets=[r for r in pairs if r['normalized_net']in {'/STEP8_FPGA','/motherboard_compute/HDMI_ENABLE'}];rows=[]
 for target in targets:
  net=target['normalized_net'];raw=target['raw_net']
  for side in ('left','right'):
   pt=Point(target[side+'_actual_at_mm']);block=[];own=[]
   for t in h['tracks']:
    if t['layer']!='F.Cu':continue
    other=L.norm(t['net']);axis=LineString([t['a'],t['b']]);distance=axis.distance(pt)-t['w']/2;required=.1+(.15 if h['domains_normalized'][net]==h['domains_normalized'].get(other)else .6)+.025
    if distance<required:
     record={'kind':'track','UUID':t['uuid'],'raw_net':t['net'],'physical_to_centre_mm':distance,'new020_axis_guard_mm':required}
     (own if other==net else block).append(record)
   for v in h['vias']:
    other=L.norm(v['net']);distance=pt.distance(Point(v['x'],v['y']));ann=v['d']/2 if 'F.Cu'in fl[v['uuid']]else 0;required=.1+(.15 if h['domains_normalized'][net]==h['domains_normalized'].get(other)else .6)+.025
    if distance-ann<required or (other==net and distance<1.2):
     record={'kind':'via','UUID':v['uuid'],'raw_net':v['net'],'centre_mm':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'centre_distance_mm':distance,'actual_native_FlashLayers':fl[v['uuid']],'physical_to_centre_mm':distance-ann,'new020_axis_guard_mm':required};(own if other==net else block).append(record)
   for p in geo['pads']:
    if 'F.Cu'not in p['layers']or p['net']==raw:continue
    body=unary_union(L.poly(O.polys(p['poly'])));other=L.norm(p['net']);required=.1+(.15 if h['domains_normalized'][net]==h['domains_normalized'].get(other)else .6)+.025;distance=body.distance(pt)
    if distance<required:block.append({'kind':'native_pad','ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'physical_to_centre_mm':distance,'new020_axis_guard_mm':required})
   row={'net':net,'native_pad':target['native_'+side+'_pad'],'at_mm':list(pt.coords[0]),'actual_J1_In1_source_covers_centre':plane.covers(pt),'centre_distance_to_actual_source_mm':pt.distance(plane),'centre_distance_to_source_boundary_mm':pt.distance(plane.boundary),'required020body_navigation_margin_mm':.100005,'actual_source_erosion_covers_axis_centre':plane.buffer(-.100005,quad_segs=128).covers(pt),'original_foreign_Cu_axis_blockers':block,'nearby_actual_same_net_old_metal_NOT_automatically_an_exemption':own};rows.append(row);print('R286',net,row['native_pad'],'source',row['actual_source_erosion_covers_axis_centre'],'foreign_blockers',len(block),flush=True)
 put('four-actual-terminal-source-and-copper-blocker-ledgers.json',rows);put('receipt.json',{'status':'ACTUAL_NATIVE_TERMINAL_BLOCKERS_BOUND_NO_ROUTE_OR_WAIVER','rows':rows,'actual_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'actual_flashes_SHA256':sha(N.R157/'actual-full-refill-via-flashes.json'),'foreign_guard_thresholds_UNCHANGED':True,'nearby_same_net_vias_NO_automatic_cap_credit':True,'native_jobs':0,'adopted':False})
if __name__=='__main__':main()
