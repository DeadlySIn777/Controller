"""Conservative host-only delta projection; native definitions are never changed.

Keep the frozen baseline's already-projected native filled copper. Subtract
only added portions of exact new/changed outward guard primitives. Removed or
shrunk cutters do not reclaim copper. Floating overlay avoids re-snapping
unchanged primitive intersections; newly owned zone geometry remains nm-bound.
This is an explicit alternative host model requiring full independent/native
checks, not a replacement of the frozen regional/global projectors.
"""
import copy
from shapely import set_precision,get_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import regional_guarded_declared_projection_r140 as P
import guarded_declared_settings_projection_r58 as PG
import complete_geometry_r2 as G
import contact_layout as C

def primitive_rows(g,h,zones,net,layer,local):
 changed=PG.changed_ids(g,h);rows={}
 for t in h['tracks']:
  if t['uuid'] not in changed or t['layer']!=layer or C.norm(t['net'])==C.norm(net):continue
  clear=max(G.gap(h,net,t['net']),local);line=LineString([t['a'],t['b']]);rows[('track',t['uuid'])]={'cut':P.bounded_buffer(line,t['w']/2+clear+.025),'body':line,'radius':t['w']/2,'required':clear+.025,'settings':{'raw_net':t['net'],'layer':layer,'width_mm':t['w'],'a':t['a'],'b':t['b']}}
 for v in h['vias']:
  if v['uuid'] not in changed or C.norm(v['net'])==C.norm(net):continue
  clear=max(G.gap(h,net,v['net']),local);radius=v['drill']/2+.275;physical_radius=v['drill']/2;required=.275
  if layer in v['flashed']:radius=max(radius,v['d']/2+clear+.025);physical_radius=v['d']/2;required=clear+.025
  rows[('via',v['uuid'])]={'cut':P.bounded_disk(v,radius),'body':Point(v['x'],v['y']),'radius':physical_radius,'required':required,'settings':{'raw_net':v['net'],'layer':layer,'diameter_mm':v['d'],'drill_mm':v['drill'],'at':[v['x'],v['y']],'flashed_layers':list(v['flashed'])}}
 for pad in h['pads']:
  if pad['uuid'] not in changed or C.norm(pad['net'])==C.norm(net):continue
  clear=max(G.gap(h,net,pad['net']),local)
  for i,shape in enumerate(C.poly(pad['layers'].get(layer,[]))):rows[('pad',pad['uuid'],i)]={'cut':P.bounded_buffer(shape,clear+.025),'body':shape,'radius':0,'required':clear+.025,'settings':{'raw_net':pad['net'],'layer':layer,'body_WKB':P.digest(shape)}}
 for q in zones:
  if q['layer']!=layer or C.norm(q['net'])==C.norm(net):continue
  clear=max(G.gap(h,net,q['net']),local,float(q.get('clearance_mm',.15)));rows[('zone',q['uuid'])]={'cut':P.bounded_buffer(q['shape'],clear+.025),'body':q['shape'],'radius':0,'required':clear+.025,'settings':{k:q.get(k) for k in ('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')}}
 return rows

def projected(g,h,zones,before_h,before_zones,before_candidate,only_nets=None):
 """Return candidate, per-native-fill operator ledger, actual guard checks."""
 old_defs={q['uuid']:q for q in before_h['zones']};old_actual={q['uuid']:q for q in before_candidate['zones']};cache={};result=[];ledger=[];guards=[]
 assert {q['uuid'] for q in h['zones']}==set(old_defs),'native definition UUID set changed'
 for q in h['zones']:assert q==old_defs[q['uuid']],('native definition changed',q['uuid'])
 for native in h['zones']:
  if only_nets is not None and C.norm(native['net']) not in only_nets:continue
  row=copy.deepcopy(native);row['fills']={};local=float(native['clearance_mm'])
  for layer,records in native['fills'].items():
   key=(native['net'],layer,local)
   if key not in cache:cache[key]=(primitive_rows(g,before_h,before_zones,*key),primitive_rows(g,h,zones,*key))
   old,new=cache[key];original=unary_union(C.poly(records));baseline=unary_union(C.poly(old_actual[native['uuid']]['fills'][layer]));remaining=set_precision(baseline,0);assert remaining.wkb==baseline.wkb
   pairs=[];unchanged=0
   for ident,value in new.items():
    cut=value['cut'];prior=old.get(ident)
    if not cut.intersects(original):continue
    if prior is not None and cut.wkb==prior['cut'].wkb and value['settings']==prior['settings']:
     assert get_precision(cut)==get_precision(prior['cut']);unchanged+=1;continue
    new_zero=set_precision(cut,0);assert new_zero.wkb==cut.wkb
    if prior is None:extra=new_zero
    else:
     old_zero=set_precision(prior['cut'],0);assert old_zero.wkb==prior['cut'].wkb;extra=new_zero.difference(old_zero)
    prev=remaining
    if not extra.is_empty:remaining=remaining.difference(extra)
    pairs.append({'key':list(ident),'before_sha256':P.digest(prior['cut']) if prior is not None else None,'after_sha256':P.digest(cut),'before_grid_mm':get_precision(prior['cut']) if prior is not None else None,'after_grid_mm':get_precision(cut),'settings':value['settings'],'required_gap_mm':value['required'],'extra_cut_sha256':P.digest(extra),'extra_cut_mm2':extra.area,'removed_actual_mm2':prev.difference(remaining).area,'operator':'unchanged_WKB_zero_tag_extra_difference_then_floating_subtract'})
   # No physical continuity may be credited from a regained old cutter region.
   added=remaining.difference(baseline).area
   assert added<=1e-12,('conservative nesting failed',native['uuid'],layer,added)
   for ident,value in new.items():
    prior=old.get(ident)
    if prior is not None and value['cut'].wkb==prior['cut'].wkb and value['settings']==prior['settings']:continue
    if not value['cut'].intersects(original):continue
    gap=remaining.distance(value['body'])-value['radius']
    guards.append({'native_zone_UUID':native['uuid'],'raw_net':native['net'],'layer':layer,'foreign_key':list(ident),'required_gap_mm':value['required'],'actual_gap_mm':gap,'PASS':gap+1e-10>=value['required']})
   row['fills'][layer]=G.records(remaining)
   ledger.append({'native_zone_UUID':native['uuid'],'raw_net':native['net'],'layer':layer,'native_definition_unchanged':True,'frozen_baseline_actual_sha256':P.digest(baseline),'candidate_actual_sha256':P.digest(remaining),'unchanged_primitive_count':unchanged,'changed_or_added_pairs':pairs,'removed_actual_Cu_mm2':baseline.difference(remaining).area,'positive_numerical_roundoff_area_mm2':added,'reclaimed_Cu_credited':False,'original_min_thickness_fill_native_gates':'OPEN'})
  result.append(row)
 for q in zones:
  result.append({'uuid':q['uuid'],'net':q['net'],'priority':int(q.get('priority',124)),'clearance_mm':float(q.get('clearance_mm',.15)),'min_thickness_mm':float(q.get('min_thickness_mm',.15)),'pad_connect_mode':q.get('pad_connect_mode','FULL_SOLID'),'island_removal_mode':int(q.get('island_removal_mode',1)),'thermal_gap_mm':float(q.get('thermal_gap_mm',.15)),'thermal_bridge_width_mm':float(q.get('thermal_bridge_width_mm',.3)),'fills':{q['layer']:G.records(q['shape'])},'prospective_not_native':True})
 return {**h,'zones':result},ledger,guards
