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
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'CORE-existing-In3-source-feed-r84';LAYERS=('In3.Cu',)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'2') for q in xs))
def pads(xs):return {q['uuid'] for q in xs if q['kind']=='pad' and q['pin']}
def main():
 assert len(sys.argv)==2
 mp=Path(sys.argv[1]).resolve();mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes())
 assert sha(mp)==r['model_sha256']=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c' and sha(mr)=='ec4a2744f502fc250ecf5f5e0e04c6e043dd7b5b1fe916419231163e4aafaf33'
 assert not OUT.exists();OUT.mkdir();old,h,binding,zones,current=pickle.loads(mp.read_bytes());import restore_SAFE_generated_precision_states_r168 as PS;assert sha(PS.__file__)=='88e352a26ee60e62f2d50d7d7c8bb2ed9cdbd1b4786a6818c6c8354676b90e54';precision_replay=PS.restore_bound_generated_precision_states(binding,zones);write(OUT/'exact-parent-generated-precision-state-replay.json',precision_replay)
 cmask=H/'coupled-recovery/c10036-peer-reference-mask-r26.wkb';cbridge=H/'coupled-recovery/c10036-reference-bridge-r24.wkb'
 assert sha(cmask)=='c15b7bc932faf123137a73c2a7ea3020e78da2e6aca94fba8cd72f5ef51e5b55' and sha(cbridge)=='ac0c4fe08eb087e21da02ac85fc71b1212fc1ee3cad4c3864976a179c3ace65e'
 creserve=unary_union([from_wkb(cmask.read_bytes()),from_wkb(cbridge.read_bytes())]);craw='/motherboard_do{slash}FIELD_B_0V'
 # R69 already contains the full outward guarded projection, pinned above.
 # There are no incremental holes or discrete items in this construction.
 iofile=H/'sbc-power/original-IO3-r172-positive-snapshot-8/proposed-zones.pkl';assert sha(iofile)=='d576613bad70e94d04e47822b0b7c42f30e7f1a72e91d4a4a9cf1f8335eac16c';iohard=pickle.loads(iofile.read_bytes())
 fieldpacket=H/'field-power/SAFE-U10017-wider-native-owned-recipe-r183';assert sha(fieldpacket/'receipt.json')=='00c4e035dc2f95f6a4e5560ec00d1393763b4386cfead6e1a104af1bdbaf123d';fr=json.loads((fieldpacket/'receipt.json').read_bytes());fpq=fieldpacket/'new-owned-zones.pkl';fpd=fieldpacket/'proposed-discrete.pkl';assert sha(fpq)==fr['new_owned_zones_sha256']and sha(fpd)==fr['proposed_discrete_sha256'];peerq=pickle.loads(fpq.read_bytes());peerd=pickle.loads(fpd.read_bytes());assert len(peerq)==1 and peerq[0]['uuid']=='e8ec0287-e6d1-597d-8ad8-c4ab74280f6c';iohard+=peerq
 assert {q['uuid']for q in peerd['tracks']}<={q['uuid']for q in h['tracks']}and {q['uuid']for q in peerd['vias']}<={q['uuid']for q in h['vias']};hard_h=h
 # Exact current R214/R201 canonical IO3 groups in zones are authoritative. Do not re-harden superseded R172 thin previews.
 assert any(q['uuid']=='ba9d5c62-8882-505e-a190-2a1ba940719b'and q['layer']=='In3.Cu'and q['net']=='/IO_3V3'for q in zones);iohard=[];write(OUT/'positive-U10017-peer-hard-binding.json',{'receipt_sha256':sha(fieldpacket/'receipt.json'),'prospective_plane_and_all_discretes_hard_only_not_appended_to_source_model':True})
 rec,trees=F.build({**hard_h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 via_by_id={v['uuid']:v for v in h['vias']};all_holes=[(p['net'],s) for p in h['pads'] for s in C.poly(p.get('hole') or [])]
 all_holes += [(v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64)) for v in hard_h['vias']]
 hole_tree=STRtree([s for raw,s in all_holes]);adds=[];rows=[];attempts=[];bank_proofs=[]
 for net,ref in [('/CORE_1V2','L2001')]:
  initial=F.graph(current,net);rr=root(initial,ref);prior_root=pads(rr);raw=next(q['net'] for q in rr if q['kind']=='pad')
  assert {p['net'] for p in h['pads'] if C.norm(p['net'])==net}=={raw}
  ownholes=unary_union([s for rn,s in all_holes if rn==raw]);domain=h['domains_normalized'][net]
  def gap(other):return .15 if h['domains_normalized'][C.norm(other)]==domain else .6
  targets=[pads(xs) for xs in initial if xs is not rr and any(q['kind']=='pad' and q['ref']=='U1001' for q in xs)];assert len(targets)==1 and len(targets[0])==21;foreign_roots=[root(F.graph(current,n),r)for n,r in [('/motherboard_do/FIELD_B_0V','J11005'),('/motherboard_motors/FIELD_GND','J11003')]];foreign_return={l:unary_union([q['shape']for rs in foreign_roots for q in rs if q['layer']==l])for l in LAYERS};logic_root=root(F.graph(current,'/LOGIC_GND'),'J11001');logic_reference={l:unary_union([q['shape']for q in logic_root if q['kind']=='fill'and q['layer']==l])for l in ('In1.Cu','In4.Cu')};legal_cache={};accepted_targets=[];source_projection=current;groups_cache=initial;source_cache=None
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
   for q in zones+adds+iohard:
    if q['layer']==layer and q['net']!=raw and not(layer=='In3.Cu'and q['uuid']=='47888e35-9a96-5393-b579-7c0b4a64ec93'and C.norm(q['net'])=='/LOGIC_GND')and search.intersects(q['shape']):obs.append(N.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))
   if layer=='In4.Cu' and raw!=craw and search.intersects(creserve):obs.append(N.bounded_buffer(creserve,max(.275,gap(craw)+.025+.000020)))
   for i in hole_tree.query(window.buffer(.3),predicate='intersects'):
    rn,s=all_holes[int(i)]
    if rn!=raw:obs.append(N.bounded_buffer(s,.275))
   for rule in h['rule_areas']:
    if rule.get('no_zones') and layer in rule['layers']:
     obs.extend(N.bounded_buffer(s,.025+.000020) for s in C.poly(rule['outline']) if search.intersects(s))
   if not foreign_return[layer].is_empty and search.intersects(foreign_return[layer]):obs.append(N.bounded_buffer(foreign_return[layer],.625+.000020))
   if layer in logic_reference and search.intersects(logic_reference[layer]):obs.append(N.bounded_buffer(logic_reference[layer],.175+.000020))
   result=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6);legal_cache[key]=result
   return result
  print('RETURN_BANK_START',net,'unrooted_groups',len(targets),flush=True)
  for target in targets:
   gs=groups_cache;rr=root(gs,ref);retained=pads(rr)
   if target<=retained:continue
   cluster=next(xs for xs in gs if pads(xs)&target)
   prefixes={v['uuid'].split('-')[0]for v in h['vias']if C.norm(v['net'])==net}
   ports={(q['uuid'],q['layer']) for q in cluster if q['kind']=='via' and q['layer'] in LAYERS and q['uuid'].split('-')[0]in prefixes};answer=None
   if not ports:
    rows.append({'net':net,'target_pad_UUIDs':sorted(target),'existing_via_ports':0,'repair':None,'ordinary_bare_pad_feed_required':True})
    write(OUT/'checkpoint.json',{'rows':rows,'attempted':attempts,'complete':False});(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    continue
   if source_cache is None:source_cache={l:unary_union([q['shape']for q in rr if q['layer']==l]).difference(ownholes)for l in LAYERS}
   source=source_cache
   # Enumerate candidates lazily so the closest usable source port can be
   # routed before hundreds of unrelated legal faces are constructed.
   def choices_for_radius(radius):
    ranked=sorted(ports,key=lambda pair:(source[pair[1]].distance(Point(via_by_id[pair[0]]['x'],via_by_id[pair[0]]['y'])),pair[1],pair[0]))
    for vid,layer in ranked:
     v=via_by_id[vid];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
     if not box(v['x']-radius,v['y']-radius,v['x']+radius,v['y']+radius).intersects(source[layer]):continue
     region=legal(layer,vid,radius)
     if not region.intersects(ann) or not region.intersects(source[layer]):continue
     for width in (4.,3.,2.,1.,.5,.35,.25):
      for part in polys(region.buffer(-width/2-.005)):
       if not part.intersects(ann) or not part.intersects(source[layer]):continue
       inner=part.buffer(-.00002);aa=inner.intersection(ann);bb=inner.intersection(source[layer])
       if aa.area>1e-8 and bb.area>1e-8:yield aa.distance(bb),-width,vid,layer,part,aa,bb,region,ann
   for radius in (5.,15.,35.,75.):
    for distance,negative_width,vid,layer,part,aa,bb,region,ann in choices_for_radius(radius):
     width=-negative_width
     if get_num_coordinates(part)>5000:
      simpler=part.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(part)
      eligible=[p for p in polys(simpler) if p.intersects(aa) and p.intersects(bb)]
      if not eligible:continue
      part=max(eligible,key=lambda p:p.area);aa=part.buffer(-.00002).intersection(aa);bb=part.buffer(-.00002).intersection(bb)
      if aa.area<=1e-8 or bb.area<=1e-8:continue
     print('CORE_LAZY_PATH',vid,layer,radius,width,get_num_coordinates(part),flush=True)
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
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-SAFE-CORE-reference-feed-r84/'+net+'/'+vid+'/'+layer+'/'+str(len(adds))))
     z={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':native,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':'CORE source feed around restored old-ground references R80'}
     zz,guard=N.normalize_owned_via_guards(h,[z]);z=zz[0]
     if z['shape'].intersection(ann).area<.01 or z['shape'].intersection(source[layer]).area<.01:continue
     # Identical projector, original source-zone inputs and all foreign new
     # cutters. Only irrelevant original non-source nets are omitted here.
     # No foreign cutter or h geometry changed. Original source-zone fills
     # from the current full GP58 projection are immutable within this bank.
     # Append exactly GP58's owned-source-row representation; prove equality
     # to a fresh ALL-net full GP58 projection again at bank completion.
     newrow=N.projected(old,{**h,'zones':[]},[z])[0]['zones']
     trial={**h,'zones':[q for q in source_projection['zones']if q['net']==raw]+newrow}
     trial_groups=F.graph(trial,net);joined=pads(root(trial_groups,ref))
     record={'target_pad_UUIDs':sorted(target),'landing_via':vid,'layer':layer,'window_radius_mm':radius,'length_mm':line.length,'minimum_core_width_mm':width,'points_mm':points,'shape_uuid':uid,'actual_source_projection_target_joined':target<=joined,'prior_root_retained':retained<=joined,'source_overlap_mm2':z['shape'].intersection(source[layer]).area,'target_annular_overlap_mm2':z['shape'].intersection(ann).area,'search':search,'outward_via_guards':guard};attempts.append(record)
     if not target<=joined or not retained<=joined:continue
     adds.append(z);source_projection=trial;groups_cache=trial_groups;source_cache=None;accepted_targets.append(target);answer=record;print('RETURN_ROOTED',net,vid,layer,line.length,width,flush=True);break
    if answer:break
   rows.append({'net':net,'target_pad_UUIDs':sorted(target),'existing_via_ports':len(ports),'repair':answer});write(OUT/'checkpoint.json',{'rows':rows,'attempted':attempts,'complete':False});(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
  cut_rows=[]
  if adds:
   cutter=unary_union([N.bounded_buffer(q['shape'],.175+.000020)for q in adds if q['layer']=='In3.Cu'])
   changed=[]
   for q in zones:
    if q['uuid']!='47888e35-9a96-5393-b579-7c0b4a64ec93':changed.append(q);continue
    assert q['layer']=='In3.Cu'and C.norm(q['net'])=='/LOGIC_GND'and float(q.get('clearance_mm',.15))==.15
    n=copy.deepcopy(q);n['shape']=q['shape'].difference(cutter);n['zone_outline_shape']=q['zone_outline_shape'].difference(cutter)
    assert n['shape'].difference(q['shape']).is_empty and n['zone_outline_shape'].difference(q['zone_outline_shape']).is_empty and not n['shape'].is_empty
    cut_rows.append({'UUID':q['uuid'],'only_new_owned_ground_plane_remove_only':True,'before_physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'after_physical_WKB_sha256':hashlib.sha256(n['shape'].wkb).hexdigest(),'removed_mm2':q['shape'].difference(n['shape']).area,'added_mm2':0.,'outward_CORE_supply_Cu_guard_mm':.175+.000020,'all_native_original_zone_outlines_and_old_Cu_unchanged':True});changed.append(n)
   assert len(cut_rows)==1;zones=changed
  write(OUT/'bounded-new-owned-In3-ground-remove-only-ledger.json',cut_rows)
  current,full_retreat=N.projected(old,h,zones+adds);fullroot=pads(root(F.graph(current,net),ref))
  source_zones={q['uuid']:(q['net'],q['fills']) for q in source_projection['zones'] if q['net']==raw};full_zones={q['uuid']:(q['net'],q['fills']) for q in current['zones'] if q['net']==raw}
  assert source_zones==full_zones,'Source-only projector differs from whole-board source fills'
  assert prior_root<=fullroot and all(t<=fullroot for t in accepted_targets),'Accepted return loses source in full projection'
  proof={'net':net,'same_original_source_and_owned_source_zone_fills_in_wholeboard_projection':True,'all_accepted_target_and_prior_root_pad_source_contacts_retained':True,'source_rooted_named_pads':len(fullroot),'full_projection_retreats':full_retreat};bank_proofs.append(proof)
  write(OUT/'bank-proofs.json',bank_proofs);print('RETURN_BANK_COMPLETE',net,len(fullroot),flush=True)
 ground_sources=[]
 for gn,ref in[('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/IO_3V3','R18001'),('/mc_local_power/CORE_5V','R11022')]:
  prior=root(F.graph(pickle.loads(mp.read_bytes())[4],gn),ref);after=root(F.graph(current,gn),ref);lost=F.discrete_keys(prior)-F.discrete_keys(after);ground_sources.append({'net':gn,'actual_source':ref+'.2','prior_source_keys_lost':[list(k)for k in sorted(lost)],'named_source_pads':len(pads(after))});write(OUT/'all3-ground-source-checkpoint.json',ground_sources);print('R84_GROUND_SOURCE',gn,len(lost),len(pads(after)),flush=True)
 model=OUT/'model.pkl';model.write_bytes(pickle.dumps((old,h,binding,zones+adds,current),protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
 write(OUT/'receipt.json',{'verdict':'EXISTING_ANNULUS_RETURN_RESTORATION_SOURCE_PROJECTION_MATCHED_MUTUAL_NATIVE_CURRENT_PENDING','baseline_model_sha256':sha(mp),'baseline_receipt_sha256':sha(mr),'model_sha256':sha(model),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_zone_shapes':len(adds),'only_one_new_owned_LG_In3_bounded_remove_only_ledger_sha256':sha(OUT/'bounded-new-owned-In3-ground-remove-only-ledger.json'),'prior_ground_source_checks':ground_sources,'all76_contacts_truegeometry_oldreferences_extraIn2_native_current_stability':'OPEN','host_retention_and_adoption_flags_NOT_GRANTED':True,'generated_precision_ledger_after_new_geometry_requires_exact_rebind':True,'new_holes':0,'old_Cu_deleted':0,'old_native_zone_outlines_changed':0,'rows':rows,'bank_source_proofs':bank_proofs,'attempts':attempts,'finite_construction_failure_is_not_proof_of_no_path':True,'C10036_peer_reference_reserved_mask_sha256':sha(cmask),'C10036_exact_bridge_reserved_sha256':sha(cbridge),'wholeboard_retained_other_net_contacts_current_native_refill_DRC':'OPEN','script_sha256':sha(Path(__file__)),'board_written':False,'native_jobs':0,'adopted':False});print('CORE_REFERENCE_FEED_FROZEN',sha(model),len(adds),flush=True)
if __name__=='__main__':main()
