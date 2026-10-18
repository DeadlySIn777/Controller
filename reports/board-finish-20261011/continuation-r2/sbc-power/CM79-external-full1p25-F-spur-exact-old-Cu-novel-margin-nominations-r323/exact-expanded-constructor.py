"""Finite external full1.25 F spurs to exact actual source/floating power Cu."""
import hashlib,json,pickle,sys,time,math,uuid,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import physical_reference_losses_r3_zero_r208 as RF
import tri_route as TR
O=H/'sbc-power/CM79-external-full1p25-F-spur-exact-old-Cu-novel-margin-nominations-r323'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(sh):z=set_precision(sh,0);assert z.wkb==sh.wkb;return z
def buf(sh,r):return zero(Z.bounded_buffer(sh,r))
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-constructor.py').write_text(s,encoding='utf-8');put(O/'exact-frozen-successor-script-authority.json',{'parent_script_sha256':frozenParentScriptSha,'retained_only_old_Cu_rule_and_extra_margin_attribution':True,'actual_clearances_widths_masks_drills_nets_source_and_old_reference_constraints_not_lowered':True});mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');NET=L.norm(old['net']);dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom[NET]else .6;region=box(104,190,138,215);wide=region.buffer(3);previous=H/'sbc-power/CM79-R315-fresh-sparse-current-source-native-reference-audit-r316';assert sha(previous/'receipt.json')=='bb93a32c96d7aab3f624152ae916eb52b128b4c899b4bc97e41cf2c2b230c249';gg=pickle.loads((previous/'actual-drilled-before-groups.pkl').read_bytes());lg=K.root(gg['/LOGIC_GND'],'J11001','2');refs={ly:zero(sh)for ly,sh in K.source_refs(lg).items()};nativeLGlocal=max(float(z['clearance_mm'])for z in c['zones']if z['net']=='/LOGIC_GND');radius=max(.375,.25+max(nativeLGlocal,.15)+.025);assert radius==.525;protected=[];omit=[]
 for t in c['tracks']:
  ly=t['layer']
  if ly not in('F.Cu','B.Cu')or t['net']=='/LOGIC_GND'or dom.get(L.norm(t['net']))!=dom['/LOGIC_GND']:continue
  if t['uuid']==old['uuid']:
   for aa,bb in((old['a'],[116.2,202.35]),([120.1,202.35],old['b'])):
    body=zero(L.body({**t,'a':aa,'b':bb}));support=body.intersection(refs[ly]);protected.append({'UUID':t['uuid'],'layer':ly,'kind':'exact_retained_original_F_anchor','shape':support})
   continue
  body=zero(L.body(t))
  if not body.envelope.intersects(wide):omit.append(t['uuid']);continue
  support=body.intersection(refs[ly])
  if not support.is_empty:protected.append({'UUID':t['uuid'],'layer':ly,'kind':'whole_old_body_BEFORE_supported_reference','shape':support})
 for z in q:
  if z['layer']not in K.MAP or dom.get(L.norm(z['net']))!=dom['/LOGIC_GND']or not z['shape'].intersects(wide):continue
  support=zero(z['shape']).intersection(refs[z['layer']])
  if not support.is_empty:protected.append({'UUID':z['uuid'],'layer':z['layer'],'kind':'actual_BEFORE_supported_DC_q_body_no_shadow_over_missing_before','shape':support})
 refcut=unary_union([buf(r['shape'],radius+.000003)for r in protected]);put(O/'exact-native-local-source-reference-mask-scope.json',{'actual_native_LG_local_mm':nativeLGlocal,'domain_native_mm':.15,'native_antipad_radius_mm':radius,'whole_original_F_B_supported_mask_count':len(protected),'old_body_envelope_disjoint_from_region_plus3mm_UUIDs':omit,'no_invented_shadow_over_before_unsupported_Cu':True});(O/'only-new-centre-obstacle-from-every-local-old-supported-body.wkb').write_bytes(refcut.wkb)
 topo=H/'sbc-power/CM79-original-CORE5-native-alternate-path-no-new-hole-topology-r319';assert sha(topo/'receipt.json')=='8bac0960b658176645c9a33842d26913c266d4fdd1cb9aa1a36ce8676457efc1';power=pickle.loads((topo/'actual-CORE5-with-only-native-middle-removed-groups.pkl').read_bytes());source=K.root(power,'R11022','2');detached=next(xs for xs in power if any(r['kind']=='track'and r['uuid']=='f0009ae2-77c0-524e-a9c6-efbe8de46b7a'for r in xs));targets={label:zero(unary_union([r['shape'].intersection(region)for r in rows if r['layer']=='F.Cu'and r['shape'].intersects(region)]))for label,rows in(('left',source),('right',detached))};put(O/'exact-actual-source-and-detached-spatial-targets.json',{label:{'actual_local_F_Cu_area_mm2':sh.area,'actual_current_group_layer_key_count':len(K.keys(rows)),'local_target_WKB_sha256':hashlib.sha256(sh.wkb).hexdigest()}for label,sh,rows in(('left',targets['left'],source),('right',targets['right'],detached))})
 oldFcu=zero(unary_union([r['shape']for xs in power for r in xs if r['layer']=='F.Cu']));beforeFcu=zero(unary_union([r['shape']for xs in gg[NET]for r in xs if r['layer']=='F.Cu']));rawgain=oldFcu.difference(beforeFcu);(O/'retained-after-middle-old-F-Cu-literal-gain-witness.wkb').write_bytes(rawgain.wkb);assert rawgain.is_empty,('Retained old power Cu has literal gain',rawgain.geom_type,rawgain.area);put(O/'exact-unchanged-native-F-Cu-novelty-authority.json',{'R319_receipt_sha256':sha(topo/'receipt.json'),'retained_only_old_F_POWER_Cu_WKB_sha256':hashlib.sha256(oldFcu.wkb).hexdigest(),'retained_old_F_Cu_literal_subset_original_BEFORE':True,'only_true_new_Cu_has_native_plus_025_guarded_margin_applied':True,'full_source_native_clearance_and_body_reference_requalification_PENDING':True});(O/'exact-retained-only-old-F-POWER-Cu.wkb').write_bytes(oldFcu.wkb)
 records,trees=F.build({**c,'zones':[]});reserve,exempt=A.reservations();vc=[];fc=[];ledger=[]
 for ly in K.LAYERS:
  for j in trees[ly].query(wide,predicate='intersects'):
   rr=records[ly][int(j)]
   if L.norm(rr['net'])==NET:continue
   req=gap(rr['net'])+.025003
   if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];base=LineString([t['a'],t['b']]);rad=t['w']/2
   elif rr['kind']=='via':v=rr['source'];base=Point(v['x'],v['y']);rad=v['d']/2
   else:base=rr['shape'];rad=0
   vc.append(buf(base,rad+.25+req))
   if ly=='F.Cu':fc.append(buf(zero(buf(base,rad+req).difference(oldFcu)),.625003))
   ledger.append({'UUID':rr['uuid'],'net':rr['net'],'layer':ly,'actual_native_clearance_mm':gap(rr['net']),'planner_reserve_mm':.025})
 for z in q:
  if L.norm(z['net'])==NET or not z['shape'].intersects(wide):continue
  req=max(gap(z['net']),float(z['clearance_mm']))+.025003;vc.append(buf(z['shape'],.25+req))
  if z['layer']=='F.Cu':fc.append(buf(zero(buf(z['shape'],req).difference(oldFcu)),.625003))
 for p in h['pads']:
  if p['smd']:
   for ly,rs in p['layers'].items():
    if ly in('F.Cu','B.Cu'):
     for sh in L.poly(rs):
      if sh.intersects(wide):vc.append(buf(sh,.380003))
 holes=[(v['uuid'],v['net'],sh)for v in h['vias']for sh in[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)]]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])]
 for u,n,sh in holes:
  if not sh.intersects(wide):continue
  vc.append(buf(sh,.380003))
  if L.norm(n)!=NET:fc.append(buf(sh,.905003))
 for v in h['vias']:
  pt=Point(v['x'],v['y'])
  if pt.intersects(wide):vc.append(buf(pt,.815003))
 for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
  for rr in rules:
   if ex and NET in exempt.get(rr['name'],set()):continue
   for sh in L.poly(rr['outline']):
    if not sh.intersects(wide):continue
    if set(rr['layers'])&set(K.LAYERS)and(ex or rr.get('no_vias')):vc.append(buf(sh,.275003))
    if'F.Cu'in rr['layers']and(ex or rr.get('no_tracks')):fc.append(buf(zero(buf(sh,.025003).difference(oldFcu)),.625003))
 ground=[[117.452,201.175],[117.452,201.805],[118.652,201.805],[118.652,201.175]];gb=unary_union([buf(LineString([a,bb]),.1)for a,bb in zip(ground,ground[1:])]);fc.append(buf(gb,.800003));board=zero(unary_union(L.poly(h['outline'])));vf=region.intersection(board.buffer(-.775003)).difference(unary_union(vc+[refcut]));ff=region.intersection(board.buffer(-1.150003)).difference(unary_union(fc));faces=RF.parts(ff);(O/'exact-external-via-centre-free.wkb').write_bytes(vf.wkb);(O/'exact-full1p25-F-centre-free.wkb').write_bytes(ff.wkb);put(O/'exact-foreign-native-Cu-obstacle-authority.json',ledger);portsPath=H/'sbc-power/CM79-widened-ordinary-power-with-existing-actual-source-LG-port-pairs-r314/actual-source-LG-port-census.json';ports=json.loads(portsPath.read_text());local=[r for r in ports if region.buffer(1).covers(Point(r['via']['x'],r['via']['y']))];rows=[];accepted={'left':[],'right':[]};count=0
 for port in local:
  gv=port['via'];gp=Point(gv['x'],gv['y'])
  for distance in(.925,.95,.975,1.):
   for degree in range(0,360,5):
    ang=math.radians(degree);pv=[round(gp.x+distance*math.cos(ang),6),round(gp.y+distance*math.sin(ang),6)];pt=Point(pv);actualD=pt.distance(gp)
    if not .9<=actualD<=1.0 or not vf.covers(pt):continue
    ux=(pt.x-gp.x)/actualD;uy=(pt.y-gp.y)/actualD;ep=[round(pt.x+.30*ux,6),round(pt.y+.30*uy,6)];end=Point(ep);count+=1
    if not ff.covers(end):continue
    for label,target in targets.items():
     if len(accepted[label])>=8:continue
     for face in faces:
      if not face.covers(end):continue
      available=face.intersection(buf(target,.624995)).buffer(-.000005)
      if available.is_empty:continue
      start=nearest_points(end,available)[1];sp=list(start.coords[0]);path,method=TR.route(face,sp,ep);path=[[round(x,6),round(y,6)]for x,y in path]
      if not face.covers(LineString(path)):continue
      body=unary_union([buf(LineString([aa,bb]),.625)for aa,bb in zip(path,path[1:])]);vb=buf(pt,.25);ann=vb.difference(buf(pt,.10000002));tap=body.intersection(target);viaContact=ann.intersection(body)
      if tap.is_empty or tap.area<=0 or viaContact.is_empty or viaContact.area<=0:continue
      # Every protected support is checked individually, including point/line
      # dimensions. The actual .525 cut is never credited as an own aperture.
      nativeCut=buf(pt,radius);bad=[{'old_UUID':r['UUID'],'layer':r['layer'],'kind':r['kind'],'literal_loss_type':sh.geom_type,'literal_loss_mm2':sh.area}for r in protected for sh in[r['shape'].intersection(nativeCut)]if not sh.is_empty]
      if bad:continue
      row={'label':label,'new_ordinary_power_via_xy_mm':pv,'diameter_drill_mm':[.5,.2],'exact_existing_source_LG_port':port,'ordinary_actual_pair_distance_mm':actualD,'fullwidth_spur_side_contact_axis_endpoint_mm':ep,'side_offset_mm':.30,'full1p25_F_spur_path':path,'route_method':method,'full_spur_width_mm':1.25,'F_spur_length_mm':sum(math.dist(a,bb)for a,bb in zip(path,path[1:])),'actual_existing_power_group_spatial_target_overlap_mm2':tap.area,'new_power_annulus_to_full_spur_finite_contact_mm2':viaContact.area,'actual_native_LG_antipad_radius_mm':radius,'every_original_before_supported_F_B_body_native_antipad_loss_count':0,'all_old_group_contacts_source_newfullbody_reference_native_current_plating_signed_drop_cap_thermal_fault':'OPEN','new_power_all6_native_masks':'PROSPECTIVE'};accepted[label].append(row);rows.append(row);put(O/'external-fullwidth-source-spur-search-progress.json',{'ordinary_existing_LG_port_count':len(local),'candidate_via_side_endpoint_count':count,'accepted':accepted});print('R323_SPUR',label,len(accepted[label]),pv,row['F_spur_length_mm'],flush=True);break
  if all(len(x)>=8 for x in accepted.values()):break
 put(O/'external-fullwidth-source-spur-search-progress.json',{'ordinary_existing_LG_port_count':len(local),'candidate_via_side_endpoint_count':count,'accepted':accepted});put(O/'receipt.json',{'verdict':'EXTERNAL_FULLWIDTH_SOURCE_SPURS_NOMINATED_COMBINED_In2_SOURCE_NATIVE_REFERENCE_CURRENT_PROOF_OPEN'if all(accepted.values())else'NO_TWO_ENDED_EXTERNAL_FULLWIDTH_SOURCE_SPUR_NOMINEE_IN_DECLARED_WINDOW_AND_ORDINARY_PORT_GRID','exact_failed_R289_model_sha256':sha(mp),'R319_actual_detached_power_graph_receipt_sha256':sha(topo/'receipt.json'),'actual_source_LG_port_census_sha256':sha(portsPath),'local_window_mm':[104,190,138,215],'existing_actual_source_LG_port_count':len(local),'qualified_via_endpoint_count':count,'fullwidth_spur_nominee_counts':{k:len(v)for k,v in accepted.items()},'actual_LG_native_local_antipad_radius_mm':radius,'actual_BEFORE_supported_DC_q_bodies_also_hard':True,'true_new_F_Cu_native_and_extra025_margin_and_rules_hard':True,'only_exact_retained_after_middle_F_POWER_Cu_unchanged_margin_attribution':True,'original_full1p25_F_anchors_and_all49_CM_primitives_hard':True,'D4_power_or_aperture_expansion_or_source_reference_waiver':False,'only_original_F_middle_withdrawal_proposed':[[116.2,202.35],[120.1,202.35]],'model_native_board_rules_current_or_signed_load_changes':0,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R323_COMPLETE',sha(O/'receipt.json'),{k:len(v)for k,v in accepted.items()},flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
