"""Construct bounded .20 signal routes on observed native copper only."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import collections,hashlib,json,pickle,sys,time,math,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import guarded_power_projection_r44 as Z
import tri_route as T
K=N.K;L=N.L;O=N.O;sha=N.sha
OUT=H/'R157-two-actual-no-via-surface-signal-bridge-constructive-screen-r285'
BASE=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
CP=H/'R157-actual-native-remaining-pad-joins-same-surface-census-r282'
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();N.assert_R157_actual_before();assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,c=pickle.loads(BASE.read_bytes());geo=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());fl=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias'];pairs=json.loads((CP/'actual-short-common-surface-pad-group-pairs-not-routes.json').read_bytes());targets=[r for r in pairs if r['normalized_net']in {'/STEP8_FPGA','/motherboard_compute/HDMI_ENABLE'}];assert len(targets)==2
 index=collections.defaultdict(list)
 for p in geo['pads']:index[p['ref'],str(p['num']),*p['at'],p['net']].append(p)
 pads=[];bindings=[]
 for p in h['pads']:
  choices=index[p['ref'],str(p['num']),p['x'],p['y'],p['net']];assert choices,(p['ref'],p['num'])
  if len(choices)>1:assert not p['layers']and all(not x['layers']for x in choices),'Ambiguous native copper pad shape forbidden'
  native=choices[0];pads.append({**p,'layers':{ly:O.polys(native['poly'])for ly in native['layers']}});bindings.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'native_actual_at':native['at'],'reported_layers':native['layers']})
 assert set(fl)=={v['uuid']for v in h['vias']};actual={**h,'pads':pads,'vias':[{**v,'flashed':fl[v['uuid']]}for v in h['vias']],'zones':[{**z,'fills':{ly:O.polys(rs)for ly,rs in z['fills'].items()}}for z in geo['zones']]};ctx=K.hole_context(actual);lg=N.bound_R663_before_groups({'/LOGIC_GND'})[0]['/LOGIC_GND'];root=K.root(lg,'J11001','2');reference=K.source_refs(root);records,trees=K.F.build(actual);dom=h['domains_normalized'];owners={z['uuid']:z for z in actual['zones']};attempts=[];accepted=[]
 for target in targets:
  raw=target['raw_net'];net=target['normalized_net'];assert dom[net]=='DOM_LOGIC';assert target['common_native_surfaces']==['F.Cu'];a=tuple(target['left_actual_at_mm']);end=tuple(target['right_actual_at_mm']);assert math.dist(a,end)<=5
  left=next(p for p in pads if p['ref']+'.'+str(p['num'])+'#0'==target['native_left_pad']);right=next(p for p in pads if p['ref']+'.'+str(p['num'])+'#0'==target['native_right_pad']);assert left['net']==right['net']==raw
  for expansion in (2.,5.,10.):
   window=box(min(a[0],end[0])-expansion,min(a[1],end[1])-expansion,max(a[0],end[0])+expansion,max(a[1],end[1])+expansion);free=reference['F.Cu'].intersection(window).buffer(-.100005,quad_segs=128);cuts=[];eligible=[]
   for i in trees['F.Cu'].query(window.buffer(2),predicate='intersects'):
    r=records['F.Cu'][int(i)];other=L.norm(r['net'])
    if other==net:continue
    gap=.15 if dom.get(other)==dom[net]else .6
    local=float(owners[r['uuid']].get('clearance_mm',0))if r['kind']=='fill'else 0;radius=.1+max(gap,local)+.025;cuts.append(Z.bounded_buffer(r['shape'],radius));eligible.append(r)
   for hole in ctx[0]:
    if hole.intersects(window):cuts.append(Z.bounded_buffer(hole,.1+.275))
   for rule in h['rule_areas']:
    if 'F.Cu'in rule.get('layers',[]):
     for shape in L.poly(rule.get('outline',[])):
      if shape.intersects(window):cuts.append(Z.bounded_buffer(shape,.1+.025))
   if cuts:free=free.difference(unary_union(cuts))
   path=None;search=None
   for component in K.RF.parts(free):
    if component.covers(Point(a))and component.covers(Point(end)):path,search=T.route(component,a,end);break
   if not path:attempts.append({'target':target,'expansion_mm':expansion,'status':'NO_PATH_IN_THIS_BOUNDED_ACTUAL_SOURCE_REFERENCE_FREE_SPACE','free':ds(free)});continue
   path=[(round(x,6),round(y,6))for x,y in path];path=[p for i,p in enumerate(path)if i==0 or p!=path[i-1]];assert path[0]==a and path[-1]==end;axis=LineString(path);body=Z.bounded_buffer(axis,.1);outside=body.difference(reference['F.Cu']);errors=[]
   for r in eligible:
    other=L.norm(r['net']);gap=.15 if dom.get(other)==dom[net]else .6;local=float(owners[r['uuid']].get('clearance_mm',0))if r['kind']=='fill'else 0;required=max(gap,local)+.025;distance=body.distance(r['shape'])
    if distance<required:errors.append({'other_UUID':r['uuid'],'kind':r['kind'],'raw_net':r['net'],'actual_conservative_body_gap_mm':distance,'guarded_required_mm':required})
   holehits=[ds(body.intersection(hole))for hole in ctx[0]if body.intersects(hole)];row={'target':target,'expansion_mm':expansion,'path_native_1nm_mm':path,'path_length_mm':axis.length,'actual_whole_body_source_reference_gap':ds(outside),'actual_foreign_Cu_guard_errors':errors,'all_original_hole_intersections':holehits,'no_new_vias_or_holes':True,'search':search,'pass':outside.is_empty and not errors and not holehits};attempts.append(row)
   if row['pass']:
    tracks=[]
    for i,(aa,bb)in enumerate(zip(path,path[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R285-observed-native-no-via/'+net+'/'+str(i))),'net':raw,'layer':'F.Cu','w':.2,'a':list(aa),'b':list(bb),'locked':False})
    accepted.append({'target':target,'tracks':tracks,'whole_body_WKB':body.wkb,'actual_reference_source':'J11001.2/In1.Cu','no_vias':True,'current_SI_full_native_DRC':'OPEN'});break
  put('checkpoint-attempts.json',attempts);print('R285_TARGET',net,'accepted',any(r['target']['normalized_net']==net for r in accepted),flush=True)
 packet=OUT/'only-constructively-cleared-no-via-new-surface-tracks-NOT_MODEL.pkl';packet.write_bytes(pickle.dumps(accepted,protocol=5));put('all-bound-route-attempts-and-raw-failures.json',attempts);put('exact-actual-all-native-pad-bindings.json',bindings);put('receipt.json',{'status':'R157_BOUNDED_ACTUAL_NO_VIA_SIGNAL_BRIDGE_NOMINEES'if accepted else'R157_TWO_BOUNDED_SURFACE_SIGNAL_BRIDGES_NO_NOMINEE','actual_native_parent_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'actual_native_parent_flash_SHA256':sha(N.R157/'actual-full-refill-via-flashes.json'),'full_actual_pad_count':len(pads),'target_count':len(targets),'constructive_nominee_count':len(accepted),'packet_SHA256':sha(packet),'all_old_Cu_holes_planes_pads_unchanged':True,'exact_packet_requires_current_replay_independent_analytic_caps_contacts_refs_native_DRC_current_SI':'OPEN','search_only_within_expansions_mm':[2,5,10],'global_no_path_NOT_claimed':True,'native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R285_COMPLETE',sha(OUT/'receipt.json'),'nominees',len(accepted),flush=True)
if __name__=='__main__':main()
