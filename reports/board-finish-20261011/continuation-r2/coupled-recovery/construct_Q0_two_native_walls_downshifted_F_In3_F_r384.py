"""Exact sparse Q0 nomination; all old power and unrelated discrete Cu hard.

No board, source, project or native process is modified. Full source/current/
reference/native qualification remains separate from this constructive probe.
"""
import sys,json,pickle,hashlib,math,re,time,copy
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent;sys.dont_write_bytecode=True
for p in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import tri_route as T
from shapely import affinity,from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
start=time.monotonic();out=H/'Q0-four-wall-two-port-route-constructor-r384';assert not out.exists();out.mkdir()
model=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,current=pickle.loads(model.read_bytes());NET='/motherboard_do/DOA_Q0_READY_N';GND='/motherboard_motors/FIELD_GND';GATE='/motherboard_do/DO00_RCB_GATE';SENSE='/motherboard_do/DOA_Q0_ISNS';dom=h['domains_normalized'];window=box(223,151,240,172)
source=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=K.A.N.SourceNets(source.read_bytes());iv=K.C.inventory(source.read_bytes());operator=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');opbytes=operator.read_bytes();assert b'Everywhere else the 0.90-1.0 mm stitch window and the 0.8 mm via spacing are unchanged.'in opbytes
delete={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'};oldtrack={t['uuid']:t for t in h['tracks']};assert delete<=oldtrack.keys();deleted={u:iv[3][u]for u in delete};padids={p['uuid']for p in h['pads']if p['ref']=='R10016'};pads={p['num']:p for p in h['pads']if p['ref']=='R10016'};newsh={n:affinity.translate(unary_union(K.L.poly(p['layers']['F.Cu'])),xoff=-.5,yoff=-.5)for n,p in pads.items()};sourcepad=next(p for p in h['pads']if(p['ref'],str(p['num']))==('U10004','1'));signalF=unary_union(K.L.poly(sourcepad['layers']['F.Cu']));sites=[('Q0-source',NET,[229.12,157.72]),('Q0-target',NET,[226.668448,163.130309])];newvias=[{'uuid':name,'net':net,'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)}for name,net,at in sites]
newvias.append({'uuid':'Q0-target-return','net':GND,'x':227.618448,'y':163.130309,'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
newvias.append({'uuid':'retained-FLT-return','net':GND,'x':227.496314,'y':157.071677,'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
FLT='/motherboard_do/DOA_FLT_N_FIELD'
groupsfile=P/'field-power/REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r384/actual-drilled-current-groups.pkl';groups=pickle.loads(groupsfile.read_bytes());root=K.root(groups[GND],'J11003','2');retained=[r for r in root if r['uuid']not in padids];uf=K.A.S.UF()
for r in retained:uf.find(r['key'])
for layer in K.LAYERS:
 rr=[r for r in retained if r['layer']==layer];tree=STRtree([r['shape']for r in rr])
 for i,r in enumerate(rr):
  for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
   j=int(j)
   if i<j and r['shape'].distance(rr[j]['shape'])<=.000002:uf.join(r['key'],rr[j]['key'])
rootkey=next(r['key']for r in retained if r['kind']=='pad'and(r['ref'],str(r['pin']))==('J11003','2'));trueRoot=[r for r in retained if uf.find(r['key'])==uf.find(rootkey)];assert K.keys(retained)==K.keys(trueRoot)
oldrefs={l:unary_union([r['shape']for r in trueRoot if r['kind']=='fill'and r['layer']==l]).intersection(window.buffer(2))for l in('In1.Cu','In4.Cu')};zby={z['uuid']:z for z in current['zones']};cutledger=[];refs={}
for layer in('In1.Cu','In4.Cu'):
 rr=[]
 for r in trueRoot:
  if r['kind']!='fill'or r['layer']!=layer or not r['shape'].intersects(window.buffer(2)):continue
  z=zby[r['uuid']];assert 'clearance_mm'in z;rad=.25+max(float(z['clearance_mm']),.15)+.025;cuts=[K.Z.bounded_disk(v,.1 if K.L.norm(v['net'])==GND else rad)for v in newvias];old=r['shape'].intersection(window.buffer(2));new=old.difference(unary_union(cuts));rr.append(new)
  if not old.equals(new):cutledger.append({'zone_UUID':r['uuid'],'layer':layer,'native_local_clearance_mm':float(z['clearance_mm']),'radius_mm':rad,'old_WKB_sha256':K.C.sha(old.wkb),'after_WKB_sha256':K.C.sha(new.wkb),'removed_mm2':old.difference(new).area,'added_mm2':new.difference(old).area})
 refs[layer]=unary_union(rr)
 for name,sh in [('before',oldrefs[layer]),('after',refs[layer])]: (out/(layer+'-'+name+'-rooted-ref-nomination.wkb')).write_bytes(sh.wkb)
put(out/'two-new-via-source-reference-local-cut-ledger.json',cutledger)
groundF=unary_union([r['shape']for r in trueRoot if r['layer']=='F.Cu']);discrete,trees=K.F.build({**h,'zones':[]});holes=[(v['uuid'],K.L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],K.L.norm(p['net']),s)for p in h['pads']for s in K.L.poly(p.get('hole')or[])];reserve,exempt=K.A.reservations();tracks=[];pathrows=[];chunks={}
def req(a,bb):return .15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6
def free(net,layer,reference,peers=(),ignore_new_Q0=False):
 obs=[]
 for j in trees[layer].query(window.buffer(1),predicate='intersects'):
  r=discrete[layer][int(j)]
  if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==net:continue
  obs.append(r['shape'].buffer(req(net,r['net'])+.030,quad_segs=128))
 for n,s in newsh.items():
  if K.L.norm(pads[n]['net'])!=net and layer=='F.Cu':obs.append(s.buffer(req(net,pads[n]['net'])+.030,quad_segs=128))
 for t in peers:
  if t['layer']==layer and K.L.norm(t['net'])!=net:obs.append(K.A.shape({'kind':'segment',**t}).buffer(req(net,t['net'])+.030,quad_segs=128))
 for v in newvias:
  if not ignore_new_Q0 and K.L.norm(v['net'])!=net:obs.append(K.Z.bounded_disk(v,.25+req(net,v['net'])+.030))
 for z in q:
  if z['layer']==layer and K.L.norm(z['net'])not in(net,GND) and z['shape'].distance(window)<1:obs.append(z['shape'].buffer(max(req(net,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
 for z in current['zones']:
  if z.get('prospective_not_native')or K.L.norm(z['net'])==net or dom.get(K.L.norm(z['net']))==dom.get(net):continue
  for s in K.L.poly(z['fills'].get(layer,[])):
   if s.distance(window)<1:obs.append(s.buffer(max(req(net,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
 for u,n,s in holes:
  if n!=net and s.distance(window)<1:obs.append(s.buffer(.280,quad_segs=128))
 for v in newvias:
  if K.L.norm(v['net'])!=net:obs.append(K.Z.bounded_disk(v,.1+.280))
 for r in h['rule_areas']:
  if layer in r['layers']and r.get('no_tracks'):obs.extend(s.buffer(.025,quad_segs=128)for s in K.L.poly(r['outline']))
 for r in reserve['keepouts']:
  if layer in r['layers']and net not in exempt.get(r['name'],set()):obs.extend(s.buffer(.025,quad_segs=128)for s in K.L.poly(r['outline']))
 debug=[]
 for lab,xy in [('source',[229.12,157.72]),('target',[226.668448,163.130309]),('sense-start',[236.8779,156.3691]),('sense-end',[228.96,159.6])]:
  pp=Point(xy);debug.append({'label':lab,'reference_distance_mm':pp.distance(reference),'reference_eroded_contains':reference.buffer(-.105,quad_segs=128).covers(pp),'obstacle_cover_count':sum(s.buffer(.105,quad_segs=128).covers(pp)for s in obs),'own_ground_current_outer_fill_allowed_retreat':True})
 put(out/('debug-'+net.rsplit('/',1)[-1]+'-'+layer+'.json'),debug)
 return window.difference(unary_union(obs)).buffer(-.105,quad_segs=128).intersection(reference.buffer(-.105,quad_segs=128))
def route_attachments(label,net,layer,reference,aa,bb,peers=(),keep_old_reference_body=None,qualified_new_own=None):
 fr=free(net,layer,reference,peers);ar=aa.intersection(fr);br=bb.intersection(fr);row={'label':label,'net':net,'layer':layer,'attachment_areas_mm2':[ar.area,br.area],'path_mm':None,'reference_scope':'actual source-nomination after exact two new signal hole cuts; global source rebuild OPEN'}
 for part in K.RF.parts(fr):
  a0=ar.intersection(part);b0=br.intersection(part)
  if a0.is_empty or b0.is_empty:continue
  p0,p1=nearest_points(a0,b0);ends=[tuple(round(t,6)for t in p.coords[0])for p in(p0,p1)]
  if not all(part.covers(Point(p))for p in ends):continue
  path,search=T.route(part,*ends);path=[[round(v,6)for v in p]for p in path]
  if not part.covers(LineString(path)):continue
  body=unary_union([K.A.shape({'kind':'segment','a':a,'b':bb,'w':.2})for a,bb in zip(path,path[1:])]);novel=body if keep_old_reference_body is None else body.difference(keep_old_reference_body);rawgap=novel.difference(refs['In1.Cu'if layer=='F.Cu'else'In4.Cu']);gap=rawgap if qualified_new_own is None else rawgap.difference(qualified_new_own);row.update(path_mm=path,body_mm2=body.area,raw_actual_body_reference_gap_mm2=rawgap.area,exact_supported_new_own_scope_used=qualified_new_own is not None,novel_actual_body_reference_gap_mm2=gap.area,novel_actual_body_reference_gap_empty=gap.is_empty,search=search)
  if not gap.is_empty:continue
  for a,bb in zip(path,path[1:]):
   uid,ch=identity.serial_segment(net,layer,a,bb,.2);assert uid not in iv[3]and uid not in chunks;chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(net),'layer':layer,'a':a,'b':bb,'w':.2})
  pathrows.append(row);print('Q0_PATH_POSITIVE',label,len(path)-1,LineString(path).length,flush=True);return True
 pathrows.append(row);print('Q0_PATH_INCOMPLETE',label,row['attachment_areas_mm2'],flush=True);return False
from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT
oldFLTvia=next(v for v in h['vias']if v['uuid'].startswith('a01ff36f'));oldFLTreturn=next(v for v in newvias if v['uuid']=='retained-FLT-return');assert .90<=math.dist([oldFLTvia['x'],oldFLTvia['y']],[oldFLTreturn['x'],oldFLTreturn['y']])<=1.0
fltOwn,fltOwnLedger=support_FLT(K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,oldFLTvia,GND,FLT,'In1.Cu')
put(out/'retained-FLT-exact-native-own-aperture-support.json',fltOwnLedger);(out/'retained-FLT-supported-own-aperture-F.wkb').write_bytes(fltOwn.wkb)
flt_old=K.A.shape({'kind':'segment',**oldtrack[next(u for u in delete if u.startswith('c76c0c67'))]});flt_terminal=K.A.shape({'kind':'segment','a':[228.45,157.55],'b':[228.5,157.6],'w':.2});assert flt_terminal.difference(flt_old).is_empty
flt_ok=route_attachments('FLT-single-F-wall-detour-retained-barrel',FLT,'F.Cu',refs['In1.Cu'].union(fltOwn),Point(229.35,158.45),Point(228.5,157.6),tracks,qualified_new_own=fltOwn)
if flt_ok:
 uid,ch=identity.serial_segment(FLT,'F.Cu',[228.45,157.55],[228.5,157.6],.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(FLT),'layer':'F.Cu','a':[228.45,157.55],'b':[228.5,157.6],'w':.2})
# Real new ground-pad source connection: old own pad is absent from trueRoot.
ground_ok=route_attachments('moved-pulldown-real-F-ground',GND,'F.Cu',refs['In1.Cu'],newsh['2'].buffer(-.04,quad_segs=128),groundF.buffer(-.02,quad_segs=128))
# Preserve actual outside chain contacts, including the short retained GATE branch.
gate_ok=True # every original GATE chunk is retained, no detour needed
# Retain exact original terminal physical Cu in the last .5mm before the SENSE
# original plated via. This is an identity-bound old body, never new disk credit.
sense_old=K.A.shape({'kind':'segment',**oldtrack['7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d']});terminal=K.A.shape({'kind':'segment','a':[228.96,159.6],'b':[228.96,160.412],'w':.2});prefix_terminal=K.A.shape({'kind':'segment','a':[228.96,156.3691],'b':[228.96,156.45],'w':.2});carry=terminal.union(prefix_terminal);assert carry.difference(sense_old).is_empty
sense_ok=route_attachments('SENSE-single-old-wall-detour',SENSE,'B.Cu',refs['In4.Cu'],Point(228.96,156.39),Point(228.96,159.6),tracks)
if sense_ok:
 for a,bb in [([228.96,156.3691],[228.96,156.45]),([228.96,159.6],[228.96,160.412])]:
  uid,ch=identity.serial_segment(SENSE,'B.Cu',a,bb,.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(SENSE),'layer':'B.Cu','a':a,'b':bb,'w':.2})
 (out/'SENSE-exact-old-terminal-physical-carry.wkb').write_bytes(carry.wkb)
pairids=['b88b7a49-a1ea-458a-9195-d0a46a3a7f66','Q0-target-return'];pairs=[];qualified=[]
for (label,net,at),pid in zip(sites,pairids):
 v=next(v for v in h['vias']+newvias if v['uuid']==pid);rows=[r for r in trueRoot if r['kind']=='via'and r['uuid']==pid];by={l:unary_union([r['shape']for r in rows if r['layer']==l])for l in('In1.Cu','In4.Cu')};annulus=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));witness={l:{'actual_source_rooted_via_layer_present':not by[l].is_empty,'actual_finite_after_reference_annular_contact_mm2':annulus.intersection(refs[l]).area,'actual_after_interior_annular_contact_mm2':annulus.buffer(-.025,quad_segs=128).intersection(refs[l]).area}for l in by};distance=math.dist(at,[v['x'],v['y']]);pass0=.90<=distance<=1.0 and all((not by[l].is_empty or pid=='Q0-target-return') and witness[l]['actual_after_interior_annular_contact_mm2']>.002 for l in by);pairs.append({'signal_port':label,'existing_return_UUID':pid,'existing_native_return_xy_mm':[v['x'],v['y']],'centre_spacing_mm':distance,'operator_stitch_window_mm':[.90,1.0],'source_return_nomination_pass':pass0,'layers':witness,'native_full_final_source_graph_required':True});qualified.append(pass0)
qref={}
for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
 own=unary_union([K.Z.bounded_disk(v,.525).intersection(oldrefs[inner])for v,ok in zip(newvias[:2],qualified)if ok]);qref[outer]=refs[inner].union(own)
qsource_ok=route_attachments('Q0-F-source',NET,'F.Cu',qref['F.Cu'],signalF.buffer(-.04,quad_segs=128),Point(sites[0][2]),tracks,qualified_new_own=qref['F.Cu'].difference(refs['In1.Cu']))
qtransport_ok=route_attachments('Q0-In3-common-transport',NET,'In3.Cu',qref['B.Cu'],Point(sites[0][2]),Point(sites[1][2]),tracks,qualified_new_own=qref['B.Cu'].difference(refs['In4.Cu']))
qtarget_ok=route_attachments('Q0-F-target-moved-R10016',NET,'F.Cu',qref['F.Cu'],Point(sites[1][2]),newsh['1'].buffer(-.04,quad_segs=128),tracks,qualified_new_own=qref['F.Cu'].difference(refs['In1.Cu']))
identity.assert_chunks(chunks)
for uid,ch in chunks.items():(out/(uid+'.segment-chunk')).write_bytes(ch)
for uid,ch in deleted.items():(out/(uid+'.exact-owned-delete-chunk')).write_bytes(ch)
put(out/'path-nominations.json',pathrows);put(out/'paired-return-nominations.json',pairs);pickle.dump({'tracks':tracks,'new_vias':newvias,'deleted_tracks':sorted(delete),'R10016_translation_mm':[-.5,-.5],'new_pad_shapes':newsh},(out/'sparse-nomination.pkl').open('wb'))
result={'verdict':'CONCRETE_Q0_COUPLED_PATH_NOMINATION_FULL_GATES_OPEN'if all([ground_ok,gate_ok,flt_ok,sense_ok,qsource_ok,qtransport_ok,qtarget_ok,*qualified])else'Q0_COUPLED_PATH_CONSTRUCTOR_INCOMPLETE','input_model_file':str(model),'input_model_sha256':sha(model),'source_file':str(source),'source_sha256':sha(source),'actual_current_source_groups_file':str(groupsfile),'actual_current_source_groups_sha256':sha(groupsfile),'operator_decisions_file':str(operator),'operator_decisions_sha256':sha(operator),'physical_port_preflight_receipt_file':str(H/'Q0-FLT-four-coupled-blockers-two-port-preflight-r348/receipt.json'),'physical_port_preflight_receipt_sha256':sha(H/'Q0-FLT-four-coupled-blockers-two-port-preflight-r348/receipt.json'),'results':{'FLT_detour':flt_ok,'real_moved_ground':ground_ok,'GATE_detour':gate_ok,'SENSE_detour':sense_ok,'Q0_F_source':qsource_ok,'Q0_B_transport':qtransport_ok,'Q0_F_target':qtarget_ok,'qualified_existing_return_nominees':qualified},'added_track_count':len(tracks),'proposed_new_ordinary_all6_signal_via_count':2,'proposed_new_ordinary_all6_GND_via_count':2,'exact_original_track_delete_count':2,'R10016_translation_mm':[-.5,-.5],'source_graph_after_all_cuts':'OPEN','all_old_contacts_source_groups_current_r06_r07_full_native_parity':'OPEN','same_domain_native_fill_retreat_current_contact_source_gates':'OPEN','new_SMD_pad_whole_body_reference_and_DC_loop_SI':'OPEN; no SMD terminal disk waiver','SENSE_terminal_exact_old_physical_body_carry_raw_old_reference_gap_mm2':terminal.difference(refs['In4.Cu']).area,'source_supported_new_own_apertures':'Nomination only; exact BEFORE-source clipped .525 for actual paired returns; global final graph/native required','unchanged_R155_R368_28_R7_CORE_ROOT42_current_native_failures_preserved':True,'production_ready':False,'board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json'),**result['results']}),flush=True)



