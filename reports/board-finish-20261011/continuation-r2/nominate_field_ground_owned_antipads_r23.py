"""Bounded ordinary dogbones for three exact untouched FAG pads.

Actual R78 plus four root return shapes is source-projected using GP58.
Only direct real inner-source annulus contacts qualify; finite failure is
not proof of global impossibility. This writes nominees, never native boards.
"""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import core_inner_feed_r18 as I
import tri_route as T
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];NET='/motherboard_motors/FIELD_GND'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def polys(s):return[q for q in ([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if q.geom_type=='Polygon'and not q.is_empty and q.area>1e-12]
def main():
 out=Path(sys.argv[1]).resolve();assert out.is_relative_to(H)and not out.exists()
 mp=Path(sys.argv[2]).resolve();mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes());assert sha(mp)==r['model_sha256'] and r['actual_C_R102_R10_composed']
 assert r['R106_model_sha256']=='3f9086799fb85283714126d51b1e7cc8dc477ffe8a3ed0b1c06edd91071dcf39'
 old,h,b,zones,current=pickle.loads(mp.read_bytes());h=copy.deepcopy(h);out.mkdir()
 raw=next(p['net']for p in h['pads']if(p['ref'],p['num'])==('U11025','2'));domain=h['domains_normalized'][NET]
 def gap(other):return .15 if h['domains_normalized'][C.norm(other)]==domain else .6
 def source_projection():return N.projected(old,{**h,'zones':[q for q in h['zones']if q['net']==raw]},zones)[0]
 current=source_projection();print('FAG_DOGBONE_SOURCE_PROJECTED',flush=True)
 root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs))
 padids=lambda xs:{q['uuid']for q in xs if q['kind']=='pad'and q['pin']}
 outline=unary_union(C.poly(h['outline'])).buffer(-.526);I.p.WINDOW=box(.526,.526,449.474,234.474);areas=I.L.live.reservations()
 # This copied planning mask is not a native keepout. Exact existing actual
 # CORE1V2 Cu, every native area, source reserve and barrier remains hard.
 hardmodel={**h,'zones':[dict(q,layers=[l for l in q['layers']if l!='In3.Cu'])if C.norm(q['net'])=='/CORE_1V2'else q for q in h['zones']]}
 hard={l:I.p.hard_shapes(hardmodel,areas,NET,l)for l in LAYERS};viahard=[s for l in LAYERS for s in I.p.hard_shapes(hardmodel,areas,NET,l,for_via=True)]
 holes=[s for p in h['pads']for s in C.poly(p.get('hole')or[])]+[N.bounded_disk(v,v['drill']/2)for v in h['vias']]
 smd=[s for p in h['pads']if p['smd']for rings in p['layers'].values()for s in C.poly(rings)]
 rows=[];new={'vias':[],'tracks':[]};targetids=['d64c464d-de71-4c7e-9d98-b870e2ad977f','6d65e765-0689-4977-98aa-e5c00d7c8922','4021795d-90df-4df0-a1b4-13cdcbdd91ac']
 for uid in targetids:
  records,trees=F.build({**h,'zones':[]});pad=next(p for p in h['pads']if p['uuid']==uid);layer=next(iter(pad['layers']));padshape=unary_union(C.poly(pad['layers'][layer]));point=Point(pad['x'],pad['y']);rr=root(F.graph(current,NET));prior=padids(rr)
  if uid in prior:rows.append({'pad_uuid':uid,'ref':pad['ref'],'pin':pad['num'],'already_actual_source_rooted':True});continue
  source={l:unary_union([q['shape']for q in rr if q['layer']==l])for l in LAYERS};answer=None;tests=[]
  for radius in(2.,5.,10.):
   win=box(point.x-radius,point.y-radius,point.x+radius,point.y+radius);search=win.buffer(2);obs=[];outer=[]
   for l in LAYERS:
    for i in trees[l].query(search,predicate='intersects'):
     q=records[l][int(i)]
     if q['net']==raw:continue
     need=gap(q['net'])+.025+.000020
     if q['kind']=='track':
      t=q['source'];axis=LineString([t['a'],t['b']]);obs.append(N.bounded_buffer(axis,t['w']/2+.25+need))
      if l==layer:outer.append(N.bounded_buffer(axis,t['w']/2+need))
     elif q['kind']=='via':
      v=q['source'];obs.append(N.bounded_disk(v,v['d']/2+.25+need))
      if l==layer:outer.append(N.bounded_disk(v,v['d']/2+need))
     else:
      obs.append(N.bounded_buffer(q['shape'],.25+need))
      if l==layer:outer.append(N.bounded_buffer(q['shape'],need))
   for q in zones:
    if q['net']==raw or not search.intersects(q['shape']):continue
    need=max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020
    obs.append(N.bounded_buffer(q['shape'],.25+need))
    if q['layer']==layer:outer.append(N.bounded_buffer(q['shape'],need))
   for s in smd:
    if search.intersects(s):obs.append(N.bounded_buffer(s,.1+.275+.000020))
   for s in holes:
    if search.intersects(s):obs.append(N.bounded_buffer(s,.1+.275+.000020));outer.append(N.bounded_buffer(s,.275+.000020))
   obs +=[N.bounded_buffer(s,.25+.025+.000020)for s in viahard if search.intersects(s)]
   outer +=[N.bounded_buffer(s,.025+.000020)for s in hard[layer]if search.intersects(s)]
   # Original filled polygons may retreat around prospective ordinary Cu.
   # No original native outline is edited. These are only nominations until
   # the full independent all-net reference/contact/source gates prove every
   # old obligation retained on the complete guarded projection.
   region=set_precision(win.intersection(outline.buffer(-.25)).difference(unary_union(obs)),1e-6)
   routefree=set_precision(win.intersection(outline).difference(unary_union(outer)).buffer(-.1-.000020),1e-6)
   startparts=[p for p in polys(routefree)if p.intersects(padshape.buffer(-.000020))];options=[]
   if not startparts:
    free=win.intersection(outline).difference(unary_union(outer))
    print('FAG_BARE_PAD_BLOCK_DIAGNOSTIC',pad['ref'],'pad_bounds',list(padshape.bounds),'available_pad_area_by_DIAGNOSTIC_ONLY_width',{str(w):free.buffer(-w/2-.000020).intersection(padshape.buffer(-.000020)).area for w in(.2,.15,.125,0.)},flush=True)
   print('FAG_BARE_R17_FACE',pad['ref'],radius,'legal_site_area',region.area,'outer_start_parts',len(startparts),'source_distances',{l:point.distance(source[l])for l in('In1.Cu','In2.Cu','In3.Cu','In4.Cu')},flush=True)
   for l in('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):
    for startpart in startparts:
     meeting=region.intersection(startpart).intersection(N.bounded_buffer(source[l],.2))
     for p in polys(meeting):
      options.extend((point.distance(s),l,s)for s in [p.representative_point(),nearest_points(p,point)[0],p.centroid]if p.covers(s))
   for _,inner,s in sorted(options,key=lambda x:x[:2]):
    site=Point(round(s.x,6),round(s.y,6));ann=N.bounded_disk({'x':site.x,'y':site.y},.25).difference(N.bounded_disk({'x':site.x,'y':site.y},.1))
    if not region.covers(site)or ann.intersection(source[inner]).area<.01:continue
    for part in startparts:
     if not part.covers(site):continue
     start=nearest_points(part.intersection(padshape.buffer(-.000020)),point)[0];chord=LineString([start,site])
     if part.covers(chord):points=list(chord.coords);method='exact_covered_chord'
     else:
      try:points,_=T.route(part,tuple(start.coords[0]),tuple(site.coords[0]));method='bounded_exact_face_tri_route'
      except(AssertionError,ValueError):continue
     points=[[round(x,6),round(y,6)]for x,y in points]
     if len(set(map(tuple,points)))<2:continue
     viaid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-ground-bare-r17/'+uid+'/via/'+repr((site.x,site.y))));v={'uuid':viaid,'net':raw,'x':site.x,'y':site.y,'d':.5,'drill':.2,'flashed':LAYERS.copy()};tracks=[]
     for i,(a,bb)in enumerate(zip(points,points[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-ground-bare-r17/'+uid+'/stub/'+repr((a,bb)))),'net':raw,'a':a,'b':bb,'w':.2,'layer':layer})
     h['vias'].append(v);h['tracks']+=tracks;trial=source_projection();joined=padids(root(F.graph(trial,NET)));ok=uid in joined and prior<=joined
     record={'pad_uuid':uid,'ref':pad['ref'],'pin':pad['num'],'outer_layer':layer,'direct_inner_actual_source_layer':inner,'site_mm':[site.x,site.y],'source_annular_overlap_mm2':ann.intersection(source[inner]).area,'window_radius_mm':radius,'points_mm':points,'length_mm':LineString(points).length,'method':method,'target_actual_source_joined':uid in joined,'all_prior_actual_source_pads_retained':prior<=joined,'accepted_source_construction_only':ok};tests.append(record)
     if ok:new['vias'].append(v);new['tracks']+=tracks;current=trial;answer=record;print('FAG_BARE_DOGBONE_SOURCE_JOINED',pad['ref'],pad['num'],site.x,site.y,inner,flush=True);break
     h['vias'].pop();del h['tracks'][-len(tracks):]
    if answer:break
   if answer:break
  rows.append({'pad_uuid':uid,'ref':pad['ref'],'pin':pad['num'],'repair':answer,'attempts':tests});write(out/'checkpoint.json',rows);(out/'proposed-discrete.pkl').write_bytes(pickle.dumps(new,protocol=5))
 model=out/'source-only-model.pkl';model.write_bytes(pickle.dumps((old,h,b,zones,current),protocol=5));report={'verdict':'BOUNDED_ORDINARY_GROUND_DOGBONES_SOURCE_ONLY_NOMINATIONS_INDEPENDENT_MUTUAL_NATIVE_CURRENT_OPEN','model_sha256':sha(model),'proposed_discrete_sha256':sha(out/'proposed-discrete.pkl'),'rows':rows,'new_vias':len(new['vias']),'new_tracks':len(new['tracks']),'old_Cu_deleted':0,'old_native_zone_outlines_changed':0,'no_native_board_written':True,'source_projection':'GP58 source-only; full allnet exact source/contact/reference/newhole/drill/aperture/cap/mesh/native/DRC gates OPEN','actual_corrected_R106_C_CORE91_ROOT4_R10_context_unqualified':True,'original_fill_retreat_nomination_requires_explicit_full_all_net_retained_contact_reference_source_gate':True,'inputs':{str(p.resolve()):sha(p)for p in(Path(__file__),mp,mr,Path(N.__file__),Path(F.__file__),Path(I.p.__file__),Path(I.L.live.__file__))},'finite_failure_is_not_global_no_path_proof':True,'native_jobs':0,'adopted':False};write(out/'receipt.json',report);print(json.dumps({'new_vias':len(new['vias']),'new_tracks':len(new['tracks']),'missing':[r['ref']+'.'+r['pin']for r in rows if r.get('repair')is None and not r.get('already_actual_source_rooted')]}),flush=True)
if __name__=='__main__':main()
