"""Separate physical F escape from actual reference obstacles; no waiver."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'diagnose_Q0_lost_power_group_actual_F_escape_r444.py'
code=base.read_text().replace('Q0-lost-power-group-actual-F-escape-r444','Q0-power-physical-F-reference-causes-r448')
code=code.replace("fr=free(POWER,'F.Cu',refs['In1.Cu'],peer)","fr=free(POWER,'F.Cu',window,peer)")
start=code.index("ok=route_attachments(");end=code.index("for uid,ch in chunks.items()",start)
replacement="""ok=False;physical_paths=[]
for part in K.RF.parts(fr):
 aa=attach.buffer(-.04,quad_segs=128).intersection(part);bb=target.buffer(-.02,quad_segs=128).intersection(part)
 if aa.is_empty or bb.is_empty:continue
 pp,qq=nearest_points(aa,bb);ends=[tuple(round(v,6)for v in p.coords[0])for p in(pp,qq)]
 if not all(part.covers(Point(xy))for xy in ends):continue
 path,search=T.route(part,*ends);path=[[round(v,6)for v in xy]for xy in path]
 if not part.covers(LineString(path)):continue
 body=unary_union([K.A.shape({'kind':'segment','a':a,'b':bb,'w':.2})for a,bb in zip(path,path[1:])]);rawgap=body.difference(refs['In1.Cu']);causes=[]
 for v in newvias:
  cut=K.Z.bounded_disk(v,.1 if K.L.norm(v['net'])==GND else .525);hit=rawgap.intersection(cut)
  if not hit.is_empty:causes.append({'new_via_role':v['uuid'],'raw_net':v['net'],'intersection_mm2':hit.area,'intersection_WKB_sha256':K.C.sha(hit.wkb)})
 (out/'physical-power-F-candidate-body.wkb').write_bytes(body.wkb);(out/'physical-power-F-raw-ground-reference-gap.wkb').write_bytes(rawgap.wkb)
 physical_paths.append({'path_mm':path,'length_mm':LineString(path).length,'source_actual_lost_group_and_root_contact_nomination':True,'true_physical_free_fullbody_coverage':True,'raw_source_ground_reference_gap_mm2':rawgap.area,'raw_reference_gap_empty':rawgap.is_empty,'new_via_gap_attribution':causes,'search':search,'qualification':'OPEN; no own-hole or neighboring-void credit'})
 for a,bb in zip(path,path[1:]):
  uid,ch=identity.serial_segment(POWER,'F.Cu',a,bb,.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(POWER),'layer':'F.Cu','a':a,'b':bb,'w':.2})
 ok=True;break
put(out/'physical-power-F-source-and-reference-cause-ledger.json',physical_paths)
"""
code=code[:start]+replacement+code[end:]
code=code.replace("'verdict':'ACTUAL_LOST_POWER_F_SOURCE_PATH_NOMINATED_FULL_GATES_OPEN'if ok else'ACTUAL_LOST_POWER_F_ATTACHMENTS_INCOMPLETE'","'verdict':'PHYSICAL_POWER_F_ESCAPE_NOMINATED_RAW_REFERENCE_CURRENT_NATIVE_OPEN'if ok else'PHYSICAL_POWER_F_ESCAPE_INCOMPLETE'")
exec(compile(code,str(base),'exec'))
