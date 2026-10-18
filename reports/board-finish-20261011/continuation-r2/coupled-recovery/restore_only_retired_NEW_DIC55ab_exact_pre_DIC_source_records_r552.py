"""Retire only NEW55ab cache cutters against exact pinned pre-DIC records.

Every current native filled array remains literally unchanged. Source
fragments are added only inside the exact frozen owned cutter and the exact
pre-DIC source primitive, minus retained current Cu/holes/roles/keepouts.
This is an exploratory current-cache operation, never a native fill claim.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,copy
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import immutable_local_fill_subtraction_r254 as IM
from shapely import from_wkb,set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}

def main():
 st=time.monotonic();out=H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552';assert not out.exists();out.mkdir()
 mp=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(mp)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14'
 pp=H/'CORE-R112-per-polygon-immutable-owned-construction-r250/model.pkl';assert sha(pp)=='96d3f55a95b770a2a7f46e3b25274723946fe1572c6c82d81b7355b660360868'
 lp=H/'DIC-C1022-exact-R250-original-guard-construction-r262/incremental-original-fill-cut-ledger.json';assert sha(lp)=='9a2c5fbadea12bcd9c407237820f1699572b3e7d7af4fbe911a2348cf67ff599'
 dp=H/'DIC-native-owned-ledger-r212/receipt.json';assert sha(dp)=='9e63e595cbea54c90b4e340fbb68cfd5e920a25dee0ae4c40a94b6e555bfb543'
 sp=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sp)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
 source=sp.read_bytes();iv=K.C.inventory(source);g,h,b,q,c=pickle.loads(mp.read_bytes());pg,ph,pb,pq,pre=pickle.loads(pp.read_bytes());uid='55ab5777-4032-59ab-94d1-d5a4478c7a72';NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';assert uid not in iv[3]
 oldvia=next(v for v in h['vias']if v['uuid']==uid);assert (oldvia['net'],oldvia['x'],oldvia['y'],oldvia['d'],oldvia['drill'])==(NET,130.782294,90.235607,.5,.2)
 d=json.loads(dp.read_bytes());native_row=next(r for r in d['rows']if r['uuid']==uid);assert native_row['action']=='add';ch=Path(native_row['exact_chunk_path']).read_bytes();assert K.C.sha(ch)==native_row['exact_chunk_sha256'];parsed=K.A.G.parse(uid,ch,{});assert(parsed['net'],parsed['at'],parsed['d'],parsed['drill'])==(NET,[130.782294,90.235607],.5,.2)
 retired={};othercuts={};read={str(f.resolve()):sha(f)for f in(Path(__file__),mp,pp,lp,dp,sp,Path(native_row['exact_chunk_path']))}
 for row in json.loads(lp.read_bytes()):
  matches=[r for r in row['cutters']if r['new_UUID']==uid]
  if not matches:continue
  assert len(matches)==1;key=(row['zone_UUID'],row['layer']);rr=matches[0];cp=Path(rr['exact_cutter_file']);assert sha(cp)==rr['exact_outward_cutter_WKB_sha256'];retired[key]=(from_wkb(cp.read_bytes()),rr,row);read[str(cp.resolve())]=sha(cp);others=[]
  for r in row['cutters']:
   if r['new_UUID']==uid:continue
   cp=Path(r['exact_cutter_file']);assert sha(cp)==r['exact_outward_cutter_WKB_sha256'];others.append(from_wkb(cp.read_bytes()));read[str(cp.resolve())]=sha(cp)
  othercuts[key]=others
 assert retired and all(zid in iv[3]for zid,ly in retired),'No new/generated/native-unbound roles may be restored'
 byold={z['uuid']:z for z in pre['zones']};bycur={z['uuid']:z for z in c['zones']};hret={**h,'vias':[v for v in h['vias']if v['uuid']!=uid]};records,trees=K.F.build({**hret,'zones':[]});dom=h['domains_normalized'];gap=lambda a,n:.15 if dom[K.L.norm(a)]==dom[K.L.norm(n)]else .6;zones=copy.deepcopy(c['zones']);zby={z['uuid']:z for z in zones};ledger=[];fail=[];added=[]
 for (zid,ly),(mask,maskrow,oldledger)in sorted(retired.items()):
  z=zby[zid];pz=byold[zid];assert K.L.norm(z['net'])==K.L.norm(pz['net']);assert float(z['clearance_mm'])==float(pz['clearance_mm'])==float(oldledger['exact_native_or_owned_local_mm']);local=float(z['clearance_mm']);net=K.L.norm(z['net']);assert ly in z['fills']and ly in pz['fills'];oldrs=z['fills'][ly];parentrs=pz['fills'][ly];Pparts=K.L.poly(parentrs);assert len(Pparts)==len(parentrs);masks=list(othercuts[zid,ly]);barrier=[]
  for j in trees[ly].query(mask.buffer(1),predicate='intersects'):
   r=records[ly][int(j)]
   if K.L.norm(r['net'])==net:continue
   req=max(local,gap(net,r['net']))+.025;cut=K.Z.bounded_buffer(r['shape'],req)
   if cut.intersects(mask):masks.append(cut);barrier.append({'kind':'retained_current_native_effective_Cu','UUID':r['uuid'],'raw_net':r['net'],'layer':ly,'outward_mm':req,'mask_WKB_SHA256':K.C.sha(cut.wkb)})
  for v in hret['vias']:
   cut=K.Z.bounded_disk(v,v['drill']/2)
   if not cut.intersects(mask):continue
   masks.append(cut);barrier.append({'kind':'every_retained_physical_barrel_hole','UUID':v['uuid'],'mask_WKB_SHA256':K.C.sha(cut.wkb)})
  for p in hret['pads']:
   for sh in K.L.poly(p.get('hole')or[]):
    if sh.intersects(mask):masks.append(sh);barrier.append({'kind':'every_pad_hole','UUID':p['uuid'],'mask_WKB_SHA256':K.C.sha(sh.wkb)})
  for r in hret['rule_areas']:
   if ly in r['layers']and r.get('no_zones'):
    for sh in K.L.poly(r['outline']):
     cut=K.Z.bounded_buffer(sh,.025)
     if cut.intersects(mask):masks.append(cut);barrier.append({'kind':'native_no_zones','UUID':r['uuid'],'mask_WKB_SHA256':K.C.sha(cut.wkb)})
  # Every current foreign role and filled piece is retained as a hard
  # barrier; restoration cannot consume a later source-positive proposal.
  for oz in q:
   if oz['layer']!=ly or K.L.norm(oz['net'])==net or oz['shape'].distance(mask)>1:continue
   req=max(local,float(oz['clearance_mm']),gap(net,oz['net']))+.025;cut=K.Z.bounded_buffer(oz['shape'],req)
   if cut.intersects(mask):masks.append(cut);barrier.append({'kind':'later_current_owned_role','UUID':oz['uuid'],'role_WKB_SHA256':K.C.sha(oz['shape'].wkb),'mask_WKB_SHA256':K.C.sha(cut.wkb)})
  for oz in c['zones']:
   if K.L.norm(oz['net'])==net:continue
   for sh in K.L.poly(oz['fills'].get(ly,[])):
    if sh.distance(mask)>1:continue
    req=max(local,float(oz['clearance_mm']),gap(net,oz['net']))+.025;cut=K.Z.bounded_buffer(sh,req)
    if cut.intersects(mask):masks.append(cut);barrier.append({'kind':'later_current_foreign_actual_fill','UUID':oz['uuid'],'raw_net':oz['net'],'actual_fill_WKB_SHA256':K.C.sha(sh.wkb),'mask_WKB_SHA256':K.C.sha(cut.wkb)})
  allbarrier=unary_union(masks);fragments=[];rows=[]
  for i,Pshape in enumerate(Pparts):
   if not Pshape.intersects(mask):continue
   assert set_precision(Pshape,0).wkb==Pshape.wkb;sh=Pshape.intersection(mask).difference(allbarrier);raw=sh;reserves=[]
   # Strict literal containment. If GEOS serialization creates any literal
   # gain, withdraw only the newly restored fragment around that witness.
   for it in range(16):
    rs=IM.records(sh);actual=unary_union(K.L.poly(rs));bad=unary_union([actual.difference(Pshape),actual.difference(mask),actual.intersection(allbarrier)])
    if bad.is_empty:break
    fp=out/(zid+'-'+ly+'-'+str(i)+'-'+str(it)+'-literal-fragment-bound-FAIL.wkb');fp.write_bytes(bad.wkb);reserve=K.Z.bounded_buffer(bad,.0001);rp=out/(zid+'-'+ly+'-'+str(i)+'-'+str(it)+'-explicit-fragment-only-100nm-negative.wkb');rp.write_bytes(reserve.wkb);sh=actual.difference(reserve).intersection(Pshape).intersection(mask).difference(allbarrier);reserves.append({'raw_FAIL_file':str(fp.resolve()),'raw_FAIL_WKB_SHA256':K.C.sha(bad.wkb),'only_new_fragment_negative_file':str(rp.resolve()),'negative_WKB_SHA256':K.C.sha(reserve.wkb),'literal_gains_or_barrier_contacts_NOT_waived':True})
   rs=IM.records(sh);actual=unary_union(K.L.poly(rs));bad=unary_union([actual.difference(Pshape),actual.difference(mask),actual.intersection(allbarrier)])
   row={'exact_pre_DIC_record':i,'parent_array_SHA256':K.C.sha(json.dumps(parentrs[i],separators=(',',':')).encode()),'parent_physical_WKB_SHA256':K.C.sha(Pshape.wkb),'exact_retired_cutter_WKB_SHA256':K.C.sha(mask.wkb),'raw_bound_restore':info(raw),'actual_fragment':info(actual),'literal_bound_failure':info(bad),'explicit_new_fragment_negative_reserves':reserves}
   rows.append(row)
   if not bad.is_empty:fail.append({'zone_UUID':zid,'layer':ly,**row});continue
   for rr in rs:fragments.append(rr)
   af=out/(zid+'-'+ly+'-'+str(i)+'-exact-bound-restored-fragment.wkb');af.write_bytes(actual.wkb);row['actual_fragment_file']=str(af.resolve());added.append((net,ly,actual))
  z['fills'][ly]=oldrs+fragments;assert z['fills'][ly][:len(oldrs)]==bycur[zid]['fills'][ly];ledger.append({'zone_UUID':zid,'layer':ly,'raw_net':z['net'],'only_retired_NEW_UUID':uid,'native_zone_original_chunk_SHA256':K.C.sha(iv[3][zid]),'pre_DIC_source_record_parent_SHA256':sha(pp),'current_all_filled_arrays_exact_prefix_preserved':True,'exact_current_array_count':len(oldrs),'explicit_new_fragment_count':len(fragments),'exact_owned_retired_cutter':maskrow,'retained_other_owned_cut_count':len(othercuts[zid,ly]),'current_Cu_hole_rule_foreign_fill_barriers':barrier,'per_exact_pre_DIC_primitive_restoration':rows})
  print('R552_LOCAL_REPLAY',zid,ly,'fragments',len(fragments),'boundfail',len(fail),flush=True)
 for old,new in zip(c['zones'],zones):
  assert old['uuid']==new['uuid'];assert {k:v for k,v in old.items()if k!='fills'}=={k:v for k,v in new.items()if k!='fills'}
  for ly,rs in old['fills'].items():
   if(old['uuid'],ly)not in retired:assert new['fills'][ly]==rs
   else:assert new['fills'][ly][:len(rs)]==rs
 candidate={**c,'vias':hret['vias'],'zones':zones};put(out/'exact-retirement-and-local-source-restoration-ledger.json',ledger);put(out/'raw-literal-bound-failures.json',fail)
 if fail:put(out/'receipt.json',{'verdict':'EXACT_RETIRED_NEW_DIC_CUTTER_SOURCE_REPLAY_LITERAL_BOUND_FAIL_PRESERVED','failures':fail,'input_SHA256':read,'native_jobs':0,'adopted':False});return
 # Verify actual finite connection of each restored LOGIC fragment to J1;
 # the graph is rebuilt after all actual retained holes, not plane-by-name.
 _,lg=K.physical(candidate,'/LOGIC_GND',K.hole_context(candidate));r=K.root(lg,'J11001','2');rootkeys=K.keys(r);bf=H/'Q0-R526-full-current-contacts-source-reference-r528/actual-before-and-after-source-banks.pkl';assert sha(bf)=='9b48079a0eb2b1a592dca1fc195ffe70b350e9ff9a110f069178a9f207db0a17';before=pickle.loads(bf.read_bytes())['after']['/LOGIC_GND'];lost=sorted(K.keys(before)-rootkeys);sourcefills={ly:unary_union([x['shape']for x in r if x['kind']=='fill'and x['layer']==ly])for ly in K.LAYERS};restoration=[]
 for net,ly,sh in added:
  if net!='/LOGIC_GND':continue
  missing=sh.difference(sourcefills[ly]);restoration.append({'layer':ly,'exact_fragment':info(sh),'actual_J1_source_not_connected':info(missing),'root_fragment_member_or_union':'Actual physical drilled graph; no generic neighboring plane credit'})
 model=out/'exact-retired-NEW55ab-only-cache-restoration-INTERMEDIATE_NOT_ADOPTED.pkl';model.write_bytes(pickle.dumps((g,hret,b,q,candidate),protocol=5));gp=out/'actual-J1-source-groups-after-only-owned-retirement-replay.pkl';gp.write_bytes(pickle.dumps(lg,protocol=5));put(out/'actual-J1-key-and-restored-fragment-source-proof.json',{'lost_prior_keys':[list(k)for k in lost],'restored_fragments':restoration});read[str(bf.resolve())]=sha(bf)
 rec={'verdict':'EXACT_RETIRED_NEW_DIC55ab_SOURCE_PRIMITIVE_LOCAL_CACHE_REPLAY_CONSTRUCTIVE_FULL_GATES_OPEN','original_native_eedf_UID_absent':uid not in iv[3],'retired_only_unaccepted_NEW_UID':uid,'exact_NEW55ab_native_recipe_chunk_SHA256':K.C.sha(ch),'exact_retired_cut_family_count':len(retired),'all_current_native_filled_arrays_and_every_far_record_preserved_exact':True,'source_cache_additions_only_inside_exact_retired_owned_cutter_AND_exact_pre_DIC_primitives':True,'all_CURRENT_g_b_q_physical_intended_native_profiles_FP_otherCu_unchanged':True,'current_h_ONLY_retired_NEW55ab_via_temporarily_absent':True,'actual_J1_source_keys_lost':[list(k)for k in lost],'actual_restored_fragment_source_rows':restoration,'native_fill_min_feature_all_3_pairs_lock_contact_source_reference_current':'OPEN; intermediate retirement/replay, no finished DIC claim','new_DIC_own_scope_generic_disk_or_plane_credit':False,'native_jobs':0,'adopted':False,'source_board_project_written':False,'model_file':str(model.resolve()),'model_SHA256':sha(model),'actual_J1_groups_file':str(gp.resolve()),'actual_J1_groups_SHA256':sha(gp),'input_SHA256':read,'output_SHA256':{str(f.resolve()):sha(f)for f in out.iterdir()if f.is_file()},'elapsed_seconds':time.monotonic()-st};put(out/'receipt.json',rec);print('R552_COMPLETE',sha(out/'receipt.json'),rec['model_SHA256'],'J1oldkeyloss',len(lost),flush=True)
if __name__=='__main__':main()
