"""Independent exact C10036 recipe rebuild, physical contacts and reference.

Every drill is subtracted before contact graphs; split fill/track pieces have
distinct identities. No native invocation, board/source/zone write or waiver.
"""
import sys,json,pickle,math,copy,time,collections,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP))
import contact_layout as L
import fast_contacts as F
sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as Z
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
from shapely.geometry import Point,LineString,Polygon
from shapely import from_wkb
from verify_source import parse,children,child,atom
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
POWER='/motherboard_do/DOB_FIELD_3V3';GROUND='/motherboard_do/FIELD_B_0V';GATE='/motherboard_do/DO12_RCB_GATE';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def pieces(sh):return [sh] if sh.geom_type=='Polygon' else[q for q in getattr(sh,'geoms',[]) if q.geom_type=='Polygon']
def physical(g,net):
 rec,_=F.build(g,nets={net});holes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128) for v in g['vias']]+[sh for p in g['pads'] for sh in L.poly(p.get('hole') or [])];ht=STRtree(holes);uf=S.UF();rows=[]
 for l,xs in rec.items():
  rr=[]
  for r in xs:
   body=r['shape'].difference(unary_union([holes[int(i)] for i in ht.query(r['shape'],predicate='intersects')]))
   for sh in pieces(body):
    k=(r['kind'],r['uuid']) if r['kind'] in('pad','via') else(r['kind'],r['uuid'],l,C.sha(sh.wkb));rr.append({**r,'key':k,'shape':sh})
  tree=STRtree([r['shape'] for r in rr])
  for i,r in enumerate(rr):
   uf.find(r['key']);rows.append(r)
   for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
    if i<int(j) and r['shape'].distance(rr[int(j)]['shape'])<=.000002:uf.join(r['key'],rr[int(j)]['key'])
 groups=collections.defaultdict(list)
 for r in rows:groups[uf.find(r['key'])].append(r)
 return uf,list(groups.values())
