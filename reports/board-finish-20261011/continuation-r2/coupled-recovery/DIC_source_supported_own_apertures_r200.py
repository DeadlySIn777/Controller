"""Source-supported new apertures and exact retained CMD own-hole isolation.

Only the new signal's previously rooted copper can be consumed by its own
aperture. An old CMD hole is reconstructed from actual root-zone design
outlines, excluding every other copper/hole/rule/foreign-plane cut.
"""
import sys,math,re
from pathlib import Path
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_c10036_r24_full_independent_r30 as Q
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent))
import refresh_combined_zone_cache_r5 as CACHE
C=A.C;GND='/LOGIC_GND';CMD='/motherboard_io_control/DIC_IOL1_CMD_BUFFER';NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER'
MAP={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'}

def scopes(before,h,oldroot,oldrefs,qualified,inventory):
 A.read(__file__);A.read(CACHE.__file__);A.read(CACHE.H.__file__)
 oldvias={v['uuid']:v for v in before['vias']};allvias={v['uuid']:v for v in h['vias']};result={};rows=[];errors=[];records,trees=F.build({**h,'zones':[]});domains=h['domains_normalized'];zoneheader={z['uuid']:z for z in before['zones']};native_outlines={}
 for uid,net,rawdisk in qualified:
  sig=allvias[uid]
  if uid not in oldvias:
   assert net==NET and(sig['d'],sig['drill'])==(.5,.2)
   for layer,plane in MAP.items():
    if layer not in oldrefs:continue
    allowed=rawdisk.intersection(oldrefs[layer]);result.setdefault((net,layer),[]).append(allowed);rows.append({'signal_UUID':uid,'signal_new':True,'used_or_checked_signal_layer':layer,'actual_source_reference_layer':plane,'raw_exact_own_disk_WKB_sha256':C.sha(rawdisk.wkb),'own_credit_WKB_sha256':C.sha(allowed.wkb),'own_credit_area_mm2':allowed.area,'pre_existing_non_source_void_denied_mm2':rawdisk.difference(allowed).area,'credit_rule':'EXACT_NEW_APERTURE_INTERSECTION_BEFORE_ROOTED_PHYSICAL_REFERENCE','radius_expansion_mm':0})
   continue
  assert uid=='1f815e33-e973-46e2-833e-96fee8d37fcf' and net==CMD and sig==oldvias[uid] and(sig['x'],sig['y'],sig['d'],sig['drill'])==(128.549999,100.55,.6,.3)
  layer='B.Cu';plane=MAP[layer];nativeids={q['uuid'] for q in oldroot if q['kind']=='fill' and q['layer']==plane and q['shape'].distance(rawdisk)<.8};owner=[];ownerledger=[]
  for zid in sorted(nativeids):
   if zid not in inventory[3]:continue
   ch=inventory[3][zid];assert C.pcbtext.chunk_kind(ch)=='zone';plain,spans=CACHE.strip_cache(ch);ast=Q.parse(plain.decode());assert Q.atom(ast,'net')==GND;ls=Q.atom(ast,'layer');layers=[ls] if ls else Q.child(ast,'layers')[1:]
   if plane not in layers:continue
   rings=[[(float(p[1]),float(p[2])) for p in Q.child(pp,'pts')[1:]] for pp in Q.children(ast,'polygon')];assert rings;shape=Polygon(rings[0],rings[1:]);assert shape.is_valid;header=zoneheader[zid];local=float(header['clearance_mm']);assert local==.25
   if not shape.intersects(rawdisk):continue
   owner.append(shape);ownerledger.append({'actual_root_zone_UUID':zid,'source_chunk_sha256':C.sha(ch),'definition_without_derived_cache_sha256':C.sha(plain),'removed_only_derived_cache_children':[q[2] for q in spans],'actual_native_design_outline_WKB_sha256':C.sha(shape.wkb),'exact_native_local_mm':local})
  if not owner:
   errors.append({'kind':'old_CMD_own_hole_has_no_actual_root_native_outline_authority','signal_UUID':uid});continue
  support=rawdisk.intersection(unary_union(owner));local=.25;cuts=[];cutledger=[]
  for i in trees[plane].query(rawdisk.buffer(1),predicate='intersects'):
   q=records[plane][int(i)];other=L.norm(q['net'])
   if q['uuid']==uid or other==GND:continue
   clearance=max(local,.15 if domains.get(other)==domains[GND] else .6)+.025;cut=Z.bounded_buffer(q['shape'],clearance)
   if cut.intersects(support):cuts.append(cut);cutledger.append({'kind':'other_actual_reference_layer_Cu','UUID':q['uuid'],'raw_net':q['net'],'actual_layer':plane,'clearance_mm':clearance,'WKB_sha256':C.sha(cut.wkb)})
  for v in h['vias']:
   if v['uuid']==uid:continue
   cut=Z.bounded_disk(v,v['drill']/2+.005)
   if cut.intersects(support):cuts.append(cut);cutledger.append({'kind':'every_other_actual_drill','UUID':v['uuid'],'radius_mm':v['drill']/2+.005,'WKB_sha256':C.sha(cut.wkb)})
  for pad in h['pads']:
   for hole in L.poly(pad.get('hole') or []):
    cut=Z.bounded_buffer(hole,.005)
    if cut.intersects(support):cuts.append(cut);cutledger.append({'kind':'other_plated_or_mechanical_pad_hole','UUID':pad['uuid'],'WKB_sha256':C.sha(cut.wkb)})
  for rule in h['rule_areas']:
   if plane not in rule['layers'] or not rule.get('no_zones'):continue
   for sh in L.poly(rule['outline']):
    cut=Z.bounded_buffer(sh,.025)
    if cut.intersects(support):cuts.append(cut);cutledger.append({'kind':'actual_native_no_zones','UUID':rule['uuid'],'WKB_sha256':C.sha(cut.wkb)})
  # An original root-zone outline is not authority to fill a current foreign
  # source plane or the body of an owned power proposal.
  for z in before['zones']:
   if L.norm(z['net'])==GND:continue
   for sh in L.poly(z['fills'].get(plane,[])):
    if sh.distance(rawdisk)>1:continue
    clearance=max(local,float(z['clearance_mm']),.15 if domains.get(L.norm(z['net']))==domains[GND] else .6)+.025;cut=Z.bounded_buffer(sh,clearance)
    if cut.intersects(support):cuts.append(cut);cutledger.append({'kind':'current_foreign_physical_fill','UUID':z['uuid'],'raw_net':z['net'],'WKB_sha256':C.sha(cut.wkb)})
  allowed=support.difference(unary_union(cuts));result.setdefault((net,layer),[]).append(allowed);rows.append({'signal_UUID':uid,'signal_new':False,'unchanged_exact_own_radius_mm':.575,'radius_expansion_mm':0,'actual_root_native_outline_ledger':ownerledger,'every_other_actual_Cu_hole_no_zones_foreign_fill_ledger':cutledger,'raw_exact_own_disk_WKB_sha256':C.sha(rawdisk.wkb),'own_credit_WKB_sha256':C.sha(allowed.wkb),'own_credit_area_mm2':allowed.area,'other_boundary_void_denied_mm2':rawdisk.difference(allowed).area,'credit_rule':'ONLY_ACTUAL_UNCHANGED_CMD_OWN_HOLE_CLIPPED_NATIVE_OUTLINES_OTHER_PHYSICAL_CUTS','actual_new_GND_annuli_refill_and_full_joint_native_gate':'OPEN'})
 return {key:unary_union(shapes) for key,shapes in result.items()},{'source_supported_own_aperture_ledger':rows,'errors':errors,'new_own_disks_clipped_to_exact_before_rooted_reference':True,'old_CMD_pose_annuli_native_aperture_only_no_radius_increase':True,'native_jobs':0}
