"""Nominate ordinary HOST ports near real existing two-plane LG returns.

This is only a finite geometry/source screen. No copper or model is written;
joint routing, every old reference and the drilled after graph remain gates.
"""
import hashlib,json,math,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_declared_settings_projection_r58 as N
OUT=H/'R10007-HOST-existing-source-return-B-F-port-screen-r229'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def main():
 assert not OUT.exists();OUT.mkdir()
 rp=H/'U10003-R10007-shared-return-logic-side-source-reference-rigid-pose-nomination-r220/receipt.json'
 assert sha(rp)=='eee449f4ea7a7ae2b39041cacf46258332b8eb3d6171a868fdefb40bd999409b'
 r=json.loads(rp.read_bytes());mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl'
 assert sha(mp)==r['model_sha256'];g,h,b,q,full=pickle.loads(mp.read_bytes())
 own={p['uuid']for p in r['original_pads']};net=K.L.norm(next(p['net']for p in r['original_pads']if p['num']=='1'));LG='/LOGIC_GND'
 withdrawn=set(r['only_unadopted_wall_UUIDs_withdrawn_for_joint_nomination']);assert len(withdrawn)==9
 scene={**full,'pads':[p for p in full['pads']if p['uuid']not in own]}
 _,groups=K.physical(scene,LG,K.hole_context(scene));root=K.root(groups,'J11001','2');kk=K.keys(root)
 refs={l:unary_union([z['shape']for z in root if z['kind']=='fill'and z['layer']==l])for l in ('In1.Cu','In4.Cu')}
 for l,s in refs.items():(OUT/('actual-J1-'+l+'-source-reference.wkb')).write_bytes(s.wkb)
 _,sg=K.physical(scene,net,K.hole_context(scene));host=K.root(sg,'U13004','31');assert any(z['kind']=='pad'and z['ref']=='U10003'and str(z['pin'])=='3'for z in host)
 hostF=unary_union([z['shape']for z in host if z['layer']=='F.Cu']);(OUT/'complete-actual-HOST-F-source.wkb').write_bytes(hostF.wkb)
 hard={**h,'pads':scene['pads'],'tracks':[t for t in h['tracks']if t['uuid']not in withdrawn]}
 records,trees=K.F.build({**hard,'zones':[]});dom=h['domains_normalized'];gap=lambda a,c:.15 if dom[K.L.norm(a)]==dom[K.L.norm(c)]else .6
 courts=[(f['ref'],l,s)for f in h['footprints']if f['ref']!='R10007'for l in ('F','B')for s in K.L.poly(f['courtyard'].get(l,[]))];ct=STRtree([x[2]for x in courts])
 holes=[(v['uuid'],Point(v['x'],v['y']),v['drill']/2)for v in h['vias']]
 ht=STRtree([x[1]for x in holes]);hole_query=max(.815,.1+.275+max(x[2]for x in holes))
 padholes=[s for p in scene['pads']for s in K.L.poly(p.get('hole')or[])];pht=STRtree(padholes)
 foreign={l:[(z,s)for z in full['zones']if K.L.norm(z['net'])!=net and dom[K.L.norm(z['net'])]!=dom[net]for s in K.L.poly(z['fills'].get(l,[]))]for l in K.LAYERS}
 ztrees={l:STRtree([x[1]for x in xs])for l,xs in foreign.items()}
 zquery={l:.25+.025+max([.6]+[float(z['clearance_mm'])for z,s in xs])for l,xs in foreign.items()}
 board_interior=unary_union(K.L.poly(h['outline'])).buffer(-.525)

 smd=[(p['uuid'],s)for p in scene['pads']if p['smd']for l in ('F.Cu','B.Cu')for s in K.L.poly(p['layers'].get(l,[]))];st=STRtree([x[1]for x in smd])
 reserve,exempt=K.A.reservations();window=box(192,125,215,147)
 returns=[v for v in h['vias']if K.L.norm(v['net'])==LG and window.covers(Point(v['x'],v['y']))and all(('via',v['uuid'],l)in kk for l in refs)]
 print('R229_ACTUAL_SOURCE_RETURNS',len(returns),'HOST_F',hostF.bounds,flush=True)
 candidates=[];reason_counts={};tested=0
 interior_refs={l:s.buffer(-.075,quad_segs=128)for l,s in refs.items()}
 for ret in returns:
  centre=Point(ret['x'],ret['y']);ann=centre.buffer(ret['d']/2,quad_segs=128).difference(centre.buffer(ret['drill']/2,quad_segs=128))
  annareas={l:ann.intersection(s).area for l,s in interior_refs.items()}
  if min(annareas.values())<=0:continue
  for radius in (.925,.95,.975):
   for i in range(96):
    a=i*math.tau/96;xy=[round(ret['x']+radius*math.cos(a),6),round(ret['y']+radius*math.sin(a),6)];p=Point(xy);tested+=1;bad=[]
    if not window.covers(p):continue
    if not board_interior.covers(p):bad.append('board_edge')
    for j in ht.query(p.buffer(hole_query),predicate='intersects'):
     uid,c,dr=holes[int(j)]
     if p.distance(c)<.815:bad.append('ordinary_via_pitch');break
     if p.distance(c)-.1-dr<.275:bad.append('drill_to_drill');break
    if bad:reason_counts[bad[0]]=reason_counts.get(bad[0],0)+1;continue
    for j in ct.query(p.buffer(.35),predicate='intersects'):
     if p.distance(courts[int(j)][2])<.35:bad.append('native_courtyard');break
    for j in pht.query(p.buffer(.375),predicate='intersects'):
     if p.distance(padholes[int(j)])-.1<.275:bad.append('pad_hole_to_signal_drill');break
    for j in st.query(p.buffer(.375),predicate='intersects'):
     if p.distance(smd[int(j)][1])-.1<.275:bad.append('SMD_to_drill');break
    for l in K.LAYERS:
     if bad:break
     for j in trees[l].query(p.buffer(1.1),predicate='intersects'):
      z=records[l][int(j)]
      if K.L.norm(z['net'])!=net and p.distance(z['shape'])-.25<gap(net,z['net'])+.025:bad.append('actual_foreign_'+l);break
     for z in q:
      if z['layer']==l and K.L.norm(z['net'])!=net and p.distance(z['shape'])-.25<max(gap(net,z['net']),float(z['clearance_mm']))+.025:bad.append('owned_positive_'+l);break
     for j in ztrees[l].query(p.buffer(zquery[l]),predicate='intersects'):
      z,s=foreign[l][int(j)];other=K.L.norm(z['net'])
      if p.distance(s)-.25<max(gap(net,other),float(z['clearance_mm']))+.025:bad.append('original_other_domain_fill_'+l);break
     for z in h['rule_areas']:
      if z.get('no_vias')and l in z['layers']and any(p.distance(s)<.275 for s in K.L.poly(z['outline'])):bad.append('native_no_via');break
     for z in reserve['keepouts']:
      if l in z['layers']and net not in exempt.get(z['name'],set())and any(p.distance(s)<.275 for s in K.L.poly(z['outline'])):bad.append('reserved');break
    if bad:reason_counts[bad[0]]=reason_counts.get(bad[0],0)+1;continue
    candidates.append({'signal_xy_mm':xy,'signal_size_drill_mm':[.5,.2],'existing_return_UUID':ret['uuid'],'existing_return_xy_mm':[ret['x'],ret['y']],'actual_pair_mm':p.distance(centre),'return_actual_In1_In4_source_annuli_mm2':annareas,'distance_to_complete_actual_HOST_F_mm':p.distance(hostF),'finite_port_only_not_routed':True})
  print('R229_RETURN',ret['uuid'],'ports',len(candidates),flush=True)
 candidates.sort(key=lambda x:(min(Point(x['signal_xy_mm']).distance(Point(*pose['new_native_root_xy_mm']))for pose in r['nominees']),x['distance_to_complete_actual_HOST_F_mm']))
 put('receipt.json',{'verdict':'ORDINARY_EXISTING_SOURCE_RETURN_PORTS_NOMINATED_ROUTES_ALL_REFERENCE_AFTER_GRAPHS_OPEN'if candidates else'FINITE_EXISTING_TWO_PLANE_SOURCE_RETURN_PORT_SCREEN_NO_PORT','model_sha256':sha(mp),'pose_receipt_sha256':sha(rp),'complete_actual_HOST_group_keys':len(K.keys(host)),'real_existing_source_returns':len(returns),'tested_signal_centres':tested,'rejection_counts':reason_counts,'candidates':candidates,'nine_unadopted_bodies_withdrawn_only':sorted(withdrawn),'no_original_Cu_edit':True,'broadphase_only_same_exact_distance_predicates':True,'additional_board_edge_and_native_pad_hole_checks':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False})
 print('R229_COMPLETE',len(candidates),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
