"""Move only new DI15 entry/path/strip, and close R150 nomination omissions."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_new_only_reference_branches_r150.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r150','r152').replace('R150','R152')
old="overlap=line.intersection(cur['source_planes']['In1.Cu'].buffer(-.110,quad_segs=128)).intersection(connected)"
new="""r90p=H/'di15-adjacent-reference-handoff-geometric-nomination-r90.json';r90=json.loads(A.read(r90p));assert C.sha(A.read(r90p))=='71e9cb9446100ddeca47f8dd2acbdd73af4703fda83501edf98d87e100b714d5';r90raw=A.read(r90['saved_geometry']);assert C.sha(r90raw)==r90['saved_geometry_sha256'];r90model=pickle.loads(r90raw);physical=r90model['models'][76]['physical_In2_center_region'];domains=h0['domains_normalized'];hard=[Z.bounded_buffer(z['shape'],.105+max(float(z.get('clearance_mm',.15)),.15 if domains.get(L.norm(z['net']))==domains['/motherboard_di/DI15_LOGIC'] else .6)+.030) for z in cur['zones'] if z['layer']=='In2.Cu' and L.norm(z['net'])!='/motherboard_di/DI15_LOGIC'];physical=physical.difference(unary_union(hard));source_parts=[q for q in K.pieces(physical.intersection(cur['source_planes']['In1.Cu'].buffer(-.110,quad_segs=128))) if q.covers(Point(119.835668,89.798413))];assert len(source_parts)==1;sourcecomp=source_parts[0];overlap=sourcecomp.intersection(connected).intersection(win)"""
assert old in s;s=s.replace(old,new)
s=s.replace("overlap.buffer(.990,quad_segs=128)","overlap.buffer(.990,quad_segs=128)")
old="shared=nearest_points(overlap,p)[0];nominations.append({**site,'existing_source_annular_contacts_mm2':areas,'proposed_handoff_point_mm':list(shared.coords)[0],'handoff_return_distance_mm':shared.distance(p)})"
new="""if math.dist(site['at_mm'],[128.695,109.614094])<.815:continue
  handregion=overlap.intersection(p.buffer(.990,quad_segs=128).difference(p.buffer(.550,quad_segs=128)));hands=K.sites(handregion,[123.675923,103.21109],3)
  for hand in hands:nominations.append({**site,'existing_source_annular_contacts_mm2':areas,'proposed_handoff_point_mm':hand['at_mm'],'handoff_return_distance_mm':math.dist(site['at_mm'],hand['at_mm']),'actual_source_In2_In1_component_sha256':C.sha(sourcecomp.wkb)})"""
assert old in s;s=s.replace(old,new)
s=s.replace("'potential_overlap_length_mm':overlap.length","'potential_source_handoff_area_mm2':overlap.area")
old="shape=island.union(unary_union(branches));uid="
new="""handoff=entry['proposed_handoff_point_mm'];carrier_region=connected.intersection(physical).difference(unary_union([Z.bounded_disk(v,.535) for v in nv]));carrier_parts=[q for q in K.pieces(carrier_region) if q.covers(Point(handoff)) and q.intersects(islandcore)];row['new_only_joint_signal_ground_carrier_components']=len(carrier_parts)
  if not carrier_parts:continue
  carrier_end=nearest_points(carrier_parts[0].intersection(islandcore),Point(handoff))[0];carrier_points,carrier_search=T.route(carrier_parts[0],tuple(handoff),tuple(carrier_end.coords)[0]);carrier_points=[[round(x,6),round(y,6)] for x,y in carrier_points];carrier=Z.bounded_buffer(LineString(carrier_points),.15);row['new_only_carrier']={'points_mm':carrier_points,'length_mm':LineString(carrier_points).length,'ground_width_mm':.30,'strict_original_DI13_and_power_legal_covers':legal.covers(carrier),'search':carrier_search}
  if not legal.covers(carrier):continue
  shape=island.union(unary_union(branches)).union(carrier);uid="""
assert old in s;s=s.replace(old,new)
old="gap=body.difference(refs['In1.Cu'].union(refs['In3.Cu']));shared=line.intersection(refs['In1.Cu'].buffer(-.110,quad_segs=128)).intersection(refs['In3.Cu'].buffer(-.110,quad_segs=128));pairproof=[]"
new="""physical_final=physical.difference(unary_union([Z.bounded_disk(v,.530) for v in nv]));entry_handoff=entry['proposed_handoff_point_mm'];exit_handoff=[129.043609356,109.208265565];signal_plan=[('In1.Cu',[119.835668,89.798413],entry_handoff),('In3.Cu',entry_handoff,exit_handoff),('In1.Cu',exit_handoff,[131.25,112.35])];signal_parts=[]
  for plane,pa,pb in signal_plan:
   allowed=physical_final.intersection(refs[plane].buffer(-.105,quad_segs=128));parts=[q for q in K.pieces(allowed) if q.covers(Point(pa)) and q.covers(Point(pb))];q={'actual_reference_layer':plane,'a_mm':pa,'b_mm':pb,'continuous_components':len(parts)};signal_parts.append(q)
   if not parts:break
   path,search=T.route(parts[0],tuple(pa),tuple(pb));path=[[round(x,6),round(y,6)] for x,y in path];routebody=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(path,path[1:])]);q.update({'points_mm':path,'length_mm':LineString(path).length,'strict_full_body_gap_mm2_before_endpoint_signal_holes':routebody.difference(refs[plane]).area,'search':search})
  row['explicit_In2_reference_assignment_parts']=signal_parts
  if len(signal_parts)!=3 or any('points_mm' not in q or q['strict_full_body_gap_mm2_before_endpoint_signal_holes']>0 for q in signal_parts):continue
  newpoints=signal_parts[0]['points_mm']+signal_parts[1]['points_mm'][1:]+signal_parts[2]['points_mm'][1:];body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(newpoints,newpoints[1:])]);gap=body.difference(refs['In1.Cu'].union(refs['In3.Cu']));shared=LineString(newpoints).intersection(refs['In1.Cu'].buffer(-.105,quad_segs=128)).intersection(refs['In3.Cu'].buffer(-.105,quad_segs=128));pairproof=[]"""
assert old in s;s=s.replace(old,new)
old="hand=nearest_points(shared,p)[0] if not shared.is_empty else Point();pairproof.append("
new="hand=Point(entry_handoff if len(pairproof)==0 else exit_handoff);pairproof.append("
assert old in s;s=s.replace(old,new)
s=s.replace("'points':saved['points']","'points':newpoints,'explicit_reference_parts':signal_parts")
s=s.replace("'actual_handoff_pairs':pairproof","'actual_handoff_pairs':pairproof,'new_mutual_return_pitch_mm':math.dist(pos,exit_at)")
s=s.replace("'potential_actual_In1_overlap_length_mm':overlap.length","'potential_actual_In1_source_handoff_area_mm2':overlap.area,'historical_R90_In2_physical_mask_is_nomination_only_current_full_independent_mask_required':True,'mutual_ordinary_return_pitch_minimum_mm':.815,'actual_In2_reference_assignments_required':True")
dst=H/'construct_DI15_moved_entry_reference_strip_r152.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI15-moved-entry-strip-r152.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'R150 only rooted a central strip from two too-close EXIT returns. R152 enforces .815mm mutual return pitch, chooses ENTRY in the actual source-side In2/In1 physical component instead of on the saved line, carries new signal/ground together through exact original DI13 and power-hard masks, and requires explicit In1/In3/In1 full-body assignment with distinct real entry/exit handoffs. Historical signal mask nomination only; final independent/native gates open.'},indent=1)+'\n');print(sha(dst.read_bytes()))
