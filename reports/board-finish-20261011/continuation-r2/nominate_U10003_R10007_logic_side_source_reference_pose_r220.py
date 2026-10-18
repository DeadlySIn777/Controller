"""Find a rigid resistor pose on the actual logic-side source reference."""
from pathlib import Path
H=Path(__file__).resolve().parent;wrapperPath=H/'nominate_U10003_R10007_exact_nine_body_shared_return_pose_r214.py'
prefix=wrapperPath.read_text().split("exec(compile(code,str(src),'exec'))")[0];exec(compile(prefix,str(wrapperPath),'exec'))
code=code.replace('exact-nine-body-rigid-pose-nomination-r214','logic-side-source-reference-rigid-pose-nomination-r220')
needle="poses=sorted([(a,dx/2,dy/2)for a in(0,90,180,-90)for dx in range(-9,10)";assert code.count(needle)==1
code=code.replace(needle,"poses=sorted([(a,dx/2,dy/2)for a in(0,90,180,-90)for dx in range(-30,10)")
needle=" poses=sorted([";assert code.count(needle)==1
code=code.replace(needle,"""
 proof=H/'U10003-R10007-rigid-pose-actual-source-bodies-r215/receipt.json';assert sha(proof)=='95e1c3a8c07c99512f0bfcee5b086c0a44ccdd05ac6668c06b4549e4addcbfd8';assert json.loads(proof.read_bytes())['all_prior_actual_J1_source_keys_retained_after_old_pad_withdrawal']
 source_without_old_pads={**full,'pads':[p for p in full['pads']if p['uuid']not in own]};_,groups=K.physical(source_without_old_pads,'/LOGIC_GND',K.hole_context(source_without_old_pads));actual_root=K.root(groups,'J11001','2');logicref=unary_union([x['shape']for x in actual_root if x['kind']=='fill'and x['layer']=='In4.Cu']);logicB=unary_union([x['shape']for x in actual_root if x['layer']=='B.Cu']);(OUT/'actual-J1-In4-full-source-reference.wkb').write_bytes(logicref.wkb);(OUT/'actual-J1-B-full-source-Cu.wkb').write_bytes(logicB.wkb)
 poses=sorted([""")
needle="  row={'pose':[angle,dx,dy],'errors':bad};rows.append(row)";assert code.count(needle)==1
code=code.replace(needle,"""  refrows=[]
  for num,s in new.items():
   rawgap=s.difference(logicref);refrows.append({'pin':num,'actual_J1_In4_full_pad_reference_gap_mm2':rawgap.area,'full_reference_gap_empty':rawgap.is_empty,'actual_J1_B_source_overlap_mm2':s.intersection(logicB).area if num=='2'else None,'actual_J1_B_source_distance_mm':s.distance(logicB)if num=='2'else None})
   if not rawgap.is_empty:bad.append({'kind':'actual_source_rooted_full_pad_reference','pin':num,'raw_gap_mm2':rawgap.area})
  row={'pose':[angle,dx,dy],'errors':bad,'actual_source_reference_rows':refrows};rows.append(row)""")
code=code.replace("'native_jobs':0","'old_both_R10007_pads_absent_from_reference_source_witness':True,'actual_J1_source_pad_withdrawal_proof_sha256':sha(proof),'native_jobs':0")
exec(compile(code,str(wrapperPath),'exec'))
