"""Ordinary ground fanout nominees with exact NEW-plane-only clearance cuts."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import core_inner_feed_r18 as I
import tri_route as T
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];NET='/motherboard_motors/FIELD_GND'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def polys(sh):return[q for q in ([sh]if sh.geom_type=='Polygon'else getattr(sh,'geoms',[]))if q.geom_type=='Polygon'and not q.is_empty and q.area>1e-12]
def main():
 mp=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();r=json.loads(mp.with_name('receipt.json').read_bytes());assert sha(mp)==r['model_sha256']and r['verdict']=='PASS_SAFE_FIVE_LOGIC_AND_EXPLICIT_FAG_MARGIN_HOST_SOURCE_REFERENCE_CONTACT_NATIVE_CURRENT_OPEN'and not out.exists()and out.is_relative_to(H)
 g,h,b,z,full=pickle.loads(mp.read_bytes());h=copy.deepcopy(h);z=copy.deepcopy(z);out.mkdir();raw=next(p['net']for p in h['pads']if(p['ref'],p['num'])==('U11025','2'));domain=h['domains_normalized'][NET]
 protected={q['uuid']for q in pickle.loads(mp.with_name('proposed-zones.pkl').read_bytes())};peer=H/'field-power/regulated-four-retained-hard-snapshot-r127';pr=json.loads((peer/'receipt.json').read_bytes());assert sha(peer/'proposed-zones.pkl')==pr['retained_zone_sha256']and sha(peer/'proposed-discrete.pkl')==pr['retained_discrete_sha256'];peerq=pickle.loads((peer/'proposed-zones.pkl').read_bytes());peerd=pickle.loads((peer/'proposed-discrete.pkl').read_bytes())
 def gap(other):return .15 if h['domains_normalized'][C.norm(other)]==domain else .6
 source=lambda:N.projected(g,{**h,'zones':[q for q in h['zones']if q['net']==raw]},z)[0]
 current=full;root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs));padids=lambda xs:{q['uuid']for q in xs if q['kind']=='pad'and q['pin']}
 outline=unary_union(C.poly(h['outline'])).buffer(-.526);I.p.WINDOW=box(.526,.526,449.474,234.474);areas=I.L.live.reservations();hardmodel={**h,'zones':[dict(q,layers=[l for l in q['layers']if l!='In3.Cu'])if C.norm(q['net'])=='/CORE_1V2'else q for q in h['zones']]};hard={l:I.p.hard_shapes(hardmodel,areas,NET,l)for l in LAYERS};viahard=[s for l in LAYERS for s in I.p.hard_shapes(hardmodel,areas,NET,l,for_via=True)]
 foot=next(q for q in h['footprints']if q['ref']=='U10003');courts=[s.buffer(.6)for rings in foot['courtyard'].values()for s in C.poly(rings)];p9=next(q for q in h['pads']if(q['ref'],q['num'])==('U10003','9'));assert C.norm(p9['net'])==NET and list(p9['layers'])==['B.Cu'];corridor=box(p9['x']+.55,p9['y']-.21,p9['x']+2.5,p9['y']+.21)
 rowpins=[q for q in h['pads']if q['ref']=='U10003'];assert all(corridor.bounds[0]>q['x']for q in rowpins);barrier={'ref':'U10003','pin':'9','layer':'B.Cu','corridor_bounds_mm':list(corridor.bounds),'only_own_conservative_courtyard_outer_track_mask_change':True,'native_keepouts_via_masks_foreign_Cu_pad_spacing_unchanged':True,'central_pad_row_gap_not_crossed':True}
 def outerhard(layer,uid):
  if uid!=p9['uuid']:return hard[layer]
  found=[s for s in hard[layer]if any(s.equals(c)for c in courts)];assert len(found)==len(courts)>0
  return[s.difference(corridor)if any(s.equals(c)for c in courts)else s for s in hard[layer]]
 new={'vias':[],'tracks':[]};rows=[];carves=[];originalz={q['uuid']:copy.deepcopy(q)for q in z};targets=['d64c464d-de71-4c7e-9d98-b870e2ad977f','6d65e765-0689-4977-98aa-e5c00d7c8922','4021795d-90df-4df0-a1b4-13cdcbdd91ac']
 for uid in targets:
  maskh={**h,'vias':h['vias']+peerd['vias'],'tracks':h['tracks']+peerd['tracks']};records,trees=F.build({**maskh,'zones':[]});holes=[s for p in h['pads']for s in C.poly(p.get('hole')or[])]+[N.bounded_disk(v,v['drill']/2)for v in maskh['vias']];smd=[s for p in h['pads']if p['smd']for rings in p['layers'].values()for s in C.poly(rings)];pad=next(p for p in h['pads']if p['uuid']==uid);layer=next(iter(pad['layers']));padshape=unary_union(C.poly(pad['layers'][layer]));point=Point(pad['x'],pad['y']);rr=root(F.graph(current,NET));prior=padids(rr);sources={l:unary_union([q['shape']for q in rr if q['layer']==l])for l in LAYERS};answer=None;attempts=[]
  for radius in (2.,5.,10.):
   win=box(point.x-radius,point.y-radius,point.x+radius,point.y+radius);search=win.buffer(2);obs=[];outer=[]
   for l in LAYERS:
    for i in trees[l].query(search,predicate='intersects'):
     q=records[l][int(i)]
     if q['net']==raw:continue
     n=gap(q['net'])+.025+.000020
     if q['kind']=='track':t=q['source'];axis=LineString([t['a'],t['b']]);vcut=N.bounded_buffer(axis,t['w']/2+.25+n);tcut=N.bounded_buffer(axis,t['w']/2+n)
     elif q['kind']=='via':v=q['source'];vcut=N.bounded_disk(v,v['d']/2+.25+n);tcut=N.bounded_disk(v,v['d']/2+n)
     else:vcut=N.bounded_buffer(q['shape'],.25+n);tcut=N.bounded_buffer(q['shape'],n)
     obs.append(vcut)
     if l==layer:outer.append(tcut)
   for q in [q for q in z if q['uuid']in protected]+peerq:
    if q['net']==raw or not search.intersects(q['shape']):continue
    n=max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020;obs.append(N.bounded_buffer(q['shape'],.25+n))
    if q['layer']==layer:outer.append(N.bounded_buffer(q['shape'],n))
   for s in smd+holes:
    if search.intersects(s):obs.append(N.bounded_buffer(s,.375+.000020))
   outer.extend(N.bounded_buffer(s,.275+.000020)for s in holes if search.intersects(s));obs.extend(N.bounded_buffer(s,.275+.000020)for s in viahard if search.intersects(s));outer.extend(N.bounded_buffer(s,.025+.000020)for s in outerhard(layer,uid)if search.intersects(s))
   region=set_precision(win.intersection(outline.buffer(-.25)).difference(unary_union(obs)),1e-6);free=set_precision(win.intersection(outline).difference(unary_union(outer)).buffer(-.1-.000020),1e-6);faces=[p for p in polys(free)if p.intersects(padshape.buffer(-.000020))];options=[]
   print('R24_FIELD_SITE_FACE',pad['ref'],radius,region.area,len(faces),flush=True)
   for inner in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):
    for face in faces:
     for piece in polys(region.intersection(face).intersection(N.bounded_buffer(sources[inner],.2))):
      options.extend((point.distance(s),inner,s,face)for s in (piece.representative_point(),nearest_points(piece,point)[0],piece.centroid)if piece.covers(s))
   for _,inner,s,face in sorted(options,key=lambda x:x[:2]):
    site=Point(round(s.x,6),round(s.y,6));ann=N.bounded_disk({'x':site.x,'y':site.y},.25).difference(N.bounded_disk({'x':site.x,'y':site.y},.1))
    if not region.covers(site)or not face.covers(site)or ann.intersection(sources[inner]).area<.01:continue
    start=nearest_points(face.intersection(padshape.buffer(-.000020)),point)[0];chord=LineString([start,site])
    if face.covers(chord):points=list(chord.coords)
    else:
     try:points,_=T.route(face,tuple(start.coords[0]),tuple(site.coords[0]))
     except(AssertionError,ValueError):continue
    points=[[round(x,6),round(y,6)]for x,y in points]
    if len(set(map(tuple,points)))<2:continue
    vid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-ground-bare-r26/'+uid+'/via/'+repr((site.x,site.y))));v={'uuid':vid,'net':raw,'x':site.x,'y':site.y,'d':.5,'drill':.2,'flashed':LAYERS.copy()};ts=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-ground-bare-r26/'+uid+'/track/'+repr((a,bb)))),'net':raw,'a':a,'b':bb,'w':.2,'layer':layer}for a,bb in zip(points,points[1:])];previous=z;trialz=[];cuts=[]
    for q in z:
     if q['net']==raw or q['uuid']in protected:trialz.append(q);continue
     n=max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020;cut=N.bounded_disk(v,.25+n)
     if q['layer']==layer:cut=unary_union([cut]+[N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+n)for t in ts])
     oldsh=q['shape'];oldnative=q.get('zone_outline_shape',oldsh);sh=set_precision(oldsh.difference(cut),1e-6);native=set_precision(oldnative.difference(cut),1e-6)
     if oldsh.equals(sh)and oldnative.equals(native):trialz.append(q);continue
     if sh.is_empty or native.is_empty:trialz=[];break
     assert sh.difference(oldsh).area==0 and native.difference(oldnative).area==0;qq=copy.deepcopy(q);qq.update(shape=sh,zone_outline_shape=native);trialz.append(qq);cuts.append({'owned_new_zone_uuid':q['uuid'],'new_via_uuid':vid,'layer':q['layer'],'before_sha256':hashlib.sha256(oldsh.wkb).hexdigest(),'after_sha256':hashlib.sha256(sh.wkb).hexdigest(),'removed_area_mm2':oldsh.difference(sh).area,'full_guard_mm':n})
    if not trialz:continue
    z=trialz;h['vias'].append(v);h['tracks']+=ts;trial=source();joined=padids(root(F.graph(trial,NET)));ok=uid in joined and prior<=joined;record={'ref':pad['ref'],'pin':pad['num'],'pad_uuid':uid,'via_uuid':vid,'site_mm':[site.x,site.y],'outer_layer':layer,'chosen_direct_source_inner_layer':inner,'source_annular_overlap_mm2':ann.intersection(sources[inner]).area,'points_mm':points,'minimum_width_mm':.2,'length_mm':LineString(points).length,'target_actual_J3_source_joined':uid in joined,'all_prior_named_J3_source_pads_retained':prior<=joined,'source_only_nomination':ok,'owned_new_cut_count':len(cuts)};attempts.append(record)
    if ok:carves+=cuts;new['vias'].append(v);new['tracks']+=ts;current=trial;answer=record;print('R24_FIELD_NOMINATED',pad['ref'],vid,len(cuts),flush=True);break
    h['vias'].pop();del h['tracks'][-len(ts):];z=previous
   if answer:break
  rows.append({'pad_uuid':uid,'ref':pad['ref'],'pin':pad['num'],'repair':answer,'attempts':attempts});write(out/'checkpoint.json',rows);(out/'proposed-discrete.pkl').write_bytes(pickle.dumps(new,protocol=5));write(out/'owned-new-antipad-carves.json',carves)
 updates=[q for q in z if not q['shape'].equals(originalz[q['uuid']]['shape'])or not q.get('zone_outline_shape',q['shape']).equals(originalz[q['uuid']].get('zone_outline_shape',originalz[q['uuid']]['shape']))];(out/'owned-new-zone-updates.pkl').write_bytes(pickle.dumps(updates,protocol=5));write(out/'own-barrier-planning-corridor.json',barrier);model=out/'source-only-model.pkl';model.write_bytes(pickle.dumps((g,h,b,z,current),protocol=5))
 write(out/'receipt.json',{'verdict':'ORDINARY_GROUND_NEW_ONLY_ANTIPAD_SOURCE_NOMINATIONS_FULL_GATE_OPEN','model_sha256':sha(model),'parent_model_sha256':sha(mp),'proposed_discrete_sha256':sha(out/'proposed-discrete.pkl'),'owned_zone_updates_sha256':sha(out/'owned-new-zone-updates.pkl'),'owned_antipad_ledger_sha256':sha(out/'owned-new-antipad-carves.json'),'own_barrier_planning_corridor_sha256':sha(out/'own-barrier-planning-corridor.json'),'hard_peer_receipt_sha256':sha(peer/'receipt.json'),'rows':rows,'new_vias':len(new['vias']),'new_tracks':len(new['tracks']),'original_native_outlines_or_old_Cu_deleted':0,'all_real_pads_holes_areas_foreign_clearances_and_minimum_width_unchanged':True,'all_new_via_flashes':'PROSPECTIVE_ORDINARY_ALL6_MUST_PROVE_NATIVE','full_ALLnet_contacts_reference_source_current_DRILL_SMD_native_DRC_gates':'OPEN','script_sha256':sha(__file__),'finite_failure_not_global_no_path':True,'native_jobs':0,'board_written':False,'adopted':False});print('R24_COMPLETE',len(new['vias']),len(new['tracks']),flush=True)
if __name__=='__main__':main()
