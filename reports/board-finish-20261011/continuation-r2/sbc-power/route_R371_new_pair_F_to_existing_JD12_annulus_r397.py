"""Two-leg actual-source encoder reconnect, retaining the original R7036 function."""
import sys,json,pickle,hashlib,time,uuid,traceback
from pathlib import Path
from shapely import set_precision
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
import tri_route as TR
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
N=H/'sbc-power/CM79-R371-new-ordinary-ENC-plus-LG-pair-signal-side-original-R7036-r396'
P=H/'sbc-power/CM79-R371-ENC3-actual-existing-lower-layer-source-port-attribution-r387'
O=H/'sbc-power/CM79-R371-new-ordinary-pair-F-In3-actual-JD12-B3-source-reconnect-r397'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def parts(s):return []if s.is_empty else list(s.geoms)if s.geom_type=='MultiPolygon'else[s]if s.geom_type=='Polygon'else[]
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'model.pkl')=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());pose=pickle.loads((N/'exact-R7035-pose-and-existing-IO3-reconnect.pkl').read_bytes());scope=pose['scope'];mm=pose['R7035'];own={p['uuid']for p in scope['pads']};net=L.norm(scope['source_pin_nets']['2']);np=next(p for p in mm['pads']if str(p['old']['num'])=='2');pairs=json.loads((N/'eligible-new-ordinary-SIG-source-LG-pairs.json').read_text());base={**c,'pads':[p for p in c['pads']if p['uuid']not in own]};rec,trees=F.build(base,layers={'F.Cu','In3.Cu','B.Cu'});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');refs={ly:zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']==ly]))for ly in('In1.Cu','In4.Cu')};enc=pickle.loads((P/'actual-old-ENC3-contact-components-after-owned-pad-withdrawal.pkl').read_bytes());padUID='16e8ee74-9639-4eb1-b885-c52eac87d0d4';oldpad=next(p for p in h['pads']if p['uuid']==padUID);holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for uid,sh in holes]);reserve,exempt=A.reservations();native=A.C.inventory((H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb').read_bytes());zoneMap={z['uuid']:z for z in c['zones']};attempts=[];winner=None;fixed={};holeCuts={};local=box(74,17,87,33)
 def fixed_obstacles(layer):
  if layer in fixed:return fixed[layer]
  cuts=[]
  for j in trees[layer].query(local.buffer(1),predicate='intersects'):
   rr=rec[layer][int(j)]
   if L.norm(rr['net'])==net or rr['kind']=='fill'and L.norm(rr['net'])=='/LOGIC_GND'and rr['uuid']in native[3]:continue
   clear=float(zoneMap[rr['uuid']]['clearance_mm'])if rr['kind']=='fill'and rr['uuid']in zoneMap else .15;cuts.append(Z.bounded_buffer(rr['shape'].intersection(local.buffer(1)),.1+max(clear,gap(net,rr['net']))+.025))
  for z in q:
   if z['layer']==layer and L.norm(z['net'])!=net and z['shape'].intersects(local.buffer(1)):cuts.append(Z.bounded_buffer(z['shape'].intersection(local.buffer(1)),.1+max(float(z['clearance_mm']),gap(net,z['net']))+.025))
  for rr,ex in[(r,False)for r in h['rule_areas']]+[(r,True)for r in reserve['keepouts']]:
   if layer not in rr['layers']or(not ex and not rr.get('no_tracks'))or(ex and net in exempt.get(rr['name'],set())):continue
   cuts.extend(Z.bounded_buffer(sh,.125)for sh in L.poly(rr['outline'])if sh.intersects(local.buffer(1)))
  fixed[layer]=unary_union(cuts);return fixed[layer]
 def route(pair,layer,start,end,startCap,endCap,targetShape):
  sig=Point(*pair['new_SIG_xy']);gp=Point(*pair['new_LG_xy']);rlayer='In1.Cu'if layer=='F.Cu'else'In4.Cu';ops=[x for x in pair['signal_hole_ops']if L.norm(x['raw_net'])=='/LOGIC_GND'and x['layer']==rlayer];radius=max([x['actual_native_antipad_radius_mm']for x in ops],default=.5);ref=refs[rlayer].intersection(local.buffer(1)).difference(sig.buffer(radius,quad_segs=128)).difference(gp.buffer(.1,quad_segs=128));allowed=unary_union([ref,startCap,endCap]);cuts=[fixed_obstacles(layer),Z.bounded_buffer(gp,.525)];excluded=padUID if layer!='F.Cu'else None
  if excluded not in holeCuts:holeCuts[excluded]=unary_union([Z.bounded_buffer(holes[int(j)][1],.38)for j in ht.query(local.buffer(1),predicate='intersects')if holes[int(j)][0]!=excluded])
  cuts.append(holeCuts[excluded])
  if layer=='F.Cu':
   for mp in mm['pads']:
    if L.norm(mp['old']['net'])!=net:cuts.append(Z.bounded_buffer(mp['shape'],.275))
   cuts.append(Z.bounded_buffer(LineString(pose['IO3_path']['path']),.375))
  free=local.difference(unary_union(cuts)).intersection(allowed.buffer(-.105,quad_segs=128));face=next((sh for sh in parts(free.buffer(-.000002,quad_segs=64))if sh.covers(Point(*start))and sh.covers(Point(*end))),None);row={'SIG_xy':pair['new_SIG_xy'],'LG_xy':pair['new_LG_xy'],'layer':layer,'start':start,'end':end,'Cu_reference_free_face':face is not None,'start_in_free':free.covers(Point(*start)),'end_in_free':free.covers(Point(*end))};attempts.append(row)
  if face is None:return None
  direct=LineString([start,end]);path=[start,end]if face.covers(direct)else TR.route(face,start,end)[0]
  if not path:return None
  path=[[round(float(x),6),round(float(y),6)]for x,y in path]
  if not all(free.covers(LineString([a,bb]))for a,bb in zip(path,path[1:])):return None
  tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R397:'+str(pair['new_SIG_xy'])+':'+str(pair['new_LG_xy'])+':'+layer+':'+str(i))),'net':scope['source_pin_nets']['2'],'layer':layer,'w':.2,'a':a,'b':bb}for i,(a,bb)in enumerate(zip(path,path[1:]))];body=zero(unary_union([Z.bounded_buffer(LineString([t['a'],t['b']]),.1)for t in tracks]));actual=body.difference(unary_union([sh for uid,sh in holes]+[sig.buffer(.1,quad_segs=128),gp.buffer(.1,quad_segs=128)]));rg=actual.difference(unary_union([startCap,endCap])).difference(ref);startAnn=sig.buffer(.25,quad_segs=128).difference(sig.buffer(.1,quad_segs=128));so=actual.intersection(startAnn).area;to=actual.intersection(targetShape).area;row.update({'path':path,'length_mm':LineString(path).length,'exact_terminal_guards_reference_gap_EMPTY':rg.is_empty,'new_SIG_annulus_positive_contact_mm2':so,'actual_target_positive_contact_mm2':to});return tracks if rg.is_empty and so>0 and to>0 else None
 pairs=sorted(pairs,key=lambda pp:Point(*pp['new_SIG_xy']).distance(Point(*np['xy'])))[:160]
 for pair in pairs:
  sig=Point(*pair['new_SIG_xy']);cap=sig.buffer(.525,quad_segs=128);ftracks=route(pair,'F.Cu',pair['new_SIG_xy'],np['xy'],cap,Point().buffer(0),np['shape'])
  if ftracks is None:continue
  for layer in('In3.Cu','B.Cu'):
   actualPad=next(rr['shape']for xs in enc for rr in xs if rr['uuid']==padUID and rr['layer']==layer);rawPad=unary_union(L.poly(oldpad['layers'][layer]));sourceGuard=Z.bounded_buffer(rawPad,.275);ends=[]
   for i in range(24):
    a=2*3.141592653589793*i/24;xy=[round(oldpad['x']+1.05*__import__('math').cos(a),6),round(oldpad['y']+1.05*__import__('math').sin(a),6)]
    if actualPad.covers(Point(*xy)):ends.append(xy)
   ends=sorted(ends,key=lambda xy:Point(*xy).distance(sig))
   for end in ends:
    lower=route(pair,layer,pair['new_SIG_xy'],end,cap,sourceGuard,actualPad)
    if lower is None:continue
    winner={'R7035_pose_and_source_scope':pose,'R7036_original_native_AST_exact':True,'new_ordinary_SIG_LG_pair':pair,'new_F_tracks':ftracks,'new_lower_tracks':lower,'exact_original_JD12_B3_pad_UUID':padUID,'original_JD12_B3_actual_annulus_endpoint':end,'new_SIG_own_guard_radius_mm':.525,'original_JD12_own_guard':'original actual full pad shape + .275, exact named pad/hole only','layer_leg_count':2,'fresh_complete_sources_oldrelationships_oldrefs_everyhole_native_masks_fill_current_thermal':'OPEN'};break
   if winner:break
  put(O/'finite-exact-F-and-original-annulus-lower-reference-path-attempts.json',attempts)
  if winner:break
 if winner:(O/'only-new-ordinary-pair-two-leg-R7035-ENC-source-reconnect.pkl').write_bytes(pickle.dumps(winner,protocol=5))
 put(O/'finite-exact-F-and-original-annulus-lower-reference-path-attempts.json',attempts);put(O/'receipt.json',{'verdict':'GENUINE_R7035_TWO_LAYER_LEG_ORDINARY_PAIR_ACTUAL_JD12_SOURCE_RECONNECT'if winner else'NO_EXACT_REFERENCE_PATH_IN_160_ELIGIBLE_NEW_ORDINARY_PAIRS','R371_model_sha256':sha(D/'model.pkl'),'R396_receipt_sha256':sha(N/'receipt.json'),'eligible_pair_count_tested':len(pairs),'path_attempt_count':len(attempts),'winner':bool(winner),'packet_sha256':sha(O/'only-new-ordinary-pair-two-leg-R7035-ENC-source-reconnect.pkl')if winner else None,'R7036_original_and_all_foreign_Cu_planes_holes_courts_rules_held':True,'adoption':False,'native_and_fullsource_masks_current_thermal':'OPEN','elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R397',sha(O/'receipt.json'),bool(winner),len(attempts),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
