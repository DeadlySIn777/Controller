"""Preserve the empty-geometry failed nomination and filter only empty faces."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;s=H/'nominate_field_ground_owned_antipads_r24.py';o=H/'nominate_field_ground_owned_antipads_r26.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old="def polys(sh):return [sh]if sh.geom_type=='Polygon'else[q for q in getattr(sh,'geoms',[])if q.geom_type=='Polygon'and not q.is_empty]"
new="def polys(sh):return[q for q in ([sh]if sh.geom_type=='Polygon'else getattr(sh,'geoms',[]))if q.geom_type=='Polygon'and not q.is_empty and q.area>1e-12]"
text=s.read_text();assert text.count(old)==1 and not o.exists();text=text.replace(old,new).replace('controller-ground-bare-r24/','controller-ground-bare-r26/');compile(text,str(o),'exec');o.write_text(text)
failure=H/'field-ground-owned-antipads-r24/interrupted-before-nomination.json';assert not failure.exists();failure.write_text(json.dumps({'verdict':'FAILED_EMPTY_POLYGON_PASSED_TO_NEAREST_POINTS','exit_code':1,'phase':'first_U11025_candidate_face_enumeration','any_accepted_nominee':False,'board_written':False,'source_script_sha256':sha(s),'original_all_actual_geometry_clearance_and_planning_inputs_unchanged':True},indent=1)+'\n')
(H/'field-bare-empty-safe-r26-derivation.json').write_text(json.dumps({'source_script_sha256':sha(s),'derived_script_sha256':sha(o),'only_empty_degenerate_area_faces_filtered_and_fresh_UUID_seed':True,'all_actual_source_geometry_native_clearance_barrier_Cu_hole_pad_and_NEW_only_cut_gates_unchanged':True,'native_jobs':0,'board_written':False},indent=1)+'\n');print(sha(o))
