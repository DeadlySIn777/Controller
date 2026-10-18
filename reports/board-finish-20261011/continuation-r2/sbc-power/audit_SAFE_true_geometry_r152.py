"""Independent true-caps/pads/actual-annuli and ordinary-aperture SAFE gate."""
from pathlib import Path
import sys,pickle,json,hashlib
from shapely.geometry import Point,LineString
from shapely import STRtree
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import complete_geometry_r2 as G
O=H/'sbc-power/SAFE-independent-true-geometry-r152'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert len(sys.argv)==2 and not O.exists();O.mkdir();mp=Path(sys.argv[1]);old,h,b,z,current=pickle.loads(mp.read_bytes());errors=[];counts={};web=[]
 pads={l:[] for l in h['copper_layers']};tracks={l:[] for l in h['copper_layers']}
 for p in h['pads']:
  for l,ps in p['layers'].items():
   for s in C.poly(ps):pads[l].append((p,s))
 for t in h['tracks']:tracks[t['layer']].append((t,LineString([t['a'],t['b']])))
 pt={l:STRtree([s for p,s in rows]) for l,rows in pads.items()};tt={l:STRtree([s for t,s in rows]) for l,rows in tracks.items()}
 vp=[Point(v['x'],v['y']) for v in h['vias']];vt=STRtree(vp)
 holes=[(p,s) for p in h['pads'] for s in C.poly(p.get('hole') or [])];ht=STRtree([s for p,s in holes])
 def check(kind,q,other,gap,req,**extra):
  counts[kind]=counts.get(kind,0)+1
  if gap<req:errors.append({'gate':kind,'owned_UUID':q['uuid'],'other_UUID':other['uuid'],'actual_gap_mm':gap,'required_gap_mm':req,**extra})
 for qi,q in enumerate(z):
  s=q['shape'];l=q['layer'];raw=q['net'];near=s.buffer(2)
  for j in pt[l].query(near,predicate='intersects'):
   p,sh=pads[l][int(j)]
   if p['net']!=raw:check('NEW_zone_native_pad',q,p,s.distance(sh),max(G.gap(h,raw,p['net']),float(q.get('clearance_mm',.15)))+.025,layer=l)
  for j in tt[l].query(near,predicate='intersects'):
   t,line=tracks[l][int(j)]
   if t['net']!=raw:check('NEW_zone_true_track_caps',q,t,s.distance(line)-t['w']/2,max(G.gap(h,raw,t['net']),float(q.get('clearance_mm',.15)))+.025,layer=l)
  for j in vt.query(near,predicate='intersects'):
   v=h['vias'][int(j)];point=vp[int(j)]
   if v['net']==raw:continue
   if l in v['flashed']:check('NEW_zone_actual_layer_annulus',q,v,s.distance(point)-v['d']/2,max(G.gap(h,raw,v['net']),float(q.get('clearance_mm',.15)))+.025,layer=l)
   check('NEW_zone_every_foreign_drill',q,v,s.distance(point)-v['drill']/2,.275,layer=l)
  for j in ht.query(near,predicate='intersects'):
   p,sh=holes[int(j)]
   if p['net']!=raw:check('NEW_zone_native_hole',q,p,s.distance(sh),.275,layer=l)
  for peer in z[qi+1:]:
   if peer['layer']==l and peer['net']!=raw and near.intersects(peer['shape']):check('NEW_zone_mutual_foreign_plane',q,peer,s.distance(peer['shape']),max(G.gap(h,raw,peer['net']),float(q.get('clearance_mm',.15)),float(peer.get('clearance_mm',.15)))+.025,layer=l)
  for partno,part in enumerate(G.p.hubs.components(q.get('zone_outline_shape',s))):web.append({'UUID':q['uuid'],'part_index':partno,'declared_min_thickness_mm':float(q.get('min_thickness_mm',.15)),'eroded_interior_nonempty':not part.buffer(-float(q.get('min_thickness_mm',.15))/2).is_empty,'area_mm2':part.area})
  if qi%5==0:
   (O/'checkpoint.json').write_text(json.dumps({'zones_done':qi+1,'counts':counts,'errors':errors,'web':web},indent=1)+'\n');print('SAFE_ANALYTIC_ZONES',qi+1,len(z),'errors',len(errors),flush=True)
 base=pickle.loads((H/'field-power/native-bound-field-base-r5/model.pkl').read_bytes())['discrete'];ids={v['uuid'] for v in base['vias']};nv=[v for v in h['vias'] if v['uuid'] not in ids]
 smd=[(p,s) for l,rows in pads.items() for p,s in rows if p['smd']];st=STRtree([s for p,s in smd])
 for v in nv:
  point=Point(v['x'],v['y']);near=point.buffer(2)
  for j in st.query(near,predicate='intersects'):
   p,s=smd[int(j)];check('NEW_via_hole_every_SMD_Cu',v,p,point.distance(s)-v['drill']/2,.275)
  for j in vt.query(near,predicate='intersects'):
   peer=h['vias'][int(j)]
   if peer['uuid']!=v['uuid']:check('NEW_via_every_native_or_NEW_drill',v,peer,point.distance(vp[int(j)])-(v['drill']+peer['drill'])/2,.275)
  for j in ht.query(near,predicate='intersects'):
   p,s=holes[int(j)];check('NEW_via_every_pad_hole',v,p,point.distance(s)-v['drill']/2,.275)
 receipt={'verdict':'PASS_STRICT_TRUE_GEOMETRY_SCOPE' if not errors else 'FAIL_STRICT_TRUE_GEOMETRY_SCOPE','model_file':str(mp.resolve()),'model_sha256':sha(mp),'counts':counts,'errors':errors,'owned_zones':len(z),'ordinary_new_vias':len(nv),'minimum_web_rows':web,'strict_true_track_caps_native_pad_polygons_actual_layer_annuli_all_drills':True,'no_gap_or_area_tolerance':True,'Cu_domain_plus_planning_mm':.025,'ordinary_hole_every_SMD_and_drill_mm':.275,'source_reference_retained_contact_native_current_gates':'OPEN','board_written':False,'native_jobs':0}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('SAFE_ANALYTIC_COMPLETE',receipt['verdict'],len(errors),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
