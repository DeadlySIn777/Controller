"""Retained-VS connectivity test before permitting exact one-wall removal."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_u10017_coupled_vs_wall_r134.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u10017-coupled-vdd-vs-wall-nominee-r134'", "O=H/'u10017-redundant-vs-wall-removal-r151'")
start=s.index(' a,bb=nearest_points(target[\'shape\'],goal);trials=[];answer=None')
s=s[:start]+''' from audit_field_io3_crossings_r15e import losses
 current=H/'paired-regional-six-regulated-full-contact-audit-r142/REG_R130-regional-model.pkl';prior=pickle.loads(current.read_bytes())[4];protected=C.norm(old['net']);before=F.graph(prior,protected);without=copy.deepcopy(prior);without['tracks']=[q for q in without['tracks'] if q['uuid']!=old['uuid']];after=F.graph(without,protected);beforefiltered=[[q for q in xs if not(q['kind']=='track' and q['uuid']==old['uuid'])] for xs in before];bad=losses(beforefiltered,after)
 root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==('U11006','17') for q in xs));lost=F.discrete_keys(root(before))-{('track',old['uuid'])}-F.discrete_keys(root(after));write(O/'protected-removal-contact-check.json',{'retained_old_relationship_losses':bad,'retained_protected_source_keys_lost':[list(k) for k in sorted(lost)],'source':'U11006.17','candidate_model_sha256':sha(current),'new_body_foreign_fill_current_effect_not_yet_projected':True})
 trials=[];answer=None
 if not bad and not lost:
  a,bb=nearest_points(target['shape'],goal)
  for margin in (3.,8.,18.):
   win=box(min(a.x,bb.x)-margin,min(a.y,bb.y)-margin,max(a.x,bb.x)+margin,max(a.y,bb.y)+margin);join=route(legal(target['net'],win),target['shape'],goal,.2);trials.append({'window_margin_mm':margin,'VDD_source_join':bool(join)})
   if not join:continue
   points,line,body,search=join;adds=[]
   for j,(pa,pb) in enumerate(zip(points,points[1:])):
    if pa==pb:continue
    adds.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u10017-redundant-wall-r151/VDD/{j}')),'net':target['net'],'layer':'F.Cu','a':pa,'b':pb,'w':.2,'locked':False,'prospective_not_native':True})
   answer={'target_physical_UUID':target['uuid'],'source':'U11038.1','VDD_raw':target['net'],'VDD_points_mm':points,'VDD_length_mm':line.length,'VDD_width_mm':.2,'old_owned_wall_UUID':old['uuid'],'protected_raw':old['net'],'old_protected_width_mm':old['w'],'removal_retains_all_outside_physical_relationships_and_actual_source_keys':True,'retained_protected_capacity_effect':'A parallel .3F path is removed. No current/barrel/constriction capacity claim is granted; full TPS274 2A output/current sharing remains unchanged and needs final PDN solve.'};(O/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5));(O/'exact-old-owned-track-records.pkl').write_bytes(pickle.dumps([old],protocol=5));break
 write(O/'trials.json',trials);write(O/'receipt.json',{'verdict':'COUPLED_U10017_VDD_ONE_REDUNDANT_VS_WALL_NOMINATION' if answer else 'NO_RETAINED_SOURCE_RELATIONSHIP_SAFE_REMOVAL_OR_VDD_ROUTE','row':answer,'old_exact_wall_UUID':old['uuid'],'protected_removal_check_sha256':sha(O/'protected-removal-contact-check.json'),'retained_old_contact_loss_count':len(bad),'source_keys_lost_count':len(lost),'R22_model_sha256':sha(base/'model.pkl'),'R142_candidate_sha256':sha(current),'proposed_tracks_sha256':sha(O/'proposed-tracks.pkl') if answer else None,'exact_old_track_sha256':sha(O/'exact-old-owned-track-records.pkl') if answer else None,'retained_outside_contacts_source_reference_current_native_gates':'MANDATORY_OPEN','board_written':False,'native_jobs':0});print('R151',sha(O/'receipt.json'),len(bad),len(lost),json.dumps(answer),flush=True)
if __name__=='__main__':main()
'''
s=s.replace('.read_text()', ".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_u10017_coupled_vs_wall_r134.py'),'exec'))
