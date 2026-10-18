"""Genuine second resistor pose screen around a frozen legal ordinary signal port."""
import json,pickle,hashlib,sys,time,math,traceback,collections
from pathlib import Path
from shapely import affinity,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
P=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381'
Q=H/'sbc-power/CM79-R371-R7036-exact-source-native-Cu-and-local-reference-scope-r389'
N=H/'sbc-power/CM79-R371-R7035-one-ENC-ordinary-signal-via-existing-LG-return-eligibility-r388'
O=H/'sbc-power/CM79-R371-coupled-R7036-minimal-rigid-pad-poses-ordinary-ENC-port-r391'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def moved(scope,pose):
 fp=scope['footprint'];a,dx,dy=pose;rigid=lambda sh:affinity.translate(affinity.rotate(sh,a,origin=(fp['x'],fp['y'])),dx,dy)
 return {'pose':pose,'root_xy':[round(fp['x']+dx,6),round(fp['y']+dy,6)],'court':rigid(unary_union(L.poly(fp['courtyard']['F']))),'pads':[{'old':p,'shape':rigid(unary_union(L.poly(p['layers']['F.Cu']))),'xy':[round(rigid(Point(p['x'],p['y'])).x,6),round(rigid(Point(p['x'],p['y'])).y,6)]}for p in scope['pads']]}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';assert sha(Q/'receipt.json')=='759624f2ed33d21a00b766a12ddeb9fd60ae739a79327da40f356138716103a2'
 g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());s35=pickle.loads((P/'exact-original-R7035-source-native-pose-contact-packet.pkl').read_bytes());s36=pickle.loads((Q/'exact-original-R7036-source-native-pose-contact-packet.pkl').read_bytes());own={p['uuid']for s in(s35,s36)for p in s['pads']};rows=json.loads((N/'finite-ordinary-signal-via-original-source-return-old-mask-native-guard-census.json').read_text());port=next(r for r in rows if r['host_R7035_pose']==[180,-3.4,3.0]and r['new_signal_xy']==[77.607292,26.524919]);assert len(port['deficits'])==2 and {x.get('UUID',x.get('ref'))for x in port['deficits']}=={'425e7f48-d649-4152-89d7-97554df1c73f','R7036'};m35=moved(s35,port['host_R7035_pose']);put(O/'exact-selected-frozen-R388-port-and-R7035-IO3-route.json',port)
 base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};rec,trees=F.build(base,layers={'F.Cu'});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');env=box(70,20,88,34);ref=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In1.Cu']).intersection(env));sig=Point(*port['new_signal_xy']);sigcut=Z.bounded_buffer(sig,.525);ref=ref.difference(sigcut);ioPath=LineString(port['successful_IO3_reconnect']['path']);ioBody=Z.bounded_buffer(ioPath,.1);holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for uid,sh in holes]);courts=[(f['ref'],sh)for f in h['footprints']if f['ref']not in('R7035','R7036')for side,ps in f['courtyard'].items()if side=='F'for sh in L.poly(ps)];ct=STRtree([sh for rr,sh in courts]);reserve,exempt=A.reservations();attempts=[];legal=[];courtSkip=0
 poses=sorted([(a,round(dx*.1,6),round(dy*.1,6))for a in(0,-90,90,180)for dx in range(-30,31)for dy in range(-35,36)if 0<math.hypot(dx*.1,dy*.1)<=3.5],key=lambda v:(math.hypot(v[1],v[2])+.05*abs(v[0])/90,abs(v[1]),v[2],v[0]))
 for pose in poses:
  mm=moved(s36,pose);mc=mm['court']
  if mc.distance(sig)<.275 or mc.distance(m35['court'])<.025:courtSkip+=1;continue
  if any(mc.distance(courts[int(j)][1])<.025 for j in ct.query(mc.buffer(.025),predicate='intersects')):courtSkip+=1;continue
  bad=[];refs=[]
  for np in mm['pads']:
   p=np['old'];sh=np['shape'];net=L.norm(p['net']);rg=sh.difference(ref);refs.append({'pin':p['num'],'whole_actual_In1_reference_gap_EMPTY':rg.is_empty,'gap_mm2':rg.area})
   if not rg.is_empty:bad.append({'kind':'new_whole_SMD_actual_source_In1_reference','pin':p['num'],'gap_mm2':rg.area})
   for j in trees['F.Cu'].query(sh.buffer(1),predicate='intersects'):
    rr=rec['F.Cu'][int(j)]
    if L.norm(rr['net'])==net or rr['kind']=='fill'and L.norm(rr['net'])=='/LOGIC_GND':continue
    local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;req=max(local,gap(net,rr['net']))+.025;dd=sh.distance(rr['shape'])
    if dd<req:bad.append({'kind':'original_foreign_native_Cu','UUID':rr['uuid'],'raw_net':rr['net'],'gap_mm':dd,'required_mm':req})
   for z in q:
    if z['layer']=='F.Cu'and L.norm(z['net'])!=net and sh.distance(z['shape'])<max(float(z['clearance_mm']),gap(net,z['net']))+.025:bad.append({'kind':'foreign_owned_physical_role','UUID':z['uuid']})
   for j in ht.query(sh.buffer(.285),predicate='intersects'):
    uid,hs=holes[int(j)];dd=sh.distance(hs)
    if dd<.28:bad.append({'kind':'all_original_real_hole_new_SMD_guard','UUID':uid,'gap_mm':dd})
   for rules,ex in[(h['rule_areas'],False),(reserve['keepouts'],True)]:
    for rr in rules:
     if 'F.Cu'not in rr['layers']or(not ex and not rr.get('no_pads'))or(ex and net in exempt.get(rr['name'],set())):continue
     if any(sh.distance(rs)<.025 for rs in L.poly(rr['outline'])):bad.append({'kind':'native_or_frozen_reserved_pad_rule','name':rr.get('name',rr.get('uuid'))})
   for np35 in m35['pads']:
    if L.norm(np35['old']['net'])!=net and sh.distance(np35['shape'])<.175:bad.append({'kind':'other_genuinely_moved_R7035_pad','pin':p['num']})
   if sh.distance(ioBody)<.175:bad.append({'kind':'frozen_qualified_IO3_reconnect_foreign_Cu','pin':p['num']})
   if sh.distance(sig)-.25<.175:bad.append({'kind':'new_ordinary_ENC_plus_via_Cu','pin':p['num']})
   if sh.distance(sig)-.1<.28:bad.append({'kind':'new_ordinary_ENC_plus_drill_SMD_guard','pin':p['num']})
  row={'host_R7036_pose':list(pose),'new_root_xy':mm['root_xy'],'new_whole_SMD_source_reference':refs,'deficits':bad};attempts.append(row)
  if not bad:legal.append({'R7036':mm,'R7035':m35,'selected_ordinary_ENC_port':port,'R7036_source_scope':s36})
  if len(attempts)%100==0:put(O/'finite-genuine-R7036-rigid-pad-pose-screen.json',attempts)
 put(O/'finite-genuine-R7036-rigid-pad-pose-screen.json',attempts);(O/'all-pad-legal-genuine-coupled-pose-nominations.pkl').write_bytes(pickle.dumps(legal,protocol=5));put(O/'receipt.json',{'verdict':'GENUINE_COUPLED_R7036_PAD_POSE_SCREEN_NO_ADOPTION','R371_model_sha256':sha(D/'model.pkl'),'R389_exact_scope_receipt_sha256':sha(Q/'receipt.json'),'R388_selected_port_native_and_mask_guards_retained_except_exact_owned_R7036_pad_and_court':True,'candidate_count':len(poses),'courtyard_or_signal_port_prefilter_reject_count':courtSkip,'actual_pad_test_count':len(attempts),'pad_legal_pose_count':len(legal),'minimal_pad_legal_poses':[x['R7036']['pose']for x in legal[:20]],'all_original_Cu_kept_other_than_genuinely_moved_four_owned_SMD_pads':True,'whole_SMD_actual_source_ref_after_explicit_native_SIG_antipad':True,'electrical_reconnects_fullsource_oldref_true_native_pose_masks_current_thermal':'OPEN','model_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R391',sha(O/'receipt.json'),len(poses),len(attempts),len(legal),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
