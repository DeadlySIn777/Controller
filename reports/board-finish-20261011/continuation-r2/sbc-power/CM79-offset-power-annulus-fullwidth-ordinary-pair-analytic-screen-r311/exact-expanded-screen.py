"""Read-only offset annulus ports; preserve full1.25 bodies and ordinary window."""
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
O=H/'sbc-power/CM79-offset-power-annulus-fullwidth-ordinary-pair-analytic-screen-r311'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();put(O/'exact-successor-scope.json',{'parent_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'analytic_point_to_actual_Cu_distance_minus_full_Cu_radius_mm':.25,'same_finite_grid':True,'no_clearance_or_source_obstacle_relaxed':True});(O/'exact-expanded-screen.py').write_text(s,encoding='utf-8');mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');power=old['net'];assert old['w']==1.25;authority=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');assert sha(authority)=='392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5';records,trees=F.build({**c,'zones':[]});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;reserve,exempt=A.reservations();holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for u,sh in holes]);smd=[sh for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree(smd);vpts=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vpts)
 _,groups=K.physical(c,'/LOGIC_GND',K.hole_context(c));root=K.root(groups,'J11001','2');fill={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')};oldbody=Z.bounded_buffer(LineString([old['a'],old['b']]),.625);oldbody=set_precision(oldbody,0);pre=Z.bounded_buffer(LineString([old['a'],[116.2,202.35]]),.625);post=Z.bounded_buffer(LineString([[120.1,202.35],old['b']]),.625);mid=Z.bounded_buffer(LineString([[116.2,202.35],[120.1,202.35]]),.625);pre,post,mid=[set_precision(x,0)for x in(pre,post,mid)];owned=[]
 for z in q:
  owned.append((z['uuid'],z['net'],z['layer'],set_precision(z['shape'],0)))
 checks=0
 def check(net,x,y):
  nonlocal checks;checks+=1;pt=Point(x,y);disk=set_precision(Z.bounded_buffer(pt,.25),0);bad=[]
  for ly in K.LAYERS:
   for j in trees[ly].query(pt.buffer(1.5),predicate='intersects'):
    r=records[ly][int(j)]
    if L.norm(r['net'])==L.norm(net):continue
    if r['kind']=='track'and not r['source'].get('m'):t=r['source'];d=pt.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
    elif r['kind']=='via':vv=r['source'];d=pt.distance(Point(vv['x'],vv['y']))-.25-vv['d']/2
    else:d=pt.distance(r['shape'])-.25
    req=gap(net,r['net'])+.025003
    if d<req:bad.append({'uuid':r['uuid'],'layer':ly,'kind':r['kind'],'net':r['net'],'gap':d,'required':req})
  for u,n,ly,sh in owned:
   if L.norm(n)!=L.norm(net)and pt.distance(sh)-.25<gap(net,n)+.025003:bad.append({'uuid':u,'layer':ly,'kind':'owned-q-hard','net':n,'gap':pt.distance(sh)-.25,'required':gap(net,n)+.025003})
  sm=pt.distance(smd[int(st.nearest(pt))])-.105;hd=pt.distance(holes[int(ht.nearest(pt))][1])-.105;pitch=pt.distance(vpts[int(vt.nearest(pt))]);rb=[]
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for r in rules:
    if not ex and not r.get('no_vias'):continue
    if ex and L.norm(net)in exempt.get(r['name'],set()):continue
    if any(pt.distance(sh)-.25<.025003 for sh in L.poly(r['outline'])):rb.append(r.get('name',r.get('uuid')))
  return {'net':net,'x':x,'y':y,'d':.5,'drill':.2,'foreign_actual_discrete_or_owned_q_deficits':bad,'SMD_drill_guarded_gap_mm':sm,'old_drill_guarded_gap_mm':hd,'old_via_pitch_mm':pitch,'native_and_frozen_rule_failures':rb,'PASS':not bad and sm>=.275 and hd>=.275 and pitch>=.815 and not rb}
 powers={};pairs={};census={}
 for label,xlo,xhi,anchor in(('left',115.7,116.575,pre),('right',119.725,120.6,post)):
  valid=[];reason={};rejected=[]
  for ix in range(round((xhi-xlo)/.025)+1):
   x=round(xlo+ix*.025,6)
   for iy in range(21):
    y=round(202.15+iy*.025,6);pt=Point(x,y);disk=set_precision(Z.bounded_buffer(pt,.25),0)
    if not anchor.covers(disk):continue
    rr=check(power,x,y);ann=disk.difference(pt.buffer(.1,quad_segs=128));rr['F_original_retained_anchor_finite_annulus_mm2']=ann.intersection(anchor).area;rr['In2_full1p25_candidate_finite_annulus_mm2']=ann.intersection(mid).area
    if rr['PASS']and rr['In2_full1p25_candidate_finite_annulus_mm2']>0:valid.append(rr)
    else:
     for bb in rr['foreign_actual_discrete_or_owned_q_deficits']:reason[bb['uuid']]=reason.get(bb['uuid'],0)+1
     if len(rejected)<30:rejected.append(rr)
  powers[label]=valid;census[label]={'offset_power_sites_PASS_count':len(valid),'reject_blocker_occurrences':reason,'first30_rejected':rejected};found=[]
  for pp in valid:
   for distance in(.925,.95,.975,1.0):
    for degree in range(45,136,5):
     ang=math.radians(degree);gx=round(pp['x']+distance*math.cos(ang),6);gy=round(pp['y']+distance*math.sin(ang),6);dist=math.hypot(gx-pp['x'],gy-pp['y'])
     if not .9<=dist<=1.0:continue
     pt=Point(gx,gy);disk=set_precision(Z.bounded_buffer(pt,.25),0)
     if pt.distance(LineString([old['a'],old['b']]))-.875<.175003:continue
     if pt.distance(mid)-.25<.175003:continue
     rr=check('/LOGIC_GND',gx,gy)
     if not rr['PASS']:continue
     ann=disk.difference(pt.buffer(.1,quad_segs=128));aa={ly:ann.intersection(sh).area for ly,sh in fill.items()}
     if not all(v>0 for v in aa.values()):continue
     found.append({'power':pp,'ground':rr,'ordinary_actual_pair_distance_mm':dist,'actual_current_J11001_root_filled_annulus_mm2':aa,'full1p25_power_trunk_remains_hard':True,'all6_flash_native_current_contact_reference_capacity':'PROSPECTIVE_OPEN'})
   if len(found)>=20:break
  pairs[label]=found;put(O/'offset-sites-pair-census.json',{'census':census,'powers':powers,'pairs':pairs});print('R311_SIDE',label,len(valid),len(found),flush=True)
 put(O/'receipt.json',{'verdict':'ORDINARY_OFFSET_FULLWIDTH_PORT_PAIRS_NOMINATED_PENDING_ALL_GATES'if all(pairs.values())else'NO_TWO_ENDED_OFFSET_FULLWIDTH_ORDINARY_PORT_NOMINATION_IN_DECLARED_GRID','model_sha256':sha(mp),'authority_sha256':sha(authority),'checked_site_count':checks,'candidate_pair_counts':{k:len(v)for k,v in pairs.items()},'exact_native_original_full1p25_F_pre_and_post_anchor_bodies_retained':True,'no_D4_POWER_permission_aperture_expansion_or_rule_exception':True,'no_model_source_or_native_changes':True,'all_inherited_failed_fullbody_source_reference_current_gates_retained':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R311_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
