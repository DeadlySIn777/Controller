"""Reconnect a logic-side resistor pose to real retained B copper."""
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import affinity,from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'U10003-R10007-source-reference-B-reconnection-nomination-r221'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();root=H/'U10003-R10007-shared-return-logic-side-source-reference-rigid-pose-nomination-r220';rp=root/'receipt.json';assert sha(rp)=='eee449f4ea7a7ae2b39041cacf46258332b8eb3d6171a868fdefb40bd999409b';r=json.loads(rp.read_bytes());mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';assert sha(mp)==r['model_sha256'];g,h,b,q,full=pickle.loads(mp.read_bytes());pads={p['num']:p for p in r['original_pads']};ids={p['uuid']for p in pads.values()};fp=r['original_footprint'];SIG=K.L.norm(pads['1']['net']);LG='/LOGIC_GND';ref=from_wkb((root/'actual-J1-In4-full-source-reference.wkb').read_bytes());lgsource=from_wkb((root/'actual-J1-B-full-source-Cu.wkb').read_bytes());sigsource=from_wkb((H/'U10003-R10007-rigid-pose-actual-source-bodies-r215/actual-retained-SDI-B-Cu.wkb').read_bytes());hard={**h,'pads':[p for p in h['pads']if p['uuid']not in ids]};records,trees=K.F.build({**hard,'zones':[]},layers={'B.Cu'});areas,exempt=K.A.reservations();dom=h['domains_normalized'];gap=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else.6;rows=[];nominee=None
 for pose in r['nominees']:
  angle,dx,dy=pose['pose'];trans=lambda s:affinity.translate(affinity.rotate(s,angle,origin=(fp['x'],fp['y'])),dx,dy);newsh={num:trans(unary_union(K.L.poly(p['layers']['B.Cu'])))for num,p in pads.items()};added=[];routes=[];ok=True
  for num,net,target in [('2',LG,lgsource),('1',SIG,sigsource)]:
   answer=None
   for margin in(4,8,12):
    x,y=pose['new_native_root_xy_mm'];win=box(x-margin,y-margin,x+margin,y+margin);query=win.buffer(1);cuts=[]
    for j in trees['B.Cu'].query(query,predicate='intersects'):
     z=records['B.Cu'][int(j)]
     if K.L.norm(z['net'])!=net:cuts.append(N.bounded_buffer(z['shape'].intersection(query),gap(net,z['net'])+.025+.10002))
    for othernum,shape in newsh.items():
     othernet=pads[othernum]['net']
     if K.L.norm(othernet)!=net:cuts.append(N.bounded_buffer(shape,gap(net,othernet)+.025+.10002))
    for t in added:
     if K.L.norm(t['net'])!=net:cuts.append(N.bounded_buffer(LineString([t['a'],t['b']]),gap(net,t['net'])+.025+.20002))
    for z in q:
     if z['layer']=='B.Cu'and K.L.norm(z['net'])!=net and z['shape'].intersects(query):cuts.append(N.bounded_buffer(z['shape'].intersection(query),max(gap(net,z['net']),float(z['clearance_mm']))+.025+.10002))
    for z in full['zones']:
     other=K.L.norm(z['net'])
     if other==net or dom[other]==dom[net]:continue
     for sh in K.L.poly(z['fills'].get('B.Cu',[])):
      if sh.intersects(query):cuts.append(N.bounded_buffer(sh.intersection(query),max(gap(net,other),float(z['clearance_mm']))+.025+.10002))
    for v in h['vias']:
     if K.L.norm(v['net'])!=net and query.intersects(Point(v['x'],v['y'])):cuts.append(N.bounded_disk(v,v['drill']/2+.275+.10002))
    for p in h['pads']:
     for sh in K.L.poly(p.get('hole')or[]):
      if K.L.norm(p['net'])!=net and sh.intersects(query):cuts.append(N.bounded_buffer(sh,.275+.10002))
    for area in h['rule_areas']:
     if area.get('no_tracks')and 'B.Cu'in area['layers']:cuts.extend(N.bounded_buffer(sh,.025+.10002)for sh in K.L.poly(area['outline'])if sh.intersects(query))
    for area in areas['keepouts']:
     if 'B.Cu'in area['layers']and net not in exempt.get(area['name'],set()):cuts.extend(N.bounded_buffer(sh,.025+.10002)for sh in K.L.poly(area['outline'])if sh.intersects(query))
    free=win.difference(unary_union(cuts)).intersection(ref.buffer(-.10002));start=newsh[num].buffer(-.02).intersection(free);end=target.buffer(-.005).intersection(free);common=[]
    for part in K.RF.parts(free):
     aa=start.intersection(part);bb=end.intersection(part)
     if not aa.is_empty and not bb.is_empty:common.append((part,aa,bb))
    rows.append({'pose':pose['pose'],'pin':num,'margin_mm':margin,'start_area_mm2':start.area,'real_retained_source_target_area_mm2':end.area,'physical_and_full_source_reference_common_faces':len(common)})
    for part,aa,bb in common:
     a,bb=nearest_points(aa,bb);ends=[(round(p.x,6),round(p.y,6))for p in(a,bb)]
     if not all(part.covers(Point(p))for p in ends):continue
     axis=LineString(ends)
     if not part.covers(axis):
      try:xy,_=T.route(part,*ends);axis=LineString([(round(x,6),round(y,6))for x,y in xy])
      except(ValueError,AssertionError):continue
     if not part.covers(axis):continue
     xy=list(axis.coords);tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R10007-r221/'+str(pose['pose'])+'/'+num+'/'+str(i))),'net':pads[num]['net'],'layer':'B.Cu','w':.2,'a':list(a),'b':list(bb),'prospective_not_native':True}for i,(a,bb)in enumerate(zip(xy,xy[1:]))if a!=bb];body=unary_union([K.A.shape({'kind':'segment',**t})for t in tracks]);rawgap=body.difference(ref)
     if not tracks or not rawgap.is_empty or min(body.intersection(newsh[num]).area,body.intersection(target).area)<=0:continue
     answer={'pin':num,'net':net,'tracks':tracks,'length_mm':axis.length,'strict_full_body_actual_J1_In4_gap_empty':True,'new_pad_and_actual_retained_target_overlap_mm2':[body.intersection(newsh[num]).area,body.intersection(target).area]};added+=tracks;routes.append(answer);break
    if answer:break
   if not answer:ok=False;break
  if ok:nominee={'pose':pose,'new_tracks':added,'routes':routes};break
 result={'verdict':'ACTUAL_SOURCE_REFERENCED_R10007_B_RECONNECTION_NOMINATED_JOINT_FG_CLOCK_FAULT_OPEN'if nominee else'FINITE_R10007_B_RECONNECTION_WITH_FULL_SOURCE_REFERENCE_NO_NOMINEE','pose_receipt_sha256':sha(rp),'model_sha256':sha(mp),'nominee':nominee,'finite_rows':rows,'both_old_pads_removed_from_actual_target_source_witness':True,'exact_original_Cu_deleted':0,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R221_COMPLETE',bool(nominee),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
