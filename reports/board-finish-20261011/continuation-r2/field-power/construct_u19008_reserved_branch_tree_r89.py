"""Derived branch-contact topology constructor; failed R88 is preserved."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_u19008_reserved_power_tree_r88.py').read_text()
s=s.replace("OUT=HERE/'u19008-outside-reservation-power-tree-r88'","OUT=HERE/'u19008-outside-reservation-branch-tree-r89'")
s=s.replace("starts=part.intersection(contactsh['4b070be4-ead5-4ab1-908b-65f9fcd63eb3'].buffer(.398));ends=part.intersection(contactsh['6e675361-9509-4d5c-b9b4-ad0603306a5f'].buffer(.398))", "starts=part.intersection(contactsh['54de4982-589d-4603-bc04-aaf050683680'].buffer(.25));ends=part.intersection(contactsh['cb440930-5805-49fd-8873-4220cdf5f0d1'].buffer(.25))")
s=s.replace("loss=[{'uuid':r['uuid'],'overlap_mm2':body.intersection(contactsh[r['uuid']]).area} for r in contacts if body.intersection(contactsh[r['uuid']]).area<.001]", "loss=[];joined=unary_union([body]+list(contactsh.values()));parts=polys(joined);mainpart=next((q for q in parts if q.intersection(body).area>body.area-.000001),None)\n   if mainpart is None:loss=[{'kind':'new_power_tree_split'}]\n   else:loss=[{'uuid':r['uuid'],'lost_physical_branch_area_mm2':contactsh[r['uuid']].difference(mainpart).area} for r in contacts if contactsh[r['uuid']].difference(mainpart).area>.000001]\n   for mandatory in ('54de4982-589d-4603-bc04-aaf050683680','cb440930-5805-49fd-8873-4220cdf5f0d1'):\n    if body.intersection(contactsh[mandatory]).area<.001:loss.append({'uuid':mandatory,'insufficient_direct_attachment_mm2':body.intersection(contactsh[mandatory]).area})")
s=s.replace("replacement_overlap_mm2=body.intersection(contactsh[r['uuid']]).area", "replacement_overlap_mm2=body.intersection(contactsh[r['uuid']]).area,retained_branch_in_same_physical_component=contactsh[r['uuid']].difference(mainpart).area<=.000001")
s=s.replace("controller-u19008-r88/", "controller-u19008-r89/")
s=s.replace("print('R88", "print('R89")
exec(compile(s,str(p/'construct_u19008_reserved_power_tree_r88.py'),'exec'))
