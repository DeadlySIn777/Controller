"""Exact regulated search base on the latest joint CORE/protected checkpoint.

Own R41 candidates are revised explicitly. No original native item is
withdrawn, and protected/CORE contact qualification stays with its owner.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy,sys,hashlib
from pathlib import Path
from shapely import set_precision,from_wkb
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
from regulated_outer_joins_r51 import PORTS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'regulated-final-power-search-base-r70'
WITHDRAW={
 'aeb2c3c8-5214-5918-86bf-b4db2cd59377':('11a7cc38-5c1a-572d-88d1-5f9a9f9f4f6b','U11014','3','72f55b8d-c877-5bb9-9067-cd5efeab0772'),
 '123d0875-7228-5ee5-9a07-ae0ef5b69b53':('851a5cd5-ac72-59c7-aa54-4afc35fb1098','R11058','1','4203c48e-c268-56c2-94c6-6c4f3d133829'),
 '0cae08f1-3783-5a82-959f-9d8c9cae6f0e':('116ed1e7-2940-5f18-961d-4436b602ec01','R14065','1','ba9ee402-5755-5e5a-bee5-b018c7a98be6'),
}
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def itemsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir()
 sp=ROOT/'sbc-power/core-protected-outward-joint-r59/model.pkl'
 assert sha(sp)=='a77ba8a283d9b1e856ec6e4627363f9ba413e9db5c5af4c5fa1b8e3c41c32682'
 g,h,binding,zones,candidate=pickle.loads(sp.read_bytes());assert candidate is not None
 rp=HERE/'regulated-field-source-feeds-r41';rr=json.loads((rp/'receipt.json').read_text())
 assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'];assert sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256']
 originald=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());owned=pickle.loads((rp/'proposed-zones.pkl').read_bytes())
 vi={v['uuid']:v for v in originald['vias']};tr={t['uuid']:t for t in originald['tracks']};withdraw=[]
 for uid,(tid,ref,pin,wall) in WITHDRAW.items():
  assert uid in vi and tid in tr
  assert uid not in {v['uuid'] for v in h['vias']} and tid not in {t['uuid'] for t in h['tracks']}
  pads=[q for q in h['pads'] if q['ref']==ref and q['num']==pin]
  assert pads
  withdraw.append({'prospective_via':vi[uid],'prospective_via_metadata_sha256':itemsha(vi[uid]),'prospective_stub':tr[tid],'prospective_stub_metadata_sha256':itemsha(tr[tid]),'retained_target_native_pads':[{'uuid':q['uuid'],'ref':q['ref'],'pin':q['num'],'raw_net':q['net']} for q in pads],'foreign_protected_plane_uuid':wall,'native_items_removed':0,'target_source_feed_still_required':True})
 d={'vias':[v for v in originald['vias'] if v['uuid'] not in WITHDRAW],'tracks':[t for t in originald['tracks'] if t['uuid'] not in {r[0] for r in WITHDRAW.values()}]}
 assert len(d['vias'])==17 and len(d['tracks'])==17
 assert not({q['uuid'] for q in d['vias']} & {q['uuid'] for q in h['vias']})
 assert not({q['uuid'] for q in d['tracks']} & {q['uuid'] for q in h['tracks']})
 h={**h,'vias':h['vias']+d['vias'],'tracks':h['tracks']+d['tracks']}
 pp=ROOT/'protected24-on-corrected-core-r9/proposed-zones.pkl';assert sha(pp)=='e88d9750d99e46cb875925a338e4901e5085f5cf84a239d459d01053d57aeb16'
 rootq=pickle.loads(pp.read_bytes());assert len(rootq)==10
 assert {q['uuid'] for q in rootq}<={q['uuid'] for q in zones}
 mp=ROOT/'coupled-recovery/c10036-peer-reference-mask-r26.wkb';assert sha(mp)=='c15b7bc932faf123137a73c2a7ea3020e78da2e6aca94fba8cd72f5ef51e5b55'
 cp=ROOT/'coupled-recovery/c10036-reference-bridge-r24.wkb';assert sha(cp)=='ac0c4fe08eb087e21da02ac85fc71b1212fc1ee3cad4c3864976a179c3ace65e'
 referencecut=P.bounded_buffer(unary_union([from_wkb(mp.read_bytes()),from_wkb(cp.read_bytes())]),.275)
 (OUT/'C10036_full_reference_cutter.wkb').write_bytes(referencecut.wkb)
 rec,trees=F.build({**h,'zones':[]});updated=[];ledger=[]
 for z in owned:
  before=z['shape'];outline=z.get('zone_outline_shape',before);domain=h['domains_normalized'][C.norm(z['net'])];cuts=[];rows=[]
  for i in trees[z['layer']].query(outline.buffer(.627),predicate='intersects'):
   q=rec[z['layer']][int(i)]
   if q['net']==z['net']:continue
   req=(.15 if q['domain']==domain else .6)+.025;cut=P.bounded_buffer(q['shape'],req);cuts.append(cut);rows.append({'kind':q['kind'],'uuid':q['uuid'],'raw_net':q['net'],'required_mm':req,'cutter_sha256':P.digest(cut)})
  for q in zones+owned:
   if q['layer']!=z['layer'] or q['net']==z['net'] or q['shape'].distance(outline)>.627:continue
   req=max(.15 if h['domains_normalized'].get(C.norm(q['net']))==domain else .6,float(q.get('clearance_mm',.15)),float(z.get('clearance_mm',.15)))+.025
   cut=P.bounded_buffer(q['shape'],req);cuts.append(cut);rows.append({'kind':'proposal','uuid':q['uuid'],'raw_net':q['net'],'required_mm':req,'cutter_sha256':P.digest(cut)})
  if z['uuid']=='630264b1-3d8f-5604-aedd-209dc0a5eaa3':cuts.append(referencecut);rows.append({'kind':'C10036_all_retained_B_power_reference_and_checked_return','required_mm':.275,'cutter_sha256':P.digest(referencecut)})
  cutter=unary_union(cuts);body=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);native=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6)
  updated.append({**z,'shape':body,'zone_outline_shape':native,'R70_latest_CORE_protected_and_C10036_correction':True})
  removed=OUT/(z['uuid']+'.removed.wkb');added=OUT/(z['uuid']+'.quantization-added.wkb');removed.write_bytes(before.difference(body).wkb);added.write_bytes(body.difference(before).wkb)
  ledger.append({'uuid':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'original_R41_physical_sha256':P.digest(before),'corrected_physical_sha256':P.digest(body),'original_R41_intended_sha256':P.digest(outline),'corrected_intended_sha256':P.digest(native),'removed_area_mm2':before.difference(body).area,'positive_quantization_area_mm2':body.difference(before).area,'removed_file_sha256':sha(removed),'positive_delta_sha256':sha(added),'cutters':rows})
 zones,guards=P.normalize_owned_via_guards(h,zones+updated);ids={q['uuid'] for q in updated};updated=[q for q in zones if q['uuid'] in ids]
 binding=copy.deepcopy(binding);binding['field_regulated_search_hard_nominees']={'already_composed':True,'discrete':{'vias':[],'tracks':[]},'planes':[],'protected_final10_source_file_sha256':sha(pp),'protected_objects_present_in_h_and_zones':True,'not_source_contact_or_current_credit':True}
 print('project exact joint R59 plus regulated17/17/18',len(zones),flush=True)
 after,retreats=P.projected(g,h,zones);groups={};census=[]
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs))
  census.append({'bank':bank,'net':net,'actual_source':ref+'.'+pin,'source_group':ri,'remaining':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]});write(OUT/'source-census-checkpoint.json',census);print(bank,'remaining',len(census[-1]['remaining']),flush=True)
 (OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(updated,protocol=5));(OUT/'retained-regulated-discrete.pkl').write_bytes(pickle.dumps(d,protocol=5));(OUT/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 write(OUT/'proposal-withdrawal-ledger.json',withdraw);write(OUT/'shape-delta-ledger.json',ledger);write(OUT/'owned-via-guard-ledger.json',guards);write(OUT/'oldfill-retreat-ledger.json',retreats)
 write(OUT/'receipt.json',{'verdict':'FROZEN_ACTUAL_JOINT_POWER_REGULATED_SEARCH_BASE_COMPLETION_GATES_OPEN','model_sha256':sha(OUT/'model.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'retained_regulated_discrete_sha256':sha(OUT/'retained-regulated-discrete.pkl'),'source_groups_sha256':sha(OUT/'source-groups.pkl'),'source_census':census,'SBC_joint_R59_model_sha256':sha(sp),'SBC_joint_R59_receipt_sha256':sha(sp.parent/'receipt.json'),'original_R41_discrete_sha256':sha(rp/'proposed-discrete.pkl'),'original_R41_planes_sha256':sha(rp/'proposed-zones.pkl'),'protected_final10_sha256':sha(pp),'proposal_withdrawal_ledger_sha256':sha(OUT/'proposal-withdrawal-ledger.json'),'withdrawn_prospective_vias':3,'withdrawn_prospective_stubs':3,'retained_regulated_vias':17,'retained_regulated_stubs':17,'native_items_removed_by_this_composer':0,'owned_regulated_planes':18,'shape_delta_ledger_sha256':sha(OUT/'shape-delta-ledger.json'),'owned_via_ledger_sha256':sha(OUT/'owned-via-guard-ledger.json'),'oldfill_ledger_sha256':sha(OUT/'oldfill-retreat-ledger.json'),'C10036_peer_mask_sha256':sha(mp),'C10036_reference_bridge_sha256':sha(cp),'C10036_reference_cutter_sha256':sha(OUT/'C10036_full_reference_cutter.wkb'),'original_zone_definitions_untouched':True,'protected_CORE_objects_present_in_h_zones_and_projected_after':True,'protected_CORE_source_current_no_loss_claim_by_this_composer':False,'native_jobs':0,'board_written':False,'full_joint_source_no_loss_current_native_refill_and_flash_gates':'OPEN'})
 print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
