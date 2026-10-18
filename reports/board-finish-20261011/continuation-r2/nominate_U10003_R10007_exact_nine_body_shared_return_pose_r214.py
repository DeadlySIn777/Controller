"""Restrict the diagnostic withdrawal to the nine R196 bodies only."""
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_U10003_R10007_shared_return_rigid_pose_r213.py';code=src.read_text().replace('rigid-pose-nomination-r213','exact-nine-body-rigid-pose-nomination-r214')
needle="nativeids={t['uuid']for t in g['tracks']};terminal=[]";assert code.count(needle)==1
code=code.replace(needle,"base=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';assert sha(base)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144';_,baseh,_,_,_=pickle.loads(base.read_bytes());baseids={t['uuid']for t in baseh['tracks']};nativeids={t['uuid']for t in g['tracks']};terminal=[]")
needle="newwalls={t['uuid']for t in h['tracks']if t['uuid']not in nativeids and K.L.norm(t['net'])in(FG,CLK,FLT)}";assert code.count(needle)==1
code=code.replace(needle,"newwalls={t['uuid']for t in h['tracks']if t['uuid']not in baseids};assert len(newwalls)==9;assert all(K.L.norm(t['net'])in(FG,CLK,FLT)for t in h['tracks']if t['uuid']in newwalls)")
needle="row={'pose':[angle,dx,dy],'errors':bad};rows.append(row)";assert code.count(needle)==1
code=code.replace(needle,"""for rule in h['rule_areas']:
   if 'B.Cu'in rule['layers']and rule.get('no_footprints')and any(nc.distance(x)<.025 for x in K.L.poly(rule['outline'])):bad.append({'kind':'native_no_footprint_area','UUID':rule['uuid']})
  row={'pose':[angle,dx,dy],'errors':bad};rows.append(row)""")
code=code.replace("'native_jobs':0","'earlier_R213_broad_unadopted_scene_not_acceptance':True,'exact_R196_nine_body_nomination_scope_only':True,'native_jobs':0")
exec(compile(code,str(src),'exec'))
