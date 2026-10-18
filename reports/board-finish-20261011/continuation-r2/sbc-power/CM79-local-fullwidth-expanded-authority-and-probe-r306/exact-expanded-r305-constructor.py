"""Exact single full1.25 CORE5 wall restoration + CM79 .20F source join.

Only nomination and conditional local trace arithmetic; every simultaneous
signed load remains retained and whole current/return/drop/native stays open.
"""
import hashlib,json,pickle,sys,uuid,traceback,math
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import physical_reference_losses_r3_zero_r208 as RF
import audit_aux_exact_raw as A
import tri_route as TR
O=H/'sbc-power/CM79-local-fullwidth-CORE5-three-owned-stitch-endpoint-preserving-nomination-r305'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def buf(sh,r):b=Z.bounded_buffer(sh,r);z=set_precision(b,0);assert z.wkb==b.wkb;return z
def main():
 assert not O.exists();O.mkdir();base=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289';mp=base/'model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());peer=H/'coupled-recovery/CM-J15002-pin79-additional-old-F-walls-r326/receipt.json';assert sha(peer)=='bd87259b1d25d7133ab8a3b0213d160b04a5f689db5ccbba649696911c835051';uid='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1';old=next(t for t in h['tracks']if t['uuid']==uid);assert old['net']=='/mc_local_power{slash}CORE_5V'and old['w']==1.25 and old['layer']=='F.Cu';source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';raw=source.read_bytes();iv=A.C.inventory(raw);identity=A.N.SourceNets(raw);chunk=iv[3][uid];parsed=A.G.parse(uid,chunk,{});assert(parsed['net'],parsed['layer'],parsed['w'],parsed['a'],parsed['b'])==(L.norm(old['net']),old['layer'],old['w'],old['a'],old['b']);(O/(uid+'.exact-old-CORE5-delete-chunk')).write_bytes(chunk);p=next(p for p in h['pads']if(p['ref'],p['num'])==('J15002','79'));target=next(p for p in h['pads']if(p['ref'],p['num'])==('J15002','73'));assert p['net']==target['net']=='/LOGIC_GND';owned_removed={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('a060edb3-')),'4eb351fd-d29e-562b-95ba-98a5f14deb87','855a5b14-80a8-5583-86ff-6f64a1a2d868'};selected=[t for t in h['tracks']if t['uuid']in owned_removed];assert len(selected)==3;assert all(t['uuid']not in iv[3]and t['net']=='/LOGIC_GND'and t['layer']=='F.Cu'and t['w']==.2 for t in selected);rtracks=[]
 for t in selected:
  rp=[t['a'],[t['a'][0],203.629990],[120.0,203.629990],t['b']]
  rtracks.extend({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R305-owned-leg:'+t['uuid']+':'+str(i))),'net':t['net'],'layer':'F.Cu','w':.2,'a':aa,'b':bb}for i,(aa,bb)in enumerate(zip(rp,rp[1:]))if aa!=bb)
 restored_ground_body=unary_union([buf(LineString([t['a'],t['b']]),.1)for t in rtracks]);put(O/'exact-three-owned-CM49-original-leg-selectors.json',selected);put(O/'three-owned-CM49-proposed-endpoint-preserving-legs.json',rtracks);rec,trees=F.build({**c,'zones':[]},layers={'F.Cu'});holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);outline=unary_union(L.poly(h['outline'])).buffer(-.525);reserve,exempt=A.reservations();dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6
 def free(net,width,clip,extra=()):
  rad=width/2;cuts=[]
  for j in trees['F.Cu'].query(clip.buffer(2),predicate='intersects'):
   rr=rec['F.Cu'][int(j)]
   if rr['uuid']==uid or rr['uuid']in owned_removed or L.norm(rr['net'])==L.norm(net):continue
   req=gap(net,rr['net'])+.025+.000003
   if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];cut=buf(LineString([t['a'],t['b']]),t['w']/2+rad+req)
   elif rr['kind']=='via':v=rr['source'];cut=buf(Point(v['x'],v['y']),v['d']/2+rad+req)
   else:cut=buf(rr['shape'],rad+req)
   cuts.append(cut)
  for j in ht.query(clip.buffer(2),predicate='intersects'):
   u,n,sh=holes[int(j)]
   if L.norm(n)!=L.norm(net):cuts.append(buf(sh,rad+.275+.005003))
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rule in rules:
    if ex and L.norm(net)in exempt.get(rule['name'],set()):continue
    if'F.Cu'in rule['layers']and(ex or rule.get('no_tracks')):
     cuts.extend(buf(sh,rad+.025003)for sh in L.poly(rule['outline'])if sh.intersects(clip))
  cuts.extend(buf(sh,rad+.175003)for sh in extra);return clip.intersection(outline.buffer(-rad-.000003)).difference(unary_union(cuts))
 ra=H/'sbc-power/CM79-power-terminal-exact-native-frozen-rule-area-diagnosis-r292/receipt.json';assert sha(ra)=='0c0ab17cd9cf8571d712d16265b9774909d6c7392086805aad82d73abcd1ed4f';cases=[];winner=None;oldlength=math.dist(old['a'],old['b']);oldbody=buf(LineString([old['a'],old['b']]),.625);anchor_start=[120.1,202.35];local_start=[116.2,202.35];preanchor={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R305-exact-unchanged-original-CORE5-preanchor')),'net':old['net'],'layer':'F.Cu','w':1.25,'a':old['a'],'b':local_start};prebody=buf(LineString([preanchor['a'],preanchor['b']]),.625);assert prebody.difference(oldbody).is_empty;anchor={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R305-exact-unchanged-original-CORE5-anchor')),'net':old['net'],'layer':'F.Cu','w':1.25,'a':anchor_start,'b':old['b']};anchorbody=buf(LineString([anchor['a'],anchor['b']]),.625);assert anchorbody.difference(oldbody).is_empty
 for y in(201.800005,201.805,201.81,201.815):
  gp=[[p['x'],p['y']],[p['x'],y],[target['x'],y],[target['x'],target['y']]];gt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R305:'+str(y)+':ground:'+str(i))),'net':'/LOGIC_GND','layer':'F.Cu','w':.2,'a':aa,'b':bb}for i,(aa,bb)in enumerate(zip(gp,gp[1:]))];gb=unary_union([buf(LineString([t['a'],t['b']]),.1)for t in gt]);small=box(114,198,121,205);gf=free('/LOGIC_GND',.2,small);row={'ground_y_mm':y,'fixed_ground_legs_exact_foreign_Cu_and_hole_polygon_covered':gf.covers(LineString(gp)),'power_route_windows':[]};cases.append(row)
  if not row['fixed_ground_legs_exact_foreign_Cu_and_hole_polygon_covered']:continue
  for radius in(8.,16.,25.,40.):
   mid=[(old['a'][0]+old['b'][0])/2,old['a'][1]];clip=box(mid[0]-radius,mid[1]-radius,mid[0]+radius,mid[1]+radius);pf=free(old['net'],1.25,clip,[gb,restored_ground_body]);faces=[ff for ff in RF.parts(pf)if ff.covers(Point(local_start))and ff.covers(Point(anchor_start))];rrow={'radius_mm':radius,'whole_fullwidth_original_endpoint_face_count':len(faces),'exact_old_local_preanchor_entry_free':pf.covers(Point(local_start)),'old_reserved_anchor_entry_axis_free':pf.covers(Point(anchor_start))};row['power_route_windows'].append(rrow)
   if not faces:continue
   path,method=TR.route(faces[0],local_start,anchor_start);path=[[round(xx,6),round(yy,6)]for xx,yy in path]
   if not faces[0].covers(LineString(path)):rrow['failure']='New power path rounding leaves exact free polygon';continue
   pt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R305:'+str(y)+':CORE5:'+str(i))),'net':old['net'],'layer':'F.Cu','w':1.25,'a':aa,'b':bb}for i,(aa,bb)in enumerate(zip(path,path[1:]))];pt.extend([preanchor,anchor]);powerbody=unary_union([buf(LineString([t['a'],t['b']]),.625)for t in pt]);novel=powerbody.difference(oldbody);rule_rows=[];rule_bad=[]
   for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
    for rule in rules:
     if'F.Cu'not in rule['layers']or(not ex and not rule.get('no_tracks'))or(ex and L.norm(old['net'])in exempt.get(rule['name'],set())):continue
     for sh in L.poly(rule['outline']):
      if powerbody.distance(sh)<.025:
       row0={'rule':rule.get('name',rule.get('uuid')),'full_new_body_overlap_mm2':powerbody.intersection(sh).area,'exact_unchanged_old_body_overlap_mm2':oldbody.intersection(sh).area,'true_novel_body_overlap_mm2':novel.intersection(sh).area,'true_novel_body_rule_gap_mm':novel.distance(sh),'no_new_native_or_frozen_exception':True};rule_rows.append(row0)
       if novel.distance(sh)<.025:rule_bad.append(row0)
   rrow['exact_old_anchor_novel_rule_rows']=rule_rows
   if rule_bad:rrow['failure']='Novel power body enters exact frozen rule reserve';continue
   gf2=free('/LOGIC_GND',.2,box(110,198,136,208),[powerbody]);owned_bad=[t['uuid']for t in rtracks if not gf2.covers(LineString([t['a'],t['b']]))];rrow['three_owned_full_20_legs_outside_all_native_Cu_hole_rule_and_new_fullwidth_power_failure_UUIDs']=owned_bad
   if owned_bad:continue
   trial={**c,'tracks':[t for t in c['tracks']if t['uuid']!=uid and t['uuid']not in owned_removed]+gt+rtracks+pt};ctx=K.hole_context(c);_,aa=K.physical(c,L.norm(old['net']),ctx);_,bb=K.physical(trial,L.norm(old['net']),ctx);proof,loss=K.contact_losses(aa,bb,{uid});rrow['all_retained_old_actual_power_relationship_losses']=loss
   if loss:continue
   length=sum(math.dist(t['a'],t['b'])for t in pt);conditional=[]
   for cu in(35,25):
    for temp in(60,100,125):
     rho=1.7241e-8*(1+.00393*(temp-20));sheet=rho/(cu*1e-6);conditional.append({'conditional_Cu_um':cu,'conditional_Copper_C':temp,'old_single_physical_1p25_trunk_R_ohm':sheet*oldlength/1.25,'new_fullwidth_path_R_ohm':sheet*length/1.25,'incremental_R_ohm':sheet*(length-oldlength)/1.25,'if_all_full_signed_CORE5_7p882034293398381A_used_this_piece_delta_drop_mV_BOUND_ONLY':7.882034293398381*sheet*(length-oldlength)/1.25*1000,'no_real_port_sharing_or_current_capacity_or_total_drop_claim':True})
   winner={'ground_path':gp,'new_tracks':gt+rtracks+pt,'owned_CM49_removed_track_UUIDs':sorted(owned_removed),'owned_CM49_barrels_relocated':0,'all_three_own_leg_actual_endpoints_exact':True,'owned_CM49_three_leg_new_track_count':len(rtracks),'new_ground_track_count':len(gt),'new_CORE5_full1p25_track_count':len(pt),'original_native_pre_and_post_anchor_Cu_is_exact_subset_only':True,'local_novel_detour_original_coords_mm':[local_start,anchor_start],'exact_old_anchor_novel_rule_rows':rule_rows,'true_novel_power_WKB_sha256':__import__('hashlib').sha256(novel.wkb).hexdigest(),'removed_original_track_UUIDs':[uid],'power_path':path,'power_route_method':method,'old_single_physical_1p25_length_mm':oldlength,'new_fullwidth_power_length_mm':length,'actual_old_power_contact_relationship_loss_count':len(loss),'conditional_local_full_signed_load_drop_cases':conditional,'raw_source_power_token_exact':identity.raw(L.norm(old['net'])),'all_old_SMD_pose_native_via_annuli_source_rules_unchanged':True,'current_reference_full_source_field_successor_mutual_fault_native':'OPEN'};break
  put(O/'finite-fullwidth-current-preserving-matrix.json',cases)
  if winner:break
 put(O/'finite-fullwidth-current-preserving-matrix.json',cases)
 if winner:(O/'only-coupled-CM79-CORE5-discrete-and-exact-single-delete.pkl').write_bytes(pickle.dumps({'tracks':winner['new_tracks'],'vias':[],'removed_original_track_UUIDs':[uid],'removed_only_unadopted_CM49_owner_track_UUIDs':sorted(owned_removed)},protocol=5))
 put(O/'receipt.json',{'verdict':'COUPLED_CM79_FULLWIDTH_POWER_WALL_NOMINEE_PENDING_ALL_CURRENT_SOURCE_REFERENCE_GATES'if winner else'NO_FULLWIDTH_CM79_POWER_WALL_COUPLED_NOMINEE_IN_DECLARED_WINDOWS','exact_latest_CM_FIELD393_model_sha256':sha(mp),'exact_old_power_wall_source_obligation_receipt_sha256':sha(peer),'exact_original_power_source_chunk_sha256':sha(O/(uid+'.exact-old-CORE5-delete-chunk')),'winner':winner,'new_or_relocated_native_vias':0,'existing_49_CM_barrels_and_all_unselected_paths_untouched':True,'only_three_owned_20F_stitch_legs_renominated_endpoint_preserving':True,'all49_CM_actual_source_physics_and_latest_field_rebind':'PENDING','full_signed_CORE5_7p882A_CM3p559_return_other_loads_not_reduced':True,'no_full_current_return_mesh_solve_while_CM51_disconnected':True,'source_return_total_drop_capacity_fault_native_and_failed_reference_gates':'FAIL_OR_OPEN_RETAINED','board_written':False,'native_jobs':0,'adopted':False,'script_sha256':sha(__file__)});print('R305_COMPLETE',winner is not None,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