def discrete_keys(rows):return {(r['kind'],r['uuid']) for r in rows if r['kind']!='fill'}
def main():
 started=time.monotonic();out=HERE/'c10036-r24-independent-complete-r28.json';assert not out.exists();rp=FP/'local-and-b5-return-audit-r25'
 receipt=json.loads(A.read(HERE/'c10036-r25-reference-bridge-recipe-r24.json'));assert C.sha(A.read(HERE/'c10036-r25-reference-bridge-recipe-r24.json'))=='016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e'
 for p,pin in receipt['read_files_sha256'].items():assert C.sha(Path(p).read_bytes())==pin,p
 for p,pin in receipt['source_R25_bound_inputs'].items():assert C.sha(A.read(p))==pin,p
 source=A.read(Path(receipt['source_parent']));assert C.sha(source)==receipt['source_parent_sha256'];identity=N.SourceNets(source)
 before=pickle.loads(A.read(rp/'geometry.pkl'));base=pickle.loads(A.read(rp/'discrete.pkl'));zones=pickle.loads(A.read(rp/'proposed-zones.pkl'));old,_,_,_,_=pickle.loads(A.read(FP.parent/'sbc-power/io3-field-crossings-r15/model.pkl'))
 removed=set(receipt['removed_source_UUIDs']);bt={t['uuid']:t for t in base['tracks']};parsed={u:G.parse(u,ch.encode(),{}) for u,ch in receipt['exact_new_chunks'].items()};identity.assert_chunks({u:ch.encode() for u,ch in receipt['exact_new_chunks'].items()})
 for u,ch in receipt['exact_removed_chunks'].items():
  b=ch.encode();i=source.index(b);assert source.count(b)==1;row=G.parse(u,b,{});t=bt[u];assert(row['layer'],row['w'],row['net'],tuple(row['a']),tuple(row['b']))==(t['layer'],t['w'],L.norm(t['net']),tuple(t['a']),tuple(t['b']))
 nv=[];nt=[]
 for u,q in parsed.items():
  assert q['net'] in(GROUND,GATE,POWER)
  if q['kind']=='via':
   assert q['net']==GROUND and(q['d'],q['drill'])==(.5,.2);nv.append({'uuid':u,'net':identity.raw(q['net']),'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill'],'span':['F.Cu','B.Cu'],'flashed':LAYERS})
  else:
   assert q['kind']=='segment' and ((q['net']==POWER and q['layer']=='B.Cu' and q['w']==.3) or(q['net'] in(GROUND,GATE) and q['layer']=='F.Cu' and q['w']==.2));nt.append({'uuid':u,'net':identity.raw(q['net']),'a':q['a'],'b':q['b'],'w':q['w'],'layer':'F.Cu'})
 assert len(nv)==2 and len(nt)==6 and len(removed)==6
 h={**base,'tracks':[t for t in base['tracks'] if t['uuid'] not in removed]+nt,'vias':base['vias']+nv};records,trees=F.build({**h,'zones':[]});errors=[];clear=[]
 def gap(net,other):return .15 if h['domains_normalized'].get(L.norm(net))==h['domains_normalized'].get(L.norm(other)) else .6
 for q in nv+nt:
  net=L.norm(q['net']);body=Point(q['x'],q['y']).buffer(q['d']/2,quad_segs=128) if 'd' in q else A.shape({'kind':'segment',**q});ls=LAYERS if 'd' in q else[q['layer']];mins=[]
  for l in ls:
   near=[]
   for i in trees[l].query(body.buffer(.7),predicate='intersects'):
    r=records[l][int(i)]
    if L.norm(r['net'])==net:continue
    d=body.distance(r['shape']);req=gap(net,r['net'])+.025;near.append((d,r['uuid'],r['net'],req))
    if d<req-1e-8:errors.append({'kind':'FOREIGN_DISCRETE_Cu','uuid':q['uuid'],'layer':l,'other_uuid':r['uuid'],'other_net':r['net'],'distance_mm':d,'required_mm':req})
   for z in zones:
    if z['layer']!=l or L.norm(z['net'])==net:continue
    d=body.distance(z['shape']);req=gap(net,z['net'])+.025
    if d<req-1e-8:errors.append({'kind':'PROPOSED_FOREIGN_ZONE','uuid':q['uuid'],'layer':l,'other_uuid':z['uuid'],'other_net':z['net'],'distance_mm':d,'required_mm':req})
   mins.append({'layer':l,'nearest_foreign':min(near) if near else None})
  clear.append({'uuid':q['uuid'],'per_layer':mins})
 smd=[{'pad_uuid':p['uuid'],'ref':p['ref'],'pin':p['num'],'shape':sh} for p in h['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(rs)];st=STRtree([p['shape'] for p in smd]);aperture=[]
 for v in nv:
  point=Point(v['x'],v['y']);near=smd[int(st.nearest(point))];d=point.distance(near['shape'])-v['drill']/2-.005
  holes=[{'uuid':q['uuid'],'gap_mm':point.distance(sh)-v['drill']/2-.005,'kind':'pad'} for q in h['pads'] for sh in L.poly(q.get('hole') or [])]
  holes += [{'uuid':q['uuid'],'gap_mm':point.distance(Point(q['x'],q['y']))-(v['drill']+q['drill'])/2,'kind':'via','centre_mm':point.distance(Point(q['x'],q['y']))} for q in h['vias'] if q['uuid']!=v['uuid']]
  minh=min(holes,key=lambda q:q['gap_mm']);minpitch=min((q for q in holes if q['kind']=='via'),key=lambda q:q['centre_mm']);row={'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'nearest_SMD_uuid':near['pad_uuid'],'guarded_SMD_hole_edge_mm':d,'nearest_drill':minh,'nearest_via_centre':minpitch,'required_SMD_drill_mm':.275,'required_all_drill_mm':.275,'required_via_pitch_mm':.81};aperture.append(row)
  if d<.275 or minh['gap_mm']<.275 or minpitch['centre_mm']<.81:errors.append({'kind':'ORDINARY_APERTURE_OR_PITCH',**row})

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
 print('C10036_EXACT_CU',len(errors),flush=True)
 after,cutledger=Z.projected(old,h,zones);zonechecks=[];affected={GROUND,GATE,POWER}
 oldzones={z['uuid']:z for z in before['zones']}
 for z in after['zones']:
  prior=oldzones[z['uuid']]
  for l,rs in z['fills'].items():
   a=unary_union(L.poly(prior['fills'].get(l,[])));b=unary_union(L.poly(rs));loss=a.difference(b)
   if loss.area>1e-9:affected.add(L.norm(z['net']));zonechecks.append({'uuid':z['uuid'],'raw_net':z['net'],'layer':l,'lost_area_mm2':loss.area,'actual_native_local_clearance_mm':z.get('clearance_mm'),'after_physical_piece_count':len(pieces(b))})
 contactloss=[];obligations=[];baseline={};final={};ufnew={};source=[]
 for net in sorted(affected):
  print('C10036_PHYSICAL_GRAPH',net,flush=True);ua,aa=physical(before,net);ub,bb=physical(after,net);baseline[net]=aa;final[net]=bb;ufnew[net]=ub;mapping=collections.defaultdict(set)
  for i,xs in enumerate(bb):
   for k in discrete_keys(xs):mapping[k].add(i)
  for i,xs in enumerate(aa):
   keys=discrete_keys(xs)-{('track',u) for u in removed};parts=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set();row={'net':net,'old_group':i,'surviving_discrete_keys':[list(k) for k in sorted(keys)],'new_physical_components':sorted(str(x) for x in parts)};obligations.append(row)
   if len(parts)>1 or 'MISSING' in parts:contactloss.append(row)
 root=next(xs for xs in final[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));source.append({'net':GROUND,'actual_source':'J11005.2','target_C10036_2_in_same_root_group':any(q['kind']=='pad' and(q['ref'],q['pin'])==('C10036','2') for q in root),'new_via_in_same_root_group':all(any(q['uuid']==v['uuid'] for q in root) for v in nv)})
 refs={'F.Cu':unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']=='In1.Cu']),'B.Cu':unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']=='In4.Cu'])};reference=[]
 inherited=next(v for v in before['vias'] if v['uuid']=='40bdf2f9-776c-4aa5-bca6-7921f7c90b54');assert(inherited['x'],inherited['y'],inherited['d'],inherited['drill'],L.norm(inherited['net']))==(66.55,95.35,.6,.3,GATE);native=json.loads(A.read(HERE.parent/'native-198b-geometry/geometry.json'));vold=next(v for v in native['vias'] if v['uuid']==inherited['uuid']);assert(vold['at'],vold['w'],vold['drill'],vold['net'])==([66.55,95.35],.6,.3,inherited['net']);fl=json.loads(A.read(HERE.parent/'native-198b-geometry/actual-via-flashes.json'))['vias'];assert set(fl[inherited['uuid']])==set(inherited['flashed'])==set(LAYERS);paired=next(v for v in nv if v['uuid']==receipt['new_return_UUID']);dist=math.dist((paired['x'],paired['y']),(66.55,95.35));assert .81<=dist<=1.;ann=Point(paired['x'],paired['y']).buffer(.25,quad_segs=128).difference(Point(paired['x'],paired['y']).buffer(.1,quad_segs=128));annareas={l:refs[outer].buffer(-.075).intersection(ann).area for l,outer in [('In1.Cu','F.Cu'),('In4.Cu','B.Cu')]};assert all(a>=.004 for a in annareas.values());pairedproof={'inherited_signal_UUID':inherited['uuid'],'actual_signal_at_mm':[66.55,95.35],'actual_signal_diameter_drill_mm':[.6,.3],'actual_signal_annuli':fl[inherited['uuid']],'new_return_UUID':paired['uuid'],'return_at_mm':[paired['x'],paired['y']],'distance_mm':dist,'finite_source_rooted_annular_interior_mm2':annareas,'source_root':'J11005.2','native_candidate_actual_annuli_and_fills':'OPEN'}
 def vertices(sh):
  if sh.is_empty:return []
  if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for ring in sh.interiors for p in ring.coords]
  return [p for q in sh.geoms for p in vertices(q)]
 for t in nt:
  net=L.norm(t['net'])
  if net not in(GATE,POWER):continue
  body=A.shape({'kind':'segment',**t});uncovered=body.difference(refs[t['layer']]);area=uncovered.area;maxradius=max((math.dist(p[:2],(66.55,95.35)) for p in vertices(uncovered)),default=0.);own=net==GATE and area>1e-9 and maxradius<=.575;reference.append({'uuid':t['uuid'],'net':net,'layer':t['layer'],'full_body_uncovered_mm2':area,'bounds_mm':list(uncovered.bounds) if not uncovered.is_empty else [],'own_transition_exceptions':1 if own else 0,'actual_own_transition_UUID':inherited['uuid'] if own else None,'actual_own_unchanged_radius_mm':.575 if own else None,'maximum_gap_vertex_radius_mm':maxradius if own else None,'convex_analytic_disk_contains_all_gap_vertices_edges_and_interior':own,'radius_expansion_mm':0,'paired_actual_rooted_return_UUID':paired['uuid'] if own else None,'reference_gap_after_exact_own_transition_scope_mm2':0 if own else area})
 referrors=[r for r in reference if r['reference_gap_after_exact_own_transition_scope_mm2']>1e-9]
 oldroot=next(xs for xs in baseline[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));oldrefs={'F.Cu':unary_union([q['shape'] for q in oldroot if q['kind']=='fill' and q['layer']=='In1.Cu']),'B.Cu':unary_union([q['shape'] for q in oldroot if q['kind']=='fill' and q['layer']=='In4.Cu'])};neighbor=[]
 for t in before['tracks']:
  if t['uuid'] in removed or t['layer'] not in refs or L.norm(t['net'])==GROUND or before['domains_normalized'].get(L.norm(t['net']))!=before['domains_normalized'][GROUND]:continue
  body=A.shape({'kind':'segment',**t}) if t.get('m') is None else L.body(t);lost=body.intersection(oldrefs[t['layer']]).difference(refs[t['layer']])
  if lost.area>1e-9:neighbor.append({'uuid':t['uuid'],'net':t['net'],'layer':t['layer'],'prior_source_rooted_reference_lost_mm2':lost.area})
 # Actual native r06/r07/current pad partitions are authoritative, translated
 # only by exact stable source pad UUID identities, not rounded locations.
 counters=collections.Counter();padmap={}
 for p in before['pads']:
  name=p['ref']+'.'+str(p['num']);i=counters[name];counters[name]+=1;padmap[name+'#'+str(i)]=p['uuid']
 nativechecks=[];padloss=[]
 for label,path in [('current198b',G.REPORT/'measure/r07-four-fag-shared/partitions.json'),('r06',P.R.R06_PART),('r07',P.R.R07_PART)]:
  parts={L.norm(n):xs for n,xs in json.loads(A.read(path))['nets'].items()}

  currentpads={p['uuid']:p for p in before['pads']}
  for net in(GATE,POWER,GROUND):
   for rel in parts[net]:
    ids=[padmap[x] for x in rel];unchanged=[u for u in ids if L.norm(currentpads[u]['net'])==net];retagged=[{'uuid':u,'actual_current_raw_net':currentpads[u]['net'],'baseline_raw_net':net,'source_frozen_intentional_retag_authority':'R25 source-parent/fresh070444; full final source ledger remains root-owned'} for u in ids if u not in unchanged];components={ufnew[net].find(('pad',u)) for u in unchanged};row={'baseline':label,'net':net,'exact_native_pad_ids':rel,'physical_pad_UUIDs':ids,'source_net_unchanged_physical_pad_UUIDs':unchanged,'separately_owned_source_retags':retagged,'candidate_component_count':len(components)};nativechecks.append(row)
    if len(components)>1:padloss.append(row)
 passed=not(errors or contactloss or padloss or referrors or neighbor) and all(r['target_C10036_2_in_same_root_group'] and r['new_via_in_same_root_group'] for r in source)
 report={'verdict':'INDEPENDENT_C10036_R25_CONTACT_CLEARANCE_REFERENCE_PASS_NATIVE_AND_MUTUAL_R41_OPEN' if passed else 'INDEPENDENT_C10036_R25_OPERATION_INCOMPLETE','exact_recipe_sha256':C.sha(A.read(HERE/'c10036-r25-reference-bridge-recipe-r24.json')),'source_parent_sha256':receipt['source_parent_sha256'],'same_domain_old_native_fill_retreat_uses_local_clearance_guard':True,'all_drills_subtracted_before_physical_graph':True,'every_fill_and_split_track_piece_has_distinct_graph_identity':True,'new_Cu_clearance':clear,'clearance_errors':errors,'ordinary_aperture':aperture,'source_root_status':source,'complete_surviving_discrete_relationship_obligations':obligations,'surviving_contact_losses':contactloss,'actual_native_gate_pad_partition_checks':nativechecks,'native_gate_pad_relationship_losses':padloss,'prospective_old_fill_deltas':zonechecks,'complete_projection_cuts':cutledger,'new_signal_and_power_full_body_reference':reference,'inherited_transition_qualified_source_return':pairedproof,'new_reference_zone_exact_AST_and_core':zoneproof,'independent_frozen_hard_and_outline_predicates':hardledger,'mutual_R41_source_feed_reference_gate':receipt['R41_mutual_reference_verdict'],'mutual_R41_conflicting_mesh_UUID':receipt['R41_conflicting_prospective_In4_mesh_UUID'],'new_reference_errors':referrors,'unchanged_neighbor_reference_losses':neighbor,'all_new_via_native_all6_annuli':'OPEN; all6 conservative host clearance','new_via_direct_source_annular_contacts':{l:sum(q['shape'].area for q in root if q['uuid']==nv[0]['uuid'] and q['layer']==l) for l in('In1.Cu','In4.Cu')},'signed_gate_waveform_SI_and_ground_current_PDN':'OPEN','full_final_source_current_r06_r07_native_refill_DRC_mutual_power_composition':'OPEN','board_emitted':False,'native_jobs':0,'gpu_jobs':0,'recipe_on_R25_only':True,'R41_future_feed_revision_and_full_final_joint_power_source_capacity_required':True,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 for p,pin in A.READS.items():assert C.sha(Path(p).read_bytes())==pin,p
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'clearance':len(errors),'contact':len(contactloss),'native_pad_losses':len(padloss),'new_reference':len(referrors),'unchanged_reference':len(neighbor),'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()

