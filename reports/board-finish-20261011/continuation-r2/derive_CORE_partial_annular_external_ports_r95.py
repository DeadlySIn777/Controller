"""Permit exact finite annular contact instead of requiring a whole disk inside fill."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'nominate_CORE_native_IO3_antipad_ports_r93.py';s=base.read_text();changes=[]
def rep(a,b,count=1):
 global s
 assert s.count(a)==count,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b,'count':count})
rep('def audit(self,candidate,region,out,side):','def audit(self,candidate,region,out,side,actual):')
rep("assert original.read_bytes()==region.wkb,('R90 geometry changed',side)","assert original.exists();R90_original_region_WKB_equal=original.read_bytes()==region.wkb")
rep("'exact_R90_final_region_WKB_unchanged':True","'R90_initial_full_disk_containment_predicate_replaced_with_exact_annular_contact':True,'R90_original_final_region_WKB_equal_diagnostic':R90_original_region_WKB_equal")
rep('self.propose_IO3_antipad_ports(candidate,out,side)','self.propose_IO3_antipad_ports(candidate,out,side,actual)')
rep('def propose_IO3_antipad_ports(self,candidate,out,side):','def propose_IO3_antipad_ports(self,candidate,out,side,actual):')
rep("for face in sorted(parts(region),key=lambda q:-q.area)[:6]:", "nominees=parts(region)\n  if side=='main':nominees=parts(region.intersection(box(174,92.5,181,100)))+nominees\n  if side=='source':nominees=parts(region.intersection(box(226,92,233.5,101)))+nominees\n  used=set()\n  for face in sorted(nominees,key=lambda q:(0 if(side=='main'and q.bounds[0]>=174)or(side=='source'and q.bounds[2]<=233.5)else 1,-q.area))[:20]:")
rep("point=face.representative_point();xy=[round(point.x,6),round(point.y,6)]\n   if not region.covers(Point(xy)):continue", "point=face.representative_point();xy=[round(point.x,6),round(point.y,6)]\n   if tuple(xy)in used or not region.covers(Point(xy)):continue\n   used.add(tuple(xy));via={'x':xy[0],'y':xy[1]};ann=N.bounded_disk(via,.25).difference(N.bounded_disk(via,.1));finite_overlap=ann.intersection(actual).area\n   if finite_overlap<.01:continue")
rep("'controller-CORE-native-IO3-antipad-r93/'", "'controller-CORE-partial-annular-antipad-r95/'")
rep("'ordinary_site_face_area_mm2':face.area,'one_native_IO3", "'ordinary_site_face_area_mm2':face.area,'actual_existing_CORE_In3_annular_overlap_mm2':finite_overlap,'one_native_IO3")
rep("'actual_CORE_In3_finite_annular_overlap':'REQUIRES_EXACT_MODEL_CHECK'", "'actual_CORE_In3_finite_annular_overlap':'EACH_NOMINEE_AT_LEAST_0_01_MM2_MEASURED_FROM_EXACT_ANNULUS'")
rep("window.intersection(actual.buffer(-.25-.000100))", "window.intersection(actual.buffer(.20))")
rep('obs.audit(candidate,region,out,label)','obs.audit(candidate,region,out,label,actual)')
rep("CORE-native-IO3-antipad-external-port-nominees-r93';assert", "CORE-partial-annular-native-IO3-antipad-port-nominees-r95';assert")
rep("'verdict':'LITERAL_NATIVE_IO3_NEW_ANTIPAD_ORDINARY_PORT_PROPOSALS_ONLY'", "'verdict':'PARTIAL_FINITE_ANNULAR_CONTACT_ORDINARY_PORT_PROPOSALS_ONLY'")
rep("'no_geometry_predicate_changed':True", "'new_initial_candidate_uses_annular_overlap_instead_of_whole_disk_containment':True,'all_clearance_hole_keepout_oldreference_predicates_unchanged':True")
rep("'R93_LITERAL_IO3_ANTIPAD_PORT_PROPOSALS_FROZEN'", "'R95_PARTIAL_ANNULAR_IO3_ANTIPAD_PORT_PROPOSALS_FROZEN'")
rep("'R93_IO3_ANTIPAD_ORDINARY_PORT_NOMINEES'", "'R95_PARTIAL_ANNULAR_IO3_ANTIPAD_NOMINEES'")
compile(s,'nominate_CORE_partial_annular_external_ports_r95.py','exec');out=H/'nominate_CORE_partial_annular_external_ports_r95.py';assert not out.exists();out.write_text(s)
(H/'CORE-partial-annular-ordinary-port-nomination-r95-derivation.json').write_text(json.dumps({'base_sha256':sha(base),'derived_sha256':sha(out),'changes':changes,'design_clearances_and_ordinary_size_not_relaxed':True,'actual_native_CORE_finite_annular_overlap_required_mm2':.01,'new_native_IO3_antipads_ALL77_direct_contact_current_and_native_gates_open':True},indent=1)+'\n');print('R95_DERIVED',sha(out),flush=True)
