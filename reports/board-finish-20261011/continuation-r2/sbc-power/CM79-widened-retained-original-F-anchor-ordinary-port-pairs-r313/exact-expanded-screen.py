"""Read-only widened original-anchor ports, ordinary pairs, all old Cu hard."""
import hashlib,json,pickle,sys,time,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-widened-retained-original-F-anchor-ordinary-port-pairs-r313'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def buf(s,r):return set_precision(Z.bounded_buffer(s,r),0)
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();put(O/'exact-successor-syntax-scope.json',{'failed_parent_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'correction':'else120.1 -> else 120.1','no_geometry_scope_change':True});(O/'exact-expanded-screen.py').write_text(s,encoding='utf-8');mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');power=old['net'];assert old['w']==1.25;authority=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');assert sha(authority)=='392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5';records,trees=F.build({**c,'zones':[]});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;reserve,exempt=A.reservations();holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for u,sh in holes]);smd=[sh for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree(smd);vpts=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vpts);owned=[(z['uuid'],z['net'],z['layer'],set_precision(z['shape'],0))for z in q];ot=STRtree([sh for u,n,l,sh in owned]);qclear={z['uuid']:float(z['clearance_mm'])for z in q};pre=buf(LineString([old['a'],[116.2,202.35]]),.625);post=buf(LineString([[120.1,202.35],old['b']]),.625);oldbody=buf(LineString([old['a'],old['b']]),.625);wide=buf(LineString([[113.5,202.35],[131.4,202.35]]),.625);assert pre.difference(oldbody).is_empty and post.difference(oldbody).is_empty;checks=0;cache={}
 def check(net,x,y):
  nonlocal checks
  key=(net,x,y)
  if key in cache:return cache[key]
  checks+=1;pt=Point(x,y);sm=pt.distance(smd[int(st.nearest(pt))])-.105;hd=pt.distance(holes[int(ht.nearest(pt))][1])-.105;pitch=pt.distance(vpts[int(vt.nearest(pt))]);bad=[];rb=[]
  rr={'net':net,'x':x,'y':y,'d':.5,'drill':.2,'SMD_drill_guarded_gap_mm':sm,'old_drill_guarded_gap_mm':hd,'old_via_pitch_mm':pitch,'foreign_actual_discrete_or_owned_q_deficits':bad,'native_and_frozen_rule_failures':rb,'PASS':False};cache[key]=rr
  if sm<.275 or hd<.275 or pitch<.815:return rr
  for ly in K.LAYERS:
   for j in trees[ly].query(pt.buffer(1.6),predicate='intersects'):
    r=records[ly][int(j)]
    if L.norm(r['net'])==L.norm(net):continue
    if r['kind']=='track'and not r['source'].get('m'):t=r['source'];d=pt.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
    elif r['kind']=='via':vv=r['source'];d=pt.distance(Point(vv['x'],vv['y']))-.25-vv['d']/2
    else:d=pt.distance(r['shape'])-.25
    req=gap(net,r['net'])+.025003
    if d<req:bad.append({'uuid':r['uuid'],'layer':ly,'kind':r['kind'],'net':r['net'],'gap':d,'required':req})
  for j in ot.query(pt.buffer(1.6),predicate='intersects'):
   u,n,ly,sh=owned[int(j)]
   if L.norm(n)==L.norm(net):continue
   d=pt.distance(sh)-.25;req=max(gap(net,n),qclear[u])+.025003
   if d<req:bad.append({'uuid':u,'layer':ly,'kind':'owned-q-hard','net':n,'gap':d,'required':req})
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for r in rules:
    if not(set(r['layers'])&set(K.LAYERS))or(not ex and not r.get('no_vias')):continue
    if ex and L.norm(net)in exempt.get(r['name'],set()):continue
    if any(pt.distance(sh)-.25<.025003 for sh in L.poly(r['outline'])):rb.append(r.get('name',r.get('uuid')))
  rr['PASS']=not bad and not rb;return rr
 # Ordinary paired-ground candidates have .175003 clear space from the exact
 # unchanged 1.25 F trunk. Finite grid excludes no old signal or owned barrel.
 ground=[];gcensus={};first=[]
 for ix in range(781):
  x=round(112.8+ix*.025,6)
  for iy in range(6):
   y=round(203.405+iy*.025,6);rr=check('/LOGIC_GND',x,y)
   if Point(x,y).distance(LineString([old['a'],old['b']]))-.875<.175003:continue
   if rr['PASS']:ground.append(rr)
   else:
    for dd in rr['foreign_actual_discrete_or_owned_q_deficits']:gcensus[dd['uuid']]=gcensus.get(dd['uuid'],0)+1
    for name in rr['native_and_frozen_rule_failures']:gcensus[name]=gcensus.get(name,0)+1
    if len(first)<50:first.append(rr)
 put(O/'ordinary-ground-finite-grid-census.json',{'grid':{'x_start':112.8,'x_step':.025,'x_count':781,'y_start':203.405,'y_step':.025,'y_count':6},'PASS_count':len(ground),'hard_blocker_occurrences':gcensus,'first50_rejected':first,'PASS_sites':ground});print('R313_GROUND',len(ground),flush=True)
 powers={};pairs={};census={}
 for label,xlo,xhi,anchor in(('left',113.5,116.575,pre),('right',119.725,131.4,post)):
  valid=[];reason={};other={};reject=[]
  for ix in range(round((xhi-xlo)/.025)+1):
   x=round(xlo+ix*.025,6)
   for iy in range(21):
    y=round(202.15+iy*.025,6);pt=Point(x,y);disk=buf(pt,.25)
    if not anchor.covers(disk):continue
    rr=check(power,x,y);rr['F_original_retained_full1p25_anchor_annulus_mm2']=disk.difference(pt.buffer(.1,quad_segs=128)).intersection(anchor).area
    if rr['PASS']:valid.append(rr)
    else:
     for dd in rr['foreign_actual_discrete_or_owned_q_deficits']:reason[dd['uuid']]=reason.get(dd['uuid'],0)+1
     for name in rr['native_and_frozen_rule_failures']:reason[name]=reason.get(name,0)+1
     for name,threshold in(('SMD_drill_guarded_gap_mm',.275),('old_drill_guarded_gap_mm',.275),('old_via_pitch_mm',.815)):
      if rr[name]<threshold:other[name]=other.get(name,0)+1
     if len(reject)<50:reject.append(rr)
  endpoint=116.2 if label=='left'else 120.1;valid.sort(key=lambda rr:(abs(rr['x']-endpoint),abs(rr['y']-202.35)));powers[label]=valid;found=[]
  for pp in valid:
   for gg in ground:
    d=math.hypot(pp['x']-gg['x'],pp['y']-gg['y'])
    if not .9<=d<=1.0:continue
    if Point(gg['x'],gg['y']).distance(wide)-.25<.175003:continue
    found.append({'power':pp,'ground':gg,'ordinary_actual_pair_distance_mm':d,'F_anchors_remain_exact_before_subsets':True,'candidate_full1p25_In2_axis_y_mm':202.35,'proposed_partial_offcentre_finite_annulus_requires_real_source_flow_and_current_bottleneck_proof':True})
   if len(found)>=30:break
  census[label]={'ordinary_power_sites_PASS_count':len(valid),'ordinary_pair_candidate_count':len(found),'hard_blocker_occurrences':reason,'mechanical_reject_counts':other,'first50_rejected':reject};pairs[label]=found;put(O/'widened-original-anchor-finite-pair-census.json',{'census':census,'power_PASS_sites':powers,'pairs':pairs});print('R313_SIDE',label,len(valid),len(found),flush=True)
 if all(pairs.values()):
  _,groups=K.physical(c,'/LOGIC_GND',K.hole_context(c));root=K.root(groups,'J11001','2');source={ly:[r['shape']for r in root if r['kind']=='fill'and r['layer']==ly]for ly in('In1.Cu','In4.Cu')};src_t={ly:STRtree(shs)for ly,shs in source.items()};qualified={}
  for label,rows in pairs.items():
   qq=[]
   for r in rows:
    gg=r['ground'];pt=Point(gg['x'],gg['y']);ann=pt.buffer(.25,quad_segs=128).difference(pt.buffer(.1,quad_segs=128));aa={}
    for ly,shs in source.items():local=unary_union([shs[int(i)]for i in src_t[ly].query(ann,predicate='intersects')]);aa[ly]=ann.intersection(local).area
    r['actual_current_J11001_source_filled_finite_annulus_mm2']=aa
    if all(v>0 for v in aa.values()):qq.append(r)
   qualified[label]=qq
  put(O/'actual-source-qualified-ordinary-offset-pairs.json',qualified)
  if all(qualified.values()):
   left=qualified['left'][0];right=qualified['right'][0];a=[left['power']['x'],202.35];bb=[right['power']['x'],202.35];body=buf(LineString([a,bb]),.625);(O/'proposed-only-new-full1p25-In2-axis-body.wkb').write_bytes(body.wkb);put(O/'first-source-bound-pair-and-exact-provisional-bridge.json',{'left':left,'right':right,'axis':[a,bb],'width_mm':1.25,'length_mm':math.dist(a,bb),'original_F_removed_axis':[[116.2,202.35],[120.1,202.35]],'original_F_middle_removed_length_mm':3.9,'additional_In2_overlap_length_mm':math.dist(a,bb)-3.9,'new_body_WKB_sha256':sha(O/'proposed-only-new-full1p25-In2-axis-body.wkb'),'source_flow_partial_annulus_all6_native_strictrefs_oldcontacts_fullreturn_cap_plating_drop_fault':'OPEN','CM49_all_contacts_reference_rebind':'OPEN'})
 else:qualified={k:[]for k in pairs}
 put(O/'receipt.json',{'verdict':'WIDENED_SOURCE_BOUND_ORDINARY_PAIRS_DIAGNOSTIC_NOMINATED_ALL_FULL_GATES_OPEN'if all(qualified.values())else'NO_TWO_ENDED_WIDENED_ORIGINAL_ANCHOR_ORDINARY_POWER_GROUND_PAIR_NOMINATION','model_sha256':sha(mp),'operator_authority_sha256':sha(authority),'checked_site_count':checks,'ordinary_pair_counts':{k:len(v)for k,v in pairs.items()},'source_qualified_pair_counts':{k:len(v)for k,v in qualified.items()},'only_proposed_original_F_middle_remove_mm':[[116.2,202.35],[120.1,202.35]],'original_full1p25_pre_and_post_anchor_preserved':True,'every_old_signal_CM49_barrel_and_owned_positive_q_hard':True,'native_fill_ordinary_retreat_not_constructed_or_accepted':True,'D4_POWER_permission_or_aperture_expansion':False,'inherited_FIELD_IO3_oldrefs_CORE_rawbody_and_signed_current_fullreturn_thermal_fault_native':'FAIL_OR_OPEN_RETAINED','new_model_native_source_jobs':0,'adopted':False,'script_sha256':sha(__file__),'elapsed_seconds':time.monotonic()-started});print('R313_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
