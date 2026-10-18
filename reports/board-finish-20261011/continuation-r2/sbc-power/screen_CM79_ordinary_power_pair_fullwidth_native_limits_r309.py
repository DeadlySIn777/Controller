"""Read-only ordinary power-pair sites; D4 signal-only is never enlarged."""
import hashlib,json,pickle,sys,math,time
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM79-four-ordinary-power-return-sites-fullwidth-native-bound-r309'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());authority=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');assert sha(authority)=='392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5';source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');_,groups=K.physical(c,'/LOGIC_GND',K.hole_context(c));root=K.root(groups,'J11001','2');fill={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')};records,trees=F.build({**c,'zones':[]});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;reserve,exempt=A.reservations();smd=[sh for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for sh in L.poly(rs)];holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];results=[]
 for gy in(203.30,203.35,203.375,203.42):
  sites=[{'label':lab,'net':raw,'x':x,'y':y,'d':.5,'drill':.2}for lab,raw,x,y in(('CORE5_left',old['net'],116.2,202.35),('CORE5_right',old['net'],120.1,202.35),('LG_left','/LOGIC_GND',116.2,gy),('LG_right','/LOGIC_GND',120.1,gy))];rows=[]
  for v in sites:
   pt=Point(v['x'],v['y']);bad=[];native_bad=[]
   for ly in K.LAYERS:
    for j in trees[ly].query(pt.buffer(1),predicate='intersects'):
     r=records[ly][int(j)]
     if L.norm(r['net'])==L.norm(v['net']):continue
     if r['kind']=='track'and not r['source'].get('m'):t=r['source'];d=pt.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
     elif r['kind']=='via':vv=r['source'];d=pt.distance(Point(vv['x'],vv['y']))-.25-vv['d']/2
     else:d=pt.distance(r['shape'])-.25
     nr=gap(v['net'],r['net']);pr=nr+.025
     if d<pr:
      rr={'other_UUID':r['uuid'],'kind':r['kind'],'layer':ly,'raw_net':r['net'],'actual_Cu_gap_mm':d,'native_required_mm':nr,'planner_required_mm':pr,'native_PASS':d>=nr};bad.append(rr)
      if d<nr:native_bad.append(rr)
   sm=min(pt.distance(sh)-.1-.005 for sh in smd);hd=min(pt.distance(sh)-.1-.005 for u,sh in holes);pitch=min(pt.distance(Point(vv['x'],vv['y']))for vv in h['vias']);rulebad=[]
   for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
    for rr in rules:
     if not ex and not rr.get('no_vias'):continue
     if ex and L.norm(v['net'])in exempt.get(rr['name'],set()):continue
     if any(pt.distance(sh)-.25<.025 for sh in L.poly(rr['outline'])):rulebad.append(rr.get('name',rr.get('uuid')))
   ann=pt.buffer(.25,quad_segs=128).difference(pt.buffer(.1,quad_segs=128));areas={ly:ann.intersection(sh).area for ly,sh in fill.items()}if v['net']=='/LOGIC_GND'else None
   rows.append({'site':v,'all6_mask_classification':'PROSPECTIVE_REQUIRE_FRESH_NATIVE_FLASH_NOT_PROOF','all_actual_before_discrete_Cu_extra_planner_deficits':bad,'actual_native_before_discrete_Cu_failure_count':len(native_bad),'every_outer_SMD_drill_guarded_edge_mm':sm,'every_old_drill_guarded_edge_mm':hd,'nearest_existing_via_pitch_mm':pitch,'ordinary_required_SMD_drill_mm':.275,'ordinary_required_pitch_mm':.815,'native_and_exact_frozen_rule_failures':rulebad,'candidate_finite_annulus_intersection_WITH_ACTUAL_CURRENT_J11001_source_fill_mm2':areas})
  dist=gy-202.35;actualgap=dist-.625-.25;pair={'CORE5_power_ports_are_D4_signal_authority_applicable':False,'ordinary_pair_centre_distance_mm':dist,'ordinary_0p90_to1p0_window_PASS':.9<=dist<=1,'full1p25_F_anchor_and_In2_bridge_to_0p5_GND_via_actual_native_gap_mm':actualgap,'actual_native_same_Cu_requirement_mm':.15,'planner_same_Cu_requirement_mm':.175,'actual_native_fullwidth_pair_PASS':actualgap>=.15,'full_extra_planner_fullwidth_pair_PASS':actualgap>=.175};results.append({'ground_y_mm':gy,'sites':rows,'fullwidth_mutual_pair':pair});put(O/'exact-four-site-native-and-source-annulus-screen.json',results)
 bound={'fullwidth_power_cap_radius_mm':.625,'ordinary_ground_via_Cu_radius_mm':.25,'actual_same_Cu_clearance_mm':.15,'minimum_fullwidth_native_pair_distance_mm':1.025,'extra_planner_minimum_pair_distance_mm':1.05,'ordinary_power_pair_maximum_mm':1.0,'native_rules_and_ordinary_window_compatible_for_exact_fullwidth_endcap':False,'no_D4_power_permission_or_aperture_radius_invented':True};put(O/'exact-fullwidth-native-versus-ordinary-window-bound.json',bound)
 put(O/'receipt.json',{'verdict':'FOUR_ORDINARY_POWER_RETURN_SITES_REJECTED_EXACT_FULLWIDTH_NATIVE_VERSUS_PAIR_WINDOW_CONFLICT','exact_current_failed_diagnostic_model_sha256':sha(mp),'exact_D4_signal_only_operator_authority_sha256':sha(authority),'exact_source_native_sha256':sha(source),'fullwidth_native_pair_bound':bound,'tested_four_site_sets':len(results),'no_isolated_model_emitted':True,'full_signed_CORE5_7p882A_CM3p559A_other_loads':'UNCHANGED','current_capacity_plating_all6_flash_fullref_fullsource_native':'FAIL_OR_OPEN_RETAINED','model_board_source_native_or_rule_changes':0,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R309_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
