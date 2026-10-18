"""Freeze exact DI6 physical nomination and audit latest prospective reference.

Keeps all current fault copper and every FP/net/project/rule byte unchanged.
No native invocation, board emission or acceptance before complete gates.
"""
import sys,pickle,json,math,time,copy,collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import guarded_power_projection_r44 as Z
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_c10036_r24_full_independent_r30 as Q
import audit_ao1_positive_operation_r4 as SERIAL
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
NET='/motherboard_di/DI6_LOGIC';GND='/LOGIC_GND';FAULT='/motherboard_io_control/DI_SENSOR_G2_FAULT';LAYERS=Q.LAYERS
def vertices(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for r in sh.interiors for p in r.coords]
 return [p for q in sh.geoms for p in vertices(q)]
def root_reference(g):
 uf,groups=Q.physical(g,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));refs={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==plane]) for l,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]};return refs,uf,groups,root
def main():
 started=time.monotonic();out=HERE/'di6-direct-latest-power-full-audit-r6.json';assert not out.exists();nompath=HERE/'di6-direct-source-escape-r5.json';nom=json.loads(A.read(nompath));assert C.sha(A.read(nompath))=='cd81ebadb6b7d5a343401734a1142646f3efe50cd9d10d8ae96943f596172e65';attempt=nom['attempts'][-1];assert len(attempt['paths'])==2
 modelpath=HERE.parent/'sbc-power/remaining-core-accepted-checkpoints-r50/stage-10/accepted-checkpoint-model.pkl';old,h,binding,zones,_=pickle.loads(A.read(modelpath));assert C.sha(A.read(modelpath))=='a1d9cc1c180c827f2a3c9582b218d8856b9cf9dc672cb97a6d5e3bbf81348bb3';h=copy.deepcopy(h)
 source=A.read(binding['exact_native_discrete_board_file']);assert C.sha(source)==binding['exact_native_discrete_board_sha256']==nom['source_parent_sha256'];identity=N.SourceNets(source);current=C.inventory(source);r9dir=HERE.parent/'protected24-on-corrected-core-r9';r9=json.loads(A.read(r9dir/'receipt.json'));z9=pickle.loads(A.read(r9dir/'proposed-zones.pkl'));d9=pickle.loads(A.read(r9dir/'proposed-discrete.pkl'));assert C.sha(A.read(r9dir/'proposed-zones.pkl'))==nom['root9_hard_zones_sha256']==r9['proposed_zones_sha256'];assert C.sha(A.read(r9dir/'proposed-discrete.pkl'))==nom['root9_hard_discrete_sha256']==r9['proposed_discrete_sha256']
 replaced=set(r9['invalid_owned_new_planes_replaced']);zids={z['uuid'] for z in z9};zones=[z for z in zones if z['uuid'] not in replaced|zids]+z9
 for k in ('tracks','vias'):
  ids={q['uuid']:q for q in h[k]}
  for q in d9[k]:
   if q['uuid'] not in ids:h[k].append(q)
   else:assert ids[q['uuid']]==q
 # Every affected current control entity remains bound to exact source.
 expected={u:G.parse(u,ch,{}) for u,ch in current[4].items() if G.parse(u,ch,{})['net'] in(NET,FAULT)}
 for k in ('tracks','vias'):
  actual={q['uuid']:q for q in h[k] if L.norm(q['net']) in(NET,FAULT)}
  want={u:q for u,q in expected.items() if(q['kind']=='via')==(k=='vias')};assert set(actual)==set(want)
  for u,q in want.items():
   t=actual[u]
   if k=='vias':assert(t['x'],t['y'],t['d'],t['drill'])==(*q['at'],q['d'],q['drill'])
   else:assert(t['a'],t['b'],t['w'],t['layer'])==(q['a'],q['b'],q['w'],q['layer'])
 policies={L.norm(n):r for n,r in json.loads(A.read(S.CONTROLLED))['nets'].items()};assert policies.get(NET,{}).get('class') in(None,'NONE');assert policies.get(FAULT,{}).get('class') in(None,'NONE')
 print('DI6_LATEST_BEFORE_OUTWARD_PROJECT',flush=True);before,oldcuts=Z.projected(old,h,zones);added={};nv=[];nt=[]
 for net,at in((NET,attempt['signal']),(GND,attempt['return'])):
  u,ch=SERIAL.serial_via(identity,net,at);added[u]=ch;nv.append({'uuid':u,'net':identity.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':LAYERS})
 for path in attempt['paths']:
  for a,b in zip(path['points_mm'],path['points_mm'][1:]):
   u,ch=identity.serial_segment(NET,path['layer'],a,b,.2);added[u]=ch;nt.append({'uuid':u,'net':identity.raw(NET),'layer':path['layer'],'a':a,'b':b,'w':.2})
 assert len(nv)==2 and len(nt)==12 and not set(added)&set(current[3]);identity.assert_chunks(added);h2={**h,'tracks':h['tracks']+nt,'vias':h['vias']+nv};after,newcuts=Z.projected(old,h2,zones)
 print('DI6_ALL_NEW_ORDINARY_CLEARANCE',flush=True);rec,trees=F.build({**h2,'zones':[]});errs=[];clear=[];smd=[(p['uuid'],sh) for p in h2['pads'] if p['smd'] for l,rs in p['layers'].items() if l in('F.Cu','B.Cu') for sh in L.poly(rs)];st=STRtree([q[1] for q in smd]);holes=[(v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)) for v in h2['vias']]+[(p['uuid'],L.norm(p['net']),sh) for p in h2['pads'] for sh in L.poly(p.get('hole') or [])];aperture=[]
 def gap(a,b):return .15 if h2['domains_normalized'].get(L.norm(a))==h2['domains_normalized'].get(L.norm(b)) else .6
 for q in nv+nt:
  net=L.norm(q['net']);body=Point(q['x'],q['y']).buffer(q['d']/2,quad_segs=128) if 'd'in q else A.shape({'kind':'segment',**q});ls=LAYERS if 'd'in q else[q['layer']];mins=[]
  for l in ls:
   near=[]
   for i in trees[l].query(body.buffer(.7),predicate='intersects'):
    r=rec[l][int(i)]
    if L.norm(r['net'])==net:continue
    d=body.distance(r['shape']);req=gap(net,r['net'])+.025;near.append((d,r['uuid'],r['net'],req))
    if d<req-1e-8:errs.append({'kind':'NEW_CU','uuid':q['uuid'],'layer':l,'other_uuid':r['uuid'],'raw_net':r['net'],'gap_mm':d,'required_mm':req})
   for z in zones:
    if z['layer']!=l or L.norm(z['net'])==net:continue
    d=body.distance(z['shape']);req=max(gap(net,z['net']),z.get('clearance_mm',.15))+.025
    if d<req-1e-8:errs.append({'kind':'OWNED_PROPOSED_ZONE','uuid':q['uuid'],'layer':l,'other_uuid':z['uuid'],'gap_mm':d,'required_mm':req})
   mins.append({'layer':l,'nearest_discrete_Cu':min(near) if near else None})
  if 'd'in q:
   p=Point(q['x'],q['y']);i=int(st.nearest(p));d=p.distance(smd[i][1])-q['drill']/2-.005;hd=min((p.distance(sh)-q['drill']/2-.005,u) for u,n,sh in holes if u!=q['uuid']);pitch=min((p.distance(Point(v['x'],v['y'])),v['uuid']) for v in h2['vias'] if v['uuid']!=q['uuid']);row={'uuid':q['uuid'],'guarded_SMD_aperture_mm':d,'nearest_SMD_uuid':smd[i][0],'guarded_drill_aperture':hd,'ordinary_pitch':pitch};aperture.append(row)
   if d<.275 or hd[0]<.275 or pitch[0]<.81:errs.append({'kind':'ORDINARY_APERTURE_PITCH',**row})
  else:
   for u,n,sh in holes:
    if n!=net and body.distance(sh)<.275-1e-8:errs.append({'kind':'FOREIGN_HOLE','uuid':q['uuid'],'other_uuid':u,'gap_mm':body.distance(sh),'required_mm':.275})
  clear.append({'uuid':q['uuid'],'per_layer':mins})
 reserve,exempt=A.reservations();outline=unary_union(L.poly(h['outline'])).buffer(-.525)
 for q in nv+nt:
  net=L.norm(q['net']);isvia='d'in q;body=Point(q['x'],q['y']).buffer(.25,quad_segs=128) if isvia else A.shape({'kind':'segment',**q});ls=LAYERS if isvia else[q['layer']]
  if not outline.covers(body):errs.append({'kind':'OUTLINE','uuid':q['uuid']})
  for r in h['rule_areas']:
   if r.get('no_vias' if isvia else'no_tracks') and set(ls)&set(r['layers']) and any(body.distance(sh)<.025 for sh in L.poly(r['outline'])):errs.append({'kind':'NATIVE_HARD','uuid':q['uuid'],'rule':r['uuid']})
  for r in reserve['keepouts']:
   if net not in exempt.get(r['name'],set()) and set(ls)&set(r['layers']) and any(body.distance(sh)<.025 for sh in L.poly(r['outline'])):errs.append({'kind':'RESERVE','uuid':q['uuid'],'rule':r['name']})
 print('DI6_CU_ERRORS',len(errs),flush=True);print('DI6_BEFORE_ACTUAL_PHYSICAL_LOGIC_ROOT',flush=True);oldrefs,ou,og,oroot=root_reference(before);print('DI6_AFTER_ACTUAL_PHYSICAL_LOGIC_ROOT',flush=True);refs,uf,groups,root=root_reference(after);retuid=nv[1]['uuid'];siguid=nv[0]['uuid'];ann=Point(attempt['return']).buffer(.25,quad_segs=128).difference(Point(attempt['return']).buffer(.1,quad_segs=128));retareas={l:refs[l].buffer(-.075).intersection(ann).area for l in('F.Cu','B.Cu')};returns=[{'signal_UUID':siguid,'return_UUID':retuid,'distance_mm':math.dist(attempt['signal'],attempt['return']),'source_root':'J11001.2','new_return_rooted':('via',retuid) in Q.discrete_keys(root),'finite_annular_interior_mm2':retareas}]
 ev=next(v for v in after['vias'] if v['uuid']=='0ff4e506-7bc1-48ad-91fd-aeb598e74c7a');er=next(v for v in after['vias'] if v['uuid']=='cb1390c8-49e9-4971-9ee8-740c03e5b93f');ea=Point(er['x'],er['y']).buffer(er['d']/2,quad_segs=128).difference(Point(er['x'],er['y']).buffer(er['drill']/2,quad_segs=128));returns.append({'signal_UUID':ev['uuid'],'return_UUID':er['uuid'],'distance_mm':math.dist((ev['x'],ev['y']),(er['x'],er['y'])),'source_root':'J11001.2','existing_return_rooted':('via',er['uuid']) in Q.discrete_keys(root),'actual_existing_signal_flash':ev['flashed'],'actual_existing_return_flash':er['flashed'],'finite_annular_interior_mm2':{l:refs[l].buffer(-.075).intersection(ea).area for l in('F.Cu','B.Cu')}})
 reference=[];gaps=[];gd=HERE/'di6-direct-r6-reference-gaps';gd.mkdir()
 for t in nt:
  body=A.shape({'kind':'segment',**t});uncovered=body.difference(refs[t['layer']]);voids=[(attempt['signal'],.525),(nom['actual_existing_target_via']['at_mm'],.575)];remaining=uncovered
  for at,radius in voids:remaining=remaining.difference(Point(at).buffer(radius,quad_segs=128))
  pts=vertices(remaining);analytic=bool(pts) and all(any(math.dist(p[:2],at)<=radius for at,radius in voids) for p in pts);row={'uuid':t['uuid'],'layer':t['layer'],'actual_source_rooted_full_body_gap_mm2':uncovered.area,'gap_outside_exact_own_native_local_voids_mm2':0 if analytic else remaining.area,'analytic_convex_disk_only':analytic,'own_voids':[{'at_mm':at,'radius_mm':r,'native_reference_local_mm':.25,'radius_expansion_mm':0} for at,r in voids]}
  if row['gap_outside_exact_own_native_local_voids_mm2']>1e-9:p=gd/(t['uuid']+'.wkb');p.write_bytes(remaining.wkb);row.update(gap_WKB_path=str(p),gap_WKB_sha256=C.sha(remaining.wkb),bounds_mm=remaining.bounds);gaps.append(row)
  reference.append(row)
 # Full surviving pad/annulus/track relationships for every additionally cut net.
 oldzs={z['uuid']:z for z in before['zones']};affected={NET,GND};fillchanges=[]
 for z in after['zones']:
  oz=oldzs[z['uuid']]
  for l,rs in z['fills'].items():
   a=unary_union(L.poly(oz['fills'].get(l,[])));b=unary_union(L.poly(rs));loss=a.difference(b)
   if loss.area>1e-9:affected.add(L.norm(z['net']));fillchanges.append({'uuid':z['uuid'],'net':z['net'],'layer':l,'lost_mm2':loss.area,'local_clearance_mm':z.get('clearance_mm')})
 obligations=[];lostcontacts=[];netufs={};netgroups={}
 for n in sorted(affected):
  print('DI6_COMPLETE_CONTACT_NET',n,flush=True)
  if n==GND:aa,bb,ub=og,groups,uf
  else:_,aa=Q.physical(before,n);ub,bb=Q.physical(after,n)
  netufs[n]=ub;netgroups[n]=bb;mapping=collections.defaultdict(set)
  for i,xs in enumerate(bb):
   for k in Q.discrete_keys(xs):mapping[k].add(i)
  for i,xs in enumerate(aa):
   keys=Q.discrete_keys(xs);parts=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set();row={'net':n,'original_group':i,'surviving_keys':[list(k) for k in sorted(keys)],'new_components':sorted(str(j) for j in parts)};obligations.append(row)
   if len(parts)>1 or 'MISSING' in parts:lostcontacts.append(row)
 counts=collections.Counter();padmap={}
 for p in before['pads']:
  name=p['ref']+'.'+str(p['num']);i=counts[name];counts[name]+=1;padmap[name+'#'+str(i)]=p['uuid']
 nativechecks=[];padloss=[]
 for label,path in [('current198b',G.REPORT/'measure/r07-four-fag-shared/partitions.json'),('r06',P.R.R06_PART),('r07',P.R.R07_PART)]:
  native={L.norm(n):xs for n,xs in json.loads(A.read(path))['nets'].items()}
  for rel in native[NET]:
   ids=[padmap[p] for p in rel];parts={netufs[NET].find(('pad',u)) for u in ids};row={'baseline':label,'exact_native_pad_ids':rel,'physical_pad_UUIDs':ids,'candidate_components':len(parts)};nativechecks.append(row)
   if len(parts)>1:padloss.append(row)
 neighbor=[]
 for t in before['tracks']:
  if t['layer'] not in refs or L.norm(t['net'])==GND or before['domains_normalized'].get(L.norm(t['net']))!=before['domains_normalized'][GND]:continue
  body=A.shape({'kind':'segment',**t});loss=body.intersection(oldrefs[t['layer']]).difference(refs[t['layer']])
  if loss.area>1e-9:neighbor.append({'uuid':t['uuid'],'net':t['net'],'layer':t['layer'],'prior_source_reference_lost_mm2':loss.area})
 cache=HERE/'di6-direct-latest-power-r6-model.pkl';cache.write_bytes(pickle.dumps({'before':before,'after':after,'h':h,'h2':h2,'old':old,'zones':zones,'oldrefs':oldrefs,'refs':refs,'groups':groups,'root':root,'new':added,'nv':nv,'nt':nt,'binding':binding},protocol=5));passed=not(errs or gaps or padloss or lostcontacts or neighbor) and all(.81<=r['distance_mm']<=1 and all(a>=.004 for a in r['finite_annular_interior_mm2'].values()) for r in returns)
 result={'verdict':'EXACT_DI6_DIRECT_LATEST_POWER_HOST_GATES_PASS_INDEPENDENT_NATIVE_OPEN' if passed else'EXACT_DI6_DIRECT_LATEST_POWER_HOST_GATES_INCOMPLETE','source_parent':binding['exact_native_discrete_board_file'],'source_parent_sha256':C.sha(source),'parent_model_sha256':C.sha(A.read(modelpath)),'root9_receipt_sha256':C.sha(A.read(r9dir/'receipt.json')),'ordinary_policy':policies.get(NET),'exact_deleted_current_chunks':{},'exact_new_chunks':{u:ch.decode() for u,ch in added.items()},'new_items_counts':{'vias':2,'segments':12},'all_current_fault_copper_preserved':True,'all20_absent_original_DI6_withdrawables_superseded_by_new_direct_path':nom['withdrawn_original_DI6_UUIDs_not_blindly_restored'],'withheld_original_drill_conflict_preserved':True,'clearance':clear,'clearance_errors':errs,'ordinary_aperture':aperture,'actual_source_rooted_returns':returns,'new_full_body_reference':reference,'reference_gaps':gaps,'current_r06_r07_pad_relationships':nativechecks,'pad_losses':padloss,'full_surviving_contact_obligations':obligations,'contact_losses':lostcontacts,'old_zone_new_cut_delta':fillchanges,'old_projection_ledger':oldcuts,'new_projection_ledger':newcuts,'unchanged_neighbor_reference_losses':neighbor,'saved_model':str(cache),'saved_model_sha256':C.sha(cache.read_bytes()),'full_native_refill_DRC_all6_source_wholeboard_r06_r07_SI_current':'OPEN','native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'verdict':result['verdict'],'clearance':len(errs),'new_reference':len(gaps),'padloss':len(padloss),'contacts':len(lostcontacts),'neighbors':len(neighbor),'returns':returns,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
