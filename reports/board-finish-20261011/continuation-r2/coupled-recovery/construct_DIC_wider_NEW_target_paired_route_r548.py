"""Materially wider NEW DIC target port/transport construction.

Only the unaccepted target signal/return, seven new In2 tracks and one new
target F track are withdrawable. Source F, every original chunk, fixed
neighbor reroute and the <=3 F/In2/F legs remain exact. Saved .90-1.0 mm
pair spacing stays hard. No native/source writes or reference adoption.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math,collections
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def serial(p):return [round(x,6)for x in p.coords[0]]

def main():
 st=time.monotonic();out=H/'DIC-wider-NEW-target-paired-route-r548';assert not out.exists();out.mkdir()
 mp=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(mp)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14'
 bf=H/'Q0-R526-full-current-contacts-source-reference-r528/actual-before-and-after-source-banks.pkl';assert sha(bf)=='9b48079a0eb2b1a592dca1fc195ffe70b350e9ff9a110f069178a9f207db0a17'
 cp=H/'DIC-original-target-and-native-same-net-ports-r546/census-components-only-NOT_ACCEPTED_MODEL.pkl';assert sha(cp)=='da79618735b2406b246a4d53135202eed29780cf31475890a46592fa17f4ab64'
 sp=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sp)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 source=sp.read_bytes();inv=K.C.inventory(source);identity=K.A.N.SourceNets(source);g,h,b,q,c=pickle.loads(mp.read_bytes());cc=pickle.loads(cp.read_bytes());root=pickle.loads(bf.read_bytes())['after']['/LOGIC_GND'];NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';LG='/LOGIC_GND';dom=h['domains_normalized'];gap=lambda a,n:.15 if dom[K.L.norm(a)]==dom[K.L.norm(n)]else .6
 refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')};cz={z['uuid']:z for z in c['zones']};targetpad=cc['target_F_component'];sig=next(v for v in h['vias']if v['uuid']=='55ab5777-4032-59ab-94d1-d5a4478c7a72');ret=next(v for v in h['vias']if v['uuid']=='9ef5dbc8-049b-5a46-b319-e13870c3e4c4');src=next(v for v in h['vias']if v['uuid']=='7a5d26bb-831f-5d1a-9459-60db126ea224')
 targettracks=[t for t in h['tracks']if K.L.norm(t['net'])==NET and(t['layer']=='In2.Cu'or t['uuid']=='d6b8c2fd-6f95-59ce-aba3-a2baec2d0177')];assert len(targettracks)==8
 withheld={sig['uuid'],ret['uuid']}|{t['uuid']for t in targettracks};assert withheld.isdisjoint(inv[3]);records,trees=K.F.build({**h,'zones':[]});window=box(121,84,140,103);reserve,exempt=K.A.reservations();req=[];rrows=[];outmap={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'}
 for outer,inner in outmap.items():
  for j in trees[outer].query(window.buffer(1),predicate='intersects'):
   r=records[outer][int(j)]
   if r['kind']!='track'or r['uuid']in withheld or K.L.norm(r['net'])==LG or dom.get(K.L.norm(r['net']))!=dom[LG]:continue
   needed=r['shape'].intersection(refs[inner])
   if needed.is_empty:continue
   req.append((r,needed));rrows.append({'UUID':r['uuid'],'layer':outer,'raw_net':r['net'],'original_UID':r['uuid']in inv[3],'actual_before_required_source_body':info(needed)})
 put(out/'all-retained-actual-before-source-reference-obligations.json',rrows)
 common=[]
 for p in h['pads']:
  if p['smd']:
   for ly,rs in p['layers'].items():
    if ly in('F.Cu','B.Cu'):common.extend(K.Z.bounded_buffer(sh,.380)for sh in K.L.poly(rs)if sh.distance(window)<.7)
  common.extend(K.Z.bounded_buffer(sh,.380)for sh in K.L.poly(p.get('hole')or[])if sh.distance(window)<.7)
 for v in h['vias']:
  if v['uuid']not in withheld and Point(v['x'],v['y']).distance(window)<1:common.append(K.Z.bounded_disk(v,max(.815,v['drill']/2+.1+.280)))
 for r in h['rule_areas']:
  if r.get('no_vias'):common.extend(K.Z.bounded_buffer(sh,.275)for sh in K.L.poly(r['outline'])if sh.distance(window)<.7)
 loci={};obledger=[]
 for label,net in(('signal',NET),('return',LG)):
  masks=list(common)
  for ly in K.LAYERS:
   for j in trees[ly].query(window.buffer(.9),predicate='intersects'):
    r=records[ly][int(j)]
    if r['uuid']in withheld or K.L.norm(r['net'])==net:continue
    rad=.25+gap(net,r['net'])+.025;masks.append(K.Z.bounded_buffer(r['shape'],rad));obledger.append({'scope':label,'kind':r['kind'],'UUID':r['uuid'],'layer':ly,'raw_net':r['net'],'radius_mm':rad})
   for z in q:
    if z['layer']!=ly or K.L.norm(z['net'])==net or z['shape'].distance(window)>.9:continue
    rad=.25+max(float(z['clearance_mm']),gap(net,z['net']))+.025;masks.append(K.Z.bounded_buffer(z['shape'],rad));obledger.append({'scope':label,'kind':'current_owned_role','UUID':z['uuid'],'layer':ly,'raw_net':z['net'],'radius_mm':rad,'physical_WKB_sha256':K.C.sha(z['shape'].wkb)})
  for r in reserve['keepouts']:
   if net not in exempt.get(r['name'],set()):masks.extend(K.Z.bounded_buffer(sh,.275)for sh in K.L.poly(r['outline'])if sh.distance(window)<.7)
  physical=window.difference(unary_union(masks));safe=physical.difference(unary_union([K.Z.bounded_buffer(body,.525 if label=='signal'else .1)for r,body in req]));loci[label]=(physical,safe);(out/(label+'-all6-physical-locus.wkb')).write_bytes(physical.wkb);(out/(label+'-strict-source-reference-safe-locus.wkb')).write_bytes(safe.wkb)
  print('R548_LOCUS',label,physical.area,safe.area,flush=True)
 put(out/'all6-current-discrete-and-owned-role-hard-ledger.json',obledger)
 # Full .20 F/In2 path masks, including every drilled aperture and frozen
 # native/reserved no_tracks areas. Same-domain native fills may retreat
 # only after a future exact contact/source proof; current owned roles hard.
 def routefree(ly):
  masks=[]
  for j in trees[ly].query(window.buffer(.9),predicate='intersects'):
   r=records[ly][int(j)]
   if r['uuid']in withheld or K.L.norm(r['net'])==NET:continue
   masks.append(K.Z.bounded_buffer(r['shape'],.1+gap(NET,r['net'])+.030))
  for z in q:
   if z['layer']==ly and K.L.norm(z['net'])!=NET and z['shape'].distance(window)<.9:masks.append(K.Z.bounded_buffer(z['shape'],.1+max(float(z['clearance_mm']),gap(NET,z['net']))+.030))
  for v in h['vias']:
   if v['uuid']not in withheld and K.L.norm(v['net'])!=NET and Point(v['x'],v['y']).distance(window)<1:masks.append(K.Z.bounded_disk(v,.1+v['drill']/2+.280))
  for p in h['pads']:
   if K.L.norm(p['net'])!=NET:masks.extend(K.Z.bounded_buffer(sh,.380)for sh in K.L.poly(p.get('hole')or[])if sh.distance(window)<.7)
  for r in h['rule_areas']:
   if ly in r['layers']and r.get('no_tracks'):masks.extend(K.Z.bounded_buffer(sh,.125)for sh in K.L.poly(r['outline'])if sh.distance(window)<.7)
  for r in reserve['keepouts']:
   if ly in r['layers']and NET not in exempt.get(r['name'],set()):masks.extend(K.Z.bounded_buffer(sh,.125)for sh in K.L.poly(r['outline'])if sh.distance(window)<.7)
  return window.difference(unary_union(masks))
 freeF=routefree('F.Cu');freeI=routefree('In2.Cu');(out/'F-strict-fullwidth-physical-centres.wkb').write_bytes(freeF.wkb);(out/'In2-strict-fullwidth-physical-centres.wkb').write_bytes(freeI.wkb)
 targetphysical=[part for part in K.RF.parts(freeF)if not part.intersection(targetpad.buffer(-.105,quad_segs=128)).is_empty];reachable=unary_union(targetphysical);signals=loci['signal'][1].intersection(reachable);(out/'target-F-reachable-reference-safe-signal-locus.wkb').write_bytes(signals.wkb)
 candidates=[]
 for part in K.RF.parts(signals.buffer(-.002,quad_segs=128)):
  for p in(part.representative_point(),nearest_points(Point(sig['x'],sig['y']),part)[1],nearest_points(targetpad,part)[1]):
   at=serial(p)
   if signals.covers(Point(at))and at not in candidates:candidates.append(at)
 # A broad source/target route nomination, not another fixed .82-mm window.
 for ix in range(121*4,140*4+1):
  for iy in range(84*4,103*4+1):
   at=[ix/4,iy/4]
   if signals.covers(Point(at))and at not in candidates:candidates.append(at)
 candidates.sort(key=lambda xy:Point(xy).distance(targetpad));put(out/'wide-target-F-reachable-serialized-signal-candidates.json',candidates)
 # Already existing actual source-linked native ground barrels have no
 # new-hole credit. Original masks are bound separately, never overridden.
 fp=P/'R155-known-reference-native-diagnostic-r157/measure/original-parent-retained-via-actual-flash-masks.json';nativeMasks=json.loads(fp.read_bytes())['retained_original_via_masks'];rootkeys=K.keys(root);existing=[]
 for v in h['vias']:
  if K.L.norm(v['net'])!=LG or v['uuid']in withheld or v['uuid']not in inv[3]:continue
  if not all(('via',v['uuid'],ly)in rootkeys and ly in nativeMasks.get(v['uuid'],[])for ly in('In1.Cu','In4.Cu')):continue
  existing.append(v)
 attempts=[];selected=None
 for xy in candidates:
  p=Point(xy);ss={**sig,'x':xy[0],'y':xy[1]};own=K.Z.bounded_disk(ss,.525);baseRef=refs['In1.Cu'].difference(own);referenced=baseRef.union(own).union(K.Z.bounded_disk(src,.525))
  ff=freeF.intersection(referenced.buffer(-.105,quad_segs=128));ii=freeI.intersection(referenced.buffer(-.105,quad_segs=128));Fpart=next((s for s in K.RF.parts(ff)if s.covers(p)and not s.intersection(targetpad.buffer(-.105,quad_segs=128)).is_empty),None);Ipart=next((s for s in K.RF.parts(ii)if s.covers(p)and s.covers(Point(src['x'],src['y']))),None)
  row={'new_signal_xy_mm':xy,'target_move_mm':p.distance(Point(sig['x'],sig['y'])),'fullwidth_F_target_part':Fpart is not None,'fullwidth_In2_source_part':Ipart is not None,'pair_candidates':[]};attempts.append(row)
  if Fpart is None or Ipart is None:continue
  pairs=[]
  for v in existing:
   d=p.distance(Point(v['x'],v['y']))
   if .90<=d<=1:pairs.append({'return':v,'new':False,'spacing_mm':d})
  ring=K.Z.bounded_disk(ss,1.0).difference(p.buffer(.90,quad_segs=256));rl=loci['return'][1].intersection(ring)
  for part in K.RF.parts(rl.buffer(-.002,quad_segs=128)):
   probes=[part.representative_point(),nearest_points(Point(ret['x'],ret['y']),part)[1]]
   for r in(.925,.95,.975):
    for i in range(96):probes.append(Point(xy[0]+r*math.cos(i*math.pi/48),xy[1]+r*math.sin(i*math.pi/48)))
   for rp in probes:
    rxy=serial(rp);pp=Point(rxy);d=p.distance(pp)
    if not rl.covers(pp)or not .90<=d<=1:continue
    if any([x['return']['x'],x['return']['y']]==rxy for x in pairs):continue
    pairs.append({'return':{**ret,'x':rxy[0],'y':rxy[1]},'new':True,'spacing_mm':d})
  pairs.sort(key=lambda r:(r['new'],math.dist([r['return']['x'],r['return']['y']],[ret['x'],ret['y']])))
  for pair in pairs[:20]:
   rv=pair['return'];rr=Point(rv['x'],rv['y']);ann=rr.buffer(rv['d']/2,quad_segs=128).difference(rr.buffer(rv['drill']/2,quad_segs=128));newrefs={ly:ref.difference(own).difference(K.Z.bounded_disk(rv,rv['drill']/2)if pair['new']else Point())for ly,ref in refs.items()};aa={ly:ann.buffer(-.025,quad_segs=128).intersection(ref).area for ly,ref in newrefs.items()}
   pr={'return_UUID':rv['uuid'],'xy_mm':[rv['x'],rv['y']],'existing_original_native':not pair['new'],'spacing_mm':pair['spacing_mm'],'actual_before_source_annular_interior_after_nominal_new_cuts_mm2':aa}
   row['pair_candidates'].append(pr)
   if any(v<.005 for v in aa.values()):continue
   # Saved other two new returns must be rechecked at their .925 nominees;
   # do not enlarge a signal aperture to justify any pair.
   other=json.loads((H/'DIC-three-return-saved-window-correction-r366/selected-minimal-ground-return-relocations.json').read_bytes());moving=[{**next(v for v in h['vias']if v['uuid']==r['old_return_UUID']),'x':r['new_xy_mm'][0],'y':r['new_xy_mm'][1]}for r in other]
   cuts={ly:[]for ly in refs}
   for rec in root:
    if rec['kind']!='fill'or rec['layer']not in refs:continue
    ly=rec['layer'];local=float(cz[rec['uuid']]['clearance_mm']);svrad=max(.1+.275,.25+max(local,.15)+.025);vs=[(ss,svrad)]+[(v,v['drill']/2)for v in moving]+([(rv,rv['drill']/2)]if pair['new']else[])
    cuts[ly].extend(rec['shape'].intersection(K.Z.bounded_disk(v,rad))for v,rad in vs if Point(v['x'],v['y']).distance(rec['shape'])<=rad)
   finalRef={ly:refs[ly].difference(unary_union(v))for ly,v in cuts.items()};losses=[]
   for r,needed in req:
    loss=needed.difference(finalRef[outmap[r['layer']]])
    if not loss.is_empty:losses.append({'UUID':r['uuid'],'raw_net':r['net'],'layer':r['layer'],'original_UID':r['uuid']in inv[3],'loss':info(loss)})
   pr['strict_retained_reference_losses_after_all_three_return_moves']=losses
   if losses:continue
   refscope=finalRef['In1.Cu'].union(own).union(K.Z.bounded_disk(src,.525));fspace=freeF.intersection(refscope.buffer(-.105,quad_segs=128));ispace=freeI.intersection(refscope.buffer(-.105,quad_segs=128));fpart=next((s for s in K.RF.parts(fspace)if s.covers(p)and not s.intersection(targetpad.buffer(-.105,quad_segs=128)).is_empty),None);ipart=next((s for s in K.RF.parts(ispace)if s.covers(p)and s.covers(Point(src['x'],src['y']))),None)
   if fpart is None or ipart is None:pr['failure']='route_part_after_three_ground_holes';continue
   attachment=serial(nearest_points(p,fpart.intersection(targetpad.buffer(-.105,quad_segs=128)))[1]);routes=[];failed=False
   for ly,part,a,bp in(('F.Cu',fpart,xy,attachment),('In2.Cu',ipart,[src['x'],src['y']],xy)):
    path,search=T.route(part,tuple(a),tuple(bp));path=[serial(Point(z))for z in path];body=unary_union([K.A.shape({'kind':'segment','a':a,'b':b,'w':.2})for a,b in zip(path,path[1:])]);bad=body.difference(refscope)
    routes.append({'layer':ly,'points_mm':path,'width_mm':.2,'fullbody_actual_reference_gap_outside_only_used_new_SIG_and_exact_existing_source_scope':info(bad),'search':search,'length_mm':LineString(path).length})
    if not bad.is_empty:failed=True
   pr['routes']=routes
   if failed:continue
   selected={'signal':ss,'return':rv,'return_is_new':pair['new'],'other_two_saved_return_moves':moving,'routes':routes,'spacing_mm':pair['spacing_mm'],'strict_retained_reference_losses':losses,'source_pair_own_scope_independent_checker_NATIVE_current_allnet_contacts':'OPEN; no generic disk or SAME_PLANE waiver'};break
  print('R548_SITE',len(attempts),xy,'F/I',Fpart is not None,Ipart is not None,'pairs',len(pairs),'selected',selected is not None,flush=True)
  if selected:break
 put(out/'wide-route-and-policy-compliant-pair-screen.json',attempts);put(out/'selected-constructive-nomination.json',selected)
 rec={'verdict':'MATERIALLY_WIDER_NEW_DIC_TARGET_PAIR_AND_F_IN2_PATH_CONSTRUCTIVE_INDEPENDENT_OPEN'if selected else'MATERIALLY_WIDER_NEW_DIC_TARGET_PAIR_AND_ROUTE_INCOMPLETE_NO_GLOBAL_IMPOSSIBILITY','input_model_sha256':sha(mp),'native_source_sha256':sha(sp),'source_bank_sha256':sha(bf),'component_cache_sha256':sha(cp),'original_native_same_NET_vias':0,'only_NEW_withdrawable_UUIDs':sorted(withheld),'kept_source_NEW_signal_and_three_F_tracks':True,'signal_chain':['F.Cu','In2.Cu','F.Cu'],'maximum_layer_legs':3,'strict_saved_return_window_mm':[.90,1.0],'window_mm':list(window.bounds),'physical_and_strict_reference_loci':{k:{'physical':info(v[0]),'safe':info(v[1])}for k,v in loci.items()},'F_target_reachable_safe_signal_locus':info(signals),'serialized_wider_signal_candidate_count':len(candidates),'route_screened_candidate_count':len(attempts),'selected':selected,'original_Cu_locked_chunks_holes_pads_FP_native_outline_source_rules_profiles_unchanged':True,'no_stale_fill_reclaim_or_old_hole_healing_credit':True,'host_own_aperture_support_fullsource_contacts_alllayer_geometry_NATIVE_current_SI':'OPEN','all_inherited_raw_failures_preserved':True,'native_jobs':0,'board_or_current_model_written':False,'adopted':False,'input_SHA256':{str(f.resolve()):sha(f)for f in(Path(__file__),mp,bf,cp,sp,fp)},'output_SHA256':{str(f.resolve()):sha(f)for f in out.iterdir()if f.is_file()},'elapsed_seconds':time.monotonic()-st}
 put(out/'receipt.json',rec);print('R548_COMPLETE',sha(out/'receipt.json'),rec['verdict'],flush=True)
if __name__=='__main__':main()
