"""Targeted analytic-bound guards for R44 new via-to-original-zone cutters.

Preserves the frozen general R1 projector and every original zone definition.
The inherited default16 circle undercuts the 25um planning guard. This helper
applies an outward polygon enclosing the analytic circle before 1nm rounding.
"""
import math,copy,hashlib
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely import set_precision
import contact_layout as C

def bounded_disk(v,radius):
 q=64
 return set_precision(Point(v['x'],v['y']).buffer((radius+.000002)/math.cos(math.pi/(4*q)),quad_segs=q),1e-6)

def correct_original_fills(after,owned_new_vias):
 result=[];ledger=[]
 for z in after['zones']:
  if z.get('prospective_not_native'):result.append(z);continue
  zz=copy.deepcopy(z);zz['fills']={}
  for l,rs in z['fills'].items():
   sh=unary_union(C.poly(rs));rows=[]
   for v in owned_new_vias:
    if v['net']==z['net']:continue
    gap=.15 if after['domains_normalized'][C.norm(v['net'])]==after['domains_normalized'][C.norm(z['net'])] else .6
    clearance=max(gap,float(z['clearance_mm']))+.025
    radius=max(v['drill']/2+.275,v['d']/2+clearance) if l in v['flashed'] else v['drill']/2+.275
    cut=bounded_disk(v,radius)
    if sh.intersects(cut):rows.append((v,cut,radius,clearance))
   if not rows:zz['fills'][l]=rs;continue
   new=sh.difference(unary_union([a[1] for a in rows]));removed=sh.difference(new)
   zz['fills'][l]=records(new)
   if not removed.is_empty:ledger.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':l,'old_effective_WKB_SHA256':hashlib.sha256(sh.wkb).hexdigest(),'new_effective_WKB_SHA256':hashlib.sha256(new.wkb).hexdigest(),'removed_area_mm2':removed.area,'removed_bounds_mm':list(removed.bounds),'cutters':[{'via_UUID':a[0]['uuid'],'analytic_radius_mm':a[2],'required_Cu_gap_with_guard_mm':a[3],'outward_256edge_cut_WKB_SHA256':hashlib.sha256(a[1].wkb).hexdigest()} for a in rows]})
  result.append(zz)
 return {**after,'zones':result},ledger

def records(s):
 ps=[s] if s.geom_type=='Polygon' else [x for x in getattr(s,'geoms',[]) if x.geom_type=='Polygon']
 return [[list(p.exterior.coords),[list(r.coords) for r in p.interiors]] for p in ps]
