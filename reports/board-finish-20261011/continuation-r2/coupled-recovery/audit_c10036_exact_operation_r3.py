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
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
GROUND='/motherboard_do/FIELD_B_0V';GATE='/motherboard_do/DO12_RCB_GATE';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
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
 started=time.monotonic();out=HERE/'c10036-exact-operation-independent-r3.json';assert not out.exists();rp=FP/'local-and-b5-return-audit-r25'
 receipt=json.loads(A.read(HERE/'c10036-coupled-wall-exact-recipe-r2.json'));assert C.sha(A.read(HERE/'c10036-coupled-wall-exact-recipe-r2.json'))=='1c10f6d5e79727bfc49d19d77ee1a73fd0532c7aace5f05d271c567e3873810f'
 for p,pin in receipt['read_files_sha256'].items():assert C.sha(Path(p).read_bytes())==pin,p
 for p,pin in receipt['source_R25_bound_inputs'].items():assert C.sha(A.read(p))==pin,p
 source=A.read(Path(receipt['source_parent']));assert C.sha(source)==receipt['source_parent_sha256'];identity=N.SourceNets(source)
 before=pickle.loads(A.read(rp/'geometry.pkl'));base=pickle.loads(A.read(rp/'discrete.pkl'));zones=pickle.loads(A.read(rp/'proposed-zones.pkl'));old,_,_,_,_=pickle.loads(A.read(FP.parent/'sbc-power/io3-field-crossings-r15/model.pkl'))
 removed=set(receipt['removed_source_UUIDs']);bt={t['uuid']:t for t in base['tracks']};parsed={u:G.parse(u,ch.encode(),{}) for u,ch in receipt['exact_new_chunks'].items()};identity.assert_chunks({u:ch.encode() for u,ch in receipt['exact_new_chunks'].items()})
 for u,ch in receipt['exact_removed_chunks'].items():
  b=ch.encode();i=source.index(b);assert source.count(b)==1;row=G.parse(u,b,{});t=bt[u];assert(row['layer'],row['w'],row['net'],tuple(row['a']),tuple(row['b']))==(t['layer'],t['w'],L.norm(t['net']),tuple(t['a']),tuple(t['b']))
 nv=[];nt=[]
 for u,q in parsed.items():
  assert q['net'] in(GROUND,GATE)
  if q['kind']=='via':
   assert q['net']==GROUND and(q['d'],q['drill'])==(.5,.2);nv.append({'uuid':u,'net':identity.raw(q['net']),'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill'],'span':['F.Cu','B.Cu'],'flashed':LAYERS})
  else:
   assert q['kind']=='segment' and q['layer']=='F.Cu' and q['w']==.2;nt.append({'uuid':u,'net':identity.raw(q['net']),'a':q['a'],'b':q['b'],'w':q['w'],'layer':'F.Cu'})
 assert len(nv)==1 and len(nt)==4 and len(removed)==5
 h={**base,'tracks':[t for t in base['tracks'] if t['uuid'] not in removed]+nt,'vias':base['vias']+nv};records,trees=F.build({**h,'zones':[]});errors=[];clear=[]
 def gap(net,other):return .15 if h['domains_normalized'].get(L.norm(net))==h['domains_normalized'].get(L.norm(other)) else .6
 for q in nv+nt:
  net=L.norm(q['net']);body=Point(q['x'],q['y']).buffer(q['d']/2,quad_segs=128) if 'd' in q else L.body(q);ls=LAYERS if 'd' in q else[q['layer']];mins=[]
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
 print('C10036_EXACT_CU',len(errors),flush=True)
 after,cutledger=Z.projected(old,h,zones);zonechecks=[];affected={GROUND,GATE}
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
 root=next(xs for xs in final[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));source.append({'net':GROUND,'actual_source':'J11005.2','target_C10036_2_in_same_root_group':any(q['kind']=='pad' and(q['ref'],q['pin'])==('C10036','2') for q in root),'new_via_in_same_root_group':any(q['uuid']==nv[0]['uuid'] for q in root)})
 refs={'F.Cu':unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']=='In1.Cu']),'B.Cu':unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']=='In4.Cu'])};reference=[]
 for t in nt:
  if L.norm(t['net'])!=GATE:continue
  body=L.body(t);uncovered=body.difference(refs['F.Cu']);reference.append({'uuid':t['uuid'],'net':GATE,'layer':'F.Cu','full_body_uncovered_mm2':uncovered.area,'bounds_mm':list(uncovered.bounds) if not uncovered.is_empty else [],'own_transition_exceptions':0})
 referrors=[r for r in reference if r['full_body_uncovered_mm2']>1e-9]
 oldroot=next(xs for xs in baseline[GROUND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));oldrefs={'F.Cu':unary_union([q['shape'] for q in oldroot if q['kind']=='fill' and q['layer']=='In1.Cu']),'B.Cu':unary_union([q['shape'] for q in oldroot if q['kind']=='fill' and q['layer']=='In4.Cu'])};neighbor=[]
 for t in before['tracks']:
  if t['uuid'] in removed or t['layer'] not in refs or L.norm(t['net'])==GROUND or before['domains_normalized'].get(L.norm(t['net']))!=before['domains_normalized'][GROUND]:continue
  body=L.body(t);lost=body.intersection(oldrefs[t['layer']]).difference(refs[t['layer']])
  if lost.area>1e-9:neighbor.append({'uuid':t['uuid'],'net':t['net'],'layer':t['layer'],'prior_source_rooted_reference_lost_mm2':lost.area})
 # Actual native r06/r07/current pad partitions are authoritative, translated
 # only by exact stable source pad UUID identities, not rounded locations.
 counters=collections.Counter();padmap={}
 for p in before['pads']:
  name=p['ref']+'.'+str(p['num']);i=counters[name];counters[name]+=1;padmap[name+'#'+str(i)]=p['uuid']
 nativechecks=[];padloss=[]
 for label,path in [('current198b',G.REPORT/'measure/r07-four-fag-shared/partitions.json'),('r06',P.R.R06_PART),('r07',P.R.R07_PART)]:
  parts={L.norm(n):xs for n,xs in json.loads(A.read(path))['nets'].items()}
  for rel in parts[GATE]:
   ids=[padmap[x] for x in rel];components={ufnew[GATE].find(('pad',u)) for u in ids};row={'baseline':label,'net':GATE,'exact_native_pad_ids':rel,'physical_pad_UUIDs':ids,'candidate_component_count':len(components)};nativechecks.append(row)
   if len(components)>1:padloss.append(row)
 passed=not(errors or contactloss or padloss or referrors or neighbor) and all(r['target_C10036_2_in_same_root_group'] and r['new_via_in_same_root_group'] for r in source)
 report={'verdict':'INDEPENDENT_C10036_PHYSICAL_CONTACT_CLEARANCE_REFERENCE_PASS_NATIVE_PENDING' if passed else 'INDEPENDENT_C10036_OPERATION_INCOMPLETE','exact_recipe_sha256':C.sha(A.read(HERE/'c10036-coupled-wall-exact-recipe-r2.json')),'source_parent_sha256':receipt['source_parent_sha256'],'same_domain_old_native_fill_retreat_uses_local_clearance_guard':True,'all_drills_subtracted_before_physical_graph':True,'every_fill_and_split_track_piece_has_distinct_graph_identity':True,'new_Cu_clearance':clear,'clearance_errors':errors,'ordinary_aperture':aperture,'source_root_status':source,'complete_surviving_discrete_relationship_obligations':obligations,'surviving_contact_losses':contactloss,'actual_native_gate_pad_partition_checks':nativechecks,'native_gate_pad_relationship_losses':padloss,'prospective_old_fill_deltas':zonechecks,'complete_projection_cuts':cutledger,'new_gate_full_body_reference':reference,'new_reference_errors':referrors,'unchanged_neighbor_reference_losses':neighbor,'all_new_via_native_all6_annuli':'OPEN; all6 conservative host clearance','new_via_direct_source_annular_contacts':{l:sum(q['shape'].area for q in root if q['uuid']==nv[0]['uuid'] and q['layer']==l) for l in('In1.Cu','In4.Cu')},'signed_gate_waveform_SI_and_ground_current_PDN':'OPEN','full_final_source_current_r06_r07_native_refill_DRC_mutual_power_composition':'OPEN','board_emitted':False,'native_jobs':0,'gpu_jobs':0,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 for p,pin in A.READS.items():assert C.sha(Path(p).read_bytes())==pin,p
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'verdict':report['verdict'],'clearance':len(errors),'contact':len(contactloss),'native_pad_losses':len(padloss),'new_reference':len(referrors),'unchanged_reference':len(neighbor),'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
