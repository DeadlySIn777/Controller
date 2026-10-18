"""Derive separate complete R24 audit; retain the incomplete C3 receipt."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'audit_c10036_exact_operation_r3.py').read_text().replace('c10036-exact-operation-independent-r3.json','c10036-r24-independent-complete-r27.json').replace('c10036-coupled-wall-exact-recipe-r2.json','c10036-r25-reference-bridge-recipe-r24.json').replace('1c10f6d5e79727bfc49d19d77ee1a73fd0532c7aace5f05d271c567e3873810f','016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e')
s=s.replace('from shapely.geometry import Point,LineString','from shapely.geometry import Point,LineString,Polygon\nfrom shapely import from_wkb\nfrom verify_source import parse,children,child,atom')
s=s.replace("GROUND='/motherboard_do/FIELD_B_0V';GATE=", "POWER='/motherboard_do/DOB_FIELD_3V3';GROUND='/motherboard_do/FIELD_B_0V';GATE=")
s=s.replace("assert q['net'] in(GROUND,GATE)","assert q['net'] in(GROUND,GATE,POWER)")
s=s.replace("assert q['kind']=='segment' and q['layer']=='F.Cu' and q['w']==.2;", "assert q['kind']=='segment' and ((q['net']==POWER and q['layer']=='B.Cu' and q['w']==.3) or(q['net'] in(GROUND,GATE) and q['layer']=='F.Cu' and q['w']==.2));")
s=s.replace("assert len(nv)==1 and len(nt)==4 and len(removed)==5", "assert len(nv)==2 and len(nt)==6 and len(removed)==6")
s=s.replace("if 'd' in q else L.body(q)","if 'd' in q else A.shape({'kind':'segment',**q})")
mark=" print('C10036_EXACT_CU',len(errors),flush=True)"
insert=r'''
 # Independently parse the exact unfilled zone outline, including hole rings.
 zm=receipt['new_zone_manifest'];zr=pickle.loads(A.read(zm['prospective_zone_pickle']));assert C.sha(A.read(zm['prospective_zone_pickle']))==zm['prospective_zone_pickle_sha256'];shape=from_wkb(A.read(zm['geometry_WKB_path']));assert C.sha(A.read(zm['geometry_WKB_path']))==zm['geometry_WKB_sha256'];assert shape.equals(zr['shape']);assert(zr['net'],zr['layer'],zr['clearance_mm'],zr['priority'])==(identity.raw(GROUND),'In4.Cu',.25,124)
 zch=receipt['exact_new_zone_chunks'][zr['uuid']];ast=parse(zch);assert atom(ast,'net')==identity.raw(GROUND) and atom(ast,'layer')=='In4.Cu' and atom(ast,'uuid')==zr['uuid'] and atom(ast,'priority')=='124';rings=[[(float(q[1]),float(q[2])) for q in child(pp,'pts')[1:]] for pp in children(ast,'polygon')];rt=Polygon(rings[0],rings[1:]);assert rt.is_valid and rt.symmetric_difference(shape).area<1e-12;assert not children(ast,'filled_polygon') and not children(ast,'fill_segments');zoneproof={'uuid':zr['uuid'],'exact_chunk_sha256':C.sha(zch.encode()),'exact_WKB_sha256':C.sha(shape.wkb),'roundtrip_error_mm2':rt.symmetric_difference(shape).area,'local_clearance_mm':.25,'priority':124,'minimum_thickness_mm':.15,'bulk_width_mm':.5,'finite_proved_continuous_core_width_mm':.31,'every_original_zone_outline_configuration_untouched':True};core=LineString(receipt['B_power_route']['points_mm']).buffer(.155,quad_segs=128);assert shape.covers(core)
 for i in trees['In4.Cu'].query(shape.buffer(.7),predicate='intersects'):
  r=records['In4.Cu'][int(i)]
  if L.norm(r['net'])==GROUND:continue
  req=max(.25,gap(GROUND,r['net']))+.025;d=shape.distance(r['shape'])
  if d<req-1e-8:errors.append({'kind':'NEW_REFERENCE_ZONE_FOREIGN_Cu','uuid':zr['uuid'],'other_uuid':r['uuid'],'other_net':r['net'],'distance_mm':d,'required_mm':req})
 for z in zones:
  if z['layer']!='In4.Cu' or L.norm(z['net'])==GROUND:continue
  req=max(.25,gap(GROUND,z['net']))+.025;d=shape.distance(z['shape'])
  if d<req-1e-8:errors.append({'kind':'NEW_REFERENCE_ZONE_FOREIGN_PROPOSAL','uuid':zr['uuid'],'other_uuid':z['uuid'],'distance_mm':d,'required_mm':req})
 outline=unary_union(L.poly(h['outline'])).buffer(-.525);res,exempt=A.reservations();hardledger=[];holed=[(v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)) for v in h['vias']]+[(p['uuid'],L.norm(p['net']),sh) for p in h['pads'] for sh in L.poly(p.get('hole') or [])]
 for q in nv+nt+[{'uuid':zr['uuid'],'net':GROUND,'layer':'In4.Cu','zone':True}]:
  net=L.norm(q['net']);isvia='d' in q;iszone=q.get('zone',False);body=shape if iszone else Point(q['x'],q['y']).buffer(q['d']/2,quad_segs=128) if isvia else A.shape({'kind':'segment',**q});ls=LAYERS if isvia else[q['layer']]
  if not outline.covers(body):errors.append({'kind':'EXACT_OUTLINE_GUARD','uuid':q['uuid']})
  for rule in h['rule_areas']:
   if not set(ls).intersection(rule['layers']) or not rule.get('no_zones' if iszone else'no_vias' if isvia else'no_tracks'):continue
   for sh in L.poly(rule['outline']):
    if body.distance(sh)<.025:errors.append({'kind':'NATIVE_HARD_AREA','uuid':q['uuid'],'rule':rule['uuid']})
  # Frozen RESERVE predicates disallow only track/via; do not invent zone bans.
  if not iszone:
   for rule in res['keepouts']:
    if net in exempt.get(rule['name'],set()) or not set(ls).intersection(rule['layers']):continue
    for sh in L.poly(rule['outline']):
     if body.distance(sh)<.025:errors.append({'kind':'FROZEN_TRACK_VIA_RESERVATION','uuid':q['uuid'],'rule':rule['name']})
  if not isvia and not iszone:
   for uid,hn,hh in holed:
    if hn==net:continue
    if body.distance(hh)<.275-1e-8:errors.append({'kind':'NEW_TRACK_FOREIGN_PHYSICAL_DRILL','uuid':q['uuid'],'other_uuid':uid,'distance_mm':body.distance(hh),'required_mm':.275})
  hardledger.append({'uuid':q['uuid'],'layer_scope':ls,'kind':'zone' if iszone else'via' if isvia else'segment','frozen_predicates_tested':True})
 zones=zones+[zr]
'''
assert mark in s;s=s.replace(mark,insert+mark)
s=s.replace("affected={GROUND,GATE}","affected={GROUND,GATE,POWER}")
s=s.replace("'new_via_in_same_root_group':any(q['uuid']==nv[0]['uuid'] for q in root)","'new_via_in_same_root_group':all(any(q['uuid']==v['uuid'] for q in root) for v in nv)")
a=s.index(" reference=[]\n for t in nt:") if " reference=[]\n for t in nt:" in s else s.index("};reference=[]\n for t in nt:")+2
b=s.index(" oldroot=",a)
newref=r'''reference=[]
 inherited=next(v for v in before['vias'] if v['uuid']=='40bdf2f9-776c-4aa5-bca6-7921f7c90b54');assert(inherited['x'],inherited['y'],inherited['d'],inherited['drill'],L.norm(inherited['net']))==(66.55,95.35,.6,.3,GATE);native=json.loads(A.read(HERE.parent/'native-198b-geometry/geometry.json'));vold=next(v for v in native['vias'] if v['uuid']==inherited['uuid']);assert(vold['at'],vold['w'],vold['drill'],vold['net'])==([66.55,95.35],.6,.3,inherited['net']);fl=json.loads(A.read(HERE.parent/'native-198b-geometry/actual-via-flashes.json'))['vias'];assert set(fl[inherited['uuid']])==set(inherited['flashed'])==set(LAYERS);paired=next(v for v in nv if v['uuid']==receipt['new_return_UUID']);dist=math.dist((paired['x'],paired['y']),(66.55,95.35));assert .81<=dist<=1.;ann=Point(paired['x'],paired['y']).buffer(.25,quad_segs=128).difference(Point(paired['x'],paired['y']).buffer(.1,quad_segs=128));annareas={l:refs[outer].buffer(-.075).intersection(ann).area for l,outer in [('In1.Cu','F.Cu'),('In4.Cu','B.Cu')]};assert all(a>=.004 for a in annareas.values());pairedproof={'inherited_signal_UUID':inherited['uuid'],'actual_signal_at_mm':[66.55,95.35],'actual_signal_diameter_drill_mm':[.6,.3],'actual_signal_annuli':fl[inherited['uuid']],'new_return_UUID':paired['uuid'],'return_at_mm':[paired['x'],paired['y']],'distance_mm':dist,'finite_source_rooted_annular_interior_mm2':annareas,'source_root':'J11005.2','native_candidate_actual_annuli_and_fills':'OPEN'}
 def vertices(sh):
  if sh.is_empty:return []
  if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for ring in sh.interiors for p in ring.coords]
  return [p for q in sh.geoms for p in vertices(q)]
 for t in nt:
  net=L.norm(t['net'])
  if net not in(GATE,POWER):continue
  body=A.shape({'kind':'segment',**t});uncovered=body.difference(refs[t['layer']]);area=uncovered.area;maxradius=max((math.dist(p[:2],(66.55,95.35)) for p in vertices(uncovered)),default=0.);own=net==GATE and area>1e-9 and maxradius<=.575;reference.append({'uuid':t['uuid'],'net':net,'layer':t['layer'],'full_body_uncovered_mm2':area,'bounds_mm':list(uncovered.bounds) if not uncovered.is_empty else [],'own_transition_exceptions':1 if own else0,'actual_own_transition_UUID':inherited['uuid'] if own else None,'actual_own_unchanged_radius_mm':.575 if own else None,'maximum_gap_vertex_radius_mm':maxradius if own else None,'convex_analytic_disk_contains_all_gap_vertices_edges_and_interior':own,'radius_expansion_mm':0,'paired_actual_rooted_return_UUID':paired['uuid'] if own else None,'reference_gap_after_exact_own_transition_scope_mm2':0 if own else area})
 referrors=[r for r in reference if r['reference_gap_after_exact_own_transition_scope_mm2']>1e-9]
'''
# The preceding inline assignment ends with semicolon; preserve the refs dict.
s=s[:a]+newref+s[b:]
s=s.replace("body=L.body(t);lost=", "body=A.shape({'kind':'segment',**t}) if t.get('m') is None else L.body(t);lost=")
start=s.index("  for rel in parts[GATE]:")
end=s.index(" passed=",start)
native=r'''
  currentpads={p['uuid']:p for p in before['pads']}
  for net in(GATE,POWER,GROUND):
   for rel in parts[net]:
    ids=[padmap[x] for x in rel];unchanged=[u for u in ids if L.norm(currentpads[u]['net'])==net];retagged=[{'uuid':u,'actual_current_raw_net':currentpads[u]['net'],'baseline_raw_net':net,'source_frozen_intentional_retag_authority':'R25 source-parent/fresh070444; full final source ledger remains root-owned'} for u in ids if u not in unchanged];components={ufnew[net].find(('pad',u)) for u in unchanged};row={'baseline':label,'net':net,'exact_native_pad_ids':rel,'physical_pad_UUIDs':ids,'source_net_unchanged_physical_pad_UUIDs':unchanged,'separately_owned_source_retags':retagged,'candidate_component_count':len(components)};nativechecks.append(row)
    if len(components)>1:padloss.append(row)
'''
s=s[:start]+native+s[end:]
s=s.replace("'new_gate_full_body_reference':reference", "'new_signal_and_power_full_body_reference':reference,'inherited_transition_qualified_source_return':pairedproof,'new_reference_zone_exact_AST_and_core':zoneproof,'independent_frozen_hard_and_outline_predicates':hardledger,'mutual_R41_source_feed_reference_gate':receipt['R41_mutual_reference_verdict'],'mutual_R41_conflicting_mesh_UUID':receipt['R41_conflicting_prospective_In4_mesh_UUID']")
s=s.replace("'native_jobs':0,'gpu_jobs':0", "'native_jobs':0,'gpu_jobs':0,'recipe_on_R25_only':True,'R41_future_feed_revision_and_full_final_joint_power_source_capacity_required':True")
s=s.replace("else 'INDEPENDENT_C10036_OPERATION_INCOMPLETE'", "else 'INDEPENDENT_C10036_R25_OPERATION_INCOMPLETE'")
s=s.replace("'INDEPENDENT_C10036_PHYSICAL_CONTACT_CLEARANCE_REFERENCE_PASS_NATIVE_PENDING'", "'INDEPENDENT_C10036_R25_CONTACT_CLEARANCE_REFERENCE_PASS_NATIVE_AND_MUTUAL_R41_OPEN'")
t=HERE/'audit_c10036_r24_full_independent_r27.py';assert not t.exists();t.write_text(s);print(t)
