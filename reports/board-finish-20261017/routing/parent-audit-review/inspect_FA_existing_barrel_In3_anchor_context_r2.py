"""Read immutable actual FA ports, existing In3 branches and source FG floor."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import pickle,json,hashlib,time,runpy,gc,math
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parents[3];P=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';OUT=H/'FA-existing-barrel-In3-anchor-context-r2';T=runpy.run_path(str(H/'triage_reference_current_causal_geometry_r1.py'))
OLD=ROOT/'reports/board-finish-20261011/continuation-r2'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;NET='/motherboard_power_entry/FA_SHDN_CONTACT';GROUND='/motherboard_motors/FIELD_GND';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 t=time.monotonic();assert not OUT.exists();OUT.mkdir();mf=P/'actual-combined-full-after-model.pkl';gf=P/'actual-combined-full-after-all-net-groups.pkl';h=pickle.loads(mf.read_bytes());groups=pickle.loads(gf.read_bytes());root=K.root(groups[GROUND],'J11003','2');keys=K.keys(root);floor=unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']=='In4.Cu']);faroot=next(g for g in groups[NET]if any(r['kind']=='via'and r['uuid'].startswith('19ec6624')for r in g));put('FA-current-cached-physical-groups.json',[{'group':i,'keys':len(K.keys(g)),'via_UUIDs':sorted({r['uuid']for r in g if r['kind']=='via'}),'pads':sorted({(r['ref'],str(r['pin']),r['uuid'])for r in g if r['kind']=='pad'})}for i,g in enumerate(groups[NET])]);del groups;gc.collect();(OUT/'actual-R299-source-rooted-FG-In4-floor.wkb').write_bytes(floor.wkb)
 ports=[]
 for prefix in('19ec6624','85f79857'):
  v=next(v for v in h['vias']if v['uuid'].startswith(prefix));q=Point(v['x'],v['y']);adj=[];anchors=[]
  for r in h['tracks']:
   if T['norm'](r['net'])!=NET or r['layer']!='In3.Cu':continue
   axis=LineString([r['a'],r['b']]);d=q.distance(axis)
   if d>v['d']/2+r['w']/2:continue
   adj.append(r)
   for f in(.1,.25,.5,.75,.9):
    qq=axis.interpolate(f,normalized=True);body=qq.buffer(.1,quad_segs=256)
    if floor.covers(body):anchors.append({'existing_In3_track_UUID':r['uuid'],'point_mm':[qq.x,qq.y],'finite_existing_Cu_axis_point':True,'point_to_port_mm':q.distance(qq),'prospective_new_width_mm':.2,'current_source_rooted_FG_floor_covers_round_cap':True})
  returns=[{'UUID':r['uuid'],'at_mm':[r['x'],r['y']],'distance_mm':q.distance(Point(r['x'],r['y'])),'actual_source_rooted_all6_layer_keys':all(('via',r['uuid'],ly)in keys for ly in K.LAYERS),'flashed':r['flashed']}for r in h['vias']if T['norm'](r['net'])==GROUND and q.distance(Point(r['x'],r['y']))<1.5]
  ports.append({'via':v,'existing_same_FA_In3_tracks_touching_true_nominal_via_Cu':adj,'source_rooted_FG_In4_axis_center_location':floor.contains(q),'source_rooted_FG_In4_to_port_distance_mm':floor.distance(q),'existing_In3_attachment_hypotheses_outside_any_unsupported_port_region':anchors,'nearby_same_domain_ground_vias':sorted(returns,key=lambda r:r['distance_mm'])})
 put('ports-and-existing-In3-anchors.json',ports);put('receipt.json',{'status':'IMMUTABLE_ACTUAL_FA_EXISTING_PORT_AND_IN3_ANCHOR_CONTEXT_NOT_ROUTE_PASS','source_FG_named_root':['J11003','2'],'source_FG_root_layer_keys':len(keys),'actual_source_FG_In4_floor_area_mm2':floor.area,'actual_source_FG_In4_floor_bounds':list(floor.bounds),'both_port_contexts_observed':True,'new_via_or_cap_or_floor_exception_created':False,'full_new_route_actual_old_source_floor_rule_Cu_current_return_gates':'OPEN_REQUIRED','native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),mf,gf)},'elapsed_seconds':time.monotonic()-t});print('FA_PORT_CONTEXT',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
