"""Fresh exact sparse bytes/actual contacts/source/refs/native, no gate waiver."""
import hashlib,json,pickle,sys,time,collections,math,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import physical_reference_losses_r3_zero_r208 as RF
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-R315-fresh-sparse-current-source-native-reference-audit-r316'
ROOTS=K.ROOTS+[('/mc_local_power/CORE_5V','R11022','2'),('/motherboard_motors/AUX_5V_B','U11014','6')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def signature(c,net):return pickle.dumps({k:[x for x in c[k]if L.norm(x['net'])==net]for k in('tracks','vias','pads','zones')},protocol=5)
def allparts(sh):
 if sh.is_empty:return []
 return sum((allparts(x)for x in sh.geoms),[])if hasattr(sh,'geoms')else[sh]
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();p=H/'sbc-power/CM79-exact-R289-existing-return-fullwidth-sparse-diagnostic-r315';r=json.loads((p/'receipt.json').read_text());assert sha(p/'receipt.json')=='2c86eed57b368e0470cfaa0540899b2c446e758b6e359fae234e82d977227106';mp=p/'model.pkl';assert sha(mp)==r['model_sha256']=='df44ef8d66cc4bea0b2dd1bf1e8ab9d9c54e4c88e41c92fefd0301f5555391bf';g,h,b,q,after=pickle.loads(mp.read_bytes());bp=Path(r['exact_current_parent_model_file']);assert sha(bp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';bg,bh,bb,bq,before=pickle.loads(bp.read_bytes());assert g==bg;d=pickle.loads((p/'only-CM79-six-tracks-two-power-vias-one-exact-old-delete.pkl').read_bytes());assert sha(p/'only-CM79-six-tracks-two-power-vias-one-exact-old-delete.pkl')==r['sparse_discrete_sha256'];removed=set(d['removed_original_track_UUIDs']);assert removed=={'dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1'};nt=d['tracks'];nv=d['vias'];assert len(nt)==6 and len(nv)==2;assert h['tracks']==[x for x in bh['tracks']if x['uuid']not in removed]+nt and h['vias']==bh['vias']+nv;assert all(h[k]==bh[k]for k in h if k not in('tracks','vias'));assert all(a['uuid']==z['uuid']and all(a[role].wkb==z[role].wkb for role in('shape','zone_outline_shape'))for a,z in zip(q,bq));assert len(q)==len(bq);ops=json.loads((p/'exact-sparse-new-CM-native-operation-ledger.json').read_text());source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';raw=source.read_bytes();iv=A.C.inventory(raw);identity=A.N.SourceNets(raw);native={};parsed=[]
 for op in ops:
  if op['action']=='delete':ch=Path(op['exact_old_native_source_chunk_path']).read_bytes();assert sha(Path(op['exact_old_native_source_chunk_path']))==op['exact_old_native_source_chunk_sha256'];assert iv[3][op['uuid']]==ch;continue
  ch=Path(op['exact_chunk_path']).read_bytes();assert sha(Path(op['exact_chunk_path']))==op['exact_chunk_sha256'];native[op['uuid']]=ch;pp=A.G.parse(op['uuid'],ch,{});x=op['exact_geometry'];assert identity.raw(pp['net'])==x['net']
  if pp['kind']=='segment':assert(pp['layer'],pp['w'],pp['a'],pp['b'])==(x['layer'],x['w'],x['a'],x['b'])
  else:assert(pp['d'],pp['drill'],pp['at'])==(x['d'],x['drill'],[x['x'],x['y']])
  parsed.append(op['uuid'])
 identity.assert_chunks(native);assert len(native)==8 and len(parsed)==8
 changed=[];fill_gains=[]
 for zz,aa in zip(before['zones'],after['zones']):
  assert {k:v for k,v in zz.items()if k!='fills'}=={k:v for k,v in aa.items()if k!='fills'}
  for ly,rs in zz['fills'].items():
   if rs==aa['fills'][ly]:continue
   old=zero(unary_union(L.poly(rs)));new=zero(unary_union(L.poly(aa['fills'][ly])));gain=new.difference(old);changed.append((zz['uuid'],ly));
   if not gain.is_empty:fn=O/(zz['uuid']+'-'+ly+'-literal-aggregate-filled-gain.wkb');fn.write_bytes(gain.wkb);fill_gains.append({'zone':zz['uuid'],'layer':ly,'area_mm2':gain.area,'type':gain.geom_type,'sha256':sha(fn)})
 put(O/'independent-native-bytes-settings-and-local-fill-scope.json',{'new_native_chunks':parsed,'removed_exact_original_UUIDs':sorted(removed),'all_q_roles_WKB_exact':True,'all_native_zone_definitions_and_settings_exact':True,'only_changed_current_filled_scopes':changed,'literal_union_raw_gain_failures':fill_gains,'constructor_per_original_record_raw_gain_and_local100nm_ledgers_retained':True,'unrelated_q93_outside_physical_FAIL_not_retested_or_waived':True})
 cp=H/'sbc-power/CM-sparse-exact-current-R364-only-new-role-withdrawal-inherited-fills-FAIL-r283/model.pkl';assert sha(cp)=='592ca2e2137c1e38e91eb1c9fe6a8ca29fdc549cbf27b209ea2518ad8e952151';cg,ch,cb,cq,cached=pickle.loads(cp.read_bytes());cache=H/'sbc-power/CM-R283-current-independent-all-contact-source-native-rule-r284';cr=json.loads((cache/'receipt.json').read_text());assert sha(cache/'receipt.json')=='877050f6d37de31e39381d08a08c39f8acf789da412853b3ae65aa607af7fa62';assert sha(cache/'actual-drilled-current-groups.pkl')==cr['actual_current_groups_sha256'];cachedgroups=pickle.loads((cache/'actual-drilled-current-groups.pkl').read_bytes());assert bh['vias']==ch['vias']and bh['pads']==ch['pads'];oldctx=K.hole_context(before);newctx=K.hole_context(after);drills=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in nv];dt=STRtree(drills);oldgroups={};groups={};contact=[];losses=[];reuse=[];nets=sorted(set(cachedgroups)|{L.norm(x['net'])for k in('tracks','vias','pads','zones')for x in before[k]if x['net']})
 for net in nets:
  exact_cache=net in cachedgroups and signature(before,net)==signature(cached,net)
  if exact_cache:old=cachedgroups[net]
  else:_,old=K.physical(before,net,oldctx)
  unchanged=signature(after,net)==signature(before,net);disjoint=all(not len(dt.query(rr['shape'],predicate='intersects'))for xs in old for rr in xs)
  if unchanged and disjoint:new=old
  else:_,new=K.physical(after,net,newctx)
  oldgroups[net]=old;groups[net]=new;rr,ll=K.contact_losses(old,new,removed);contact.append({'net':net,'physical_before_cache_exact_per_net_metadata_and_fill':exact_cache,'before_to_after_same_Cu_and_filled_arrays':unchanged,'all_new_true_drills_disjoint':disjoint,'old_group_retained_relationship_ledger':rr,'losses':ll});losses.extend({'net':net,**x}for x in ll);reuse.append({'net':net,'before_cache_used_only_after_all_net_native_item_and_filled_array_equality':exact_cache,'after_reused_only_if_exact_all_net_native_item_fill_equality_and_every_Cu_piece_new_drill_disjoint':unchanged and disjoint});put(O/'all-current-contact-progress.json',contact);print('R316_CONTACT',net,len(ll),exact_cache,unchanged and disjoint,flush=True)
 (O/'actual-drilled-before-groups.pkl').write_bytes(pickle.dumps(oldgroups,protocol=5));(O/'actual-drilled-after-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));direct=[];directloss=[]
 for net in r['affected_nets']:
  old=oldgroups[net];new=groups[net];final=collections.defaultdict(list)
  for xs in new:
   for rr in xs:
    if rr['kind']=='fill':final[rr['uuid'],rr['layer']].append(rr['shape'])
  for ly in K.LAYERS:
   metal=[rr for xs in old for rr in xs if rr['kind']!='fill'and rr['layer']==ly and rr['uuid']not in removed];tree=STRtree([rr['shape']for rr in metal])
   for fill in(rr for xs in old for rr in xs if rr['kind']=='fill'and rr['layer']==ly and(rr['uuid'],ly)in changed):
    for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
     rr=metal[int(j)]
     if rr['shape'].distance(fill['shape'])>.000002:continue
     keep=any(sh.distance(rr['shape'])<=.000002 for sh in final[fill['uuid'],ly]);row={'net':net,'zone':fill['uuid'],'layer':ly,'retained_actual_layer_key':[rr['kind'],rr['uuid'],ly],'same_native_current_fill_direct_contact_retained':keep};direct.append(row)
     if not keep:directloss.append(row)
 sources=[];refs=[];literal=[]
 for net,ref,pin in ROOTS:
  aa=K.root(oldgroups[net],ref,pin);nn=K.root(groups[net],ref,pin);missing=sorted(k for k in K.keys(aa)-K.keys(nn)if not(k[0]=='track'and k[1]in removed));sources.append({'net':net,'source':ref+'.'+pin,'missing_retained_source_layer_keys':[list(k)for k in missing]})
  if ref not in('J11001','J11003','J11005'):continue
  ar={ly:zero(sh)for ly,sh in K.source_refs(aa).items()};nr={ly:zero(sh)for ly,sh in K.source_refs(nn).items()};ll,pf=RF.audit(before,ar,nr,net,removed);refs.append({'bank':net,'RF_r3_losses':ll,'proof':pf});delta={ly:ar[ly].difference(nr[ly])for ly in ar};pieces={ly:allparts(sh)for ly,sh in delta.items()};tt={ly:STRtree(shs)for ly,shs in pieces.items()}
  for t in before['tracks']:
   ly=t['layer'];rawnet=L.norm(t['net'])
   if t['uuid']in removed or ly not in ar or rawnet==net or before['domains_normalized'].get(rawnet)!=before['domains_normalized'][net]:continue
   body=zero(L.body(t));ix=tt[ly].query(body.envelope.buffer(.000000001),predicate='intersects')
   if not len(ix):continue
   selected=unary_union([pieces[ly][int(i)]for i in ix]);lost=body.intersection(selected)
   if not lost.is_empty:fn=O/(t['uuid']+'-strict-incremental-all-dimensional-source-reference-loss.wkb');fn.write_bytes(lost.wkb);literal.append({'bank':net,'track':t['uuid'],'net':t['net'],'layer':ly,'loss_area_mm2':lost.area,'loss_type':lost.geom_type,'every_nonempty_line_point_polygon_retained':True,'loss_sha256':sha(fn)})
 lg=K.root(groups['/LOGIC_GND'],'J11001','2');keys=K.keys(lg);cm=[p for p in h['pads']if p['ref']in('J15001','J15002')and p['net']=='/LOGIC_GND'];assert len(cm)==51;cmrows=[{'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'actual_source_rooted':any(('pad',p['uuid'],ly)in keys for ly in p['layers'])}for p in cm];lgrefs={ly:zero(sh)for ly,sh in K.source_refs(lg).items()};bodyref=[]
 for t in nt:
  net=L.norm(t['net']);actual=unary_union([rr['shape']for xs in groups[net]for rr in xs if rr['kind']=='track'and rr['uuid']==t['uuid']and rr['layer']==t['layer']]);lost=zero(actual).difference(lgrefs[t['layer']]);fn=O/(t['uuid']+'-new-actual-body-fill-only-source-reference-gap.wkb');fn.write_bytes(lost.wkb);bodyref.append({'UUID':t['uuid'],'net':t['net'],'layer':t['layer'],'actual_body_area_mm2':actual.area,'full_source_fill_reference_gap_empty':lost.is_empty,'gap_area_mm2':lost.area,'gap_type':lost.geom_type,'gap_sha256':sha(fn),'full_original_power_F_anchor_inherited_scope':t['net']!='/LOGIC_GND'and t['layer']=='F.Cu'})
 records,trees=F.build({**after,'zones':[]});filled={ly:[]for ly in K.LAYERS}
 for z in after['zones']:
  for ly,rs in z['fills'].items():filled[ly].extend({'kind':'fill','uuid':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':sh}for sh in L.poly(rs))
 ft={ly:STRtree([rr['shape']for rr in xs])for ly,xs in filled.items()};dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for u,n,sh in holes]);smd=[(p,sh)for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree([sh for p,sh in smd]);reserve,exempt=A.reservations();old=next(t for t in bh['tracks']if t['uuid']in removed);oldbody=zero(Z.bounded_buffer(LineString([old['a'],old['b']]),.625));checks=[];nativebad=[];planner=[];inherited=[]
 for x in nt+nv:
  via='d'in x;axis=Point(x['x'],x['y'])if via else LineString([x['a'],x['b']]);rad=x['d']/2 if via else x['w']/2;body=zero(Z.bounded_buffer(axis,rad));lyrs=K.LAYERS if via else[x['layer']];anchor=(not via and x['net']==old['net']and x['layer']=='F.Cu');novel=body.difference(oldbody)if anchor else body
  for ly in lyrs:
   targets=[records[ly][int(i)]for i in trees[ly].query(body.buffer(1),predicate='intersects')]+[filled[ly][int(i)]for i in ft[ly].query(body.buffer(1),predicate='intersects')]
   for rr in targets:
    if L.norm(rr['net'])==L.norm(x['net']):continue
    if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];dist=axis.distance(LineString([t['a'],t['b']]))-rad-t['w']/2
    elif rr['kind']=='via':v=rr['source'];dist=axis.distance(Point(v['x'],v['y']))-rad-v['d']/2
    else:dist=axis.distance(rr['shape'])-rad
    req=max(gap(x['net'],rr['net']),rr.get('local',0));row={'new_UUID':x['uuid'],'other_UUID':rr['uuid'],'layer':ly,'kind':rr['kind'],'actual_gap_mm':dist,'actual_native_required_mm':req,'fullbody_planner_required_mm':req+.025,'exact_original_F_anchor_novel_Cu_empty':anchor and novel.is_empty};checks.append(row)
    if dist<req:nativebad.append(row)
    if dist<req+.025:(inherited if anchor and novel.is_empty else planner).append(row)
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rr in rules:
    if ex and L.norm(x['net'])in exempt.get(rr['name'],set()):continue
    if set(lyrs)&set(rr['layers'])and(ex or rr.get('no_vias'if via else'no_tracks'))and any((novel if anchor else body).distance(sh)<.025 for sh in L.poly(rr['outline'])):nativebad.append({'kind':'native_or_frozen_keepout','new_UUID':x['uuid'],'rule':rr.get('name',rr.get('uuid'))})
  if via:
   near=smd[int(st.nearest(axis))];sg=axis.distance(near[1])-x['drill']/2-.005;hg=min(axis.distance(sh)-x['drill']/2-.005 for uid,n,sh in holes if uid!=x['uuid']);vp=min(axis.distance(Point(v['x'],v['y']))for v in h['vias']if v['uuid']!=x['uuid']);row={'new_UUID':x['uuid'],'kind':'ordinary_SMD_drill_pitch','SMD_gap_mm':sg,'old_or_peer_drill_gap_mm':hg,'old_or_peer_via_pitch_mm':vp};checks.append(row)
   if sg<.275 or hg<.275 or vp<.815:nativebad.append(row)
  else:
   for j in ht.query(body.buffer(.285),predicate='intersects'):
    uid,n,sh=holes[int(j)]
    if L.norm(n)==L.norm(x['net']):continue
    dd=axis.distance(sh)-rad-.005
    if dd<.275:nativebad.append({'kind':'every_foreign_real_hole_track_guard','new_UUID':x['uuid'],'other_UUID':uid,'gap_mm':dd,'required_mm':.275})
 pairs=json.loads((p/'bound-existing-return-port-and-fullwidth-proposal.json').read_text());conditional=[]
 for current in(4.396304643962848,7.882034293398379):
  for plating in(20,25):
   for temp in(60,100,125):
    rho=1.7241e-8*(1+.00393*(temp-20));barrel=rho*.000620/(math.pi*((.0001+plating*.000001)**2-.0001**2));conditional.append({'conserved_signed_branch_or_full_source_stress_A':current,'conditional_finished_plating_um':plating,'conditional_Cu_C':temp,'conditional_two_F_to_In2_used_barrels_length_each_mm':.620,'series_two_barrel_R_ohm':2*barrel,'series_two_barrel_drop_mV':current*2*barrel*1000,'series_two_barrel_power_W':current*current*2*barrel,'barrel_plating_stack_load_allocation_spreading_full_supply_and_return_thermal_qualification':'OPEN','no_equalsharing_capacity_or_total_loop_voltage_claim':True})
 put(O/'all-contact-losses.json',losses);put(O/'all-direct-native-fill-contact-ledger.json',direct);put(O/'all-direct-native-fill-contact-losses.json',directloss);put(O/'all-nine-prior-source-layer-key-proof.json',sources);put(O/'all-three-bank-RF-r3-oldref-proof.json',refs);put(O/'strict-all-dimensional-incremental-oldref-losses.json',literal);put(O/'all51-CM-source-pad-membership.json',cmrows);put(O/'all-six-new-body-fill-only-reference-gaps.json',bodyref);put(O/'all-new-true-Cu-native-geometry-ledger.json',checks);put(O/'all-new-native-rule-errors.json',nativebad);put(O/'all-actually-novel-extra-planner-deficits.json',planner);put(O/'full-new-anchor-only-inherited-planner-deficits.json',inherited);put(O/'exact-equality-and-drill-disjoint-cache-reuse.json',reuse);put(O/'conditional-signed-current-two-single-barrel-bottleneck.json',conditional);result={'verdict':'CM79_INCREMENTAL_DIAGNOSTIC_NEW_SOURCE_NATIVE_REFERENCE_RESULTS_FULL_BOARD_GATES_RETAINED','model_sha256':sha(mp),'parent_model_sha256':sha(bp),'actual_net_count':len(groups),'retained_actual_contact_loss_count':len(losses),'direct_original_fill_contact_loss_count':len(directloss),'nine_retained_prior_source_key_loss_count':sum(len(x['missing_retained_source_layer_keys'])for x in sources),'strict_all_dimensional_incremental_oldref_loss_count':len(literal),'new_actual_native_rule_error_count':len(nativebad),'new_novel_extra_planner_deficit_count':len(planner),'exact_unchanged_original_F_anchor_inherited_planner_deficit_count':len(inherited),'CM_actual_source_rooted_pad_count':sum(x['actual_source_rooted']for x in cmrows),'CM_remaining_unrooted':[x for x in cmrows if not x['actual_source_rooted']],'all_six_new_fullbody_fill_only_reference_FAIL_count':sum(not x['full_source_fill_reference_gap_empty']for x in bodyref),'literal_aggregate_filled_gain_FAIL_count':len(fill_gains),'actual_after_group_cache_sha256':sha(O/'actual-drilled-after-groups.pkl'),'allCM49_native_all6_and_raw_body_reference_current_plating_capacity_shared_signed_fullreturn_fault':'FAIL_OR_OPEN_RETAINED','before_FIELD_IO3_split_oldref_CORE93_q93outside_R7planner_NOZONE_failure_flags':'FAIL_OR_OPEN_RETAINED','native_jobs':0,'source_board_rules_or_adoption_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)};put(O/'receipt.json',result);print('R316_COMPLETE',sha(O/'receipt.json'),json.dumps(result),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
