"""Direct primitive IO3 source nominations before expensive face routing."""
import copy,hashlib,json,pickle,sys,uuid,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import audit_c10036_r24_full_independent_r30 as Q
import audit_aux_exact_raw as A
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/remaining-original-IO3-indexed-direct-source-nominees-r219';RAW='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def keys(xs):return {(q['kind'],q['uuid']) for q in xs if q['kind'] in ('pad','track','via')}
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin) for q in xs))
def main():
 assert not O.exists();O.mkdir();(O/'effective-source-used.py').write_text(EFFECTIVE_SOURCE);mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 g,h,b,z,c=pickle.loads(mp.read_bytes());groups=F.graph(c,RAW);src=root(groups,'R18001','2');prior=keys(src);bare=[p for p in h['pads'] if p['net']==RAW and ('pad',p['uuid']) not in prior];assert len(bare)==23
 _,gg=Q.physical(c,'/LOGIC_GND');gr=root(gg,'J11001','2');refs={l:unary_union([q['shape'] for q in gr if q['kind']=='fill'and q['layer']==inner]) for l,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
 (O/'exact-source-ground-reference.pkl').write_bytes(pickle.dumps(refs,protocol=5));print('R217_DRILLED_SOURCE_REFERENCE_READY',flush=True)
 rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526);res,ex=A.reservations()
 holes=[(p['uuid'],p['net'],s) for p in h['pads'] for s in C.poly(p.get('hole') or [])]+[(v['uuid'],v['net'],GP.bounded_disk(v,v['drill']/2)) for v in h['vias']];ht=STRtree([s for u,n,s in holes]);nativeids={q['uuid'] for q in g['zones']}
 pf=H/'field-power/B3-exact-cross-layer-pair-r206/cross-layer-discrete.pkl';assert sha(pf)=='7509b690027467fed1c9bd4ee57ed863eccbec2ae0bb7b9b26cb9ea0c5c014fb';pd=pickle.loads(pf.read_bytes())
 native_outer_fills={layer:[] for layer in ('F.Cu','B.Cu')}
 for index,q in enumerate(c['zones']):
  if q['uuid'] not in nativeids or q['net']==RAW or C.norm(q['net'])=='/LOGIC_GND':continue
  req=max(GP.G.gap(h,RAW,q['net']),float(q['clearance_mm']))+.025+.000020
  for layer in native_outer_fills:
   cache=C.poly(q['fills'].get(layer,[]))
   # Re-reading exactly the same unchanged rings must preserve each WKB.
   assert [sh.wkb for sh in cache]==[sh.wkb for sh in C.poly(q['fills'].get(layer,[]))]
   native_outer_fills[layer]+=[{'zone_index':index,'component_index':j,'uuid':q['uuid'],'req':req,'shape':sh} for j,sh in enumerate(cache)]
 native_outer_trees={l:STRtree([r['shape'] for r in rs]) for l,rs in native_outer_fills.items()}
 query_guard=max([r['req'] for rs in native_outer_fills.values() for r in rs]+[.7])+.000020
 (O/'exact-native-outer-fill-cache.pkl').write_bytes(pickle.dumps(native_outer_fills,protocol=5))
 put(O/'exact-native-outer-fill-cache-binding.json',{'model_sha256':sha(mp),'cache_sha256':sha(O/'exact-native-outer-fill-cache.pkl'),'per_layer_polygon_counts':{l:len(rs) for l,rs in native_outer_fills.items()},'every_cached_C_poly_WKB_matches_second_read':True,'predicate_query_radius_mm':query_guard,'no_buffer_operator_or_geometry_change':True})
 print('R217_EXACT_NATIVE_OUTER_FILL_CACHE_READY', {l:len(rs) for l,rs in native_outer_fills.items()},flush=True)
 def screen(points,width,layer):
  body=GP.bounded_buffer(LineString(points),width/2);bad=[]
  if not outline.covers(body):bad.append(('outline','outside'))
  for i in trees[layer].query(body.buffer(.7),predicate='intersects'):
   r=rec[layer][int(i)]
   if r['net']==RAW:continue
   req=GP.G.gap(h,RAW,r['net'])+.025+.000020
   if r['kind']=='track':t=r['source'];distance=LineString(points).distance(LineString([t['a'],t['b']]))-(width+t['w'])/2
   elif r['kind']=='via':v=r['source'];distance=LineString(points).distance(Point(v['x'],v['y']))-width/2-v['d']/2
   else:distance=body.distance(r['shape']);req+=.005 if r['kind']=='pad' else 0
   if distance<req:bad.append((r['kind'],r['uuid'],distance,req))
  for q in z:
   if q['layer']!=layer or q['net']==RAW:continue
   req=max(GP.G.gap(h,RAW,q['net']),float(q.get('clearance_mm',.15)))+.025+.000020;distance=body.distance(q['shape'])
   if distance<req:bad.append(('owned_plane',q['uuid'],distance,req))
  near=sorted([int(i) for i in native_outer_trees[layer].query(body.buffer(query_guard),predicate='intersects')],key=lambda i:(native_outer_fills[layer][i]['zone_index'],native_outer_fills[layer][i]['component_index']))
  rejected=set()
  for i in near:
   r=native_outer_fills[layer][i]
   if r['uuid'] in rejected:continue
   distance=body.distance(r['shape'])
   if distance<r['req']:bad.append(('original_supply_or_foreign_fill',r['uuid'],distance,r['req']));rejected.add(r['uuid'])
  for i in ht.query(body.buffer(.3),predicate='intersects'):
   uid,n,s=holes[int(i)]
   if n!=RAW and body.distance(s)<.275000020:bad.append(('foreign_hole',uid,body.distance(s),.275000020))
  for q in h['rule_areas']:
   if q.get('no_tracks') and layer in q['layers']:
    for s in C.poly(q['outline']):
     if body.distance(s)<.025000020:bad.append(('native_no_track',q['uuid']))
  for q in res['keepouts']:
   if RAW in ex.get(q['name'],set()) or layer not in q['layers']:continue
   for s in C.poly(q['outline']):
    if body.distance(s)<.025000020:bad.append(('reserved_rule',q['name']))
  for v in pd['vias']:
   if v['net']!=RAW and layer in v['flashed']:
    req=GP.G.gap(h,RAW,v['net'])+.025000020;dist=LineString(points).distance(Point(v['x'],v['y']))-width/2-v['d']/2
    if dist<req:bad.append(('held_B3_barrel',v['uuid'],dist,req))
  return body,bad
 new=[];accepted=[];fails=[]
 for p in sorted(bare,key=lambda p:p['ref']):
  if ('pad',p['uuid']) in prior:continue
  options=[];tested=[]
  for layer in p['layers']:
   if layer not in refs:continue
   target=unary_union(C.poly(p['layers'][layer]));source_rows=[q for q in src if q['layer']==layer];source_shapes=[q['shape'] for q in source_rows];st=STRtree(source_shapes)
   near=sorted([int(i) for i in st.query(target.buffer(25),predicate='intersects')],key=lambda i:target.distance(source_shapes[i]))[:16]
   endpoints=[]
   for i in near:
    sh=source_shapes[i];a,bb=nearest_points(target,sh);endpoints.append((list(a.coords[0]),list(bb.coords[0]),source_rows[i]['uuid'],source_rows[i]['kind']))
    inner=sh.buffer(-.03)
    if not inner.is_empty:a,bb=nearest_points(target,inner);endpoints.append((list(a.coords[0]),list(bb.coords[0]),source_rows[i]['uuid'],source_rows[i]['kind']))
   start=[p['x'],p['y']]
   for a,end,port,kind in endpoints:
    # Pad-center start retains literal pad overlap; body-edge port is inset when possible.
    for points in ([start,end],[start,[start[0],end[1]],end],[start,[end[0],start[1]],end]):
     points=[[round(x,6),round(y,6)] for x,y in points];points=[q for i,q in enumerate(points) if i==0 or q!=points[i-1]]
     if len(points)<2:continue
     for width in (.3,.25,.2):
      body,bad=screen(points,width,layer)
      if bad:tested.append({'source_port':port,'layer':layer,'width_mm':width,'points_mm':points,'first_primitive_failures':bad[:4]});continue
      trial=copy.deepcopy(c);nt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/remaining-IO3-r216/'+p['uuid']+'/'+layer+'/'+str(i)+'/'+str(width)+'/'+str(points))),'net':RAW,'layer':layer,'w':width,'a':a,'b':bb} for i,(a,bb) in enumerate(zip(points,points[1:]))];trial['tracks']+=new+nt;actual_src=root(F.graph(trial,RAW),'R18001','2');actual=keys(actual_src)
      if prior-actual or ('pad',p['uuid']) not in actual:continue
      refgap=body.difference(refs[layer]);options.append({'new_tracks':nt,'source_group':actual_src,'actual_keys':actual,'body':body,'refgap':refgap,'length':LineString(points).length,'source_port':port,'source_port_kind':kind,'layer':layer,'width':width,'points':points})
  if not options:fails.append({'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'at_mm':[p['x'],p['y']],'tested_capsule_paths':len(tested),'first_failures':tested[:15],'next_scope':'ordinary dogbone or exact pad-contact-preserving pose/owned wall correction'});print('R216_DIRECT_PENDING',p['ref'],p['num'],len(tested),flush=True)
  else:
   a=min(options,key=lambda q:(not q['refgap'].is_empty,q['refgap'].area,q['length'],-q['width']));new+=a['new_tracks'];src=a['source_group'];prior=a['actual_keys'];path=O/(p['uuid']+'-new-body-reference-gap.wkb');path.write_bytes(a['refgap'].wkb);accepted.append({'ref':p['ref'],'pin':p['num'],'pad_UUID':p['uuid'],'actual_R18001_2_source_joined':True,'source_port':a['source_port'],'source_port_kind':a['source_port_kind'],'layer':a['layer'],'width_mm':a['width'],'length_mm':a['length'],'points_mm':a['points'],'new_track_UUIDs':[t['uuid'] for t in a['new_tracks']],'new_full_body_source_reference_gap_mm2':a['refgap'].area,'reference_gap_file':str(path.resolve()),'reference_gap_sha256':sha(path),'source_geometry_only_not_qualified_current':True});print('R216_DIRECT_SOURCE_NOMINEE',p['ref'],p['num'],a['layer'],a['width'],'length',a['length'],'refgap',a['refgap'].area,flush=True)
   (O/'proposed-tracks.pkl').write_bytes(pickle.dumps(new,protocol=5))
  if p['ref']=='C10025':
   expected=json.loads((H/'sbc-power/remaining-original-IO3-direct-capsule-source-nominees-r216/checkpoint.json').read_text())['pending_direct_primitives'][0]
   assert not options and fails[-1]['tested_capsule_paths']==expected['tested_capsule_paths'] and json.loads(json.dumps(fails[-1]['first_failures']))==expected['first_failures'], 'exact cached screen differs from preserved C10025 negative'
   put(O/'exact-C10025-cached-vs-original-screen-equivalence.json',{'negative_path_count':expected['tested_capsule_paths'],'all_first15_path_coordinates_widths_and_first4_failures_exact':True,'old_checkpoint_sha256':sha(H/'sbc-power/remaining-original-IO3-direct-capsule-source-nominees-r216/checkpoint.json')})
 put(O/'checkpoint.json',{'accepted_source_nominations':accepted,'pending_direct_primitives':fails,'still_unrooted_named_pad_UUIDs':[p['uuid'] for p in bare if ('pad',p['uuid']) not in prior],'native_jobs':0,'board_written':False})
 put(O/'receipt.json',{'verdict':'DIRECT_PRIMITIVE_SOURCE_NOMINATIONS_ALL_FOREIGN_CONTACT_PAIRED_REFERENCE_CURRENT_GATES_REQUIRED','exact_positive_R214_model_sha256':sha(mp),'accepted_source_nominations':accepted,'pending_direct_primitives':fails,'new_tracks':len(new),'new_holes':0,'original_discrete_source_native_outlines_changed':0,'full_IO3_A_retained':2.0,'no_current_or_quiet_stem_derating':True,'held_B3_exact_discrete_sha256':sha(pf),'full_contact_native_reference_PDN_current':'OPEN','no_area_or_reference_waiver':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__),'effective_source_sha256':sha(O/'effective-source-used.py')})
 print('R216_COMPLETE',len(accepted),len(new),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__),'effective_source_sha256':sha(O/'effective-source-used.py')})
  raise
