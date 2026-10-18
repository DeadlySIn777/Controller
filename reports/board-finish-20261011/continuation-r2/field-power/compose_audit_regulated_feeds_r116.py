"""Fresh source/retained-contact/reference audit of the completed R114 pass."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import STRtree
import contact_layout as C
import fast_contacts as F
from inventory import sha
from regulated_outer_joins_r51 import PORTS
from audit_field_io3_crossings_r15e import losses
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT/'sbc-power'));sys.path.insert(0,str(ROOT/'coupled-recovery'))
import guarded_power_projection_r44 as P
import owned_analytic_track_guards_r75 as TG
import physical_reference_losses_r1 as REF
O=H/'regulated-source-contact-reference-audit-r116'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();bp=H/'corrected-regulated-native-bound-search-base-r111';assert sha(bp/'model.pkl')=='722fae195cecfcfa07729dd243c2d74a0a0088e672582363265a2c15553db4d8';g,h,b,z,prior=pickle.loads((bp/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z)
 rp=H/'regulated-quantized-inner-source-feeds-r114';assert sha(rp/'receipt.json')=='15b86661ee65d1961e865caea2862346757c7a9ff70aa47101b6d62cf9812eef';r=json.loads((rp/'receipt.json').read_text());d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());newq=pickle.loads((rp/'proposed-zones.pkl').read_bytes());up=pickle.loads((rp/'owned-new-return-updates.pkl').read_bytes());assert sha(rp/'proposed-discrete.pkl')==r['proposed_discrete_sha256'] and sha(rp/'proposed-zones.pkl')==r['proposed_zones_sha256'] and sha(rp/'owned-new-return-updates.pkl')==r['owned_return_updates_sha256']
 current={q['uuid']:q for q in z};update={q['uuid']:q for q in up};assert set(update)<=set(current)
 for uid,q in update.items():
  steps=[x for x in r['owned_return_carves'] if x['owned_new_return_uuid']==uid];assert P.digest(current[uid]['shape'])==steps[0]['physical_before_sha256'] and P.digest(q['shape'])==steps[-1]['physical_after_sha256'];assert current[uid]['net']==q['net'] and current[uid]['layer']==q['layer']
 z=[update.get(q['uuid'],q) for q in z]
 for k in ('tracks','vias'):
  assert not {q['uuid'] for q in d[k]}&{q['uuid'] for q in h[k]};h[k]+=d[k]
 newq,vg=P.normalize_owned_via_guards(h,newq);newq,tg,geom=TG.normalize_owned_track_guards(h,newq);z+=newq
 for uid,shapes in geom.items():
  for kind,sh in shapes.items():(O/(uid+'.'+kind+'.wkb')).write_bytes(sh.wkb)
 b['regulated_R114_actual_owned_delta']={'receipt_file':str((rp/'receipt.json').resolve()),'receipt_sha256':sha(rp/'receipt.json'),'new_zone_UUIDs':[q['uuid'] for q in newq],'new_via_UUIDs':[q['uuid'] for q in d['vias']],'new_track_UUIDs':[q['uuid'] for q in d['tracks']],'requires_final_source_reference_current_native_gates':True}
 print('R116 full guarded projection',len(z),'zones',len(d['vias']),'new vias',flush=True);after,oldfill=P.projected(g,h,z);groups={};rows=[]
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));old=pickle.loads((bp/'source-groups.pkl').read_bytes())[net];bad=losses(old,gs);remaining=[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)];rows.append({'bank':bank,'net':net,'source':ref+'.'+pin,'source_group':ri,'all_named_pads_rooted':not remaining,'unrooted_named_groups':remaining,'R111_old_contact_losses':bad,'actual_owned_target_source_membership':[{ 'bridge_uuid':x['source_bridge_uuid'],'all_target_pads_source_rooted':all(a['uuid'] in {q['uuid'] for q in gs[ri] if q['kind']=='pad'} for a in x['pads'])} for x in r['rows'] if x['bank']==bank]});print(bank,'unrooted',len(remaining),'old losses',len(bad),flush=True);write(O/'checkpoint.json',rows)
 # Chosen-layer-only ordinary barrel stress graph cannot gain a source path
 # from an unverified flash on another inner layer.
 required={x['new_via_uuid']:[x['stub_layer'],x['source_bridge_layer']] for x in r['rows'] if x['new_via_uuid']};minimal={**after,'vias':[{**q,'flashed':required[q['uuid']]} if q['uuid'] in required else q for q in after['vias']]};minimalrows=[]
 for bank,net,ref,pin,policy in PORTS:
  if not any(C.norm(v['net'])==net for v in d['vias']):continue
  gs=F.graph(minimal,net);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));minimalrows.append({'net':net,'source':ref+'.'+pin,'all_new_chosen_layer_only_vias_rooted':all(any(q['uuid']==v['uuid'] for q in gs[ri]) for v in d['vias'] if C.norm(v['net'])==net),'explicit_minimal_required_native_flashes':{v['uuid']:required[v['uuid']] for v in d['vias'] if C.norm(v['net'])==net}})
 grounds=[];refs=[]
 for net,ref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/LOGIC_GND','J11001')]:
  print('R116 ground graph',net,flush=True);old=F.graph(prior,net);new=F.graph(after,net);groups[net]=new;oi=next(i for i,xs in enumerate(old) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));ni=next(i for i,xs in enumerate(new) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));bad=losses(old,new);rootlost=sorted(F.discrete_keys(old[oi])-F.discrete_keys(new[ni]));grounds.append({'net':net,'source':ref+'.2','old_R111_contact_losses':bad,'prior_source_keys_lost':[list(x) for x in rootlost],'rooted_named_physical_pad_count':len({q['uuid'] for q in new[ni] if q['kind']=='pad' and q['pin']})});print(net,'loss groups',len(bad),'prior source keys lost',len(rootlost),flush=True)
  oldrefs={outer:unary_union([q['shape'] for q in old[oi] if q['layer']==inner and q['kind']=='fill']) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newrefs={outer:unary_union([q['shape'] for q in new[ni] if q['layer']==inner and q['kind']=='fill']) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};loss,diag=REF.audit(prior,oldrefs,newrefs,net);refs.append({'ground_net':net,'source':ref+'.2','retained_outer_track_reference_losses':loss,'exact_accelerated_reference_proof':diag});print(net,'retained outer reference losses',len(loss),flush=True)
  write(O/'ground-contact-checkpoint.json',grounds);write(O/'reference-checkpoint.json',refs)
 write(O/'source-rows.json',rows);write(O/'minimal-barrel-source-rows.json',minimalrows);write(O/'ground-contacts.json',grounds);write(O/'reference-losses.json',refs);write(O/'new-via-guard-corrections.json',vg);write(O/'new-track-guard-corrections.json',tg);write(O/'oldfill-retreats.json',oldfill);(O/'proposed-zones.pkl').write_bytes(pickle.dumps(newq,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 write(O/'receipt.json',{'verdict':'CONSTRUCTED_SOURCE_AND_SCOPE_PASS_PENDING_REMAINING_LOADS_AND_FULL_MUTUAL_NATIVE_CURRENT' if all(not q['R111_old_contact_losses'] for q in rows) and all(not q['old_R111_contact_losses'] and not q['prior_source_keys_lost'] for q in grounds) and all(not q['retained_outer_track_reference_losses'] for q in refs) and all(q['all_new_chosen_layer_only_vias_rooted'] for q in minimalrows) else 'JOINT_OLD_CONTACT_REFERENCE_REPAIR_REQUIRED','model_sha256':sha(O/'model.pkl'),'input_R111_model_sha256':sha(bp/'model.pkl'),'R114_delta_receipt_sha256':sha(rp/'receipt.json'),'new_owned_guarded_zone_sha256':sha(O/'proposed-zones.pkl'),'source_rows_sha256':sha(O/'source-rows.json'),'minimal_barrel_source_sha256':sha(O/'minimal-barrel-source-rows.json'),'ground_contacts_sha256':sha(O/'ground-contacts.json'),'reference_losses_sha256':sha(O/'reference-losses.json'),'group_cache_sha256':sha(O/'groups.pkl'),'new_owned_via_guard_sha256':sha(O/'new-via-guard-corrections.json'),'new_owned_track_guard_sha256':sha(O/'new-track-guard-corrections.json'),'oldfill_retreat_sha256':sha(O/'oldfill-retreats.json'),'original198b_dc936_full_retention_vs_R111_scoped_receipt':'SEPARATE_MANDATORY_GATE','all_analytic_raw_domain_aperture_mutual_current_barrel_native_FLASH_DRC_gates':'OPEN','board_written':False,'native_jobs':0});print('R116 frozen',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
