"""Regional existing-annulus return routing with exact source-only projections.

The same authoritative declared-settings projector computes each source net.
Whole-board projections after each bank prove identical source zone fills and
contact membership; no partial graph is substituted for final global audits.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision,get_num_coordinates,from_wkb
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'sbc-power/major-rail-coupled-source-exit-feeds-r121';LAYERS=('In4.Cu','In2.Cu','In3.Cu','In1.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'2') for q in xs))
def pads(xs):return {q['uuid'] for q in xs if q['kind']=='pad' and q['pin']}
def main():
 assert len(sys.argv)==2
 specfile=Path(sys.argv[1]).resolve();spec=json.loads(specfile.read_bytes())
 mp=Path(spec['model_file']).resolve();mr=Path(spec['receipt_file']).resolve()
 assert sha(mp)==spec['model_sha256'] and sha(mr)==spec['receipt_sha256']
 r=json.loads(mr.read_bytes());assert r['model_sha256']==sha(mp)
 assert spec['all_later_actual_model_geometry_is_hard'] is True
 assert spec['no_native_or_source_adoption'] is True
 assert not OUT.exists();OUT.mkdir();old,h,binding,zones,current=pickle.loads(mp.read_bytes())
 cmask=H/'coupled-recovery/c10036-peer-reference-mask-r26.wkb';cbridge=H/'coupled-recovery/c10036-reference-bridge-r24.wkb'
 assert sha(cmask)=='c15b7bc932faf123137a73c2a7ea3020e78da2e6aca94fba8cd72f5ef51e5b55' and sha(cbridge)=='ac0c4fe08eb087e21da02ac85fc71b1212fc1ee3cad4c3864976a179c3ace65e'
 creserve=unary_union([from_wkb(cmask.read_bytes()),from_wkb(cbridge.read_bytes())]);craw='/motherboard_do{slash}FIELD_B_0V'
 # The exact frozen input supplies all actual later discrete and new-plane geometry.
 # There are no incremental holes or discrete items in this construction.
 peer_zones=[];hard_h={**h,'vias':list(h['vias']),'tracks':list(h['tracks'])};peer_bindings=[]
 for peer in spec.get('hard_only_peer_proposals',[]):
  qf=Path(peer['zones_file']);rf=Path(peer['receipt_file'])
  assert sha(qf)==peer['zones_sha256'] and sha(rf)==peer['receipt_sha256']
  if 'discrete_file' in peer:
   df=Path(peer['discrete_file']);assert sha(df)==peer['discrete_sha256'];ds=pickle.loads(df.read_bytes())
  else:ds={'vias':[],'tracks':[]};assert peer['new_holes']==0 and peer['new_tracks']==0
  qs=pickle.loads(qf.read_bytes());assert len(qs)==peer['expected_zone_shapes']
  peer_zones+=qs
  for kind in ('vias','tracks'):
   by={q['uuid']:q for q in hard_h[kind]}
   for q in ds[kind]:
    if q['uuid'] in by:assert q==by[q['uuid']]
    else:hard_h[kind].append(q)
  peer_bindings.append(peer)
 binding['major_rail_hard_only_later_foreign_proposals']=peer_bindings
 rec,trees=F.build({**hard_h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 via_by_id={v['uuid']:v for v in h['vias']};all_holes=[(p['net'],s) for p in h['pads'] for s in C.poly(p.get('hole') or [])]
 all_holes += [(v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64)) for v in hard_h['vias']]
 hole_tree=STRtree([s for raw,s in all_holes]);adds=[];rows=[];attempts=[];bank_proofs=[];carves=[]
 coupled_uid='c7e36847-4380-503d-80f2-836420105d9e';core_raw='/mc_local_power{slash}CORE_5V';core_net=C.norm(core_raw)
 escape=set_precision(box(233.212,91.61,239.212,97.61),1e-6)
 assert next(q for q in zones if q['uuid']==coupled_uid)['net']==core_raw
 def exact_source(model,net,ref,pin):
  import io3_contact_restore_r2 as Q
  Q.NET=net;gs,parts,assignment=Q.groups(model,return_details=True)
  rr=next(xs for xs in gs if any((r['ref'],r['pad'])==(ref,pin) for r in xs));return {r['uuid'] for r in rr},parts,assignment
 core_selected={**h,'zones':[q for q in h['zones'] if q['net']==core_raw]}
 core_baseline,_=N.projected(old,core_selected,zones)
 core_prior_exact,_,_=exact_source(core_baseline,core_net,'R11022','2')
 core_source_projection=core_baseline
 print('COUPLED_SOURCE_EXIT_BASELINE_CORE_EXACT_CONTACTS',len(core_prior_exact),flush=True)
 for net,ref in [('/CORE_1V2','L2001'),('/IO_3V3','R18001')]:
  initial=F.graph(current,net);rr=root(initial,ref);prior_root=pads(rr);raw=next(q['net'] for q in rr if q['kind']=='pad')
  assert {p['net'] for p in h['pads'] if C.norm(p['net'])==net}=={raw}
  ownholes=unary_union([s for rn,s in all_holes if rn==raw]);domain=h['domains_normalized'][net]
  def gap(other):return .15 if h['domains_normalized'][C.norm(other)]==domain else .6
  targets=[pads(xs) for xs in initial if xs is not rr and pads(xs)];legal_cache={};accepted_targets=[];source_projection=current
  def legal(layer,vid,radius):
   key=layer,vid,radius
   if key in legal_cache:return legal_cache[key]
   v=via_by_id[vid];window=box(v['x']-radius,v['y']-radius,v['x']+radius,v['y']+radius);search=window.buffer(1.5);obs=[]
   for i in trees[layer].query(search,predicate='intersects'):
    q=rec[layer][int(i)]
    if q['net']!=raw:
     clear=gap(q['net'])+.025+.000020
     if q['kind']=='track':
      t=q['source'];obs.append(N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear))
     elif q['kind']=='via':
      v=q['source'];obs.append(N.bounded_disk(v,v['d']/2+clear))
     else:obs.append(N.bounded_buffer(q['shape'],clear))
   for q in zones+adds+peer_zones:
    if q['layer']==layer and q['net']!=raw and search.intersects(q['shape']):
     obstruction=q['shape']
     if net=='/CORE_1V2' and layer=='In4.Cu' and q['uuid']==coupled_uid:obstruction=obstruction.difference(escape)
     obs.append(N.bounded_buffer(obstruction,max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))
   if layer=='In4.Cu' and raw!=craw and search.intersects(creserve):obs.append(N.bounded_buffer(creserve,max(.275,gap(craw)+.025+.000020)))
   for i in hole_tree.query(window.buffer(.3),predicate='intersects'):
    rn,s=all_holes[int(i)]
    if rn!=raw:obs.append(N.bounded_buffer(s,.275))
   for rule in h['rule_areas']:
    if rule.get('no_zones') and layer in rule['layers']:
     obs.extend(N.bounded_buffer(s,.025+.000020) for s in C.poly(rule['outline']) if search.intersects(s))
   result=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6);legal_cache[key]=result
   return result
  print('RETURN_BANK_START',net,'unrooted_groups',len(targets),flush=True)
  for target in targets:
   gs=F.graph(source_projection,net);rr=root(gs,ref);retained=pads(rr)
   if target<=retained:continue
   cluster=next(xs for xs in gs if pads(xs)&target);source={l:unary_union([q['shape'] for q in rr if q['layer']==l]).difference(ownholes) for l in LAYERS}
   ports={(q['uuid'],q['layer']) for q in cluster if q['kind']=='via' and q['layer'] in LAYERS};answer=None
   # Enumerate candidates lazily so the closest usable source port can be
   # routed before hundreds of unrelated legal faces are constructed.
   def choices_for_radius(radius):
    ranked=sorted(ports,key=lambda pair:((pair[1]!='In4.Cu') if net=='/CORE_1V2' else False,source[pair[1]].distance(Point(via_by_id[pair[0]]['x'],via_by_id[pair[0]]['y'])),pair[1],pair[0]))
    for vid,layer in ranked:
     if source[layer].is_empty:continue
     v=via_by_id[vid];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
     if not box(v['x']-radius,v['y']-radius,v['x']+radius,v['y']+radius).intersects(source[layer]):continue
     print('MAJOR_RAIL_LAZY_LEGAL',net,vid,layer,radius,flush=True)
     region=legal(layer,vid,radius)
     if not region.intersects(ann) or not region.intersects(source[layer]):continue
     for width in (1.25,1.,.8,.5,.35,.25,.20):
      for part in polys(region.buffer(-width/2-.005)):
       if not part.intersects(ann) or not part.intersects(source[layer]):continue
       inner=part.buffer(-.00002);aa=inner.intersection(ann);bb=inner.intersection(source[layer])
       if aa.area>1e-8 and bb.area>1e-8:yield aa.distance(bb),-width,vid,layer,part,aa,bb,region,ann
   for radius in (5.,15.,35.,75.,800.):
    for distance,negative_width,vid,layer,part,aa,bb,region,ann in choices_for_radius(radius):
     width=-negative_width
     if get_num_coordinates(part)>5000:
      simpler=part.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(part)
      eligible=[p for p in polys(simpler) if p.intersects(aa) and p.intersects(bb)]
      if not eligible:continue
      part=max(eligible,key=lambda p:p.area);aa=part.buffer(-.00002).intersection(aa);bb=part.buffer(-.00002).intersection(bb)
      if aa.area<=1e-8 or bb.area<=1e-8:continue
     print('MAJOR_RAIL_LAZY_PATH',net,vid,layer,radius,width,get_num_coordinates(part),flush=True)
     a,b=nearest_points(aa,bb);chord=LineString([a,b])
     if part.covers(chord):points=list(chord.coords);search={'method':'exact_covered_nearest_chord'}
     else:
      try:points,search=T.route(part,tuple(a.coords[0]),tuple(b.coords[0]))
      except (AssertionError,ValueError):continue
     points=[[round(x,6),round(y,6)] for x,y in points]
     if len(set(map(tuple,points)))<2:continue
     line=LineString(points);core=line.buffer(width/2,quad_segs=64)
     if not region.buffer(.000001).covers(core):continue
     native=set_precision(unary_union([p for p in polys(line.buffer(max(.6,width),quad_segs=64).intersection(region)) if p.intersection(core).area>1e-9]),1e-6);physical=set_precision(native.difference(ownholes),1e-6)
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-major-rail-coupled-source-exit-r121/'+net+'/'+vid+'/'+layer+'/'+str(len(adds))))
     z={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':native,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':'Major rail coupled bounded owned source exit R121'}
     zz,guard=N.normalize_owned_via_guards(hard_h,[z]);z=zz[0]
     import owned_analytic_track_guards_r75 as AT
     import owned_native_pad_guards_r98 as AP
     zz,track_guard,_=AT.normalize_owned_track_guards(hard_h,[z]);z=zz[0]
     zz,pad_guard,_=AP.normalize_owned_pad_guards(h,[z]);z=zz[0]
     if z['shape'].intersection(ann).area<.01 or z['shape'].intersection(source[layer]).area<.01:continue
     # Identical projector, original source-zone inputs and all foreign new
     # cutters. Only irrelevant original non-source nets are omitted here.
     proposed_base=list(zones);carve=None
     if net=='/CORE_1V2' and layer=='In4.Cu':
      oldq=next(q for q in zones if q['uuid']==coupled_uid)
      distance=max(gap(core_raw),float(oldq.get('clearance_mm',.15)),float(z.get('clearance_mm',.15)))+.025+.000020
      cutter=N.bounded_buffer(z['shape'],distance)
      removed=oldq['shape'].intersection(cutter)
      if not removed.is_empty:
       # A bounded source exit can alter this one NEW owned plane only.
       if not escape.covers(removed):continue
       before=oldq['shape'];before_outline=oldq.get('zone_outline_shape',before)
       after=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);after_outline=set_precision(set_precision(before_outline,1e-6).difference(cutter),1e-6)
       if after.is_empty or not escape.covers(before_outline.difference(after_outline)):continue
       newq={**oldq,'shape':after,'zone_outline_shape':after_outline,'precarve_route_minimum_cross_section_and_current_must_be_requalified':True}
       proposed_base=[newq if q['uuid']==coupled_uid else q for q in zones]
       carve={'zone_UUID':coupled_uid,'raw_net':core_raw,'layer':layer,'physical_before_SHA256':N.digest(before),'physical_after_SHA256':N.digest(after),'outline_before_SHA256':N.digest(before_outline),'outline_after_SHA256':N.digest(after_outline),'physical_removed_mm2':before.difference(after).area,'physical_quantization_added_mm2':after.difference(before).area,'outline_removed_mm2':before_outline.difference(after_outline).area,'outline_quantization_added_mm2':after_outline.difference(before_outline).area,'bounded_exit_scope_WKB_SHA256':N.digest(escape),'exact_outward_cutter_WKB_SHA256':N.digest(cutter),'original_native_zone_definitions_unchanged':True}
     selected={**h,'zones':[q for q in h['zones'] if q['net']==raw]}
     trial,retreat=N.projected(old,selected,proposed_base+adds+[z]);joined=pads(root(F.graph(trial,net),ref))
     record={'target_pad_UUIDs':sorted(target),'landing_via':vid,'layer':layer,'window_radius_mm':radius,'length_mm':line.length,'minimum_core_width_mm':width,'points_mm':points,'shape_uuid':uid,'actual_source_projection_target_joined':target<=joined,'prior_root_retained':retained<=joined,'source_overlap_mm2':z['shape'].intersection(source[layer]).area,'target_annular_overlap_mm2':z['shape'].intersection(ann).area,'search':search,'outward_via_guards':guard,'outward_track_guards':track_guard,'outward_pad_guards_with_explicit_20nm_construction_reserve':pad_guard,'bounded_new_owned_CORE_source_exit_carve':carve};attempts.append(record)
     if not target<=joined or not retained<=joined:continue
     exact_joined,_,_=exact_source(trial,net,ref,'2')
     if not target<=exact_joined or not retained<=exact_joined:record['exact_integer_source_gate']='FAIL';continue
     core_trial,_=N.projected(old,core_selected,proposed_base+adds+[z])
     core_exact,core_parts,core_assignment=exact_source(core_trial,core_net,'R11022','2')
     if not core_prior_exact<=core_exact:record['CORE_source_contacts_lost']=sorted(core_prior_exact-core_exact);continue
     # Each component of every retained/new CORE proposal must remain rooted,
     # including pad-free pieces after the owned notch.
     import io3_contact_restore_r2 as Q
     Q.NET=core_net;core_groups,core_parts,core_assignment=Q.groups(core_trial,return_details=True)
     core_root_index=next(i for i,xs in enumerate(core_groups) if any((r['ref'],r['pad'])==('R11022','2') for r in xs))
     floating=[]
     for cq in proposed_base+adds:
      if C.norm(cq['net'])!=core_net:continue
      for part in polys(cq['shape']):
       hits={a for piece,a in zip(core_parts[cq['layer']],core_assignment[cq['layer']]) if piece.intersection(part).area>0}
       if hits!={core_root_index}:floating.append({'UUID':cq['uuid'],'area_mm2':part.area,'groups':list(hits)})
     if floating:record['CORE_detached_new_components']=floating;continue
     record['exact_integer_source_gate']='PASS';record['all_prior_CORE_exact_pad_track_via_contacts_source_retained']=True
     if carve:
      folder=OUT/('accepted-carve-'+str(len(carves)+1));folder.mkdir()
      for label,sh in [('physical-before',before),('physical-after',after),('outline-before',before_outline),('outline-after',after_outline),('cutter',cutter),('bounded-exit-scope',escape)]:
       file=folder/(label+'.wkb');file.write_bytes(sh.wkb)
      write(folder/'ledger.json',carve);carves.append(carve)
     zones=proposed_base;adds.append(z);source_projection=trial;core_source_projection=core_trial;accepted_targets.append(target);answer=record;legal_cache.clear()
     snapshot=OUT/('accepted-positive-snapshot-'+str(len(adds)));snapshot.mkdir();(snapshot/'new-feed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5));(snapshot/'all-owned-zones-with-carves.pkl').write_bytes(pickle.dumps(zones+adds,protocol=5));write(snapshot/'receipt.json',{'verdict':'EXACT_INTEGER_1V2_AND_CORE_SOURCE_CONTACT_CONSTRUCTION_NATIVE_CURRENT_FOREIGN_GATES_OPEN','row':record,'new_feed_zones_sha256':sha(snapshot/'new-feed-zones.pkl'),'all_owned_zones_with_carves_sha256':sha(snapshot/'all-owned-zones-with-carves.pkl'),'prospective_source_extra_flash_requires_native_refill':True,'native_jobs':0,'board_written':False})
     print('COUPLED_MAJOR_RAIL_ROOTED',net,vid,layer,line.length,width,'exact COREcontacts',len(core_exact),flush=True);break
    if answer:break
   rows.append({'net':net,'target_pad_UUIDs':sorted(target),'existing_via_ports':len(ports),'repair':answer});write(OUT/'checkpoint.json',{'rows':rows,'attempted':attempts,'complete':False});(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
  current,full_retreat=N.projected(old,h,zones+adds);fullroot=pads(root(F.graph(current,net),ref))
  core_source_zones={q['uuid']:(q['net'],q['fills']) for q in core_source_projection['zones'] if q['net']==core_raw};core_full_zones={q['uuid']:(q['net'],q['fills']) for q in current['zones'] if q['net']==core_raw};assert core_source_zones==core_full_zones,'CORE source-only and full projection disagree'
  source_zones={q['uuid']:(q['net'],q['fills']) for q in source_projection['zones'] if q['net']==raw};full_zones={q['uuid']:(q['net'],q['fills']) for q in current['zones'] if q['net']==raw}
  assert source_zones==full_zones,'Source-only projector differs from whole-board source fills'
  assert prior_root<=fullroot and all(t<=fullroot for t in accepted_targets),'Accepted return loses source in full projection'
  proof={'net':net,'same_original_source_and_owned_source_zone_fills_in_wholeboard_projection':True,'all_accepted_target_and_prior_root_pad_source_contacts_retained':True,'source_rooted_named_pads':len(fullroot),'full_projection_retreats':full_retreat};bank_proofs.append(proof)
  write(OUT/'bank-proofs.json',bank_proofs);print('RETURN_BANK_COMPLETE',net,len(fullroot),flush=True)
 model=OUT/'model.pkl';model.write_bytes(pickle.dumps((old,h,binding,zones+adds,current),protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
 write(OUT/'receipt.json',{'verdict':'MAJOR_RAIL_LAZY_EXISTING_ANNULUS_FEEDS_SOURCE_PROJECTION_MATCHED_MUTUAL_EXACT_CONTACT_NATIVE_CURRENT_PENDING','baseline_model_sha256':sha(mp),'baseline_receipt_sha256':sha(mr),'model_sha256':sha(model),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_zone_shapes':len(adds),'input_binding_file':str(specfile),'input_binding_sha256':sha(specfile),'full_fitted_CORE1V2_load_A':.8,'IO3_full_fitted_output_envelope_A':2.,'geometry_width_does_not_grant_current_or_sharing':True,'explicit_source_layer_hypothesis_requires_native_flash_refill_and_full_foreign_contact_proof':True,'hard_only_peer_proposals':peer_bindings,'explicit_bounded_new_CORE_carve_ledger':carves,'fast_graph_2nm_intersection_tolerance_requires_independent_exact_integer_contact_gate':True,'new_holes':0,'old_Cu_deleted':0,'old_native_zone_outlines_changed':0,'rows':rows,'bank_source_proofs':bank_proofs,'attempts':attempts,'finite_construction_failure_is_not_proof_of_no_path':True,'C10036_peer_reference_reserved_mask_sha256':sha(cmask),'C10036_exact_bridge_reserved_sha256':sha(cbridge),'wholeboard_retained_other_net_contacts_current_native_refill_DRC':'OPEN','script_sha256':sha(Path(__file__)),'board_written':False,'native_jobs':0,'adopted':False});print('MAJOR_RAIL_COUPLED_SOURCE_R121_FROZEN',sha(model),len(adds),flush=True)
if __name__=='__main__':main()
