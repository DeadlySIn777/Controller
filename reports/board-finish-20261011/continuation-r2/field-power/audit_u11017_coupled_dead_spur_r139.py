"""Full scoped source/contact/reference audit of exact three spur deletes."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
from audit_field_io3_crossings_r15e import losses
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'));sys.path.insert(0,str(H.parent/'coupled-recovery'))
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
O=H/'u11017-coupled-dead-spur-source-contact-audit-r139'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'safe-root22-regulated-source-contact-audit-r130';assert sha(base/'model.pkl')=='c9454c9ab38a87c23eb16c33c05cda5f10237627c4986ab1e052296859ad342b';g,h,b,z,before=pickle.loads((base/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);owned=H/'u11017-dead-spur-native-owned-recipe-r138';assert sha(owned/'receipt.json')=='20ac505b73835aa9b4eca17e598b77f24b1503ef024de818a43985ce758ac4d7';rr=json.loads((owned/'receipt.json').read_text());removed={q['uuid'] for q in rr['delete_rows']};adds=pickle.loads((owned/'proposed-tracks.pkl').read_bytes());h['tracks']=[t for t in h['tracks'] if t['uuid'] not in removed]+adds;print('R139 regional full projection',flush=True);after,retreat=P.projected(g,h,z);rec,trees=F.build({**h,'zones':[]});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']};errors=[];checks=[]
 for t in adds:
  line=LineString([t['a'],t['b']]);body=P.bounded_buffer(line,t['w']/2);l=t['layer'];clear=.15 if h['domains_normalized'][C.norm(t['net'])]=='FA' else None
  for idx in trees[l].query(body.buffer(.627),predicate='intersects'):
   a=rec[l][int(idx)]
   if C.norm(a['net'])==C.norm(t['net']):continue
   req=G.gap(h,t['net'],a['net'])+.025;gap=line.distance(a['shape'])-t['w']/2
   if a['kind']=='track':other=tm[a['uuid']];gap=line.distance(LineString([other['a'],other['b']]))-(t['w']+other['w'])/2
   if a['kind']=='via':v=vm[a['uuid']];gap=line.distance(Point(v['x'],v['y']))-t['w']/2-v['d']/2
   row={'new_track':t['uuid'],'foreign_item':a['uuid'],'kind':a['kind'],'required_mm':req,'analytic_gap_mm':gap};checks.append(row)
   if gap+1e-10<req:errors.append(row)
  for q in z:
   if q['layer']!=l or C.norm(q['net'])==C.norm(t['net']):continue
   req=max(G.gap(h,t['net'],q['net']),float(q.get('clearance_mm',.15)))+.025;gap=line.distance(q['shape'])-t['w']/2
   if gap<req+.01:
    row={'new_track':t['uuid'],'foreign_item':q['uuid'],'kind':'new_plane','required_mm':req,'analytic_gap_mm':gap};checks.append(row)
    if gap+1e-10<req:errors.append(row)
 write(O/'analytic-checks.json',checks);write(O/'analytic-errors.json',errors);oldcache=pickle.loads((base/'groups.pkl').read_bytes());rows=[];groups={};groundrows=[];refs=[]
 nets=['/motherboard_power_entry/FIELD_5V','/motherboard_power_entry/FIELD_A_24V_PROTECTED','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V','/LOGIC_GND']
 for net in nets:
  old=oldcache.get(net)
  if old is None:old=F.graph(before,net)
  new=F.graph(after,net);groups[net]=new;oldret=[[q for q in xs if q['uuid'] not in removed] for xs in old];bad=losses(oldret,new);row={'net':net,'owned_deleted_discrete_UUIDs':sorted(removed) if 'PROTECTED' in net else [],'all_retained_old_relationship_losses':bad};rows.append(row);print('R139',net,'oldloss',len(bad),flush=True)
  if net=='/motherboard_power_entry/FIELD_5V':root=next(xs for xs in new if any(q['kind']=='pad' and(q['ref'],q['pin'])==('L11003','2') for q in xs));row['U11017_IN8_EN5_actual_source_rooted']=all(any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11017',pin) for q in root) for pin in ('8','5'));row['source']='L11003.2'
  if net=='/motherboard_power_entry/FIELD_A_24V_PROTECTED':root=next(xs for xs in new if any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11004','17') for q in xs));okeys=next(xs for xs in old if any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11004','17') for q in xs));row['retained_protected_source_keys_lost']=[list(k) for k in sorted(F.discrete_keys(okeys)-{('track',uid) for uid in removed}-F.discrete_keys(root))]
  if net in ('/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V','/LOGIC_GND'):
   ref={'/motherboard_motors/FIELD_GND':'J11003','/motherboard_do/FIELD_B_0V':'J11005','/LOGIC_GND':'J11001'}[net];find=lambda xs:next(q for q in xs if any(a['kind']=='pad' and(a['ref'],a['pin'])==(ref,'2') for a in q));a,bb=find(old),find(new);lost=F.discrete_keys(a)-F.discrete_keys(bb);groundrows.append({'net':net,'source':ref+'.2','prior_source_keys_lost':[list(k) for k in sorted(lost)]});oldref={out:unary_union([q['shape'] for q in a if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newref={out:unary_union([q['shape'] for q in bb if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};rl,diag=REF.audit(before,oldref,newref,net,removed=removed);refs.append({'ground':net,'incremental_retained_outer_reference_losses':rl,'proof':diag})
   if net=='/motherboard_motors/FIELD_GND':new_track_refs=[{'uuid':t['uuid'],'new_fullcap_source_ground_reference_missing_mm2':P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2).difference(newref['F.Cu']).area} for t in adds];write(O/'new-track-source-reference.json',new_track_refs)
  write(O/'contact-checkpoint.json',rows)
 b['U11017_owned_dead_spur_local_join_r138']={'recipe_file':str((owned/'receipt.json').resolve()),'recipe_sha256':sha(owned/'receipt.json'),'remove_only_recipe_file':str((owned/'remove-only-recipe.json').resolve()),'remove_only_recipe_sha256':sha(owned/'remove-only-recipe.json'),'owned_deleted_UUIDs':sorted(removed),'owned_added_UUIDs':[q['uuid'] for q in adds],'all_output_limits_BOM_source_net_assignments_unchanged':True};(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));write(O/'contact-rows.json',rows);write(O/'ground-source-rows.json',groundrows);write(O/'reference-rows.json',refs);write(O/'oldfill-retreats.json',retreat);ok=not errors and not any(r['all_retained_old_relationship_losses'] for r in rows) and not any(r['prior_source_keys_lost'] for r in groundrows) and not any(r['incremental_retained_outer_reference_losses'] for r in refs) and all(r['new_fullcap_source_ground_reference_missing_mm2']<1e-9 for r in new_track_refs);write(O/'receipt.json',{'verdict':'SCOPED_U11017_CONTACT_SOURCE_REFERENCE_ANALYTIC_PASS' if ok else 'SCOPED_U11017_REPAIR_REQUIRED','R130_base_model_sha256':sha(base/'model.pkl'),'R138_owned_recipe_sha256':sha(owned/'receipt.json'),'model_sha256':sha(O/'model.pkl'),'groups_sha256':sha(O/'groups.pkl'),'analytic_checks':len(checks),'analytic_errors':len(errors),'contact_rows_sha256':sha(O/'contact-rows.json'),'ground_source_rows_sha256':sha(O/'ground-source-rows.json'),'reference_rows_sha256':sha(O/'reference-rows.json'),'new_track_source_reference_sha256':sha(O/'new-track-source-reference.json'),'projector_file_sha256':sha(H/'regional_guarded_declared_projection_r140.py'),'global_ROOT_R22_reference_precision_history_not_waived':True,'full_original198b_r06_final_joint_current_fault_temperature_native_gates':'OPEN','board_written':False,'native_jobs':0});print('R139 frozen',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
