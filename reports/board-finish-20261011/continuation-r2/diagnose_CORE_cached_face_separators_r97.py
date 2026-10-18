"""Locate exact remaining separators between ordinary CORE port faces; no rip-up."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import LineString,Point
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for folder in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/folder))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for q in getattr(s,'geoms',[])for p in parts(q)]
def main():
 parent=H/'joint-positive-head-signal-reference-mask-proposal-r83';mp=parent/'model.pkl';assert sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';g,h,b,z,current=pickle.loads(mp.read_bytes());ports=H/'CORE-partial-annular-native-IO3-antipad-port-nominees-r95';assert sha(ports/'receipt.json')=='a4eb4c826f82ede130116afbe5def91c505e8003f3196d0600a4b32f5fb8cfb7';sources=pickle.loads((ports/'source-prospective-new-ordinary-ports.pkl').read_bytes());targets=pickle.loads((ports/'main-prospective-new-ordinary-ports.pkl').read_bytes());cache=H/'CORE-two-new-ordinary-port-layer-feed-proposals-r94';assert sha(cache/'receipt.json')=='a49cdd8478de883fd3b57c3f4b92abae2ca6cb2c51a1f0bc8209adca7a7db369';out=H/'CORE-exact-remaining-port-face-separators-r97';assert not out.exists();out.mkdir();rec,trees=F.build({**h,'zones':[]});raw='/CORE_1V2';rows=[];owned={q['uuid']for q in z};pins={str(p.resolve()):sha(p)for p in [mp,ports/'receipt.json',ports/'source-prospective-new-ordinary-ports.pkl',ports/'main-prospective-new-ordinary-ports.pkl',cache/'receipt.json']}
 def gap(net):return .15 if h['domains_normalized'][C.norm(net)]==h['domains_normalized'][raw]else .6
 for layer in ('In2.Cu','F.Cu','B.Cu','In4.Cu','In3.Cu','In1.Cu'):
  lp=cache/(layer+'-legal.wkb');pins[str(lp.resolve())]=sha(lp);legal=from_wkb(lp.read_bytes());faces=parts(legal.buffer(-.125-.000100));aa=[];bb=[]
  for side,nominees,result in [('source',sources,aa),('main',targets,bb)]:
   for nominee in nominees:
    via=nominee['via'];ann=N.bounded_disk(via,.25).difference(N.bounded_disk(via,.1))
    for index,face in enumerate(faces):
     area=face.intersection(ann).area
     if area>.01:result.append((index,face,via,area))
  pairs=sorted([(a[1].distance(c[1]),a,c)for a in aa for c in bb if a[0]!=c[0]],key=lambda q:q[0]);layerrows=[]
  for rank,(distance,a,c)in enumerate(pairs[:3]):
   pa,pc=nearest_points(a[1],c[1]);line=LineString([pa,pc]);focus=line.buffer(.125+.625+.01);blockers=[]
   for idx in trees[layer].query(focus,predicate='intersects'):
    row=rec[layer][int(idx)]
    if row['net']==raw:continue
    actual=line.distance(row['shape'])-.125
    if row['kind']=='track':t=row['source'];actual=line.distance(LineString([t['a'],t['b']]))-(t['w']/2+.125)
    elif row['kind']=='via':v=row['source'];actual=line.distance(Point(v['x'],v['y']))-(v['d']/2+.125)
    required=gap(row['net'])+.025+.000100
    if actual<required:blockers.append({'family':'actual_foreign_discrete','kind':row['kind'],'UUID':row['uuid'],'raw_net':row['net'],'required_gap_mm':required,'actual_body_gap_mm':actual})
   for q in z:
    if q['layer']!=layer or q['net']==raw or(C.norm(q['net'])=='/LOGIC_GND'and(layer=='In2.Cu'and q['uuid'].startswith('6b1d4fb8-')or layer=='In3.Cu'and q['uuid']=='47888e35-9a96-5393-b579-7c0b4a64ec93')):continue
    required=max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000100;actual=line.distance(q['zone_outline_shape'])-.125
    if actual<required:blockers.append({'family':'held_owned_foreign_plane','UUID':q['uuid'],'raw_net':q['net'],'required_gap_mm':required,'actual_body_gap_mm':actual,'original_generated_only':True})
   for native in current['zones']:
    if native['uuid']in owned or native['uuid']=='54921f4b-0308-4821-9549-ff9360bf05ca'or C.norm(native['net'])in('/CORE_1V2','/LOGIC_GND'):continue
    for shape in C.poly(native['fills'].get(layer,[])):
     required=max(gap(native['net']),float(native.get('clearance_mm',.15)))+.025+.000100;actual=line.distance(shape)-.125
     if actual<required:blockers.append({'family':'actual_held_native_foreign_power_fill','UUID':native['uuid'],'raw_net':native['net'],'required_gap_mm':required,'actual_body_gap_mm':actual})
   blockers.sort(key=lambda q:q['actual_body_gap_mm']-q['required_gap_mm']);row={'layer':layer,'nearest_face_gap_mm':distance,'source_port_UUID':a[2]['uuid'],'main_port_UUID':c[2]['uuid'],'source_face_area_mm2':a[1].area,'main_face_area_mm2':c[1].area,'nearest_separating_chord_mm':[list(pa.coords[0]),list(pc.coords[0])],'literal_short_chord_blockers':blockers,'chord_is_diagnostic_not_routed_copper':True};layerrows.append(row);print('R97_SEPARATOR',layer,rank,distance,[(q['family'],q['UUID'],q['raw_net'])for q in blockers],flush=True)
   if rank==0:
    (out/(layer+'-nearest-source-face.wkb')).write_bytes(a[1].wkb);(out/(layer+'-nearest-main-face.wkb')).write_bytes(c[1].wkb)
  rows.append({'layer':layer,'source_reachable_faces':len(aa),'main_reachable_faces':len(bb),'nearest_separators':layerrows});put(out/'checkpoint.json',rows)
 assert all(sha(p)==value for p,value in pins.items());put(out/'input-bytes.json',pins);put(out/'receipt.json',{'verdict':'EXACT_REMAINING_PORT_FACE_SEPARATOR_ATTRIBUTION_ONLY','parent_model_sha256':sha(mp),'source_nominees':len(sources),'target_nominees':len(targets),'layers':rows,'possible_bounded_new_owned_plane_notches_or_specific_old_trace_restore_trials_require_FULL_gates':True,'no_copper_deleted_added_or_board_changed':True,'native_jobs':0,'adopted':False});print('R97_SEPARATOR_ATTRIBUTION_FROZEN',sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
