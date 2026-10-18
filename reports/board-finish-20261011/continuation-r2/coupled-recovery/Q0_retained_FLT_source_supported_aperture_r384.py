"""Explicit exact retained FLT own hole only, with all other physical cuts.

New paired-return source proof and actual native final annulus/contact checks
remain mandatory. This helper cannot grant neighbor holes or expand .575mm.
"""
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
def support_FLT(K,before,h,oldroot,inventory,sig,ground,net,plane):
 assert sig['uuid']=='a01ff36f-ac32-4648-88fe-29a54c58570b'and K.L.norm(sig['net'])==net and(sig['x'],sig['y'],sig['d'],sig['drill'])==(228.25,157.65,.6,.3)
 raw=K.Z.bounded_disk(sig,.575);C=K.C;CACHE=K.OS.CACHE;Q=K.Q;rows=[];owner=[];zoneheader={z['uuid']:z for z in before['zones']};records,trees=K.F.build({**h,'zones':[]});domains=h['domains_normalized'];cutrows=[];cuts=[]
 nativeids={r['uuid']for r in oldroot if r['kind']=='fill'and r['layer']==plane and r['shape'].distance(raw)<.8}
 for zid in sorted(nativeids):
  if zid not in inventory[3]:continue
  chunk=inventory[3][zid];assert C.pcbtext.chunk_kind(chunk)=='zone';plain,spans=CACHE.strip_cache(chunk);ast=Q.parse(plain.decode());assert K.L.norm(Q.atom(ast,'net'))==ground;ls=Q.atom(ast,'layer');layers=[ls]if ls else Q.child(ast,'layers')[1:]
  if plane not in layers:continue
  rings=[[(float(p[1]),float(p[2]))for p in Q.child(pp,'pts')[1:]]for pp in Q.children(ast,'polygon')];shape=Polygon(rings[0],rings[1:]);assert shape.is_valid;local=float(zoneheader[zid]['clearance_mm']);assert local==.25
  if not shape.intersects(raw):continue
  owner.append(shape);rows.append({'actual_root_native_zone_UUID':zid,'exact_native_chunk_sha256':C.sha(chunk),'exact_design_outline_without_cache_sha256':C.sha(plain),'outline_WKB_sha256':C.sha(shape.wkb),'actual_native_local_clearance_mm':local})
 if not owner:return unary_union([]),{'verdict':'NO_ROOT_NATIVE_OWN_OUTLINE_AUTHORITY','owners':[],'native_full_source_and_return_gate':'OPEN'}
 support=raw.intersection(unary_union(owner));local=.25
 for j in trees[plane].query(raw.buffer(1),predicate='intersects'):
  r=records[plane][int(j)];other=K.L.norm(r['net'])
  if r['uuid']==sig['uuid']or other==ground:continue
  clearance=max(local,.15 if domains.get(other)==domains[ground]else .6)+.025;cut=K.Z.bounded_buffer(r['shape'],clearance)
  if cut.intersects(support):cuts.append(cut);cutrows.append({'kind':'other_actual_reference_layer_Cu','UUID':r['uuid'],'raw_net':r['net'],'clearance_mm':clearance,'cutter_WKB_sha256':C.sha(cut.wkb)})
 for v in h['vias']:
  if v['uuid']==sig['uuid']:continue
  cut=K.Z.bounded_disk(v,v['drill']/2+.005)
  if cut.intersects(support):cuts.append(cut);cutrows.append({'kind':'every_other_actual_drill','UUID':v['uuid'],'cutter_WKB_sha256':C.sha(cut.wkb)})
 for pad in h['pads']:
  for hole in K.L.poly(pad.get('hole')or[]):
   cut=K.Z.bounded_buffer(hole,.005)
   if cut.intersects(support):cuts.append(cut);cutrows.append({'kind':'every_other_pad_hole','UUID':pad['uuid'],'cutter_WKB_sha256':C.sha(cut.wkb)})
 for rule in h['rule_areas']:
  if plane not in rule['layers']or not rule.get('no_zones'):continue
  for sh in K.L.poly(rule['outline']):
   cut=K.Z.bounded_buffer(sh,.025)
   if cut.intersects(support):cuts.append(cut);cutrows.append({'kind':'native_no_zones','UUID':rule['uuid'],'cutter_WKB_sha256':C.sha(cut.wkb)})
 for z in before['zones']:
  if K.L.norm(z['net'])==ground:continue
  for shape in K.L.poly(z['fills'].get(plane,[])):
   if shape.distance(raw)>1:continue
   clearance=max(local,float(z['clearance_mm']),.15 if domains.get(K.L.norm(z['net']))==domains[ground]else .6)+.025;cut=K.Z.bounded_buffer(shape,clearance)
   if cut.intersects(support):cuts.append(cut);cutrows.append({'kind':'current_foreign_physical_fill','UUID':z['uuid'],'net':z['net'],'cutter_WKB_sha256':C.sha(cut.wkb)})
 allowed=support.difference(unary_union(cuts));return allowed,{'verdict':'EXACT_RETAINED_FLT_OWN_APERTURE_OUTLINE_AND_OTHER_CUT_SUPPORT_ONLY','signal_UUID':sig['uuid'],'unchanged_signal_xy_diameter_drill_mm':[sig['x'],sig['y'],sig['d'],sig['drill']],'exact_own_radius_mm':.575,'radius_expansion_mm':0,'ground_source':'actual_J11003.2_group','used_signal_layer':'F.Cu','actual_reference_layer':plane,'actual_root_native_outline_owners':rows,'all_other_Cu_drills_native_no_zones_and_foreign_fill_cuts':cutrows,'raw_own_disk_WKB_sha256':C.sha(raw.wkb),'supported_own_WKB_sha256':C.sha(allowed.wkb),'denied_nonown_void_mm2':raw.difference(allowed).area,'paired_return_new_ordinary_actual_source_and_all_native_annulus_refill_gates':'MANDATORY_OPEN','no_neighbor_aperture_or_generic_disk_waiver':True}
