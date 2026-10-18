"""Actual larger ordinary port Cu/drill/old-source masks, no capacity claim."""
import hashlib,json,pickle,sys,time,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import from_wkb,set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-larger-ordinary-external-right-power-port-native-and-source-mask-screen-r325'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(sh):z=set_precision(sh,0);assert z.wkb==sh.wkb;return z
def buf(sh,r):return zero(Z.bounded_buffer(sh,r))
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());nom=H/'sbc-power/CM79-external-full1p25-F-spur-exact-old-Cu-novel-margin-nominations-r323';assert sha(nom/'receipt.json')=='aa45aba75979c06f4ef43932f0ba7fe171808e24443efd609aac7ae90e5e96f0';spurs=json.loads((nom/'external-fullwidth-source-spur-search-progress.json').read_text())['accepted']['right'];records,trees=F.build({**c,'zones':[]});dom=h['domains_normalized'];NET='/mc_local_power/CORE_5V';gap=lambda n:.15 if dom.get(L.norm(n))==dom[NET]else .6;holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for u,sh in holes]);smd=[sh for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree(smd);vp=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vp);reserve,exempt=A.reservations();oldmask=zero(from_wkb((nom/'only-new-centre-obstacle-from-every-local-old-supported-body.wkb').read_bytes()));rows=[];passed=[]
 for d,drill in((.5,.2),(.6,.3),(.7,.3),(.8,.4),(1.,.5),(1.1,.5)):
  rad=d/2;hole=drill/2;nativeHalo=max(hole+.275,rad+.25+.025);supportedMask=oldmask if d==.5 else buf(oldmask,rad-.25);min_pair=rad+.25+.175003
  for index,spur in enumerate(spurs):
   xy=spur['new_ordinary_power_via_xy_mm'];pt=Point(xy);bad=[];rulebad=[]
   for ly in K.LAYERS:
    for j in trees[ly].query(pt.buffer(2),predicate='intersects'):
     rr=records[ly][int(j)]
     if L.norm(rr['net'])==NET:continue
     if rr['kind']=='track'and not rr['source'].get('m'):tt=rr['source'];dd=pt.distance(LineString([tt['a'],tt['b']]))-rad-tt['w']/2
     elif rr['kind']=='via':vv=rr['source'];dd=pt.distance(Point(vv['x'],vv['y']))-rad-vv['d']/2
     else:dd=pt.distance(rr['shape'])-rad
     req=gap(rr['net'])+.025003
     if dd<req:bad.append({'UUID':rr['uuid'],'kind':rr['kind'],'layer':ly,'raw_net':rr['net'],'actual_gap_mm':dd,'planner_required_mm':req})
   for z in q:
    if L.norm(z['net'])==NET:continue
    dd=pt.distance(z['shape'])-rad;req=max(gap(z['net']),float(z['clearance_mm']))+.025003
    if dd<req:bad.append({'UUID':z['uuid'],'kind':'owned_positive_q_hard','layer':z['layer'],'actual_gap_mm':dd,'planner_required_mm':req})
   sm=pt.distance(smd[int(st.nearest(pt))])-hole-.005;hd=pt.distance(holes[int(ht.nearest(pt))][1])-hole-.005;pitch=pt.distance(vp[int(vt.nearest(pt))]);disk=buf(pt,rad)
   for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
    for rr in rules:
     if not(set(rr['layers'])&set(K.LAYERS))or(not ex and not rr.get('no_vias'))or(ex and NET in exempt.get(rr['name'],set())):continue
     if any(disk.distance(sh)<.025003 for sh in L.poly(rr['outline'])):rulebad.append(rr.get('name',rr.get('uuid')))
   oldsafe=not supportedMask.covers(pt);gd=spur['ordinary_actual_pair_distance_mm'];gv=spur['exact_existing_source_LG_port']['via'];pairgap=gd-rad-gv['d']/2;ann=disk.difference(buf(pt,hole+.00000002));body=unary_union([buf(LineString([aa,bb]),.625)for aa,bb in zip(spur['full1p25_F_spur_path'],spur['full1p25_F_spur_path'][1:])]);contact=ann.intersection(body);ok=not bad and not rulebad and oldsafe and sm>=.275 and hd>=.275 and pitch>=.815 and pairgap>=.175003 and .9<=gd<=1.0 and contact.area>0;row={'diameter_drill_mm':[d,drill],'right_spur_index':index,'power_xy_mm':xy,'actual_native_LG_local_clearance_mm':.25,'actual_new_LG_antipad_radius_mm':nativeHalo,'all_old_F_B_q_BEFORE_supported_reference_conservative_mask_clear':oldsafe,'actual_ordinary_ground_pair_distance_mm':gd,'POWER_to_existing_GND_actual_Cu_gap_mm':pairgap,'ordinary_ground_pair_maximum_mm':1.,'same_Cu_native_plus_025_guarded_pair_minimum_mm':min_pair,'all6_actual_foreign_Cu_or_owned_positive_deficits':bad,'native_or_frozen_rule_deficits':rulebad,'SMD_guarded_gap_mm':sm,'every_old_drill_guarded_gap_mm':hd,'nearest_existing_via_pitch_mm':pitch,'larger_power_annulus_to_unchanged_full1p25_F_spur_contact_mm2':contact.area,'full_F_spur_side_axis_offset_mm':.30,'geometry_nominee':ok,'actual_source_aftercut_annuli_native_flash_mask_current_capacity_plating_fullbody_reference_alloldsource':'OPEN'};rows.append(row)
   if ok:passed.append({'screen':row,'fullwidth_spur':spur})
 put(O/'six-size-eight-right-site-exact-screen.json',rows);put(O/'only-qualified-larger-right-spur-power-port-nominees.json',passed);counts={str((d,dr)):sum(r['geometry_nominee']for r in rows if r['diameter_drill_mm']==[d,dr])for d,dr in((.5,.2),(.6,.3),(.7,.3),(.8,.4),(1.,.5),(1.1,.5))};put(O/'receipt.json',{'verdict':'LARGER_ORDINARY_EXTERNAL_RIGHT_PORT_NOMINEES_NO_CAPACITY_OR_FULLGATE_CREDIT'if passed else'NO_LARGER_EXTERNAL_RIGHT_POWER_PORT_NOMINEE_AT_FROZEN_EIGHT_SITES','R289_model_sha256':sha(mp),'R323_spur_receipt_sha256':sha(nom/'receipt.json'),'diameter_drill_nominee_counts':counts,'source_reference_antipad_local_clearance_025_unchanged':True,'no_equalshare_plating_or_capacity_rating_inferred':True,'full_source_current_signed_drop_loop_thermal_native_all49_future_joint':'OPEN','model_source_rule_board_native_or_adoption_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R325_COMPLETE',sha(O/'receipt.json'),counts,flush=True)
if __name__=='__main__':main()
