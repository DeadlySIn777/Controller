"""Frozen regulated search base with current CORE and C10036 return mask.

Protected positive nominees are search obstacles only. Their parent retains
their actual return-carve/source/current ownership and final integration.
"""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy,sys
from pathlib import Path
from shapely import set_precision,from_wkb
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
from regulated_outer_joins_r51 import PORTS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'regulated-peer-reference-protected-base-r62'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();sp=ROOT/'sbc-power/remaining-core-accepted-checkpoints-r50/stage-3/accepted-checkpoint-model.pkl';assert sha(sp)=='d5d6efcb8ead02132103e4eb5ad33b363c8d08eed61aa5dfb5ff2d2e1df79aea';g,h,binding,zones,_=pickle.loads(sp.read_bytes())
 rp=HERE/'regulated-field-source-feeds-r41';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'];d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());h={**h,'vias':h['vias']+d['vias'],'tracks':h['tracks']+d['tracks']}
 bp=HERE/'regulated-guarded-composition-r60';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'proposed-zones.pkl')==br['proposed_zones_sha256'];owned=pickle.loads((bp/'proposed-zones.pkl').read_bytes());rec,trees=F.build({**h,'zones':[]})
 pp=ROOT/'protected24-r9-accepted-positive-snapshot-r1';pr=json.loads((pp/'receipt.json').read_text());assert sha(pp/'proposed-zones.pkl')==pr['proposed_zones_sha256'];hardq=pickle.loads((pp/'proposed-zones.pkl').read_bytes());dp=ROOT/'protected24-dogbones-r7/proposed-discrete.pkl';assert sha(dp)=='005a19f7e01d9208f01e2677eefb3de9c2d34994037fd97e3f78340b6ff82a8c';hardd=pickle.loads(dp.read_bytes());assert len(hardq)==7
 maskp=ROOT/'coupled-recovery/c10036-peer-reference-mask-r26.wkb';assert sha(maskp)=='c15b7bc932faf123137a73c2a7ea3020e78da2e6aca94fba8cd72f5ef51e5b55';bridgep=ROOT/'coupled-recovery/c10036-reference-bridge-r24.wkb';assert sha(bridgep)=='ac0c4fe08eb087e21da02ac85fc71b1212fc1ee3cad4c3864976a179c3ace65e';reference=unary_union([from_wkb(maskp.read_bytes()),from_wkb(bridgep.read_bytes())]);referencecut=P.bounded_buffer(reference,.275);(OUT/'C10036_full_reference_cutter.wkb').write_bytes(referencecut.wkb);ledger=[];updated=[]
 hardh={**h,'tracks':h['tracks']+hardd['tracks'],'vias':h['vias']+hardd['vias']};hardrec,hardtrees=F.build({**hardh,'zones':[]})
 for z in owned:
  before=z['shape'];outline=z.get('zone_outline_shape',before);domain=h['domains_normalized'][C.norm(z['net'])];cuts=[];cutrows=[]
  for i in hardtrees[z['layer']].query(outline.buffer(.627),predicate='intersects'):
   q=hardrec[z['layer']][int(i)]
   if q['net']==z['net']:continue
   req=(.15 if q['domain']==domain else .6)+.025;cut=P.bounded_buffer(q['shape'],req);cuts.append(cut);cutrows.append({'kind':q['kind'],'uuid':q['uuid'],'raw_net':q['net'],'required_mm':req,'cutter_sha256':P.digest(cut)})
  for q in zones+owned+hardq:
   if q['layer']!=z['layer'] or q['net']==z['net'] or q['shape'].distance(outline)>.627:continue
   req=(.15 if h['domains_normalized'].get(C.norm(q['net']))==domain else .6)+.025;cut=P.bounded_buffer(q['shape'],req);cuts.append(cut);cutrows.append({'kind':'proposal','uuid':q['uuid'],'raw_net':q['net'],'required_mm':req,'cutter_sha256':P.digest(cut)})
  if z['uuid']=='630264b1-3d8f-5604-aedd-209dc0a5eaa3':cuts.append(referencecut);cutrows.append({'kind':'C10036_all_retained_B_power_reference_and_new_return_bridge','required_mm':.275,'cutter_sha256':P.digest(referencecut)})
  cutter=unary_union(cuts);body=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);newoutline=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6);updated.append({**z,'shape':body,'zone_outline_shape':newoutline,'R62_peer_reference_and_frozen_power_nominee_correction':True});rf=OUT/(z['uuid']+'.removed.wkb');af=OUT/(z['uuid']+'.quantization-added.wkb');rf.write_bytes(before.difference(body).wkb);af.write_bytes(body.difference(before).wkb);ledger.append({'uuid':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'before_physical_sha256':P.digest(before),'after_physical_sha256':P.digest(body),'before_intended_sha256':P.digest(outline),'after_intended_sha256':P.digest(newoutline),'removed_area_mm2':before.difference(body).area,'positive_quantization_area_mm2':body.difference(before).area,'removed_file_sha256':sha(rf),'positive_delta_file_sha256':sha(af),'cutters':cutrows})
 zones,guards=P.normalize_owned_via_guards(h,zones+updated);ids={q['uuid'] for q in updated};updated=[q for q in zones if q['uuid'] in ids];binding=copy.deepcopy(binding);binding['field_regulated_search_hard_nominees']={'discrete':hardd,'planes':hardq,'protected_nominee_discrete_sha256':sha(dp),'protected_nominee_plane_sha256':sha(pp/'proposed-zones.pkl'),'protected_nominee_receipt_sha256':sha(pp/'receipt.json'),'not_source_contact_or_current_credit':True};print('project R62 current CORE/reg + C10036 reference mask',len(zones),flush=True);after,retreats=P.projected(g,h,zones);groups={};census=[]
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));row={'bank':bank,'net':net,'actual_source':ref+'.'+pin,'source_group':ri,'remaining':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]};census.append(row);write(OUT/'source-census-checkpoint.json',census);print(bank,'remaining',len(row['remaining']),flush=True)
 (OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(updated,protocol=5));(OUT/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));write(OUT/'shape-delta-ledger.json',ledger);write(OUT/'owned-via-guard-ledger.json',guards);write(OUT/'oldfill-retreat-ledger.json',retreats)
 receipt={'verdict':'FROZEN_REGULATED_SEARCH_BASE_SOURCE_REPAIR_AND_FULL_CONTACT_PENDING','model_sha256':sha(OUT/'model.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'source_groups_sha256':sha(OUT/'source-groups.pkl'),'source_census':census,'parent_R60_receipt_sha256':sha(bp/'receipt.json'),'SBC_stage3_model_sha256':sha(sp),'protected7_hard_nominee_plane_sha256':sha(pp/'proposed-zones.pkl'),'protected12via12stub_hard_nominee_sha256':sha(dp),'C10036_peer_mask_sha256':sha(maskp),'C10036_reference_bridge_sha256':sha(bridgep),'shape_delta_ledger_sha256':sha(OUT/'shape-delta-ledger.json'),'reference_cutter_sha256':sha(OUT/'C10036_full_reference_cutter.wkb'),'owned_via_ledger_sha256':sha(OUT/'owned-via-guard-ledger.json'),'oldfill_ledger_sha256':sha(OUT/'oldfill-retreat-ledger.json'),'original_definitions_untouched':True,'protected_objects_hard_search_only_not_composed_into_contact_candidate':True,'later_SBC_stage4plus_and_remaining_protected_replacements':'OPEN_MUTUAL_REBASE','native_jobs':0,'board_written':False,'ground_source_current_native_min_thickness_flash_reference_mutual_gates':'OPEN'};write(OUT/'receipt.json',receipt);print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
