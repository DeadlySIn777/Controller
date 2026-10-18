"""Finite .20F R7 search after literal R256 T4 ground, no barrel/waiver."""
import hashlib,json,pickle,sys,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import from_wkb
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import tri_route as TR
O=H/'sbc-power/R7-fullwidth-after-literal-T4-root-finite-r258'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def pieces(s):return[s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes())
 dp=H/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r256/proposed-discrete.pkl';d=pickle.loads(dp.read_bytes());rm=set(d['removed_original_track_UUIDs']);c={**c,'tracks':[t for t in c['tracks']if t['uuid']not in rm]+d['tracks']};rec,trees=F.build(c,layers={'F.Cu'})
 p=next(p for p in h['pads']if(p['ref'],p['num'])==('U1001','R7'));start=[p['x'],p['y']];s=Point(start)
 goal=from_wkb((H/'sbc-power/CORE-R112-exact-ground-cross-layer-topology-r249/F.Cu-exact-drilled-source-ground-union.wkb').read_bytes());goal=unary_union([goal,*[GP.bounded_buffer(LineString([t['a'],t['b']]),.1)for t in d['tracks']if t['net']=='/LOGIC_GND']]);rows=[];paths=[]
 holes=[(v['uuid'],v['net'],GP.bounded_disk(v,v['drill']/2+.00000002))for v in h['vias']]+[(p['uuid'],p['net'],sh.buffer(.00000002))for p in h['pads']for sh in C.poly(p.get('hole')or[])];ht=STRtree([x[2]for x in holes])
 for radius in (2.,5.,10.,15.):
  clip=box(s.x-radius,s.y-radius,s.x+radius,s.y+radius);cuts=[];blocking=[]
  for j in trees['F.Cu'].query(clip.buffer(.8),predicate='intersects'):
   q=rec['F.Cu'][int(j)]
   if C.norm(q['net'])=='/LOGIC_GND':continue
   clearance=GP.G.gap(h,'/LOGIC_GND',q['net'])+.025+.0000001
   if q['kind']=='track':t=q['source'];cut=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+.1+clearance)
   elif q['kind']=='via':v=q['source'];cut=GP.bounded_disk(v,v['d']/2+.1+clearance)
   else:cut=GP.bounded_buffer(q['shape'],.1+clearance)
   cuts.append(cut);blocking.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'clearance_with_planner_margin_mm':clearance})
  for j in ht.query(clip.buffer(.8),predicate='intersects'):
   uid,n,sh=holes[int(j)]
   if C.norm(n)!='/LOGIC_GND':cuts.append(GP.bounded_buffer(sh,.1+.275+.0000001))
  for q in h['rule_areas']:
   if q.get('no_tracks')and'F.Cu'in q['layers']:cuts.extend(GP.bounded_buffer(sh,.125)for sh in C.poly(q['outline'])if sh.intersects(clip))
  free=clip.difference(unary_union(cuts));faces=[p for p in pieces(free)if p.covers(s)];targets=[]
  for i,f in enumerate(faces):
   sf=O/(str(radius)+'-R7-start-face-'+str(i)+'.wkb');sf.write_bytes(f.wkb);target=f.buffer(-.00000002).intersection(goal);targets.append({'face_WKB_sha256':sha(sf),'face_area_mm2':f.area,'face_bounds':list(f.bounds),'actual_source_root_goal_intersection_mm2':target.area,'target_empty':target.is_empty})
   if target.is_empty:continue
   e=nearest_points(s,target)[1];end=[round(e.x,6),round(e.y,6)]
   try:path,method=TR.route(f,start,end)
   except Exception as err:targets[-1]['route_error']=str(err);continue
   path=[[round(x,6),round(y,6)]for x,y in path]
   if f.covers(LineString(path)):paths.append({'path':path,'method':method,'width_mm':.2,'radius_mm':radius})
  rows.append({'radius_mm':radius,'fullwidth_mm':.2,'start':start,'source_pad_UUID':p['uuid'],'start_faces':targets,'foreign_constraint_count':len(blocking),'new_T4_ground_is_actual_goal':True});put(O/'finite-search-progress.json',rows);print('R258_RADIUS',radius,len(faces),len(paths),flush=True)
  if paths:break
 put(O/'receipt.json',{'verdict':'FULL_WIDTH_F_NOMINATION_FOUND_PENDING_INDEPENDENT_PROOF'if paths else'NO_FULL_WIDTH_R7_F_PATH_IN_DECLARED_WINDOWS_AFTER_T4_ROOT','exact_R112_model_sha256':sha(mp),'exact_R256_discrete_sha256':sha(dp),'paths':paths,'finite_search_rows':rows,'no_original_rule_width_pad_or_plane_change':True,'ordinary_vias_not_nominated_here':True,'whole_stale_R246_overlay_used':False,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)});print('R258_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
