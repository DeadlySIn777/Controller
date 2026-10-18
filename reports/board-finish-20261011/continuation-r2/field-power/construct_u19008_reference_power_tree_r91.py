"""Construct on both physical B power and In4 return-free geometry."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_u19008_reserved_power_tree_r88.py').read_text()
s=s.replace("OUT=HERE/'u19008-outside-reservation-power-tree-r88'","OUT=HERE/'u19008-reference-covered-power-tree-r91'")
s=s.replace("for reference_required in (True,False):", "for reference_required in (True,):")
s=s.replace("starts=part.intersection(contactsh['4b070be4-ead5-4ab1-908b-65f9fcd63eb3'].buffer(.398));ends=part.intersection(contactsh['6e675361-9509-4d5c-b9b4-ad0603306a5f'].buffer(.398))", "upper=unary_union([contactsh[u] for u in ('4b070be4-ead5-4ab1-908b-65f9fcd63eb3','54de4982-589d-4603-bc04-aaf050683680','e37aa52a-7701-4c8d-a9cd-302b39341d68')]);lower=unary_union([contactsh[u] for u in ('6e675361-9509-4d5c-b9b4-ad0603306a5f','bd03fbb1-7847-4297-93b0-bc8fe6bebbcd','cb440930-5805-49fd-8873-4220cdf5f0d1')]);starts=part.intersection(upper.buffer(.32));ends=part.intersection(lower.buffer(.32))\n   attempts.append({'ground_ref':reference_required,'part_area':part.area,'start_area':starts.area,'end_area':ends.area})")
s=s.replace("loss=[{'uuid':r['uuid'],'overlap_mm2':body.intersection(contactsh[r['uuid']]).area} for r in contacts if body.intersection(contactsh[r['uuid']]).area<.001]", "loss=[];joined=unary_union([body]+list(contactsh.values()));parts=polys(joined);mainpart=next((q for q in parts if q.intersection(body).area>body.area-.000001),None)\n   if mainpart is None:loss=[{'kind':'new_power_tree_split'}]\n   else:loss=[{'uuid':r['uuid'],'lost_physical_branch_area_mm2':contactsh[r['uuid']].difference(mainpart).area} for r in contacts if contactsh[r['uuid']].difference(mainpart).area>.000001]\n   for anchor,sh in (('upper',upper),('lower',lower)):\n    if body.intersection(sh).area<.001:loss.append({'branch':anchor,'insufficient_direct_attachment_mm2':body.intersection(sh).area})")
s=s.replace("replacement_overlap_mm2=body.intersection(contactsh[r['uuid']]).area", "replacement_overlap_mm2=body.intersection(contactsh[r['uuid']]).area,retained_branch_in_same_physical_component=contactsh[r['uuid']].difference(mainpart).area<=.000001")
s=s.replace("controller-u19008-r88/", "controller-u19008-r91/")
s=s.replace("print('R88", "print('R91")
exec(compile(s,str(p/'construct_u19008_reserved_power_tree_r88.py'),'exec'))
