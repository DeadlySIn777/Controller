"""Identify exact all-layer obstacles after the proven same-F health bend."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import core_inner_feed_r18 as I
NET='/motherboard_motors/FIELD_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 mp=H/'field-ground-bulge-opening-r40/source-only-model.pkl';g,h,b,z,full=pickle.loads(mp.read_bytes());out=H/'field-health-ground-via-blockers-r41';assert not out.exists();out.mkdir();raw=next(p['net']for p in h['pads']if(p['ref'],p['num'])==('U11025','2'));domain=h['domains_normalized'][NET];peer=H/'field-power/regulated-four-retained-hard-snapshot-r127';pq=pickle.loads((peer/'proposed-zones.pkl').read_bytes());pd=pickle.loads((peer/'proposed-discrete.pkl').read_bytes());mh={**h,'tracks':h['tracks']+pd['tracks'],'vias':h['vias']+pd['vias']};records,trees=F.build({**mh,'zones':[]});protected={q['uuid']for q in pickle.loads((H/'safe-logic-five-and-fag-margin-r22/proposed-zones.pkl').read_bytes())};I.p.WINDOW=box(.526,.526,449.474,234.474);areas=I.L.live.reservations();barriers={q['refdes']for q in json.loads(I.p.BARRIERS.read_bytes())['barriers']};result=[]
 for x,y in [(312.,154.558),(312.1,154.558),(312.2,154.558),(312.4,154.558),(313.,154.558)]:
  p=Point(x,y);window=p.buffer(2);errors=[]
  def fail(kind,s,need,meta):
   distance=p.distance(s)
   if distance<need:errors.append({'kind':kind,'point_to_actual_obstacle_mm':distance,'required_center_distance_mm':need,**meta})
  for layer in LAYERS:
   for i in trees[layer].query(window,predicate='intersects'):
    q=records[layer][int(i)]
    if q['net']==raw:continue
    need=(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6)+.025+.000020
    if q['kind']=='track':t=q['source'];s=LineString([t['a'],t['b']]);need+=t['w']/2+.25
    elif q['kind']=='via':v=q['source'];s=Point(v['x'],v['y']);need+=v['d']/2+.25
    else:s=q['shape'];need+=.25
    fail('actual_foreign_'+q['kind'],s,need,{'layer':layer,'uuid':q['uuid'],'net_raw':q['net'],'ref':q.get('ref'),'pin':q.get('pin')})
   for q in [q for q in z if q['uuid']in protected]+pq:
    if q['layer']==layer and q['net']!=raw:fail('protected_peer_new_plane',q['shape'],.25+max(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6,float(q.get('clearance_mm',.15)))+.025+.000020,{'layer':layer,'uuid':q['uuid'],'net_raw':q['net']})
   for a in h['rule_areas']:
    if layer in a['layers']and a.get('no_vias'):
     for s in C.poly(a['outline']):fail('native_no_via_area',s,.275+.000020,{'layer':layer,'name':a.get('name'),'uuid':a.get('uuid')})
   for a in areas:
    if layer in a['layers']and NET not in a['exempt']:
     for s in C.poly(a['outline']):fail('planning_reserved_via_area',s,.275+.000020,{'layer':layer,'name':a.get('name')})
  for pad in h['pads']:
   if pad['smd']:
    for l,rings in pad['layers'].items():
     for s in C.poly(rings):
      if s.intersects(window):fail('ordinary_via_hole_SMD',s,.375+.000020,{'layer':l,'uuid':pad['uuid'],'ref':pad['ref'],'pin':pad['num']})
   for s in C.poly(pad.get('hole')or[]):
    if s.intersects(window):fail('pad_drill',s,.275+.000020,{'uuid':pad['uuid'],'ref':pad['ref'],'pin':pad['num']})
  for v in mh['vias']:
   if abs(v['x']-x)<2 and abs(v['y']-y)<2:fail('via_drill',N.bounded_disk(v,v['drill']/2),.275+.000020,{'uuid':v['uuid'],'net_raw':v['net']})
  for foot in h['footprints']:
   if foot['ref']in barriers:
    for rings in foot['courtyard'].values():
     for s in C.poly(rings):
      if s.intersects(window.buffer(.875)):fail('barrier_courtyard_all6_via_planning_mask',s.buffer(.6),.275+.000020,{'ref':foot['ref']})
  row={'site_mm':[x,y],'obstacles':errors};result.append(row);print('R41_SITE',x,y,[(e['kind'],e.get('uuid',e.get('ref',e.get('name'))),e.get('layer'))for e in errors],flush=True)
 (out/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_EXACT_ALL6_VIA_SITE_BLOCKER_ATTRIBUTION','model_sha256':sha(mp),'rows':result,'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n')
if __name__=='__main__':main()
