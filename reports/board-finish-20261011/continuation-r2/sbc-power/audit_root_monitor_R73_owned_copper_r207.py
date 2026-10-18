"""Independent exact monitor five tracks/ordinary barrel vs native Cu/holes/zones."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import complete_geometry_r2 as G
O=H/'sbc-power/ROOT-R73-independent-monitor-owned-Cu-r207'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not O.exists();O.mkdir();mp=H/'SAFE-monitor-real-source-reference-patch-r73/model.pkl';assert sha(mp)=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011'
 g,h,b,z,c=pickle.loads(mp.read_bytes());op=H/'SAFE-native-monitor-rotation-composition-r69/owned-operation.pkl';d=pickle.loads(op.read_bytes())['exact_monitor_delta'];assert len(d['tracks'])==5 and len(d['vias'])==1
 rec,trees=F.build({**h,'zones':[]});errors=[];checks=[];nv=d['vias'][0]
 def check(kind,uid,other,gap,req,layer=None):
  row={'kind':kind,'owned_UUID':uid,'foreign_UUID':other,'actual_gap_mm':gap,'required_mm':req,'layer':layer};checks.append(row)
  if gap<req:errors.append(row)
 def required(a,n):return G.gap(h,a,n)+.025
 for t in d['tracks']:
  assert next(q for q in h['tracks'] if q['uuid']==t['uuid'])==t;axis=LineString([t['a'],t['b']]);layer=t['layer']
  for j in trees[layer].query(axis.buffer(2),predicate='intersects'):
   r=rec[layer][int(j)]
   if r['uuid']==t['uuid'] or r['net']==t['net']:continue
   if r['kind']=='track':other=r['source'];gap=axis.distance(LineString([other['a'],other['b']]))-(t['w']+other['w'])/2
   elif r['kind']=='via':v=r['source'];gap=axis.distance(Point(v['x'],v['y']))-(t['w']+v['d'])/2
   else:gap=axis.distance(r['shape'])-t['w']/2
   check('monitor_track_to_'+r['kind'],t['uuid'],r['uuid'],gap,required(t['net'],r['net']),layer)
  for peer in z:
   if peer['layer']==layer and peer['net']!=t['net'] and axis.buffer(2).intersects(peer['shape']):check('monitor_track_to_owned_plane',t['uuid'],peer['uuid'],axis.distance(peer['shape'])-t['w']/2,max(G.gap(h,t['net'],peer['net']),float(peer.get('clearance_mm',.15)))+.025,layer)
 point=Point(nv['x'],nv['y']);assert next(v for v in h['vias'] if v['uuid']==nv['uuid'])==nv
 for layer in nv['flashed']:
  for j in trees[layer].query(point.buffer(2),predicate='intersects'):
   r=rec[layer][int(j)]
   if r['uuid']==nv['uuid'] or r['net']==nv['net']:continue
   if r['kind']=='track':t=r['source'];gap=point.distance(LineString([t['a'],t['b']]))-(nv['d']+t['w'])/2
   elif r['kind']=='via':v=r['source'];gap=point.distance(Point(v['x'],v['y']))-(nv['d']+v['d'])/2
   else:gap=point.distance(r['shape'])-nv['d']/2
   check('monitor_barrel_to_'+r['kind'],nv['uuid'],r['uuid'],gap,required(nv['net'],r['net']),layer)
  for peer in z:
   if peer['layer']==layer and peer['net']!=nv['net'] and point.buffer(2).intersects(peer['shape']):check('monitor_barrel_to_owned_plane',nv['uuid'],peer['uuid'],point.distance(peer['shape'])-nv['d']/2,max(G.gap(h,nv['net'],peer['net']),float(peer.get('clearance_mm',.15)))+.025,layer)
 for p in h['pads']:
  if p['smd']:
   for layer,rs in p['layers'].items():
    for s in C.poly(rs):
     if point.distance(s)<2:check('monitor_drill_to_every_SMD',nv['uuid'],p['uuid'],point.distance(s)-nv['drill']/2,.275,layer)
  for s in C.poly(p.get('hole')or[]):
   if point.distance(s)<2:check('monitor_drill_to_native_pad_hole',nv['uuid'],p['uuid'],point.distance(s)-nv['drill']/2,.275)
 for v in h['vias']:
  if v['uuid']!=nv['uuid'] and point.distance(Point(v['x'],v['y']))<2:check('monitor_drill_to_every_drill',nv['uuid'],v['uuid'],point.distance(Point(v['x'],v['y']))-(nv['drill']+v['drill'])/2,.275)
 (O/'receipt.json').write_text(json.dumps({'verdict':'PASS_MONITOR_OWNED_TRUE_CU_ORDINARY_APERTURE' if not errors else 'FAIL_MONITOR_OWNED_TRUE_CU_ORDINARY_APERTURE','model_sha256':sha(mp),'monitor_operation_sha256':sha(op),'checks':checks,'errors':errors,'no_tolerance_waiver':True,'native_current_source_threshold_qualification':'OPEN','native_jobs':0,'board_written':False,'script_sha256':sha(__file__)},indent=1)+'\n');print('R207_COMPLETE',len(errors),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
