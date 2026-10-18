"""Fresh complete scoped audit for only the two reference-safe replacements."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
from regulated_outer_joins_r51 import PORTS
from audit_field_io3_crossings_r15e import losses
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'));sys.path.insert(0,str(H.parent/'coupled-recovery'))
import guarded_power_projection_r44 as P
import owned_analytic_track_guards_r75 as TG
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
O=H/'reference-safe-regulated-source-contact-audit-r129'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'regulated-indexed-reference-wall-repair-base-r123';br=json.loads((base/'receipt.json').read_text());assert sha(base/'model.pkl')==br['model_sha256'];g,h,b,z,prior=pickle.loads((base/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z);rp=H/'regulated-reference-safe-source-replacements-r121';r=json.loads((rp/'receipt.json').read_text());assert sha(rp/'receipt.json')=='3b4f9bffa0676e13418d3f90ee341fb7859dce47c47ee5979b7beac4d0305bdc';newq=pickle.loads((rp/'proposed-zones.pkl').read_bytes());up=pickle.loads((rp/'owned-new-return-updates.pkl').read_bytes());d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());assert not d['vias'] and not d['tracks'];current={q['uuid']:q for q in z};updates={q['uuid']:q for q in up};assert set(updates)=={'ded2b949-0c87-5603-874b-a41f2f152e69'}
 for uid,q in updates.items():
  step=next(x for x in r['owned_return_carves'] if x['owned_new_return_uuid']==uid);assert P.digest(current[uid]['shape'])==step['physical_before_sha256'] and P.digest(q['shape'])==step['physical_after_sha256']
 z=[updates.get(q['uuid'],q) for q in z];newq,vg=P.normalize_owned_via_guards(h,newq);newq,tg,geoms=TG.normalize_owned_track_guards(h,newq)
 for uid,shapes in geoms.items():
  for kind,sh in shapes.items():(O/(uid+'.'+kind+'.wkb')).write_bytes(sh.wkb)
 z+=newq;print('R129 full guarded projection',len(z),flush=True);after,oldfill=P.projected(g,h,z);rec,trees=F.build({**h,'zones':[]});tmap={q['uuid']:q for q in h['tracks']};vmap={q['uuid']:q for q in h['vias']};checks=[];errors=[]
 for q in newq:
  l=q['layer'];sh=q['shape']
  for j in trees[l].query(sh.buffer(.627),predicate='intersects'):
   a=rec[l][int(j)]
   if C.norm(a['net'])==C.norm(q['net']):continue
   req=max(G.gap(h,q['net'],a['net']),float(q.get('clearance_mm',.15)))+.025;gap=sh.distance(a['shape'])
   if a['kind']=='via':v=vmap[a['uuid']];gap=sh.distance(Point(v['x'],v['y']))-v['d']/2
   if a['kind']=='track':t=tmap[a['uuid']];gap=sh.distance(LineString([t['a'],t['b']]))-t['w']/2
   row={'plane':q['uuid'],'item':a['uuid'],'kind':a['kind'],'layer':l,'required_mm':req,'actual_analytic_gap_mm':gap};checks.append(row)
   if gap+1e-10<req:errors.append(row)
  for peer in z:
   if peer['uuid']==q['uuid'] or peer['layer']!=l or C.norm(peer['net'])==C.norm(q['net']):continue
   req=max(G.gap(h,q['net'],peer['net']),float(q.get('clearance_mm',.15)),float(peer.get('clearance_mm',.15)))+.025;gap=sh.distance(peer['shape'])
   if gap<req+.01:
    row={'plane':q['uuid'],'item':peer['uuid'],'kind':'proposal','layer':l,'required_mm':req,'actual_analytic_gap_mm':gap};checks.append(row)
    if gap+1e-10<req:errors.append(row)
 write(O/'analytic-checks.json',checks);write(O/'analytic-errors.json',errors);print('R129 analytic',len(checks),'errors',len(errors),flush=True)
 oldbp=H/'corrected-regulated-native-bound-search-base-r111';oldreg=pickle.loads((oldbp/'source-groups.pkl').read_bytes());oldgrounds=pickle.loads((H/'regulated-reference-contact-diagnostic-r119/old-ground-groups.pkl').read_bytes());source=[];ground=[];refs=[];groups={}
 for bank,net,ref,pin,policy in PORTS:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));root={q['uuid'] for q in gs[ri] if q['kind']=='pad'};unroot=[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)];bad=losses(oldreg[net],gs);row={'bank':bank,'net':net,'source':ref+'.'+pin,'all_named_source_rooted':not unroot,'unrooted_named_groups':unroot,'R111_old_contact_losses':bad,'two_R121_target_memberships':[{'UUID':x['source_bridge_uuid'],'all_target_pads_rooted':all(p['uuid'] in root for p in x['pads'])} for x in r['rows'] if x['bank']==bank]};source.append(row);write(O/'source-checkpoint.json',source);print(bank,'baregroups',len(unroot),'oldloss',len(bad),flush=True)
 for net,ref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/LOGIC_GND','J11001')]:
  old=oldgrounds[net];new=F.graph(after,net);groups[net]=new;oi=next(i for i,xs in enumerate(old) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));ni=next(i for i,xs in enumerate(new) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));bad=losses(old,new);lost=sorted(F.discrete_keys(old[oi])-F.discrete_keys(new[ni]));ground.append({'net':net,'source':ref+'.2','R111_old_contact_losses':bad,'R111_prior_source_keys_lost':[list(x) for x in lost],'rooted_named_physical_pad_count':len({q['uuid'] for q in new[ni] if q['kind']=='pad' and q['pin']})});oldrefs={out:unary_union([q['shape'] for q in old[oi] if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newrefs={out:unary_union([q['shape'] for q in new[ni] if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};_,_,_,_,oldactual=pickle.loads((oldbp/'model.pkl').read_bytes());loss,diag=REF.audit(oldactual,oldrefs,newrefs,net);refs.append({'ground':net,'source':ref+'.2','retained_outer_track_reference_losses':loss,'exact_reference_audit':diag});write(O/'ground-checkpoint.json',ground);write(O/'reference-checkpoint.json',refs);print(net,'oldloss',len(bad),'sourcekeyloss',len(lost),'ref',len(loss),flush=True)
 b['REG_R121_two_reference_safe_replacements']={'receipt_file':str((rp/'receipt.json').resolve()),'receipt_sha256':sha(rp/'receipt.json'),'new_zone_UUIDs':[q['uuid'] for q in newq],'owned_ground_carves':r['owned_return_carves'],'replaces_only_two_failed_R114_In1_planes':True,'remaining_seven_pad_local_wall_work_separate':True}
 (O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(O/'new-two-zones.pkl').write_bytes(pickle.dumps(newq,protocol=5));write(O/'source-rows.json',source);write(O/'ground-rows.json',ground);write(O/'reference-losses.json',refs);write(O/'new-via-normalization.json',vg);write(O/'new-track-normalization.json',tg);write(O/'oldfill-retreats.json',oldfill)
 ok=not errors and all(not q['R111_old_contact_losses'] for q in source) and all(not q['R111_old_contact_losses'] and not q['R111_prior_source_keys_lost'] for q in ground) and all(all(x['all_target_pads_rooted'] for x in q['two_R121_target_memberships']) for q in source);write(O/'receipt.json',{'verdict':'TWO_FEED_SOURCE_CONTACT_ANALYTIC_SCOPE_PASS_REFERENCE_AND_REMAINING_LOAD_GATES_OPEN' if ok else 'TWO_FEED_REPAIR_REQUIRED','model_sha256':sha(O/'model.pkl'),'R123_model_sha256':sha(base/'model.pkl'),'R121_receipt_sha256':sha(rp/'receipt.json'),'analytic_checks':len(checks),'analytic_errors':len(errors),'source_rows_sha256':sha(O/'source-rows.json'),'ground_rows_sha256':sha(O/'ground-rows.json'),'reference_losses_sha256':sha(O/'reference-losses.json'),'new_two_zones_sha256':sha(O/'new-two-zones.pkl'),'groups_sha256':sha(O/'groups.pkl'),'ROOT_7_LG_known_reference_failure':'Explicit pending correction: two ROOT spines1bd97ebc/87644989; no reference acceptance granted','seven_bare_loads_full198b_r06_native_fullPDN_current_barrel_flash_fault_thermal_gates':'OPEN','board_written':False,'native_jobs':0});print('R129 frozen',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
