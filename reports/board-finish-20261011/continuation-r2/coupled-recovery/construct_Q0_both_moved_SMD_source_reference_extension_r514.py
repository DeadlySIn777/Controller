"""Nominate a finite actual J3-rooted In1 extension under BOTH moved pads.

No new holes, old copper/outline/filled-array edits or blanket ground credit.
Current foreign discrete/filled/owned copper and native no_zones remain hard.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,uuid
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import tri_route as T
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def arrays(sh):return [[list(s.exterior.coords),[list(r.coords)for r in s.interiors]]for s in K.RF.parts(sh)]
out=H/'Q0-both-moved-SMD-source-reference-extension-r514';assert not out.exists();out.mkdir();start=time.monotonic();mp=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl';assert sha(mp)=='f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a';g,h,b,q,current=pickle.loads(mp.read_bytes());ad=H/'Q0-R504-explicit-final-current-r506';assert sha(ad/'receipt.json')=='8eeddecee7280d2e881282eca828c3e2a209a82c89601e38bfc61fd82c88f38a';bf=ad/'actual-before-and-after-source-banks.pkl';assert sha(bf)=='b316c1eeef6b5883f13aa2b698646c4111e58a09c0a484835135c9bf963c8362';banks=pickle.loads(bf.read_bytes());GND='/motherboard_motors/FIELD_GND';layer='In1.Cu';root=banks['after'][GND];sourceplane=unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==layer]);pads=[p for p in h['pads']if p['ref']=='R10016'];assert len(pads)==2;target=unary_union([s for p in pads for s in K.L.poly(p['layers']['F.Cu'])]);dom=h['domains_normalized'];gap=lambda net:.15 if dom.get(K.L.norm(net))==dom[GND]else .6;window=box(226,163,236,171);obstacles=[];obrows=[]
records,trees=K.F.build({**h,'zones':[]})
for i in trees[layer].query(window.buffer(1),predicate='intersects'):
 r=records[layer][int(i)]
 if K.L.norm(r['net'])==GND:continue
 rad=max(.25,gap(r['net']))+.025;mask=K.Z.bounded_buffer(r['shape'],rad);obstacles.append(mask);obrows.append({'kind':'exact_current_foreign_native_discrete_'+r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'radius_mm':rad,'mask_WKB_sha256':K.C.sha(mask.wkb),'target_intersection_mm2':mask.intersection(target).area})
for z in q:
 if z['layer']!=layer or K.L.norm(z['net'])==GND or z['shape'].distance(window)>1:continue
 rad=max(.25,float(z['clearance_mm']),gap(z['net']))+.025;mask=K.Z.bounded_buffer(z['shape'],rad);obstacles.append(mask);obrows.append({'kind':'exact_current_foreign_owned_role','UUID':z['uuid'],'raw_net':z['net'],'radius_mm':rad,'mask_WKB_sha256':K.C.sha(mask.wkb),'target_intersection_mm2':mask.intersection(target).area})
for z in current['zones']:
 if K.L.norm(z['net'])==GND:continue
 for s in K.L.poly(z['fills'].get(layer,[])):
  if s.distance(window)>1:continue
  rad=max(.25,float(z['clearance_mm']),gap(z['net']))+.025;mask=K.Z.bounded_buffer(s,rad);obstacles.append(mask);obrows.append({'kind':'exact_current_foreign_actual_fill','UUID':z['uuid'],'raw_net':z['net'],'radius_mm':rad,'mask_WKB_sha256':K.C.sha(mask.wkb),'target_intersection_mm2':mask.intersection(target).area})
for v in h['vias']:
 if K.L.norm(v['net'])==GND or Point(v['x'],v['y']).distance(window)>1:continue
 mask=K.Z.bounded_disk(v,v['drill']/2+.280);obstacles.append(mask);obrows.append({'kind':'every_foreign_drill','UUID':v['uuid'],'raw_net':v['net'],'radius_mm':v['drill']/2+.280,'mask_WKB_sha256':K.C.sha(mask.wkb),'target_intersection_mm2':mask.intersection(target).area})
for p in h['pads']:
 if K.L.norm(p['net'])==GND:continue
 for sh in K.L.poly(p.get('hole')or[]):
  if sh.distance(window)>1:continue
  mask=K.Z.bounded_buffer(sh,.280);obstacles.append(mask);obrows.append({'kind':'every_foreign_pad_drill','UUID':p['uuid'],'raw_net':p['net'],'mask_WKB_sha256':K.C.sha(mask.wkb),'target_intersection_mm2':mask.intersection(target).area})
for rule in h['rule_areas']:
 if layer in rule['layers']and rule.get('no_zones'):
  for sh in K.L.poly(rule['outline']):
   if sh.distance(window)>1:continue
   mask=K.Z.bounded_buffer(sh,.025);obstacles.append(mask);obrows.append({'kind':'native_no_zones','UUID':rule['uuid'],'mask_WKB_sha256':K.C.sha(mask.wkb),'target_intersection_mm2':mask.intersection(target).area})
ob=unary_union(obstacles);free=window.difference(ob);outside=target.difference(free);(out/'exact-two-native-posed-pad-bodies.wkb').write_bytes(target.wkb);(out/'actual-J3-rooted-In1-reference-before.wkb').write_bytes(sourceplane.wkb);(out/'all-current-native-owned-physical-obstacles.wkb').write_bytes(ob.wkb);(out/'raw-two-pad-body-physical-legal-exterior.wkb').write_bytes(outside.wkb);put(out/'every-actual-layer-obstacle-and-target-intersection.json',obrows);put(out/'exact-current-SMD-source-gap-and-hard-barrier-ledger.json',[{'pad_UUID':p['uuid'],'pin':p['num'],'raw_net':p['net'],'exact_body_actual_source_gap_mm2':unary_union(K.L.poly(p['layers']['F.Cu'])).difference(sourceplane).area,'exact_body_physical_hard_barrier_gap_mm2':unary_union(K.L.poly(p['layers']['F.Cu'])).difference(free).area}for p in pads]);selected=None;attempts=[]
if outside.is_empty:
 desired=set_precision(K.Z.bounded_buffer(target,.025),1e-6,mode='pointwise');centre_free=free.buffer(-.160,quad_segs=128);entry=sourceplane.buffer(-.020,quad_segs=128).intersection(centre_free)
 for part in K.RF.parts(centre_free):
  aa=entry.intersection(part)
  if aa.is_empty:continue
  paths=[];ok=True
  for p in pads:
   body=unary_union(K.L.poly(p['layers']['F.Cu']));terminal=body.intersection(part)
   if terminal.is_empty:ok=False;break
   a,z=nearest_points(aa,terminal);ends=[tuple(round(c,6)for c in pp.coords[0])for pp in(a,z)]
   if not all(part.covers(Point(xy))for xy in ends):ok=False;break
   path,search=T.route(part,*ends);path=[[round(c,6)for c in xy]for xy in path];axis=LineString(path)
   if not part.covers(axis):ok=False;break
   paths.append({'pad_UUID':p['uuid'],'pin':p['num'],'path_mm':path,'length_mm':axis.length,'search':search})
  if not ok:continue
  intended=set_precision(unary_union([desired]+[K.Z.bounded_buffer(LineString(x['path_mm']),.155)for x in paths]),1e-6,mode='pointwise')
  if not intended.is_valid or not intended.difference(free).is_empty:attempts.append({'kind':'exact_new_intention_hard_barrier_or_invalid'});continue
  physical=intended;holeledger=[]
  for v in h['vias']:
   pt=Point(v['x'],v['y'])
   if pt.distance(physical)>v['drill']/2+.000003:continue
   mask=set_precision(K.Z.bounded_disk(v,v['drill']/2+.000002),1e-6,mode='pointwise');physical=set_precision(physical.difference(mask),1e-6,mode='pointwise');holeledger.append({'UUID':v['uuid'],'raw_net':v['net'],'actual_drill_mm':v['drill'],'only_new_physical_plane_own_drill_guard_mm':.000002,'original_native_Cu_masks_flags_unchanged':True,'actual_old_In1_flash':layer in v['flashed'],'native_intended_same_net_barrel_centre_included':K.L.norm(v['net'])==GND and intended.covers(pt),'prospective_same_net_In1_flash_requires_API':K.L.norm(v['net'])==GND and layer not in v['flashed']and intended.covers(pt)})
  for p in h['pads']:
   for hole in K.L.poly(p.get('hole')or[]):
    if hole.intersects(physical):physical=set_precision(physical.difference(set_precision(K.Z.bounded_buffer(hole,.000002),1e-6,mode='pointwise')),1e-6,mode='pointwise')
  bodygap=target.difference(physical);overlap=physical.intersection(sourceplane);assert physical.is_valid and physical.difference(intended).is_empty
  if not bodygap.is_empty or overlap.area<=.001:attempts.append({'kind':'whole_SMD_or_strong_source_contact_gap','raw_body_gap_mm2':bodygap.area,'strong_source_overlap_mm2':overlap.area});continue
  src=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';identity=K.A.N.SourceNets(src.read_bytes());uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'Q0-two-exact-R10016-SMD-reference-r514|'+K.C.sha(intended.wkb)));settings={'clearance_mm':.25,'min_thickness_mm':.15,'connect_pads':'FULL_SOLID','priority':125,'island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3};z={'uuid':uid,'net':identity.raw(GND),'layer':layer,'shape':physical,'zone_outline_shape':intended,'width_mm':.30,'name':'Q0 exact moved R10016 two-pad J3 source reference extension','native_owner_profile_explicit_new_declaration':settings,**settings};filled={'uuid':uid,'net':identity.raw(GND),'fills':{layer:arrays(physical)},'prospective_not_native':True,'name':z['name'],**settings};selected={'zone':z,'filled':filled,'paths':paths,'new_plane_only_hole_ledger':holeledger,'actual_J3_source_overlap_mm2':overlap.area,'both_exact_native_SMD_full_body_gap_empty':True};break
put(out/'finite-extension-attempt-ledger.json',attempts)
if selected:
 pp=out/'only-one-new-ground-reference-positive-zone-and-filled-record.pkl';pp.write_bytes(pickle.dumps(selected,protocol=5));after={**current,'zones':current['zones']+[selected['filled']]};_,groups=K.physical(after,GND,K.hole_context(after));newroot=K.root(groups,'J11003','2');lost=K.keys(root)-K.keys(newroot);plane=unary_union([r['shape']for r in newroot if r['kind']=='fill'and r['layer']==layer]);rawgap=target.difference(plane);assert not lost and rawgap.is_empty;put(out/'actual-J3-source-and-two-whole-pad-body-coverage.json',{'prior_actual_source_keys_lost':sorted(lost),'whole_both_pad_gap_empty':rawgap.is_empty,'actual_rooted_new_plane_present':any(r['kind']=='fill'and r['uuid']==selected['zone']['uuid']for r in newroot),'actual_source':['J11003','2']});result={'verdict':'CONCRETE_BOTH_MOVED_SMD_ACTUAL_J3_ROOTED_REFERENCE_POSITIVE_NOMINATION_ALL_INDEPENDENT_GATES_OPEN','packet_file':str(pp),'packet_sha256':sha(pp),'new_zone_UUID':selected['zone']['uuid'],'new_plane_physical_mm2':selected['zone']['shape'].area,'new_plane_intended_mm2':selected['zone']['zone_outline_shape'].area}
else:result={'verdict':'BOTH_MOVED_SMD_REFERENCE_EXTENSION_CONSTRUCTOR_INCOMPLETE','exact_pad_body_physical_barrier_gap_mm2':outside.area,'exact_pad_body_physical_barrier_gap_empty':outside.is_empty,'target_hard_blockers':[r for r in obrows if r['target_intersection_mm2']>0]}
result.update(current_model_file=str(mp),current_model_sha256=sha(mp),actual_J3_source_arrays_sha256=sha(bf),every_existing_Cu_FP_rule_native_design_outline_q_role_actual_filled_record_unchanged=True,no_new_holes=True,all_native_source_reference_contacts_direct_current_SI_and_mutual_gates='OPEN',all_existing_raw_failures_preserved=True,native_jobs=0,board_written=False,adopted=False,elapsed_seconds=time.monotonic()-start);put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
