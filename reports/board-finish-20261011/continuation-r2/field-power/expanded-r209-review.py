"""All-net incremental audit; preserve the earlier REG8b IO3 failure."""
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
from audit_field_io3_crossings_r15e import losses
H=Path(__file__).resolve().parent
for name in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/name))
import regional_guarded_declared_projection_r140 as P
import owned_analytic_track_guards_r75 as TG
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
O=H/'REG-rebuilt-B3-on-wider-IO3-full-audit-r209'
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir()
 from shapely import set_precision,get_precision
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 baseline=H/'U10017-wider-on-exact-IO3-audit-r195';assert sha(baseline/'model.pkl')=='103f9dbba8ac50bd90a913d4a7004cd94c3a06ed07d7ab5262c84de6c358f8ab'
 g,h,b,z,_=pickle.loads((baseline/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z);restore_bound_generated_precision_states(b,z)
 W=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201';assert sha(W/'receipt.json')=='cee3eacedd73ba63788decafd0a3b169afee6a0fbfa76f76e5acc60e8cc83e2d';wr=json.loads((W/'receipt.json').read_text(encoding='utf-8'));row=wr['only_one_owned_host_group_replacement'][0];oldq=next(q for q in z if q['uuid']==row['old_UUID'])
 for role,proof in row['roles'].items():assert P.digest(oldq[role])==proof['old_sha256'],('old exact IO3 group mismatch',role)
 replacement=pickle.loads((W/'exact-owned-IO3-one-In3-group-replacement.pkl').read_bytes());replacement=replacement[0] if isinstance(replacement,list) else replacement;assert replacement['uuid']==row['new_UUID']
 for role,proof in row['roles'].items():assert P.digest(replacement[role])==proof['new_sha256'];replacement[role]=set_precision(replacement[role],1e-6,mode='pointwise')
 # Preserve newly owned U10017 barrel clearances on the later IO3 group explicitly.
 c554=next(v for v in h['vias'] if v['uuid']=='c55416b9-e522-5cbf-9523-ddb093be9249');rq,rebased_via=P.normalize_owned_via_guards({**h,'vias':[c554]},[replacement]);assert len(rq)==1;z=[rq[0] if q['uuid']==oldq['uuid'] else q for q in z]
 b['IO3_R201_exact_one_group_wider_replacement']={'packet':str((W/'receipt.json').resolve()),'sha256':sha(W/'receipt.json'),'actual_U10017_barrel_guard_replay':rebased_via};print('R209 exact widened IO3 baseline',flush=True);before,basecuts=P.projected(g,h,z);oldgroups={net:F.graph(before,net) for net in sorted({C.norm(q['net']) for q in before['zones']})}
 R=H/'SAFE-regulated-u17-u10017-paired-regional-audit-r171';assert sha(R/'receipt.json')=='6be34443033d35d918f6ecebd4ca2d123b6f34cf01d81190153d7812bb8b5a0c';reg=pickle.loads((R/'proposed-discrete.pkl').read_bytes());d={'vias':[v for v in reg['vias'] if v['uuid']!='c55416b9-e522-5cbf-9523-ddb093be9249'],'tracks':[t for t in reg['tracks'] if C.norm(t['net'])=='/motherboard_power_entry/FIELD_5V']};assert len(d['vias'])==3 and len(d['tracks'])==10
 Q=H/'B3-exact-cross-layer-pair-r206';assert sha(Q/'cross-layer-receipt.json')=='3d428acae6b187050fbe6aa5c9f8a79fae6d692df65ce2186302d1fc6f956659';bd=pickle.loads((Q/'cross-layer-discrete.pkl').read_bytes());assert len(bd['vias'])==1 and not bd['tracks'];d['vias']+=bd['vias'];adds=d['tracks'];u17=H/'u11017-dead-spur-native-owned-recipe-r138';u17r=json.loads((u17/'receipt.json').read_text(encoding='utf-8'));removed={q['uuid'] for q in u17r['delete_rows']};assert len(removed)==3 and removed<={q['uuid'] for q in h['tracks']};h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+adds;assert not({v['uuid'] for v in h['vias']}&{v['uuid'] for v in d['vias']});h['vias']+=d['vias']
 newq=[q for q in pickle.loads((R/'new-owned-zones.pkl').read_bytes()) if q['uuid'] not in ('c5ba529f-a864-5662-be39-9d5cf864ee62','e8ec0287-e6d1-597d-8ad8-c4ab74280f6c')];assert len(newq)==5;newq+=pickle.loads((Q/'cross-layer-zones.pkl').read_bytes());assert len(newq)==7 and 'c5ba529f-a864-5662-be39-9d5cf864ee62' not in {q['uuid'] for q in z+newq}
 current={q['uuid']:q for q in z};base_owned=copy.deepcopy(current);replays=[]
 # Derive fresh declared cutters from exact new bodies, never restore stale R171 returns.
 for q in z:
  if q['layer'] not in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu') or C.norm(q['net']) not in ('/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V') or float(q.get('clearance_mm',.15))!=.15:continue
  foreign=[n['zone_outline_shape'] for n in newq if n['layer']==q['layer'] and C.norm(n['net'])!=C.norm(q['net']) and G.gap(h,n['net'],q['net'])==.15]
  if not foreign:continue
  cutter=P.bounded_buffer(unary_union(foreign),.175);oldsh=q['shape'];oldout=q['zone_outline_shape'];q['shape']=set_precision(oldsh.difference(cutter),1e-6);q['zone_outline_shape']=set_precision(oldout.difference(cutter),1e-6)
  if oldsh.wkb!=q['shape'].wkb or oldout.wkb!=q['zone_outline_shape'].wkb:
   cf=O/(q['uuid']+'.fresh-owned-return-cut.wkb');cf.write_bytes(cutter.wkb);replays.append({'owned_UUID':q['uuid'],'cutter_file':str(cf.resolve()),'cutter_sha256':sha(cf),'physical_before_sha256':P.digest(oldsh),'physical_after_sha256':P.digest(q['shape']),'intended_before_sha256':P.digest(oldout),'intended_after_sha256':P.digest(q['zone_outline_shape']),'required_gap_mm':.175,'added_physical_mm2':q['shape'].difference(oldsh).area,'stale_return_shape_substituted':False})
 z,viafix=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,trackfix,geoms=TG.normalize_owned_track_guards({**h,'tracks':adds},z);newq,nvg=P.normalize_owned_via_guards(h,newq);newq,ntg,ng=TG.normalize_owned_track_guards(h,newq);viafix+=nvg;trackfix+=ntg;geoms.update(ng);updates={q['uuid']:q for q in z if any(P.digest(q[role])!=P.digest(base_owned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))};z+=newq
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;write(O/'derived-generated-precision-state-ledger.json',precision);write(O/'actual-latest-owned-return-cutter-replay.json',replays);print('R209 rebuilt pair + retained regulated full projection',flush=True);after,retreat=P.projected(g,h,z)
 rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};checks=[];errors=[]
 def record(row):
  checks.append(row)
  if row['actual_mm']+1e-10<row['required_mm']:errors.append(row)
 for t in adds:
  line=LineString([t['a'],t['b']]);body=P.bounded_buffer(line,t['w']/2);l=t['layer']
  for j in trees[l].query(body.buffer(.627),predicate='intersects'):
   a=rec[l][int(j)]
   if C.norm(a['net'])==C.norm(t['net']):continue
   gap=line.distance(a['shape'])-t['w']/2
   if a['kind']=='track':other=tm[a['uuid']];gap=line.distance(LineString([other['a'],other['b']]))-(t['w']+other['w'])/2
   if a['kind']=='via':v=vm[a['uuid']];gap=line.distance(Point(v['x'],v['y']))-(t['w']+v['d'])/2
   record({'owned':t['uuid'],'foreign':a['uuid'],'kind':'track_to_'+a['kind'],'layer':l,'required_mm':G.gap(h,t['net'],a['net'])+.025,'actual_mm':gap})
  for q in z:
   if q['layer']!=l or C.norm(q['net'])==C.norm(t['net']):continue
   req=max(G.gap(h,t['net'],q['net']),float(q.get('clearance_mm',.15)))+.025;gap=line.distance(q['shape'])-t['w']/2
   if gap<req+.01:record({'owned':t['uuid'],'foreign':q['uuid'],'kind':'track_to_newplane','layer':l,'required_mm':req,'actual_mm':gap})
 for v in d['vias']:
  pt=Point(v['x'],v['y'])
  for l in ('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'):
   for j in trees[l].query(pt.buffer(v['d']/2+.627),predicate='intersects'):
    a=rec[l][int(j)]
    if C.norm(a['net'])==C.norm(v['net']):continue
    gap=pt.distance(a['shape'])-v['d']/2
    if a['kind']=='track':t=tm[a['uuid']];gap=pt.distance(LineString([t['a'],t['b']]))-(v['d']+t['w'])/2
    if a['kind']=='via':other=vm[a['uuid']];gap=pt.distance(Point(other['x'],other['y']))-(v['d']+other['d'])/2
    record({'owned':v['uuid'],'foreign':a['uuid'],'kind':'barrel_to_'+a['kind'],'layer':l,'required_mm':G.gap(h,v['net'],a['net'])+.025,'actual_mm':gap})
  for pad in h['pads']:
   if pad['smd']:
    for l,rs in pad['layers'].items():
     if l not in ('F.Cu','B.Cu'):continue
     sh=unary_union(C.poly(rs));gap=pt.distance(sh)-v['drill']/2
     if gap<.285:record({'owned':v['uuid'],'foreign':pad['uuid'],'kind':'drill_to_every_SMD','layer':l,'required_mm':.275,'actual_mm':gap})
   for sh in C.poly(pad.get('hole') or []):
    gap=pt.distance(sh)-v['drill']/2
    if gap<.285:record({'owned':v['uuid'],'foreign':pad['uuid'],'kind':'drill_to_pad_hole','required_mm':.275,'actual_mm':gap})
  for other in h['vias']:
   if other['uuid']==v['uuid']:continue
   gap=pt.distance(Point(other['x'],other['y']))-(v['drill']+other['drill'])/2
   if gap<.285:record({'owned':v['uuid'],'foreign':other['uuid'],'kind':'drill_to_every_via_hole','required_mm':.275,'actual_mm':gap})
 for q in z:
  if q['uuid'] not in {x['uuid'] for x in newq}|set(updates):continue
  sh=q['shape'];l=q['layer']
  for j in trees[l].query(sh.buffer(.627),predicate='intersects'):
   a=rec[l][int(j)]
   if C.norm(a['net'])==C.norm(q['net']):continue
   gap=sh.distance(a['shape'])
   if a['kind']=='track':t=tm[a['uuid']];gap=sh.distance(LineString([t['a'],t['b']]))-t['w']/2
   if a['kind']=='via':v=vm[a['uuid']];gap=sh.distance(Point(v['x'],v['y']))-v['d']/2
   record({'owned':q['uuid'],'foreign':a['uuid'],'kind':'plane_to_'+a['kind'],'layer':l,'required_mm':max(G.gap(h,q['net'],a['net']),float(q.get('clearance_mm',.15)))+.025,'actual_mm':gap})
  for peer in z:
   if peer['uuid']==q['uuid'] or peer['layer']!=l or C.norm(peer['net'])==C.norm(q['net']):continue
   req=max(G.gap(h,q['net'],peer['net']),float(q.get('clearance_mm',.15)),float(peer.get('clearance_mm',.15)))+.025;gap=sh.distance(peer['shape'])
   if gap<req+.01:record({'owned':q['uuid'],'foreign':peer['uuid'],'kind':'plane_to_newplane','layer':l,'required_mm':req,'actual_mm':gap})
 write(O/'analytic-checks.json',checks);write(O/'analytic-errors.json',errors);print('R209 analytic',len(checks),len(errors),flush=True);newgroups={};contacts=[]
 for net in sorted(oldgroups):
  old=oldgroups[net];new=F.graph(after,net);newgroups[net]=new;oldret=[[q for q in xs if not(q['kind']=='track' and q['uuid'] in removed)] for xs in old];bad=losses(oldret,new);contacts.append({'net':net,'baseline_retained_relationship_losses':bad});write(O/'contact-checkpoint.json',contacts);print('R209 contact',net,len(bad),flush=True)
 sources=[];refs=[]
 for net,ref,pin in [('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/LOGIC_GND','J11001','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17')]:
  root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));old,new=root(oldgroups[net]),root(newgroups[net]);lost=F.discrete_keys(old)-{('track',uid) for uid in removed}-F.discrete_keys(new);sources.append({'net':net,'source':ref+'.'+pin,'prior_source_keys_lost':[list(k) for k in sorted(lost)]})
  if pin=='2':
   a={out:unary_union([q['shape'] for q in old if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bb={out:unary_union([q['shape'] for q in new if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,diag=REF.audit(before,a,bb,net,removed=removed);refs.append({'ground':net,'retained_outer_reference_losses':bad,'proof':diag});print('R209 ref',net,len(bad),flush=True)
 memberships=[]
 for net,ref,pin,expected in [('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5'),('U9002','10'),('R11053','1')]),('/motherboard_do/DOB_FIELD_3V3','U11018','1',[('U19008','10'),('U10013','4')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')])]:
  root=next(xs for xs in newgroups[net] if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));memberships.append({'net':net,'source':ref+'.'+pin,'expected':expected,'all_expected_actual_source_rooted':all(any(q['kind']=='pad' and(q['ref'],q['pin'])==tuple(pair) for q in root) for pair in expected)})
 b['REG_rebuilt_B3_exact_R206_on_wider_IO3_R209']={'U17_remove_only_recipe_file':str((u17/'remove-only-recipe.json').resolve()),'U17_remove_only_recipe_sha256':sha(u17/'remove-only-recipe.json'),'B3_cross_layer_nomination_sha256':sha(Q/'cross-layer-receipt.json'),'failed_C5_withdrawn_exactly':True,'actual_fresh_same_domain_owned_return_cutter_file':str((O/'actual-latest-owned-return-cutter-replay.json').resolve()),'all_device_and_output_limits_current_fault_native_GATES':'OPEN'};(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));(O/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':d['vias'],'tracks':adds},protocol=5));(O/'new-owned-zones.pkl').write_bytes(pickle.dumps([q for q in z if q['uuid'] in {p['uuid'] for p in newq}],protocol=5));write(O/'contact-rows.json',contacts);write(O/'source-rows.json',sources);write(O/'reference-rows.json',refs);write(O/'memberships.json',memberships);write(O/'oldfill-retreats.json',retreat);write(O/'owned-via-normalization.json',viafix);write(O/'owned-track-normalization.json',trackfix);ok=not errors and not any(q['baseline_retained_relationship_losses'] for q in contacts) and not any(q['prior_source_keys_lost'] for q in sources) and not any(q['retained_outer_reference_losses'] for q in refs) and all(q['all_expected_actual_source_rooted'] for q in memberships);write(O/'receipt.json',{'verdict':'REG_REBUILT_B3_WIDER_IO3_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS' if ok else 'REG_REBUILT_B3_WIDER_IO3_REPAIR_REQUIRED','baseline_sha256':sha(baseline/'model.pkl'),'exact_IO3_R201_one_q_replay_and_wide_U10017_R195':True,'no_R171_whole_model_or_failed_C5_substitution':True,'model_sha256':sha(O/'model.pkl'),'groups_sha256':sha(O/'groups.pkl'),'analytic_checks':len(checks),'analytic_errors':len(errors),'checked_zone_nets':len(contacts),'contact_rows_sha256':sha(O/'contact-rows.json'),'source_rows_sha256':sha(O/'source-rows.json'),'reference_rows_sha256':sha(O/'reference-rows.json'),'memberships_sha256':sha(O/'memberships.json'),'exact_removed_original_UUIDs':sorted(removed),'new_vias':len(d['vias']),'new_tracks':len(adds),'new_plane_UUIDs':[q['uuid'] for q in newq],'all_original_unknown_sharing_full_TPS274_current_barrel_mesh_native_fault_thermal_GATES':'OPEN','board_written':False,'native_jobs':0});print('R209 complete',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
