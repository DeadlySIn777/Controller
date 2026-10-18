"""Finite rigid R10007 pose screen for the shared clock/fault FG return."""
import hashlib,json,math,pickle,sys
from pathlib import Path
from shapely import affinity
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-R10007-shared-return-rigid-pose-nomination-r213'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl'
 assert sha(mp)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5';g,h,b,q,full=pickle.loads(mp.read_bytes());fp=next(f for f in h['footprints']if f['ref']=='R10007');pads=[p for p in h['pads']if p['ref']=='R10007'];assert len(pads)==2 and fp['value']=='10000R 1%';own={p['uuid']for p in pads};oldsh={p['num']:unary_union(K.L.poly(p['layers']['B.Cu']))for p in pads};court=unary_union(K.L.poly(fp['courtyard']['B']));anchor=(fp['x'],fp['y'])
 nativeids={t['uuid']for t in g['tracks']};terminal=[]
 for t in h['tracks']:
  if t['uuid']not in nativeids or t['layer']!='B.Cu':continue
  if any(K.L.norm(t['net'])==K.L.norm(p['net'])and K.A.shape({'kind':'segment',**t}).intersects(oldsh[p['num']])for p in pads):terminal.append(t)
 withdraw={t['uuid']for t in terminal};primary='ef759308-e664-5253-b016-ff17794eac74';FG='/motherboard_motors/FIELD_GND';CLK='/motherboard_do/DOA_SCLK_FIELD';FLT='/motherboard_do/DOA_FLT_N_FIELD'
 # These wholly unadopted bodies must be rerouted after nomination; no native original waiver.
 newwalls={t['uuid']for t in h['tracks']if t['uuid']not in nativeids and K.L.norm(t['net'])in(FG,CLK,FLT)}
 shared=next(v for v in h['vias']if v['uuid']==primary);shared={**shared,'x':216.964196,'y':144.614062};SG=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');CV=next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f');pair={v['uuid']:Point(shared['x'],shared['y']).distance(Point(v['x'],v['y']))for v in(SG,CV)};assert all(.9<=d<=1 for d in pair.values())
 hard={**h,'pads':[p for p in h['pads']if p['uuid']not in own],'tracks':[t for t in h['tracks']if t['uuid']not in withdraw|newwalls],'vias':[v for v in h['vias']if v['uuid']!=primary]+[shared]};records,trees=K.F.build({**hard,'zones':[]},layers={'B.Cu'});courts=[(f['ref'],s)for f in h['footprints']if f['ref']!='R10007'for s in K.L.poly(f['courtyard'].get('B',[]))];ct=STRtree([s for _,s in courts]);holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in hard['vias']]+[(p['uuid'],s)for p in hard['pads']for s in K.L.poly(p.get('hole')or[])];ht=STRtree([s for _,s in holes]);nativefills=[(z,s)for z in full['zones']if not z.get('prospective_not_native')for s in K.L.poly(z['fills'].get('B.Cu',[]))];ft=STRtree([s for _,s in nativefills]);dom=h['domains_normalized'];gap=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else.6;rows=[];nominees=[];reserve,exempt=K.A.reservations()
 poses=sorted([(a,dx/2,dy/2)for a in(0,90,180,-90)for dx in range(-9,10)for dy in range(-10,11)if a or dx or dy],key=lambda p:(math.hypot(p[1],p[2]),abs(p[0]),p[1],p[2]))
 for angle,dx,dy in poses:
  trans=lambda s:affinity.translate(affinity.rotate(s,angle,origin=anchor),dx,dy);nc=trans(court);new={num:trans(s)for num,s in oldsh.items()};bad=[]
  for j in ct.query(nc.buffer(.025),predicate='intersects'):
   ref,s=courts[int(j)]
   if nc.distance(s)<.025:bad.append({'kind':'courtyard','ref':ref,'actual_mm':nc.distance(s)})
  if bad:rows.append({'pose':[angle,dx,dy],'errors':bad});continue
  for p in pads:
   net=K.L.norm(p['net']);s=new[p['num']]
   for j in trees['B.Cu'].query(s.buffer(.8),predicate='intersects'):
    r=records['B.Cu'][int(j)]
    if K.L.norm(r['net'])==net:continue
    d=s.distance(r['shape']);req=gap(net,r['net'])+.025
    if d<req:bad.append({'kind':'foreign_actual_discrete','pad':p['num'],'UUID':r['uuid'],'actual_mm':d,'required_mm':req})
   for j in ht.query(s.buffer(.275),predicate='intersects'):
    uid,hole=holes[int(j)];d=s.distance(hole)
    if d<.275:bad.append({'kind':'actual_SMD_every_drill','pad':p['num'],'UUID':uid,'actual_mm':d})
   for j in ft.query(s.buffer(.8),predicate='intersects'):
    z,f=nativefills[int(j)];other=K.L.norm(z['net'])
    if other==net or dom[other]==dom[net]:continue
    req=max(gap(net,other),float(z['clearance_mm']))+.025;d=s.distance(f)
    if d<req:bad.append({'kind':'other_domain_original_fill_hard','pad':p['num'],'UUID':z['uuid'],'actual_mm':d,'required_mm':req})
   for z in q:
    if z['layer']=='B.Cu'and K.L.norm(z['net'])!=net and s.distance(z['shape'])<max(gap(net,z['net']),float(z['clearance_mm']))+.025:bad.append({'kind':'current_owned_positive_hard','pad':p['num'],'UUID':z['uuid']})
   for rule in h['rule_areas']:
    if 'B.Cu'in rule['layers']and rule.get('no_pads')and any(s.distance(x)<.025 for x in K.L.poly(rule['outline'])):bad.append({'kind':'native_no_pad_area','pad':p['num'],'UUID':rule['uuid']})
  row={'pose':[angle,dx,dy],'errors':bad};rows.append(row)
  if not bad:
   root=trans(Point(*anchor));row['new_native_root_xy_mm']=[round(root.x,6),round(root.y,6)];row['native_angle_delta_degrees']=(-angle)%360;row['pad_centres_mm']={p['num']:[round(trans(Point(p['x'],p['y'])).x,6),round(trans(Point(p['x'],p['y'])).y,6)]for p in pads};nominees.append(row)
   if len(nominees)>=12:break
 result={'verdict':'RIGID_R10007_POSE_GEOMETRY_NOMINEES_SOURCE_AND_ALL_REWIRING_OPEN'if nominees else'FINITE_RIGID_R10007_POSE_SCREEN_NO_GEOMETRY_NOMINEE','model_sha256':sha(mp),'value_and_pad_UUID_rawnet_local_geometry_preserved':True,'original_footprint':fp,'original_pads':pads,'exact_original_terminal_tracks_to_restore':terminal,'only_unadopted_wall_UUIDs_withdrawn_for_joint_nomination':sorted(newwalls),'new_shared_ground_barrel':shared,'both_actual_signal_return_distances_mm':pair,'rows':rows,'nominees':nominees,'required_next_gates':'new rigid native AST/text/mask/source attestation; both actual old pin-contact graphs after removing old pads; LOGIC_GND rooted source and full new pad/track reference; every native terminal branch restored; FG/clock/fault joint reroute and literal scopes; ordinary all6 barrel/drc/current/native','native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R213_COMPLETE',len(rows),len(nominees),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
