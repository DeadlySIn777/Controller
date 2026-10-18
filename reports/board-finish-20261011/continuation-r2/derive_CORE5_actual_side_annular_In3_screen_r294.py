"""Use retained full-width side contact and actual source annular targets."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
source=H/'screen_CORE5_middle_withdrawn_In3_LGIn4_transport_r292.py';target=H/'screen_CORE5_actual_side_annular_In3_LGIn4_transport_r294.py';assert not target.exists()
s=source.read_text(encoding='utf-8').replace('r292','r294').replace('R292','R294')
old="startpoint=(start['x'],start['y']);startcap=Point(startpoint).buffer(.775,quad_segs=128)"
new="startpoint=(123.560945,206.750243);startcap=Point(start['x'],start['y']).buffer(.775,quad_segs=128)"
assert s.count(old)==1;s=s.replace(old,new)
old="endpoint=(target['x'],target['y']);a=Point(startpoint);e=Point(endpoint);faces=[p for p in RF.parts(free)if p.covers(a)and p.covers(e)]"
new="endpoint=(target['x'],target['y']);a=Point(startpoint);e=Point(endpoint);target_axis_contact=ann.buffer(.624995,quad_segs=128);faces=[p for p in RF.parts(free)if p.covers(a)and not p.intersection(target_axis_contact).is_empty]"
assert s.count(old)==1;s=s.replace(old,new)
old="for face in faces:\n   path,method=TR.route(face,startpoint,endpoint);"
new="for face in faces:\n   available=face.intersection(target_axis_contact).buffer(-.000005)\n   if available.is_empty:continue\n   endpoint=list(nearest_points(a,available)[1].coords[0]);row['actual_target_side_contact_axis_endpoint']=endpoint\n   path,method=TR.route(face,startpoint,endpoint);"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'whole_body_minus_actual_source_and_only_endpoint_inner_caps_EMPTY']=True;row['actual_target_annular_overlap_mm2']=body.intersection(ann).area", "'whole_body_minus_actual_source_and_only_endpoint_inner_caps_EMPTY']=True;row['actual_target_annular_overlap_mm2']=body.intersection(ann).area;row['actual_start_annular_overlap_mm2']=body.intersection(Point(start['x'],start['y']).buffer(.5,quad_segs=128).difference(Point(start['x'],start['y']).buffer(.25,quad_segs=128))).area\n   if row['actual_target_annular_overlap_mm2']<=0 or row['actual_start_annular_overlap_mm2']<=0:row['route']=None;continue")
compile(s,str(target),'exec');target.write_text(s,encoding='utf-8')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();receipt=H/'CORE5-actual-side-annular-In3-screen-derivation-r294.json';assert not receipt.exists();receipt.write_text(json.dumps({'source_file':str(source),'source_sha256':sha(source),'derived_file':str(target),'derived_sha256':sha(target),'source_graph_exact_middle_withdrawal_retained':True,'start_uses_actual_qualified_full_width_side_contact':True,'end_uses_finite_actual_SOURCE_annulus_contact_instead_of_barrel_centre':True,'no_power_width_or_radius_waiver':True,'native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print('R294_SCRIPT_FROZEN',sha(target),flush=True)
