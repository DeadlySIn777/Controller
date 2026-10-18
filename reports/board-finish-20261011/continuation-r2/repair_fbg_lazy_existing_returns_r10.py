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
OUT=H/'fbg-lazy-existing-return-restoration-r10';LAYERS=('In4.Cu','In2.Cu','In3.Cu','In1.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad' and (q['ref'],q['pin'])==(ref,'2') for q in xs))
def pads(xs):return {q['uuid'] for q in xs if q['kind']=='pad' and q['pin']}
def main():
 assert len(sys.argv)==2
 mp=Path(sys.argv[1]).resolve();mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes())
 assert sha(mp)==r['model_sha256'] and r['CORE_r91_explicit_option'] is True
 assert r['base_CORE_model_sha256']=='1bb0d52095c4f2ad003d0c5934d8e7fca7174c8936af19ae0bbed66021003e09'
 assert r['root_four_spines_sha256']=='213182e7ec8439cccb0087bf99b362e6e149a3f21843d103b7b50ddceb428239'
 assert r['exact_C_native_owned_ledger_sha256']=='017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb'
 assert r['C10036_pad_source_rooted'] and r['both_new_C_return_vias_source_rooted']
 assert r['U19008_delta_included'] is False and r['REG_delta_included'] is False
 assert not OUT.exists();OUT.mkdir();old,h,binding,zones,current=pickle.loads(mp.read_bytes())
 cmask=H/'coupled-recovery/c10036-peer-reference-mask-r26.wkb';cbridge=H/'coupled-recovery/c10036-reference-bridge-r24.wkb'
 assert sha(cmask)=='c15b7bc932faf123137a73c2a7ea3020e78da2e6aca94fba8cd72f5ef51e5b55' and sha(cbridge)=='ac0c4fe08eb087e21da02ac85fc71b1212fc1ee3cad4c3864976a179c3ace65e'
 creserve=unary_union([from_wkb(cmask.read_bytes()),from_wkb(cbridge.read_bytes())]);craw='/motherboard_do{slash}FIELD_B_0V'
 # R69 already contains the full outward guarded projection, pinned above.
 # There are no incremental holes or discrete items in this construction.
 rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 via_by_id={v['uuid']:v for v in h['vias']};all_holes=[(p['net'],s) for p in h['pads'] for s in C.poly(p.get('hole') or [])]
 all_holes += [(v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64)) for v in h['vias']]
 hole_tree=STRtree([s for raw,s in all_holes]);adds=[];rows=[];attempts=[];bank_proofs=[]
 for net,ref in [('/motherboard_do/FIELD_B_0V','J11005')]:
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
   for q in zones+adds:
    if q['layer']==layer and q['net']!=raw and search.intersects(q['shape']):obs.append(N.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))
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
    ranked=sorted(ports,key=lambda pair:(source[pair[1]].distance(Point(via_by_id[pair[0]]['x'],via_by_id[pair[0]]['y'])),pair[1],pair[0]))
    for vid,layer in ranked:
     v=via_by_id[vid];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
     if not box(v['x']-radius,v['y']-radius,v['x']+radius,v['y']+radius).intersects(source[layer]):continue
     region=legal(layer,vid,radius)
     if not region.intersects(ann) or not region.intersects(source[layer]):continue
     for width in (1.,.5,.35,.25):
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
     print('FBG_LAZY_PATH',vid,layer,radius,width,get_num_coordinates(part),flush=True)
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
     uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-fbg-existing-return-r10/'+net+'/'+vid+'/'+layer+'/'+str(len(adds))))
     z={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':native,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':'Field B existing-annulus return continuation R10'}
     zz,guard=N.normalize_owned_via_guards(h,[z]);z=zz[0]
     if z['shape'].intersection(ann).area<.01 or z['shape'].intersection(source[layer]).area<.01:continue
     # Identical projector, original source-zone inputs and all foreign new
     # cutters. Only irrelevant original non-source nets are omitted here.
     selected={**h,'zones':[q for q in h['zones'] if q['net']==raw]}
     trial,retreat=N.projected(old,selected,zones+adds+[z]);joined=pads(root(F.graph(trial,net),ref))
     record={'target_pad_UUIDs':sorted(target),'landing_via':vid,'layer':layer,'window_radius_mm':radius,'length_mm':line.length,'minimum_core_width_mm':width,'points_mm':points,'shape_uuid':uid,'actual_source_projection_target_joined':target<=joined,'prior_root_retained':retained<=joined,'source_overlap_mm2':z['shape'].intersection(source[layer]).area,'target_annular_overlap_mm2':z['shape'].intersection(ann).area,'search':search,'outward_via_guards':guard};attempts.append(record)
     if not target<=joined or not retained<=joined:continue
     adds.append(z);source_projection=trial;accepted_targets.append(target);answer=record;print('RETURN_ROOTED',net,vid,layer,line.length,width,flush=True);break
    if answer:break
   rows.append({'net':net,'target_pad_UUIDs':sorted(target),'existing_via_ports':len(ports),'repair':answer});write(OUT/'checkpoint.json',{'rows':rows,'attempted':attempts,'complete':False});(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
  current,full_retreat=N.projected(old,h,zones+adds);fullroot=pads(root(F.graph(current,net),ref))
  source_zones={q['uuid']:(q['net'],q['fills']) for q in source_projection['zones'] if q['net']==raw};full_zones={q['uuid']:(q['net'],q['fills']) for q in current['zones'] if q['net']==raw}
  assert source_zones==full_zones,'Source-only projector differs from whole-board source fills'
  assert prior_root<=fullroot and all(t<=fullroot for t in accepted_targets),'Accepted return loses source in full projection'
  proof={'net':net,'same_original_source_and_owned_source_zone_fills_in_wholeboard_projection':True,'all_accepted_target_and_prior_root_pad_source_contacts_retained':True,'source_rooted_named_pads':len(fullroot),'full_projection_retreats':full_retreat};bank_proofs.append(proof)
  write(OUT/'bank-proofs.json',bank_proofs);print('RETURN_BANK_COMPLETE',net,len(fullroot),flush=True)
 model=OUT/'model.pkl';model.write_bytes(pickle.dumps((old,h,binding,zones+adds,current),protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
 write(OUT/'receipt.json',{'verdict':'EXISTING_ANNULUS_RETURN_RESTORATION_SOURCE_PROJECTION_MATCHED_MUTUAL_NATIVE_CURRENT_PENDING','baseline_model_sha256':sha(mp),'baseline_receipt_sha256':sha(mr),'model_sha256':sha(model),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_zone_shapes':len(adds),'new_holes':0,'old_Cu_deleted':0,'old_native_zone_outlines_changed':0,'rows':rows,'bank_source_proofs':bank_proofs,'attempts':attempts,'finite_construction_failure_is_not_proof_of_no_path':True,'C10036_peer_reference_reserved_mask_sha256':sha(cmask),'C10036_exact_bridge_reserved_sha256':sha(cbridge),'wholeboard_retained_other_net_contacts_current_native_refill_DRC':'OPEN','script_sha256':sha(Path(__file__)),'board_written':False,'native_jobs':0,'adopted':False});print('FBG_RETURN_R10_FROZEN',sha(model),len(adds),flush=True)
if __name__=='__main__':main()
