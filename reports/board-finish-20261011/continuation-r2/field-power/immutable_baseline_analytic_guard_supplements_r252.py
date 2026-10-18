"""Explicit conservative host-only supplement to frozen delta projection.

Keep every existing primitive and its required guard. If the actual remaining
native fill still breaches a changed/new primitive's analytic guard, remove an
additional bounded disk centred on its exact nearest body point. No old zone
definition, owned plane, clearance, source allocation or reference rule changes.
This is a derived model requiring independent and native qualification.
"""
import inspect
import immutable_baseline_guard_delta_projection_r236 as BASE

source=inspect.getsource(BASE.projected)
old="""    gap=remaining.distance(value['body'])-value['radius']
    guards.append({'native_zone_UUID':native['uuid'],'raw_net':native['net'],'layer':layer,'foreign_key':list(ident),'required_gap_mm':value['required'],'actual_gap_mm':gap,'PASS':gap+1e-10>=value['required']})"""
new="""    supplements=[]
    for iteration in range(1000):
     if remaining.is_empty:break
     gap=remaining.distance(value['body'])-value['radius']
     if gap+1e-10>=value['required']:break
     point,other=nearest_points(value['body'],remaining)
     radius=value['radius']+value['required']
     circle=P.bounded_disk({'x':point.x,'y':point.y},radius)
     floating_circle=set_precision(circle,0);assert floating_circle.wkb==circle.wkb
     prior_actual=remaining;remaining=remaining.difference(floating_circle)
     supplements.append({'iteration':iteration,'exact_owned_body_point_mm':[point.x,point.y],'nearest_actual_native_point_mm':[other.x,other.y],'gap_before_mm':gap,'unchanged_required_gap_mm':value['required'],'owned_body_radius_mm':value['radius'],'guard_disk_radius_mm':radius,'outward256edge_disk_sha256':P.digest(circle),'disk_WKB_hex':circle.wkb_hex,'actual_native_removed_mm2':prior_actual.difference(remaining).area,'positive_gain_mm2':remaining.difference(prior_actual).area})
     assert remaining.difference(prior_actual).area<=1e-12,('supplement gained Cu',native['uuid'],ident)
    if remaining.is_empty:
     gap=None;passed=True
    else:
     gap=remaining.distance(value['body'])-value['radius'];passed=gap+1e-10>=value['required']
    guards.append({'native_zone_UUID':native['uuid'],'raw_net':native['net'],'layer':layer,'foreign_key':list(ident),'required_gap_mm':value['required'],'actual_gap_mm':gap,'remaining_actual_Cu_empty':remaining.is_empty,'PASS':passed,'explicit_additive_analytic_guard_disks':supplements})"""
assert source.count(old)==1
source=source.replace(old,new)
# Added disks for later rows can only remove Cu, preserving earlier guards.
# Repeat the conservative-subset check after all supplemental removals.
source=source.replace("   row['fills'][layer]=G.records(remaining)","   assert remaining.difference(baseline).area<=1e-12,('final conservative nesting',native['uuid'],layer)\n   row['fills'][layer]=G.records(remaining)\n   roundtrip=C.poly(row['fills'][layer]);expected=G.p.hubs.components(remaining);assert len(roundtrip)==len(expected) and all(a.wkb==b.wkb for a,b in zip(roundtrip,expected)),('record changed floating Cu',native['uuid'],layer)")
ns=dict(vars(BASE))
from shapely.ops import nearest_points
ns['nearest_points']=nearest_points
exec(compile(source,__file__,'exec'),ns)
projected=ns['projected']
