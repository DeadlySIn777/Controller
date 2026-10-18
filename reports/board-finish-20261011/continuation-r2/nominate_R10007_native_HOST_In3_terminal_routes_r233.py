"""Route a supported resistor pose through one real ordinary HOST barrel.

The output is a route nominee, requiring exact joint construction and every
drilled after source/contact/reference gate before any native board adoption.
"""
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import affinity,from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'R10007-joint-B-F-real-source-and-ordinary-return-route-nomination-r233'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir()
 census=H/'R10007-HOST-existing-source-return-B-F-port-screen-r229';cr=census/'receipt.json';ports=json.loads(cr.read_bytes())
 root=H/'U10003-R10007-shared-return-logic-side-source-reference-rigid-pose-nomination-r220';rp=root/'receipt.json';assert sha(rp)=='eee449f4ea7a7ae2b39041cacf46258332b8eb3d6171a868fdefb40bd999409b';r=json.loads(rp.read_bytes())
 mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';assert sha(mp)==ports['model_sha256']==r['model_sha256'];g,h,b,q,full=pickle.loads(mp.read_bytes())
 pads={p['num']:p for p in r['original_pads']};ids={p['uuid']for p in pads.values()};fp=r['original_footprint'];SIG=K.L.norm(pads['1']['net']);LG='/LOGIC_GND'
 refs={l:from_wkb((census/('actual-J1-'+inner+'-source-reference.wkb')).read_bytes())for l,inner in [('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]}
 lgsource=from_wkb((root/'actual-J1-B-full-source-Cu.wkb').read_bytes());hostF=from_wkb((census/'complete-actual-HOST-F-source.wkb').read_bytes())
 withdrawn=set(r['only_unadopted_wall_UUIDs_withdrawn_for_joint_nomination']);assert len(withdrawn)==9
 hard={**h,'pads':[p for p in h['pads']if p['uuid']not in ids],'tracks':[t for t in h['tracks']if t['uuid']not in withdrawn],'vias':[v for v in h['vias']if v['uuid']!=r['new_shared_ground_barrel']['uuid']]+[r['new_shared_ground_barrel']]}
 records,trees=K.F.build({**hard,'zones':[]},layers={'B.Cu','In3.Cu'});dom=h['domains_normalized'];gap=lambda a,c:.15 if dom[K.L.norm(a)]==dom[K.L.norm(c)]else.6
 areas,exempt=K.A.reservations();rows=[];answer=None

 oldterminal=next(v for v in h['vias']if v['uuid']=='a09f14c5-dadb-4548-9346-b2e2be83b03f')
 assert K.L.norm(oldterminal['net'])==SIG and oldterminal['flashed']==list(K.LAYERS) and (oldterminal['x'],oldterminal['y'],oldterminal['d'],oldterminal['drill'])==(206.15,146.15,.6,.3)
 _,hostgroups=K.physical(full,SIG,K.hole_context(full));actualhost=K.root(hostgroups,'U13004','31');assert ('via',oldterminal['uuid'],'In3.Cu')in K.keys(actualhost)
 oldpoint=Point(oldterminal['x'],oldterminal['y']);hostF=oldpoint.buffer(.3,quad_segs=128).difference(oldpoint.buffer(.15,quad_segs=128));oldcap=oldpoint.buffer(.575,quad_segs=128)
 poses=sorted(r['nominees'],key=lambda p:(p['pose']!=[180,-10.5,-3.5],p['pose']!=[0,-10.5,-3.5]))
 for pose in poses:
  angle,dx,dy=pose['pose'];trans=lambda s:affinity.translate(affinity.rotate(s,angle,origin=(fp['x'],fp['y'])),dx,dy);newsh={num:trans(unary_union(K.L.poly(p['layers']['B.Cu'])))for num,p in pads.items()};court=trans(unary_union(K.L.poly(fp['courtyard']['B'])));ordered=sorted(ports['candidates'],key=lambda p:Point(p['signal_xy_mm']).distance(newsh['1']))
  # A finite first64-port screen; further ports remain available after failure.
  for port in ordered[:64]:
   viaxy=port['signal_xy_mm'];vp=Point(viaxy);cap=vp.buffer(.525,quad_segs=128);ann=vp.buffer(.25,quad_segs=128).difference(vp.buffer(.1,quad_segs=128))
   if vp.distance(court)<.35 or any(vp.distance(s)-.1<.275 for s in newsh.values()):continue
   added=[];routed=[];ok=True
   for phase,num,net,layer,startshape,target in [('GND_B','2',LG,'B.Cu',newsh['2'],lgsource),('HOST_B','1',SIG,'B.Cu',newsh['1'],ann),('HOST_IN3',None,SIG,'In3.Cu',ann,hostF)]:
    result=None;ref=refs[layer];allowed=ref.union(cap).union(oldcap)if net==SIG and layer=='In3.Cu'else ref.union(cap)if net==SIG else ref
    for margin in (6,12,20):
     x,y=pose['new_native_root_xy_mm'];win=box(min(x,vp.x)-margin,min(y,vp.y)-margin,max(x,vp.x)+margin,max(y,vp.y)+margin);query=win.buffer(1);cuts=[]
     for j in trees[layer].query(query,predicate='intersects'):
      z=records[layer][int(j)]
      if K.L.norm(z['net'])!=net:cuts.append(N.bounded_buffer(z['shape'].intersection(query),gap(net,z['net'])+.025+.10002))
     if layer=='B.Cu':
      for othernum,s in newsh.items():
       if K.L.norm(pads[othernum]['net'])!=net:cuts.append(N.bounded_buffer(s,gap(net,pads[othernum]['net'])+.025+.10002))
     for t in added:
      if t['layer']==layer and K.L.norm(t['net'])!=net:cuts.append(N.bounded_buffer(LineString([t['a'],t['b']]),gap(net,t['net'])+.025+.20002))
     if net==LG:cuts.append(N.bounded_disk({'x':vp.x,'y':vp.y},.25+.15+.025+.10002))
     for z in q:
      if z['layer']==layer and K.L.norm(z['net'])!=net and z['shape'].intersects(query):cuts.append(N.bounded_buffer(z['shape'].intersection(query),max(gap(net,z['net']),float(z['clearance_mm']))+.025+.10002))
     for z in full['zones']:
      other=K.L.norm(z['net'])
      if other==net or dom[other]==dom[net]:continue
      for s in K.L.poly(z['fills'].get(layer,[])):
       if s.intersects(query):cuts.append(N.bounded_buffer(s.intersection(query),max(gap(net,other),float(z['clearance_mm']))+.025+.10002))
     for v in hard['vias']:
      if K.L.norm(v['net'])!=net and query.intersects(Point(v['x'],v['y'])):cuts.append(N.bounded_disk(v,v['drill']/2+.275+.10002))
     for p in hard['pads']:
      for s in K.L.poly(p.get('hole')or[]):
       if K.L.norm(p['net'])!=net and s.intersects(query):cuts.append(N.bounded_buffer(s,.275+.10002))
     for z in hard['rule_areas']:
      if z.get('no_tracks')and layer in z['layers']:cuts.extend(N.bounded_buffer(s,.025+.10002)for s in K.L.poly(z['outline'])if s.intersects(query))
     for z in areas['keepouts']:
      if layer in z['layers']and net not in exempt.get(z['name'],set()):cuts.extend(N.bounded_buffer(s,.025+.10002)for s in K.L.poly(z['outline'])if s.intersects(query))
     free=win.difference(unary_union(cuts)).intersection(allowed.intersection(query).buffer(-.10002));start=startshape.buffer(-.005).intersection(free);end=target.intersection(query).buffer(-.005).intersection(free);common=[]
     for part in K.RF.parts(free):
      aa=start.intersection(part);bb=end.intersection(part)
      if not aa.is_empty and not bb.is_empty:common.append((part,aa,bb))
     rows.append({'pose':pose['pose'],'port_xy_mm':viaxy,'phase':phase,'margin_mm':margin,'common_faces':len(common),'start_area_mm2':start.area,'target_area_mm2':end.area})
     for part,aa,bb in common:
      p1,p2=nearest_points(aa,bb);ends=[(round(p.x,6),round(p.y,6))for p in(p1,p2)]
      if not all(part.covers(Point(p))for p in ends):continue
      axis=LineString(ends)
      if not part.covers(axis):
       try:xy,_=T.route(part,*ends);axis=LineString([(round(x,6),round(y,6))for x,y in xy])
       except(ValueError,AssertionError):continue
      if not part.covers(axis):continue
      xy=list(axis.coords);tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R10007-r233/'+str(pose['pose'])+'/'+str(viaxy)+'/'+phase+'/'+str(i))),'net':pads['2'if net==LG else'1']['net'],'layer':layer,'w':.2,'a':list(a),'b':list(bb),'prospective_not_native':True}for i,(a,bb)in enumerate(zip(xy,xy[1:]))if a!=bb];body=unary_union([K.A.shape({'kind':'segment',**t})for t in tracks])
      if not tracks or not body.difference(allowed).is_empty or min(body.intersection(startshape).area,body.intersection(target).area)<=0:continue
      result={'phase':phase,'layer':layer,'tracks':tracks,'length_mm':axis.length,'full_body_source_reference_or_exact_supported_own_cap_empty_gap':True,'source_and_target_overlap_mm2':[body.intersection(startshape).area,body.intersection(target).area]};routed.append(result);added+=tracks;break
     if result:break
    if not result:ok=False;break
   print('R233_ATTEMPT',pose['pose'],viaxy,'phases',len(routed),'positive',ok,flush=True)
   if ok:answer={'pose':pose,'ordinary_HOST_port':port,'new_tracks':added,'routes':routed,'HOST_transport_layer_segments':['B.Cu','In3.Cu'],'exact_own_source_cap_radius_mm':.525};break
  if answer:break
 result={'verdict':'THREE_ACTUAL_SOURCE_ROUTES_NOMINATED_JOINT_CONSTRUCTION_AFTER_GRAPHS_REFERENCE_NATIVE_OPEN'if answer else'FINITE_FIRST64_PER_POSE_B_F_ROUTING_NO_NOMINEE','model_sha256':sha(mp),'port_census_sha256':sha(cr),'pose_receipt_sha256':sha(rp),'nominee':answer,'finite_rows':rows,'withdrawn_only_nine_unadopted_tracks':sorted(withdrawn),'original_Cu_deleted':0,'own_signal_cap_source_ret_annuli_required_by_port_census':True,'ordinary_return_window_mm':[.9,1],'existing_actual_HOST_source_terminal_UUID':oldterminal['uuid'],'existing_actual_source_terminal_mask_all6_unchanged':True,'terminal_own_radius_mm':.575,'existing_terminal_scope_authority_and_actual_source_ref_after_gates':'OPEN; raw inherited-before gaps must be distinguished, no neighboring aperture borrow','native_jobs':0,'adopted':False,'manufacturing_ready':False}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R233_COMPLETE',bool(answer),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
