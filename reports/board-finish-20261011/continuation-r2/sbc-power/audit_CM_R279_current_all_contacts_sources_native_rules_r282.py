"""Fresh CM physical graph/source proof on R364 diagnostic groups, no waiver."""
import hashlib,json,pickle,sys,collections,time,traceback,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import physical_reference_losses_r3_zero_r208 as RF
import guarded_power_projection_r44 as Z
import audit_aux_exact_raw as A
O=H/'sbc-power/CM-R279-current-independent-all-contact-source-native-rule-r282'
ROOTS=K.ROOTS+[('/mc_local_power/CORE_5V','R11022','2'),('/motherboard_motors/AUX_5V_B','U11014','6')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def zero(s):n=set_precision(s,0);assert n.wkb==s.wkb;return n
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();P=H/'sbc-power/CM-sparse-exact-current-R364-normal-antipads-local-negative-r279';r=json.loads((P/'receipt.json').read_text());mp=P/'model.pkl';assert sha(mp)==r['model_sha256'];g,h,b,q,after=pickle.loads(mp.read_bytes());bp=H/'field-power/REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364/model.pkl';assert sha(bp)==r['exact_current_parent_model_sha256']=='a39e7784abf8969b7f68176555b2c37b5227981cbc615c4bd542205e410373ad';bg,bh,bb,bq,before=pickle.loads(bp.read_bytes());assert g==bg;dp=P/'only-new-CM-ordinary-discrete-no-deletes.pkl';assert sha(dp)==r['sparse_discrete_sha256'];d=pickle.loads(dp.read_bytes());nt=d['tracks'];nv=d['vias'];items=nt+nv;assert not d['removed_original_track_UUIDs'];assert h['tracks']==bh['tracks']+nt and h['vias']==bh['vias']+nv;assert all(h[k]==bh[k]for k in h if k not in('tracks','vias'));assert after['tracks']==h['tracks']and after['vias']==h['vias'];fg=H/'field-power/REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368';gp=fg/'actual-drilled-current-groups.pkl';assert sha(gp)=='ee233fd9010cf3c29d0c4b47503fd93bf754dddf9dd297f9f7c58117c7589742';assert sha(fg/'receipt.json')=='e4a9373b5816de6926cc3b3cea82d1751e5db6cb70d9f150443dff577afff29e';oldgroups=pickle.loads(gp.read_bytes());affected=set(r['affected_nets']);ctx=K.hole_context(after);newholes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in nv];holeTree=STRtree(newholes);groups={};contacts=[];bad=[];reuses=[]
 for net in sorted(oldgroups):
  old=oldgroups[net];disjoint=all(not len(holeTree.query(rr['shape'],predicate='intersects'))for xs in old for rr in xs)
  if net not in affected and disjoint:
   new=old;reuses.append({'net':net,'every_old_physical_Cu_piece_disjoint_from_all_new_actual_drills':True,'all_net_geometry_and_current_filled_arrays_exact_unchanged':True})
  else:_,new=K.physical(after,net,ctx)
  groups[net]=new;rows,loss=K.contact_losses(old,new);contacts.append({'net':net,'old_actual_drilled_layer_key_relationship_losses':loss,'unchanged_disjoint_reuse':net not in affected and disjoint});bad.extend({'net':net,**x}for x in loss);put(O/'all-current-contact-progress.json',contacts);print('R282_CONTACT',net,len(loss),flush=True)
 (O/'actual-drilled-current-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));changed={(x['zone_UUID'],x['layer'])for x in json.loads((P/'only-new-CM-current-filled-record-operations.json').read_text())};direct=[];directbad=[]
 for net in affected:
  old=oldgroups[net];new=groups[net];final=collections.defaultdict(list)
  for xs in new:
   for rr in xs:
    if rr['kind']=='fill':final[rr['uuid'],rr['layer']].append(rr['shape'])
  for l in K.LAYERS:
   metal=[rr for xs in old for rr in xs if rr['kind']!='fill'and rr['layer']==l];tree=STRtree([rr['shape']for rr in metal])
   for fill in(rr for xs in old for rr in xs if rr['kind']=='fill'and rr['layer']==l and(rr['uuid'],l)in changed):
    for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
     rr=metal[int(j)]
     if rr['shape'].distance(fill['shape'])>.000002:continue
     kept=any(sh.distance(rr['shape'])<=.000002 for sh in final[fill['uuid'],l]);row={'net':net,'zone_UUID':fill['uuid'],'layer':l,'old_layer_key':[rr['kind'],rr['uuid'],l],'same_actual_native_or_owned_fill_direct_contact_retained':kept};direct.append(row)
     if not kept:directbad.append(row)
 sources=[];oldrefs=[]
 for net,ref,pin in ROOTS:
  aa=K.root(oldgroups[net],ref,pin);nn=K.root(groups[net],ref,pin);missing=sorted(K.keys(aa)-K.keys(nn));sources.append({'net':net,'actual_source':ref+'.'+pin,'lost_prior_source_physical_layer_keys':[list(k)for k in missing]})
  if ref in('J11001','J11003','J11005'):
   loss,proof=RF.audit(before,K.source_refs(aa),K.source_refs(nn),net);oldrefs.append({'net':net,'strict_ZERO_before_R364_retained_track_reference_losses':loss,'proof':proof})
 lg=K.root(groups['/LOGIC_GND'],'J11001','2');lgkeys=K.keys(lg);cm=[p for p in h['pads']if p['ref']in('J15001','J15002')and p['net']=='/LOGIC_GND'];assert len(cm)==51;cmrows=[{'ref':p['ref'],'pin':p['num'],'actual_pad_UUID':p['uuid'],'native_pose_mm':[p['x'],p['y']],'actual_source_rooted':any(('pad',p['uuid'],l)in lgkeys for l in p['layers'])}for p in cm];references={l:zero(s)for l,s in K.source_refs(lg).items()};bodyrefs=[]
 for t in nt:
  actual=unary_union([rr['shape']for xs in groups['/LOGIC_GND']for rr in xs if rr['kind']=='track'and rr['uuid']==t['uuid']and rr['layer']==t['layer']]);gap=zero(actual).difference(references[t['layer']]);f=O/(t['uuid']+'-actual-drill-subtracted-full-Cu-source-fill-reference-gap.wkb');f.write_bytes(gap.wkb);bodyrefs.append({'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'real_drill_subtracted_full_actual_Cu_reference_gap_mm2':gap.area,'gap_empty':gap.is_empty,'gap_sha256':sha(f),'no_reference_shadow_buffer_or_generic_own_disk':True})
 annuli=[]
 for v in nv:
  pieces=[rr for rr in lg if rr['kind']=='via'and rr['uuid']==v['uuid']];areas={l:sum(rr['shape'].intersection(ff['shape']).area for rr in pieces if rr['layer']==l for ff in lg if ff['kind']=='fill'and ff['layer']==l and ff['shape'].intersects(rr['shape']))for l in K.LAYERS};annuli.append({'UUID':v['uuid'],'actual_source_rooted_via':any(('via',v['uuid'],l)in lgkeys for l in v['flashed']),'actual_drilled_real_annular_source_fill_contact_mm2_by_layer':areas,'native_flash_evidence':'PROSPECTIVE_ALL6_NATIVE_PENDING'})
 rec,trees=F.build({**after,'zones':[]});filled={l:[]for l in K.LAYERS}
 for z in after['zones']:
  for l,rs in z['fills'].items():filled[l].extend({'uuid':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':sh}for sh in L.poly(rs))
 ft={l:STRtree([rr['shape']for rr in xx])for l,xx in filled.items()};dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;checks=[];errors=[];planner=[];holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for uid,n,sh in holes]);smd=[(p,sh)for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree([sh for p,sh in smd]);allv=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(allv);outline=unary_union(L.poly(h['outline'])).buffer(-.525);reserve,exempt=A.reservations()
 for x in items:
  via='d'in x;axis=Point(x['x'],x['y'])if via else LineString([x['a'],x['b']]);rad=x['d']/2 if via else x['w']/2;body=Z.bounded_buffer(axis,rad);layers=K.LAYERS if via else[x['layer']]
  for l in layers:
   targets=[rr for j in trees[l].query(body.buffer(.8),predicate='intersects')for rr in[rec[l][int(j)]]]+[{'kind':'fill',**filled[l][int(j)]}for j in ft[l].query(body.buffer(.8),predicate='intersects')]
   for rr in targets:
    if L.norm(rr['net'])=='/LOGIC_GND':continue
    if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];dist=axis.distance(LineString([t['a'],t['b']]))-rad-t['w']/2
    elif rr['kind']=='via':v=rr['source'];dist=axis.distance(Point(v['x'],v['y']))-rad-v['d']/2
    else:dist=axis.distance(rr['shape'])-rad
    native=max(gap(x['net'],rr['net']),rr.get('local',0));row={'new_UUID':x['uuid'],'other_UUID':rr['uuid'],'layer':l,'kind':rr['kind'],'true_analytic_gap_mm':dist,'actual_native_required_mm':native,'new_planner_required_mm':native+.025};checks.append(row)
    if dist<native:errors.append(row)
    if dist<native+.025:planner.append(row)
  if not outline.covers(body):errors.append({'kind':'native_edge','UUID':x['uuid']})
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rule in rules:
    if ex and'/LOGIC_GND'in exempt.get(rule['name'],set()):continue
    if set(layers)&set(rule['layers'])and(ex or rule.get('no_vias'if via else'no_tracks'))and any(body.distance(sh)<.025 for sh in L.poly(rule['outline'])):errors.append({'kind':'frozen_or_native_keepout','UUID':x['uuid'],'rule':rule.get('name',rule.get('uuid'))})
  if via:
   near=smd[int(st.nearest(axis))];sg=axis.distance(near[1])-x['drill']/2-.005;dnear=min((axis.distance(sh)-x['drill']/2-.005,uid)for uid,n,sh in holes if uid!=x['uuid']);pitch=min((axis.distance(pp),h['vias'][i]['uuid'])for i,pp in enumerate(allv)if h['vias'][i]['uuid']!=x['uuid']);row={'UUID':x['uuid'],'kind':'every_SMD_drill_ordinary_pitch','SMD_gap_mm':sg,'nearest_SMD_UUID':near[0]['uuid'],'every_drill_nearest':dnear,'ordinary_pitch_nearest':pitch};checks.append(row)
   if sg<.275 or dnear[0]<.275 or pitch[0]<.815:errors.append(row)
  else:
   for j in ht.query(body.buffer(.285),predicate='intersects'):
    uid,n,sh=holes[int(j)]
    if L.norm(n)=='/LOGIC_GND':continue
    gd=axis.distance(sh)-rad-.005;row={'UUID':x['uuid'],'kind':'every_foreign_hole_track_guard','other_UUID':uid,'guarded_gap_mm':gd,'required_mm':.275};checks.append(row)
    if gd<.275:errors.append(row)
 put(O/'all-current-retained-physical-contact-losses.json',bad);put(O/'all-direct-current-filled-contact-ledger.json',direct);put(O/'all-direct-current-filled-contact-losses.json',directbad);put(O/'all-nine-prior-source-layer-keys.json',sources);put(O/'three-bank-strict-zero-incremental-oldrefs.json',oldrefs);put(O/'all-51-CM-actual-pad-source-membership.json',cmrows);put(O/'all-new-real-annular-source-fill-contacts.json',annuli);put(O/'all-new-full-actual-drilled-body-source-reference-gaps.json',bodyrefs);put(O/'all-new-true-native-and-planning-checks.json',checks);put(O/'all-new-actual-native-errors.json',errors);put(O/'all-new-extra-planner-deficits.json',planner);put(O/'unchanged-graph-explicit-disjointness-reuse.json',reuses);result={'verdict':'CM_INCREMENTAL_PHYSICAL_SOURCE_DIAGNOSTIC_FULL_RETURN_REFERENCE_CURRENT_NATIVE_OPEN','exact_R279_model_sha256':sha(mp),'exact_R364_parent_model_sha256':sha(bp),'exact_R368_parent_actual_groups_sha256':sha(gp),'parent_R368_strict_oldrefs_FAIL_count_retained':28,'actual_current_net_count':len(groups),'retained_actual_drilled_contact_loss_count':len(bad),'direct_fill_contact_loss_count':len(directbad),'nine_prior_source_key_loss_count':sum(len(x['lost_prior_source_physical_layer_keys'])for x in sources),'strict_ZERO_incremental_R364_oldref_loss_count':sum(len(x['strict_ZERO_before_R364_retained_track_reference_losses'])for x in oldrefs),'new_actual_native_rule_error_count':len(errors),'new_extra_planner_deficit_count':len(planner),'CM_actual_source_rooted_pad_count':sum(x['actual_source_rooted']for x in cmrows),'CM_not_source_rooted':[x for x in cmrows if not x['actual_source_rooted']],'new_full_actual_drilled_Cu_reference_FAIL_count':sum(not x['gap_empty']for x in bodyrefs),'new_ordinary_via_count':len(nv),'new_real_source_rooted_via_count':sum(x['actual_source_rooted_via']for x in annuli),'all_new_via_real_finite_source_fill_annuli':all(any(a>0 for a in x['actual_drilled_real_annular_source_fill_contact_mm2_by_layer'].values())for x in annuli),'actual_current_groups_sha256':sha(O/'actual-drilled-current-groups.pkl'),'full_signed_CM_3p559304644A_no_simplex_reassignment_or_equalshare':'FAIL_OR_OPEN_UNTIL_ALL51_SOURCE_CURRENT_CAPACITY_FAULT_NATIVE','inherited_CORE_fullbody_R7_six_extra_planner_parent28_oldrefs_current_native':'FAIL_OR_OPEN_RETAINED','source_native_board_and_rules_unchanged':True,'board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)};put(O/'receipt.json',result);print('R282_COMPLETE',sha(O/'receipt.json'),result['CM_actual_source_rooted_pad_count'],len(bad),len(errors),result['strict_ZERO_incremental_R364_oldref_loss_count'],flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
