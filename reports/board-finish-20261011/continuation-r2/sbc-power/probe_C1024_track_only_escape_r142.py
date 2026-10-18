"""Construct a conservative local .20 F escape with no holes or old edits."""
from pathlib import Path
import json,pickle,hashlib,sys,uuid
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import guarded_declared_settings_projection_r58 as GP
import tri_route as T
O=H/'sbc-power/C1024-local-track-only-nominees-r142'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def polys(s):return [s] if s.geom_type=='Polygon' else [x for x in getattr(s,'geoms',[]) if x.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();cf=H/'sbc-power/C1024-local-native-bound-context-r141.json';assert sha(cf)=='9c584ad555526facfa48ba2c497779e650a563a84817e65547d9f55463aac867';c=json.loads(cf.read_bytes());raw='/CORE_1V2';reserve=.175+.000020;width=.20;obs=[]
 for p in c['pads']:
  if p['net']!=raw:obs += [GP.bounded_buffer(s,reserve+width/2) for s in C.poly(p['layers'].get('F.Cu',[]))]
  if p['net']!=raw:obs += [GP.bounded_buffer(s,.275+width/2) for s in C.poly(p.get('hole') or [])]
 for t in c['tracks_F']:
  if t['net']!=raw:obs.append(GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+reserve+width/2))
 for v in c['vias_all_layers']:
  if v['net']==raw:continue
  if 'F.Cu' in v['flashed']:obs.append(GP.bounded_disk(v,v['d']/2+reserve+width/2))
  else:obs.append(GP.bounded_disk(v,v['drill']/2+.275+width/2))
 for r in c['rules']:
  if r.get('no_tracks') and 'F.Cu' in r['layers']:obs += C.poly(r['outline'])
 free=set_precision(box(*c['window_mm']).buffer(-.2).difference(unary_union(obs)),1e-6)
 src=c['candidate_C1024'];srcbody=unary_union(C.poly(src['layers']['F.Cu'])).buffer(-.02)
 expected=set(json.loads((H/'sbc-power/frozen-regional-source-exit-replay-r129/source-scope-checkpoint.json').read_bytes())['joined_pad_keys'])
 goals=[]
 for p in c['pads']:
  if p['net']==raw and p['uuid'] in expected:
   for s in C.poly(p['layers'].get('F.Cu',[])):goals.append((p,s.buffer(-.02)))
 for v in c['vias_all_layers']:
  if v['net']==raw and 'F.Cu' in v['flashed']:goals.append((v,Point(v['x'],v['y']).buffer(v['d']/2-.04)))
 rows=[];accepted=[]
 for part in polys(free):
  aa=part.intersection(srcbody)
  if aa.is_empty:continue
  for goal,s in sorted(goals,key=lambda pair:aa.distance(pair[1])):
   bb=part.intersection(s)
   if bb.is_empty:continue
   a,b=nearest_points(aa,bb)
   try:points,search=T.route(part,tuple(a.coords[0]),tuple(b.coords[0]))
   except (AssertionError,ValueError) as e:rows.append({'goal_UUID':goal['uuid'],'error':str(e)});continue
   points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points)
   if not free.covers(line):rows.append({'goal_UUID':goal['uuid'],'error':'Quantized centerline outside exact local free region'});continue
   for i,(a,b) in enumerate(zip(points,points[1:])):
    if a==b:continue
    accepted.append(C.track('C1024-local-track-only-r142-'+str(i),raw,'F.Cu',a,b,width))
   rows.append({'goal_UUID':goal['uuid'],'goal_ref':goal.get('ref'),'goal_pin':goal.get('num'),'points_mm':points,'width_mm':width,'length_mm':line.length,'search':search,'native_source_peer':'Selected exact native source R139 proves the original FPGA island, while final full source membership remains a coupled gate.'});break
  if accepted:break
 tf=O/'proposed-tracks.pkl';tf.write_bytes(pickle.dumps(accepted,protocol=5));(O/'free-local-centerline-region.wkb').write_bytes(free.wkb)
 r={'verdict':'TRACK_ONLY_ESCAPE_NOMINEE_FULL_INVENTORY_AND_CONTACT_GATES_OPEN' if accepted else 'NO_ESCAPE_IN_THIS_FINITE_LOCAL_FACE_NOT_GLOBAL_NO_PATH_PROOF','context_sha256':sha(cf),'rows':rows,'proposed_tracks_sha256':sha(tf),'new_segments':len(accepted),'new_holes':0,'old_Cu_edits':0,'SMD_pose_changes':0,'window_mm':c['window_mm'],'strict_whole_inventory_Cu_pads_vias_rules_and_new_planes_gate':'OPEN','all_original_GND_source_contact_reference_current_and_native':'OPEN','native_jobs':0,'board_written':False}
 (O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('C1024_TRACK_ONLY_LOCAL',len(accepted),rows,flush=True)
if __name__=='__main__':main()
