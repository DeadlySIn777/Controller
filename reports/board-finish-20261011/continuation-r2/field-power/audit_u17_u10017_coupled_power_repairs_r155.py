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
O=H/'u17-u10017-coupled-incremental-audit-r155'
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();baseline=H/'paired-regional-six-regulated-full-contact-audit-r142';g,h,b,z,before=pickle.loads((baseline/'REG_R130-regional-model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z);r154=H/'u10017-protected-source-via-bypass-nominee-r154';nom=json.loads((r154/'receipt.json').read_text(encoding='utf-8'));d=pickle.loads((r154/'proposed-discrete.pkl').read_bytes());vdd=pickle.loads((H/'u10017-coupled-vdd-strong-source-bypass-base-r154/VDD-tracks.pkl').read_bytes());u17=H/'u11017-dead-spur-native-owned-recipe-r138';u17r=json.loads((u17/'receipt.json').read_text(encoding='utf-8'));u17t=pickle.loads((u17/'proposed-tracks.pkl').read_bytes());removed={r['uuid'] for r in u17r['delete_rows']}|{'5c6ebac9-c76a-41f1-8cb8-45e2321f2e89'};adds=vdd+d['tracks']+u17t;h['tracks']=[t for t in h['tracks'] if t['uuid'] not in removed]+adds;h['vias']+=d['vias'];newq=pickle.loads((r154/'proposed-zones.pkl').read_bytes());updates={q['uuid']:q for q in pickle.loads((r154/'owned-new-return-updates.pkl').read_bytes())};current={q['uuid']:q for q in z}
 for q in nom['owned_return_carves']:assert P.digest(current[q['owned_new_return_uuid']]['shape'])==q['physical_before_sha256']
 z=[updates.get(q['uuid'],q) for q in z]+newq;z,viafix=P.normalize_owned_via_guards(h,z);z,trackfix,geoms=TG.normalize_owned_track_guards(h,z);print('R155 full regional projection',flush=True);after,retreat=P.projected(g,h,z);rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};checks=[];errors=[]
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
 write(O/'analytic-checks.json',checks);write(O/'analytic-errors.json',errors);print('R155 analytic',len(checks),len(errors),flush=True);oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes());newgroups={};contacts=[]
 for net in sorted(oldgroups):
  old=oldgroups[net];new=F.graph(after,net);newgroups[net]=new;oldret=[[q for q in xs if not(q['kind']=='track' and q['uuid'] in removed)] for xs in old];bad=losses(oldret,new);contacts.append({'net':net,'baseline_retained_relationship_losses':bad});write(O/'contact-checkpoint.json',contacts);print('R155 contact',net,len(bad),flush=True)
 sources=[];refs=[]
 for net,ref,pin in [('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/LOGIC_GND','J11001','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17')]:
  root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));old,new=root(oldgroups[net]),root(newgroups[net]);lost=F.discrete_keys(old)-{('track',uid) for uid in removed}-F.discrete_keys(new);sources.append({'net':net,'source':ref+'.'+pin,'prior_source_keys_lost':[list(k) for k in sorted(lost)]})
  if pin=='2':
   a={out:unary_union([q['shape'] for q in old if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bb={out:unary_union([q['shape'] for q in new if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,diag=REF.audit(before,a,bb,net,removed=removed);refs.append({'ground':net,'retained_outer_reference_losses':bad,'proof':diag});print('R155 ref',net,len(bad),flush=True)
 memberships=[]
 for net,ref,pin,expected in [('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')]),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17',[('U10017',str(i)) for i in (34,35,36,37)])]:
  root=next(xs for xs in newgroups[net] if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));memberships.append({'net':net,'source':ref+'.'+pin,'expected':expected,'all_expected_actual_source_rooted':all(any(q['kind']=='pad' and(q['ref'],q['pin'])==tuple(pair) for q in root) for pair in expected)})
 b['U11017_owned_dead_spur_local_join_r138']={'recipe_file':str((u17/'receipt.json').resolve()),'recipe_sha256':sha(u17/'receipt.json'),'remove_only_recipe_file':str((u17/'remove-only-recipe.json').resolve()),'remove_only_recipe_sha256':sha(u17/'remove-only-recipe.json')};b['U10017_coupled_source_bypass_r154']={'nominee_receipt_sha256':sha(r154/'receipt.json'),'exact_old_owned_wall_UUID':'5c6ebac9-c76a-41f1-8cb8-45e2321f2e89','new_barrel_UUID':d['vias'][0]['uuid'],'all_TPS274_output_limits_and_current_allocation_preserved':True,'native_exact_delete_adapter_required':True};(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));(O/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':d['vias'],'tracks':adds},protocol=5));(O/'new-owned-zones.pkl').write_bytes(pickle.dumps([q for q in z if q['uuid'] in {p['uuid'] for p in newq}],protocol=5));write(O/'contact-rows.json',contacts);write(O/'source-rows.json',sources);write(O/'reference-rows.json',refs);write(O/'memberships.json',memberships);write(O/'oldfill-retreats.json',retreat);write(O/'owned-via-normalization.json',viafix);write(O/'owned-track-normalization.json',trackfix);ok=not errors and not any(q['baseline_retained_relationship_losses'] for q in contacts) and not any(q['prior_source_keys_lost'] for q in sources) and not any(q['retained_outer_reference_losses'] for q in refs) and all(q['all_expected_actual_source_rooted'] for q in memberships);write(O/'receipt.json',{'verdict':'INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS' if ok else 'COUPLED_U17_U10017_REPAIR_REQUIRED','baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True,'model_sha256':sha(O/'model.pkl'),'groups_sha256':sha(O/'groups.pkl'),'analytic_checks':len(checks),'analytic_errors':len(errors),'checked_zone_nets':len(contacts),'contact_rows_sha256':sha(O/'contact-rows.json'),'source_rows_sha256':sha(O/'source-rows.json'),'reference_rows_sha256':sha(O/'reference-rows.json'),'memberships_sha256':sha(O/'memberships.json'),'exact_removed_original_UUIDs':sorted(removed),'new_vias':len(d['vias']),'new_tracks':len(adds),'new_plane_UUIDs':[q['uuid'] for q in newq],'all_original_unknown_sharing_full_TPS274_current_barrel_mesh_native_fault_thermal_GATES':'OPEN','board_written':False,'native_jobs':0});print('R155 complete',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
