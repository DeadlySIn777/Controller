"""Replace only the overlapping owned IO3 bridge using actual source islands.

Exact native discrete, retained outer reference intersections and every later
owned power plane are hard. No source adoption or native board is performed.
"""
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision,get_num_coordinates,from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'sbc-power'));sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import owned_analytic_track_guards_r75 as AT
import owned_native_pad_guards_r98 as AP
import io3_contact_restore_r2 as Q
import tri_route as T
O=H/'sbc-power/IO3-safe-existing-via-reroute-r158'
RAW='/IO_3V3';OLD='04d140c5-3a78-5a5f-96d3-fbe2978c8eee';VID='4df659b6-03b2-580c-b6b8-1cc10e70c2c8'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n')
def polys(s):return [s] if s.geom_type=='Polygon' else [p for p in getattr(s,'geoms',[]) if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/safe-ROOT22-CORE1V2-composition-r148/unprojected-model.pkl';assert sha(mp)=='6cb9583d5a37a0e4041419da9672011dad6c52f8fd4a9178797d43d9278df7d1'
 g,h,b,z,c=pickle.loads(mp.read_bytes());cachepath=H/'sbc-power/IO3-overlapping-owned-bridge-withdrawal-source-probe-r156/source-cache.pkl';assert sha(cachepath)=='10a0b5379413135fb5379be76f359dece2aa48e09788f78c9f4c3c7d3af393ca';cache=pickle.loads(cachepath.read_bytes())
 prec=[]
 for q in z:
  if q['uuid']=='d5e1a664-0428-5fe4-aaa9-7887f79adfe7':
   for key in ('shape','zone_outline_shape'):
    if key in q:
     old=q[key].wkb;q[key]=set_precision(q[key],1e-6,mode='pointwise');assert q[key].wkb==old;prec.append({'UUID':q['uuid'],'role':key,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hashlib.sha256(old).hexdigest()})
 withdrawn=next(q for q in z if q['uuid']==OLD);remain=[q for q in z if q['uuid']!=OLD]
 rootindex=next(i for i,xs in enumerate(cache['before_groups']) if any((r['ref'],r['pad'])==('R18001','2') for r in xs));prior={r['uuid'] for r in cache['before_groups'][rootindex]}
 afterindex=next(i for i,xs in enumerate(cache['after_groups']) if any((r['ref'],r['pad'])==('R18001','2') for r in xs));v=next(v for v in h['vias'] if v['uuid']==VID);pt=Point(v['x'],v['y']);ann=pt.buffer(v['d']/2,quad_segs=128).difference(pt.buffer(v['drill']/2,quad_segs=128))
 rec,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'][RAW]
 def gap(n):return .15 if h['domains_normalized'][C.norm(n)]==dom else .6
 holes=[(p['uuid'],p['net'],s) for p in h['pads'] for s in C.poly(p.get('hole') or [])]+[(vv['uuid'],vv['net'],Point(vv['x'],vv['y']).buffer(vv['drill']/2,quad_segs=128)) for vv in h['vias']]
 ht=STRtree([s for uid,n,s in holes]);ownholes=unary_union([s for uid,n,s in holes if n==RAW]);outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 peer=[];peerbindings=[]
 for name in ('field-power/u10017-protected-source-via-bypass-nominee-r154','logic-two-reference-safe-return-restoration-r42'):
  d=H/name;qf=d/'proposed-zones.pkl';df=d/'proposed-discrete.pkl';rf=d/'receipt.json'
  if qf.exists():
   qs=pickle.loads(qf.read_bytes());peer+=qs;row={'zones_file':str(qf),'zones_sha256':sha(qf),'receipt_file':str(rf) if rf.exists() else None,'receipt_sha256':sha(rf) if rf.exists() else None,'hard_only_no_source_current_credit':True}
   if df.exists():
    ds=pickle.loads(df.read_bytes());row['discrete_sha256']=sha(df)
    for kind in ('tracks','vias'):
     by={q['uuid']:q for q in h[kind]}
     for item in ds.get(kind,[]):
      if item['uuid'] not in by:h[kind].append(item)
      else:assert item==by[item['uuid']]
   peerbindings.append(row)
 # Added hard-only peer Cu never enters the emitted model or source graph.
 hard_h=h;g,h,b,z,c=pickle.loads(mp.read_bytes())
 for q in z:
  if q['uuid']=='d5e1a664-0428-5fe4-aaa9-7887f79adfe7':
   for key in ('shape','zone_outline_shape'):
    if key in q:q[key]=set_precision(q[key],1e-6,mode='pointwise')
 remain=[q for q in z if q['uuid']!=OLD];rec,trees=F.build({**hard_h,'zones':[]})
 # Actual old source-reference intersections are a conservative hard mask.
 # A positive source feed may not erase the retained reference beneath old Cu.
 refs={};refrows=[]
 for layer,outer in [('In1.Cu',('F.Cu',)),('In4.Cu',('B.Cu','In3.Cu'))]:
  fill=unary_union([s for q in h['zones'] if C.norm(q['net'])=='/LOGIC_GND' for s in C.poly(q['fills'].get(layer,[]))]);bodies=[]
  for t in h['tracks']:
   if t['layer'] in outer and h['domains_normalized'].get(C.norm(t['net']))==h['domains_normalized']['/LOGIC_GND'] and t['net']!='/LOGIC_GND':
    body=LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128);r=body.intersection(fill)
    if not r.is_empty:bodies.append(r)
  refs[layer]=unary_union(bodies);refrows.append({'reference_layer':layer,'actual_original_fill_intersection_mm2':refs[layer].area,'hard_mask_WKB_SHA256':digest(refs[layer]),'conservative_all_original_LOGIC_fill_not_unproven_source_credit':True})
 attempts=[];answer=None;chosen=None;source={l:unary_union([p for p,a in zip(cache['after_parts'][l],cache['after_assign'][l]) if a==afterindex]).difference(ownholes) for l in h['copper_layers']}
 for radius in (5.,15.,35.,75.,125.):
  for layer in ('In2.Cu','In3.Cu','In4.Cu','In1.Cu'):
   window=box(v['x']-radius,v['y']-radius,v['x']+radius,v['y']+radius);query=window.buffer(1.5);obs=[]
   if not source[layer].intersects(window):continue
   print('IO3_SAFE_LEGAL',layer,radius,flush=True)
   for i in trees[layer].query(query,predicate='intersects'):
    r=rec[layer][int(i)]
    if r['net']==RAW:continue
    clear=gap(r['net'])+.025+.000020
    if r['kind']=='track':t=r['source'];cut=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear)
    elif r['kind']=='via':vv=r['source'];cut=GP.bounded_disk(vv,vv['d']/2+clear)
    else:cut=GP.bounded_buffer(r['shape'],clear)
    obs.append(cut)
   for q in remain+peer:
    if q['layer']==layer and q['net']!=RAW and query.intersects(q['shape']):obs.append(GP.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))
   for q in h['zones']:
    if q['net']==RAW or gap(q['net'])<.6:continue
    for s in C.poly(q['fills'].get(layer,[])):
     if query.intersects(s):obs.append(GP.bounded_buffer(s,max(.6,float(q['clearance_mm']))+.025+.000020))
   for i in ht.query(query,predicate='intersects'):
    uid,n,s=holes[int(i)]
    if n!=RAW:obs.append(GP.bounded_buffer(s,.275+.000020))
   if layer in refs and refs[layer].intersects(query):obs.append(GP.bounded_buffer(refs[layer].intersection(query),.175+.000020))
   for rule in h['rule_areas']:
    if rule.get('no_zones') and layer in rule['layers']:obs += [GP.bounded_buffer(s,.025+.000020) for s in C.poly(rule['outline']) if query.intersects(s)]
   free=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6)
   for width in (.5,.35,.25,.20):
    for part in polys(free.buffer(-width/2-.005)):
     aa=part.buffer(-.000020).intersection(ann);bb=part.buffer(-.000020).intersection(source[layer])
     if aa.area<.005 or bb.area<.005:continue
     if get_num_coordinates(part)>5000:
      simple=part.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(part);eligible=[x for x in polys(simple) if x.intersects(aa) and x.intersects(bb)]
      if not eligible:continue
      part=max(eligible,key=lambda x:x.area);aa=part.buffer(-.000020).intersection(aa);bb=part.buffer(-.000020).intersection(bb)
      if aa.area<.005 or bb.area<.005:continue
     a,bp=nearest_points(aa,bb);chord=LineString([a,bp]);print('IO3_SAFE_PATH',layer,radius,width,int(get_num_coordinates(part)),flush=True)
     if part.covers(chord):points=list(chord.coords);search={'method':'exact_covered_chord'}
     else:
      try:points,search=T.route(part,tuple(a.coords[0]),tuple(bp.coords[0]))
      except (AssertionError,ValueError) as error:attempts.append({'layer':layer,'radius':radius,'width':width,'rejected':'tri_route','error':str(error)});continue
     points=[(round(x,6),round(y,6)) for x,y in points]
     if len(set(points))<2:continue
     line=LineString(points);core=line.buffer(width/2,quad_segs=128)
     if not free.covers(core):attempts.append({'layer':layer,'radius':radius,'width':width,'rejected':'literal_free_covers_failed','outside_mm2':core.difference(free).area});continue
     intended=set_precision(unary_union([x for x in polys(line.buffer(max(.35,width),quad_segs=128).intersection(free.buffer(-.000020))) if x.intersects(core)]),1e-6);physical=set_precision(intended.difference(ownholes),1e-6)
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/IO3-SAFE-owned-replacement-r158/'+layer));nq={'uuid':uid,'net':RAW,'layer':layer,'shape':physical,'zone_outline_shape':intended,'clearance_mm':.15,'label':'Source-safe R11049 existing-via bridge R158','replaces_owned_NEW_UUID':OLD,'physical_Cu_drill_subtracted':True}
     nq=GP.normalize_owned_via_guards(hard_h,[nq])[0][0];nq=AT.normalize_owned_track_guards(hard_h,[nq])[0][0];nq=AP.normalize_owned_pad_guards(hard_h,[nq])[0][0]
     if nq['shape'].intersection(ann).area<.01 or nq['shape'].intersection(source[layer]).area<.01:continue
     hs={**h,'zones':[q for q in h['zones'] if q['net']==RAW]};trial,cuts=GP.projected(g,hs,remain+[nq]);Q.NET=RAW;gs,parts,assignment=Q.groups(trial,return_details=True);ri=next(i for i,xs in enumerate(gs) if any((r['ref'],r['pad'])==('R18001','2') for r in xs));joined={r['uuid'] for r in gs[ri]};missing=sorted(prior-joined)
     oldparts=[];lookup={r['uuid']:i for i,xs in enumerate(gs) for r in xs}
     for i,xs in enumerate(cache['before_groups']):
      destinations={lookup.get(r['uuid'],'MISSING') for r in xs}
      if len(destinations)>1 or 'MISSING' in destinations:oldparts.append({'original_group':i,'new_groups':sorted(map(str,destinations)),'keys':[r['uuid'] for r in xs]})
     row={'layer':layer,'radius_mm':radius,'minimum_core_width_mm':width,'length_mm':line.length,'points_mm':points,'new_UUID':uid,'retained_source_keys':len(joined),'lost_prior_source_keys':missing,'split_old_IO3_physical_key_groups':oldparts,'exact_source_annulus_overlap_mm2':nq['shape'].intersection(ann).area,'exact_prior_source_overlap_mm2':nq['shape'].intersection(source[layer]).area,'search':search};attempts.append(row);write(O/'attempts.json',attempts)
     if missing or oldparts:continue
     answer=row;chosen=nq;print('IO3_SAFE_SOURCE_ACCEPT',layer,line.length,width,len(joined),flush=True);break
    if answer:break
   if answer:break
  if answer:break
 write(O/'attempts.json',attempts)
 if chosen is None:write(O/'receipt.json',{'verdict':'FINITE_IO3_SAFE_REROUTE_CONSTRUCTION_NOT_FOUND_NOT_A_NOPATH_PROOF','attempts':attempts,'board_written':False,'native_jobs':0});return
 outzones=remain+[chosen];b['IO3_SAFE_existing_via_owned_bridge_replacement']={'old_UUID':OLD,'new_UUID':chosen['uuid'],'old_WKB_SHA256':digest(withdrawn['shape']),'new_WKB_SHA256':digest(chosen['shape']),'exact_later_all_native_Cu_and_protected_planes_hard':True,'source_keys_prior_count':len(prior),'source_keys_lost':[],'explicit_d5_precision_states':prec};b['SAFE_no_REG6_or_DI6_DI15_unaccepted_geometry']=True
 model=O/'unprojected-model.pkl';model.write_bytes(pickle.dumps((g,h,b,outzones,None),protocol=5));(O/'proposed-replacement-zones.pkl').write_bytes(pickle.dumps([chosen],protocol=5));(O/'scoped-source-model.pkl').write_bytes(pickle.dumps(trial,protocol=5))
 write(O/'receipt.json',{'verdict':'IO3_SAFE_EXACT_SOURCE_AND_ALL_IO3_KEY_RELATIONSHIPS_PASS_FULL_FOREIGN_REFERENCE_CURRENT_NATIVE_OPEN','parent_model_sha256':sha(mp),'model_sha256':sha(model),'proposed_replacement_zones_sha256':sha(O/'proposed-replacement-zones.pkl'),'source_cache_sha256':sha(cachepath),'withdrawn_owned_NEW_zone_UUID':OLD,'replacement':answer,'explicit_precision_states':prec,'retained_reference_hard_masks':refrows,'hard_only_peer_proposals':peerbindings,'script_sha256':sha(__file__),'all_source_current_loads_preserved':True,'original_native_zone_outlines_changed':0,'old_discrete_changed':0,'new_holes':0,'board_written':False,'native_jobs':0,'full_foreign_contact_source_reference_native_current':'OPEN'});print('IO3_SAFE_R158_FROZEN',sha(model),flush=True)
if __name__=='__main__':main()
