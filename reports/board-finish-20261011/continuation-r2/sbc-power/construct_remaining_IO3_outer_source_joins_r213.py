"""Short ordinary-width F/B joins from the exact positive R214 state.

Original isolated pads and real source Cu are used, with literal full-body
source-ground reference. No new holes, source changes or minimum-width waiver.
"""
import copy,hashlib,json,pickle,sys,uuid,traceback
from pathlib import Path
from shapely import set_precision,get_num_coordinates
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import audit_c10036_r24_full_independent_r30 as Q
import audit_aux_exact_raw as A
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
import tri_route as T
O=H/'sbc-power/remaining-original-IO3-ordinary-outer-source-joins-r213'
RAW='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def polys(s):return [s] if s.geom_type=='Polygon' else [p for p in getattr(s,'geoms',[]) if p.geom_type=='Polygon']
def root(groups,ref,pin):return next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin) for q in xs))
def keys(xs):return {(q['kind'],q['uuid']) for q in xs if q['kind'] in ('pad','track','via')}
def main():
 assert not O.exists();O.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z)
 fg=F.graph(c,RAW);source=root(fg,'R18001','2');prior=keys(source)
 named=[q for xs in fg if xs is not source for q in xs if q['kind']=='pad'and q['pin']];wanted=sorted({q['uuid'] for q in named});assert len(wanted)==23,len(wanted)
 # References are physical drilled copper in the actual J1 source component.
 _,lg=Q.physical(c,'/LOGIC_GND');ground=root(lg,'J11001','2');refs={l:unary_union([q['shape'] for q in ground if q['kind']=='fill'and q['layer']==inner]) for l,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
 rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 holes=[(p['uuid'],p['net'],s) for p in h['pads'] for s in C.poly(p.get('hole') or [])]+[(v['uuid'],v['net'],GP.bounded_disk(v,v['drill']/2)) for v in h['vias']];ht=STRtree([s for u,n,s in holes])
 reserved,exempt=A.reservations();nativeids={q['uuid'] for q in g['zones']}
 # New field B3 proposals are literal hard reservations only, without source credit.
 peerf=H/'field-power/B3-exact-cross-layer-pair-r206/cross-layer-zones.pkl';peerd=H/'field-power/B3-exact-cross-layer-pair-r206/proposed-discrete.pkl';peer=[];peertracks=[];peervias=[]
 if peerf.exists():peer=pickle.loads(peerf.read_bytes())
 # Discrete exact file name is discovered from the frozen receipt if needed.
 rr=H/'field-power/B3-exact-cross-layer-pair-r206/receipt.json'
 if peerd.exists():pd=pickle.loads(peerd.read_bytes());peertracks=pd.get('tracks',[]);peervias=pd.get('vias',[])
 put(O/'input-and-bare-pad-inventory.json',{'exact_R214_model_sha256':sha(mp),'bare_named_pad_UUIDs':wanted,'bare_pads':[{'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'x':p['x'],'y':p['y'],'layers':list(p['layers'])} for p in h['pads'] if p['uuid'] in wanted], 'source_named_pad_UUIDs':len({q['uuid'] for q in source if q['kind']=='pad'and q['pin']}),'full_IO3_current_A':2.0,'no_power_or_quiet_stem_derating':True,'new_holes':0})
 source_shapes={l:unary_union([q['shape'] for q in source if q['layer']==l]) for l in ('F.Cu','B.Cu')}
 def gap(n):return GP.G.gap(h,RAW,n)
 def free(layer,window):
  query=window.buffer(2);obs=[]
  for i in trees[layer].query(query,predicate='intersects'):
   q=rec[layer][int(i)]
   if q['net']==RAW:continue
   clear=gap(q['net'])+.025+.000020
   if q['kind']=='track':t=q['source'];s=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear)
   elif q['kind']=='via':v=q['source'];s=GP.bounded_disk(v,v['d']/2+clear)
   else:s=GP.bounded_buffer(q['shape'],clear)
   obs.append(s)
  for q in z+peer:
   if q['layer']==layer and q['net']!=RAW and q['shape'].intersects(query):obs.append(GP.bounded_buffer(q['shape'].intersection(query),max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))
  for q in c['zones']:
   if q['uuid'] not in nativeids or q['net']==RAW:continue
   # Same-domain original LG outer fills may refill around a legal new track;
   # all other original supply/domain fills are retained hard.
   if C.norm(q['net'])=='/LOGIC_GND':continue
   for s in C.poly(q['fills'].get(layer,[])):
    if s.intersects(query):obs.append(GP.bounded_buffer(s.intersection(query),max(gap(q['net']),float(q['clearance_mm']))+.025+.000020))
  for i in ht.query(query,predicate='intersects'):
   u,n,s=holes[int(i)]
   if n!=RAW:obs.append(GP.bounded_buffer(s,.275+.000020))
  for q in h['rule_areas']:
   if q.get('no_tracks') and layer in q['layers']:obs += [GP.bounded_buffer(s,.025+.000020) for s in C.poly(q['outline']) if s.intersects(query)]
  for q in reserved['rule_areas']:
   if layer in q['layers'] and RAW not in exempt.get(q['name'],set()):obs += [GP.bounded_buffer(s,.025+.000020) for s in C.poly(q['outline']) if s.intersects(query)]
  for t in peertracks:
   if t['layer']==layer and t['net']!=RAW:obs.append(GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(t['net'])+.025+.000020))
  for v in peervias:
   if v['net']!=RAW and layer in v['flashed']:obs.append(GP.bounded_disk(v,v['d']/2+gap(v['net'])+.025+.000020))
  return set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6)
 new=[];accepted=[];attempts=[];miss=[];originalpads={p['uuid']:p for p in h['pads']}
 for uid in wanted:
  if ('pad',uid) in prior:continue
  p=originalpads[uid];answer=None
  for layer in p['layers']:
   if layer not in source_shapes or source_shapes[layer].is_empty:continue
   target=unary_union(C.poly(p['layers'][layer]));aa,bb=nearest_points(target,source_shapes[layer]);distance=aa.distance(bb)
   if distance>45:attempts.append({'UUID':uid,'layer':layer,'nearest_source_gap_mm':distance,'reason':'outer_source_long_route_deferred_to_ordinary_dogbone'});continue
   for margin in (3.,8.,20.,45.):
    win=box(min(aa.x,bb.x)-margin,min(aa.y,bb.y)-margin,max(aa.x,bb.x)+margin,max(aa.y,bb.y)+margin);f=free(layer,win)
    for width in (.3,.25,.2):
     centers=f.buffer(-width/2-.000030).intersection(refs[layer].buffer(-width/2-.000030));valid=[]
     for part in polys(centers):
      a=part.intersection(target.buffer(-.000030));goal=part.intersection(source_shapes[layer].buffer(-.000030))
      if a.area<=.002 or goal.area<=.002:continue
      if get_num_coordinates(part)>6000:
       small=part.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(part);eligible=[q for q in polys(small) if q.intersects(a) and q.intersects(goal)]
       if not eligible:continue
       part=max(eligible,key=lambda q:q.area);a=a.intersection(part);goal=goal.intersection(part)
      if a.is_empty or goal.is_empty:continue
      start,end=nearest_points(a,goal);chord=LineString([start,end])
      if part.covers(chord):points=list(chord.coords);method='covered_chord'
      else:
       try:points,_=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]));method='regional_triangle_route'
       except (AssertionError,ValueError):continue
      points=[(round(x,6),round(y,6)) for x,y in points];points=[a for i,a in enumerate(points) if i==0 or a!=points[i-1]]
      if len(points)<2:continue
      body=GP.bounded_buffer(LineString(points),width/2)
      if not f.covers(body) or not body.difference(refs[layer]).is_empty:continue
      if body.intersection(target).area<=.002 or body.intersection(source_shapes[layer]).area<=.002:continue
      valid.append((LineString(points).length,points,method,body))
     if not valid:continue
     length,points,method,body=min(valid,key=lambda a:a[0]);nt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/remaining-IO3-r213/'+uid+'/'+layer+'/'+str(i))),'net':RAW,'layer':layer,'w':width,'a':list(a),'b':list(bb)} for i,(a,bb) in enumerate(zip(points,points[1:]))]
     trial=copy.deepcopy(c);trial['tracks']+=new+nt;gs=F.graph(trial,RAW);rrt=root(gs,'R18001','2');actual=keys(rrt)
     row={'pad_UUID':uid,'ref':p['ref'],'pin':p['num'],'layer':layer,'width_mm':width,'length_mm':length,'points_mm':points,'source_root':'R18001.2','all_prior_source_keys_lost':[list(k) for k in sorted(prior-actual)],'target_source_joined':('pad',uid) in actual,'literal_body_source_ground_reference_gap_mm2':body.difference(refs[layer]).area,'route_method':method,'current_per_pad_branch_unknown_NOT_DERATED':True};attempts.append(row)
     if prior-actual or ('pad',uid) not in actual:continue
     new+=nt;accepted.append(row);prior=actual;source_shapes={l:unary_union([q['shape'] for q in rrt if q['layer']==l]) for l in source_shapes};answer=row
     (O/'proposed-tracks.pkl').write_bytes(pickle.dumps(new,protocol=5));put(O/'checkpoint.json',{'accepted':accepted,'remaining_pad_UUIDs':[u for u in wanted if ('pad',u) not in prior],'native_jobs':0,'board_written':False});print('R213_IO3_SOURCE_ACCEPT',p['ref'],p['num'],layer,width,length,flush=True);break
    if answer:break
   if answer:break
  if not answer:miss.append({'UUID':uid,'ref':p['ref'],'pin':p['num'],'at_mm':[p['x'],p['y']],'no_ordinary_outer_solution_found_in_tested_faces':True,'ordinary_via_or_exact_contact_preserving_pose_correction_NEXT':True});print('R213_IO3_ORDINARY_OUTER_PENDING',p['ref'],p['num'],flush=True)
  put(O/'attempts.json',attempts)
 put(O/'receipt.json',{'verdict':'ORDINARY_OUTER_IO3_SOURCE_NOMINATIONS_FULL_CONTACT_NATIVE_CURRENT_GATES_REQUIRED','positive_R214_model_sha256':sha(mp),'accepted':accepted,'remaining':miss,'new_tracks':len(new),'new_holes':0,'no_original_discrete_or_source_changes':True,'actual_IO3_source_joined_new_pad_UUIDs':sorted({r['pad_UUID'] for r in accepted}),'literal_new_body_source_ground_reference_gaps_zero':all(r['literal_body_source_ground_reference_gap_mm2']==0 for r in accepted),'original_all_contact_foreign_fill_reference_retreat_native_current_PDN':'OPEN','native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R213_COMPLETE','accepted',len(accepted),'tracks',len(new),'remaining',len(miss),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__),'native_jobs':0,'board_written':False})
  raise
