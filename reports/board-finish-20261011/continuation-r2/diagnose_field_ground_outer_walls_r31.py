"""Read-only attribution of the three closed ground fanout pockets.

Uses the saved strict .20 track faces. Removing one obstacle below is a
diagnostic counterfactual, never a permission to remove native copper.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import core_inner_feed_r18 as I
NET='/motherboard_motors/FIELD_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def polys(s):return[q for q in ([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if q.geom_type=='Polygon'and not q.is_empty]
def main():
 mp=H/'safe-logic-five-and-fag-margin-r22/model.pkl';saved=H/'field-ground-face-masks-r29';out=H/'field-ground-outer-wall-diagnosis-r31';assert not out.exists();out.mkdir()
 g,h,b,z,full=pickle.loads(mp.read_bytes());assert sha(mp)=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a'
 peer=H/'field-power/regulated-four-retained-hard-snapshot-r127';pq=pickle.loads((peer/'proposed-zones.pkl').read_bytes());pd=pickle.loads((peer/'proposed-discrete.pkl').read_bytes());maskh={**h,'vias':h['vias']+pd['vias'],'tracks':h['tracks']+pd['tracks']}
 records,trees=F.build({**maskh,'zones':[]});areas=I.L.live.reservations();I.p.WINDOW=box(.526,.526,449.474,234.474);outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 barrier_refs={q['refdes']for q in json.loads(I.p.BARRIERS.read_bytes())['barriers']};protected={q['uuid']for q in pickle.loads(mp.with_name('proposed-zones.pkl').read_bytes())};domain=h['domains_normalized'][NET];raw=next(p['net']for p in h['pads']if(p['ref'],p['num'])==('U11025','2'));result=[];pins={str(p.resolve()):sha(p)for p in (mp,Path(__file__),peer/'proposed-zones.pkl',peer/'proposed-discrete.pkl',I.p.BARRIERS)}
 for ref,pin in [('U11025','2'),('R9026','2'),('U10003','9')]:
  pad=next(p for p in h['pads']if(p['ref'],p['num'])==(ref,pin));uid=pad['uuid'];layer=next(iter(pad['layers']));point=Point(pad['x'],pad['y']);win=box(point.x-5,point.y-5,point.x+5,point.y+5);search=win.buffer(2);facefile=saved/(uid+'-5.0-outer-face-0.wkb');legalfile=saved/(uid+'-5.0-via-legal.wkb');face=from_wkb(facefile.read_bytes());legal=from_wkb(legalfile.read_bytes());pins.update({str(p.resolve()):sha(p)for p in (facefile,legalfile)});obstacles=[]
  def add(sh,meta):
   if search.intersects(sh):obstacles.append((sh,meta))
  for i in trees[layer].query(search,predicate='intersects'):
   q=records[layer][int(i)]
   if q['net']==raw:continue
   gap=(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6)+.025+.000020;meta={'kind':q['kind'],'net_raw':q['net'],'uuid':q['uuid']}
   if q['kind']=='track':t=q['source'];sh=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap);meta.update(start_mm=t['a'],end_mm=t['b'],width_mm=t['w'])
   elif q['kind']=='via':v=q['source'];sh=N.bounded_disk(v,v['d']/2+gap);meta.update(at_mm=[v['x'],v['y']],diameter_mm=v['d'])
   else:sh=N.bounded_buffer(q['shape'],gap);meta.update(ref=q.get('ref'),pin=q.get('pin'))
   add(sh,meta)
  for q in [q for q in z if q['uuid']in protected]+pq:
   if q['net']!=raw and q['layer']==layer:add(N.bounded_buffer(q['shape'],max(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6,float(q.get('clearance_mm',.15)))+.025+.000020),{'kind':'hard_peer_new_zone','uuid':q['uuid'],'net_raw':q['net']})
  for p in h['pads']:
   for s in C.poly(p.get('hole')or[]):add(N.bounded_buffer(s,.275+.000020),{'kind':'pad_drill','uuid':p['uuid'],'ref':p['ref'],'pin':p['num']})
  for v in maskh['vias']:add(N.bounded_buffer(N.bounded_disk(v,v['drill']/2),.275+.000020),{'kind':'via_drill','uuid':v['uuid'],'net_raw':v['net']})
  for a in h['rule_areas']:
   if layer in a['layers']and(a.get('no_tracks')or a.get('no_zones')):
    for s in C.poly(a['outline']):add(N.bounded_buffer(s,.025+.000020),{'kind':'native_rule_area','name':a.get('name'),'uuid':a.get('uuid')})
  for a in areas:
   if layer in a['layers']and NET not in a['exempt']:
    for s in C.poly(a['outline']):add(N.bounded_buffer(s,.025+.000020),{'kind':'planning_reserved_area','name':a.get('name')})
  for foot in h['footprints']:
   if foot['ref']in barrier_refs:
    for rings in foot['courtyard'].values():
     for s in C.poly(rings):
      sh=s.buffer(.6)
      if ref=='U10003'and foot['ref']==ref:sh=sh.difference(box(point.x+.55,point.y-.21,point.x+2.5,point.y+.21))
      add(N.bounded_buffer(sh,.025+.000020),{'kind':'barrier_courtyard_planning_mask','ref':foot['ref']})
  boundary=face.boundary;rows=[];touch=[]
  for index,(s,meta)in enumerate(obstacles):
   cs=N.bounded_buffer(s,.100020);distance=boundary.distance(cs)
   if distance<=.000006:
    length=boundary.intersection(cs.buffer(.000006)).length;rows.append({**meta,'index':index,'guard_shape_sha256':hashlib.sha256(s.wkb).hexdigest(),'boundary_contact_length_mm':length,'boundary_distance_mm':distance,'pad_center_to_original_guard_mm':point.distance(s)});touch.append(index)
  rows.sort(key=lambda r:-r['boundary_contact_length_mm']);counter=[];padshape=unary_union(C.poly(pad['layers'][layer]))
  for index in touch:
   free=set_precision(win.intersection(outline).difference(unary_union([s for j,(s,m)in enumerate(obstacles)if j!=index])).buffer(-.100020),1e-6);faces=[f for f in polys(free)if f.intersects(padshape.buffer(-.000020))]
   area=sum(f.area for f in faces);site=sum(f.intersection(legal).area for f in faces)
   if area>face.area+.000001 or site>0:counter.append({**obstacles[index][1],'index':index,'counterfactual_face_area_mm2':area,'additional_face_area_mm2':area-face.area,'unchanged_saved_all6_legal_via_site_meeting_area_mm2':site,'no_actual_deletion_or_route_authorized':True})
  r={'ref':ref,'pin':pin,'pad_uuid':uid,'layer':layer,'saved_strict_face_area_mm2':face.area,'walls':rows,'single_obstacle_counterfactual_openings':counter};result.append(r);put(out/'checkpoint.json',result);print('R31_WALLS',ref,len(rows),[(q['kind'],q.get('ref',q.get('net_raw',q.get('name'))),q.get('uuid'),round(q['boundary_contact_length_mm'],5))for q in rows[:12]],flush=True);print('R31_OPENINGS',ref,[(q['kind'],q.get('uuid',q.get('name')),round(q['additional_face_area_mm2'],5),round(q['unchanged_saved_all6_legal_via_site_meeting_area_mm2'],5))for q in counter],flush=True)
 assert all(sha(p)==v for p,v in pins.items());put(out/'receipt.json',{'verdict':'READ_ONLY_EXACT_LOCAL_OUTER_WALL_ATTRIBUTION','rows':result,'input_sha256':pins,'new_Cu_or_source_changes':0,'native_jobs':0,'board_written':False,'adopted':False})
if __name__=='__main__':main()
