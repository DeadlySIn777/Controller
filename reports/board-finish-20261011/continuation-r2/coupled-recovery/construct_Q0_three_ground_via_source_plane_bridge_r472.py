"""Construct a true source-connected plane bridge to the retained FG island.

Only a new owned zone is nominated. Original Cu/holes/native design outlines
and every current filled record are retained verbatim. No native job is run.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,uuid,copy
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import tri_route as T
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def arrays(sh):return[[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in K.RF.parts(sh)]
start=time.monotonic();out=H/'Q0-three-ground-via-source-plane-bridge-r472';assert not out.exists();out.mkdir();md=H/'Q0-exact-R464-current-filled-only-r466';mr=json.loads((md/'receipt.json').read_bytes());assert sha(md/'receipt.json')=='992fa6a0a0ed542abce804eadd0f43a30144b3dc6667626688d3fdc56c1798d1';mp=Path(mr['model_file']);assert sha(mp)==mr['model_sha256'];g,h,b,q,current=pickle.loads(mp.read_bytes());cp=H/'Q0-R466-ground-neck-safe-empty-geometry-r470/ground-source-checkpoint.pkl';assert sha(cp)=='0a7e0ec4c70f7817acc25cad5f2414e70ac797926e4c632108add1985375a31b';checkpoint=pickle.loads(cp.read_bytes());root=checkpoint['root'];island=checkpoint['island'];GND='/motherboard_motors/FIELD_GND';dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(K.L.norm(n))==dom[GND]else .6;source=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';identity=K.A.N.SourceNets(source.read_bytes());window=box(227,162,237,171);rr,tt=K.F.build({**h,'zones':[]});rows=[];selected=None
for layer in('In4.Cu','In1.Cu'):
 obstacles=[];obrows=[]
 for j in tt[layer].query(window.buffer(1),predicate='intersects'):
  r=rr[layer][int(j)]
  if K.L.norm(r['net'])==GND:continue
  rad=max(.25,gap(r['net']))+.025;cut=K.Z.bounded_buffer(r['shape'],rad);obstacles.append(cut);obrows.append({'kind':'all_actual_foreign_layer_Cu','UUID':r['uuid'],'net':r['net'],'radius_mm':rad,'mask_sha256':K.C.sha(cut.wkb)})
 for z in q:
  if z['layer']!=layer or K.L.norm(z['net'])==GND or z['shape'].distance(window)>1:continue
  rad=max(.25,float(z['clearance_mm']),gap(z['net']))+.025;cut=K.Z.bounded_buffer(z['shape'],rad);obstacles.append(cut);obrows.append({'kind':'owned_foreign_current_power_hard','UUID':z['uuid'],'radius_mm':rad,'mask_sha256':K.C.sha(cut.wkb)})
 for z in current['zones']:
  if K.L.norm(z['net'])==GND:continue
  for sh in K.L.poly(z['fills'].get(layer,[])):
   if sh.distance(window)>1:continue
   rad=max(.25,float(z['clearance_mm']),gap(z['net']))+.025;cut=K.Z.bounded_buffer(sh,rad);obstacles.append(cut);obrows.append({'kind':'literal_actual_foreign_fill','UUID':z['uuid'],'radius_mm':rad,'mask_sha256':K.C.sha(cut.wkb)})
 for v in h['vias']:
  if K.L.norm(v['net'])==GND or Point(v['x'],v['y']).distance(window)>1:continue
  cut=K.Z.bounded_disk(v,v['drill']/2+.280);obstacles.append(cut);obrows.append({'kind':'every_foreign_drill','UUID':v['uuid'],'mask_sha256':K.C.sha(cut.wkb)})
 for p in h['pads']:
  for hole in K.L.poly(p.get('hole')or[]):
   if hole.distance(window)>1:continue
   if K.L.norm(p['net'])!=GND:obstacles.append(K.Z.bounded_buffer(hole,.280))
 for rule in h['rule_areas']:
  if layer in rule['layers']and rule.get('no_zones'):obstacles.extend(K.Z.bounded_buffer(s,.025)for s in K.L.poly(rule['outline']))
 free=window.difference(unary_union(obstacles)).buffer(-.160,quad_segs=128);src=unary_union([r['shape']for r in root if r['layer']==layer and r['kind']=='fill']);dst=unary_union([r['shape']for r in island if r['layer']==layer and r['kind']=='fill']);entry=src.buffer(-.015,quad_segs=128).intersection(free);exit=dst.buffer(-.015,quad_segs=128).intersection(free);row={'layer':layer,'entry_area_mm2':entry.area,'exit_area_mm2':exit.area,'path_mm':None};put(out/(layer+'-frozen-physical-obstacles.json'),obrows);(out/(layer+'-new-plane-legal-centres.wkb')).write_bytes(free.wkb)
 for part in K.RF.parts(free):
  aa=entry.intersection(part);bb=exit.intersection(part)
  if aa.is_empty or bb.is_empty:continue
  ap,bp=nearest_points(aa,bb);ends=[tuple(round(v,6)for v in p.coords[0])for p in(ap,bp)]
  if not all(part.covers(Point(p))for p in ends):continue
  path,search=T.route(part,*ends);path=[[round(v,6)for v in p]for p in path]
  if not part.covers(LineString(path)):continue
  intended=set_precision(K.Z.bounded_buffer(LineString(path),.155),1e-6,mode='pointwise');assert intended.is_valid and not intended.intersects(unary_union(obstacles));physical=intended;holeledger=[]
  for v in h['vias']:
   pp=Point(v['x'],v['y'])
   if pp.distance(intended)>v['drill']/2+.00001:continue
   mask=set_precision(K.Z.bounded_disk(v,v['drill']/2+.000002),1e-6,mode='pointwise');physical=set_precision(physical.difference(mask),1e-6,mode='pointwise');holeledger.append({'UUID':v['uuid'],'net':v['net'],'native_drill_mm':v['drill'],'explicit_new_plane_only_negative_own_hole_guard_mm':.000002,'physical_mask_sha256':K.C.sha(mask.wkb),'original_via_Cu_native_flags_unchanged':True,'intended_own_barrel_center_included':intended.covers(pp)})
  for p in h['pads']:
   for hole in K.L.poly(p.get('hole')or[]):
    if hole.intersects(physical):physical=set_precision(physical.difference(set_precision(K.Z.bounded_buffer(hole,.000002),1e-6,mode='pointwise')),1e-6,mode='pointwise')
  assert physical.is_valid and physical.difference(intended).is_empty
  uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'Q0-FG-island-source-bridge-r472|'+layer+'|'+K.C.sha(intended.wkb)));settings={'clearance_mm':.25,'min_thickness_mm':.15,'connect_pads':'FULL_SOLID','priority':124,'island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3};zone={'uuid':uid,'net':identity.raw(GND),'layer':layer,'shape':physical,'zone_outline_shape':intended,'width_mm':.30,'name':'Q0 retained three FG via actual source bridge','native_owner_profile_explicit_new_declaration':settings,**settings};filled={'uuid':uid,'net':identity.raw(GND),'fills':{layer:arrays(physical)},'prospective_not_native':True,'name':zone['name'],**settings};row.update(path_mm=path,length_mm=LineString(path).length,physical_mm2=physical.area,intended_mm2=intended.area,search=search,actual_source_fill_contact_mm2=physical.intersection(src).area,actual_island_fill_contact_mm2=physical.intersection(dst).area);assert row['actual_source_fill_contact_mm2']>.001 and row['actual_island_fill_contact_mm2']>.001;selected={'zone':zone,'filled':filled,'row':row,'new_plane_only_hole_ledger':holeledger};break
 rows.append(row)
 if selected:break
put(out/'source-plane-bridge-nominations.json',rows)
if selected:
 pp=out/'only-new-source-plane-and-filled-record.pkl';pp.write_bytes(pickle.dumps(selected,protocol=5));after={**current,'zones':current['zones']+[selected['filled']]};newgroups=K.physical(after,GND,K.hole_context(after))[1];newroot=K.root(newgroups,'J11003','2');lost=K.keys(root)-K.keys(newroot);islandlost=K.keys(island)-K.keys(newroot);assert not lost and not islandlost;(out/'actual-new-ground-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));put(out/'actual-ground-source-key-join-ledger.json',{'prior_actual_source_keys_lost':sorted(lost),'all_three_via_island_actual_source_keys_lost':sorted(islandlost),'all_21_native_ground_via_track_layer_keys_restored':True,'actual_source':['J11003','2']})
 result={'verdict':'CONCRETE_NEW_GROUND_PLANE_ACTUAL_SOURCE_KEYS_RESTORED_ALL_INDEPENDENT_GATES_OPEN','packet_file':str(pp),'packet_sha256':sha(pp),'new_zone_UUID':selected['zone']['uuid'],'source_and_all_21_prior_native_island_keys_restored':True}
else:result={'verdict':'NEW_GROUND_SOURCE_PLANE_CONSTRUCTOR_INCOMPLETE'}
result.update(current_model_sha256=sha(mp),actual_source_checkpoint_sha256=sha(cp),only_one_NEW_ground_zone_proposed=bool(selected),every_current_discrete_Cu_FP_rule_native_outline_and_actual_old_fill_array_unchanged=True,all_ordinary_native_source_contact_reference_current_SI_and_joint_profile_gates='OPEN',all_original_raw_failures_preserved=True,native_jobs=0,adopted=False,elapsed_seconds=time.monotonic()-start);put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
