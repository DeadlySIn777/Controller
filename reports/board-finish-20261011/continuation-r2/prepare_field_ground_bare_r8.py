"""Preserve the unaccepted R7 failure and skip empty exact source pockets."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'nominate_field_ground_bare_dogbones_r7.py';out=H/'nominate_field_ground_bare_dogbones_r8.py';r=H/'field-ground-bare-r8-derivation.json'
assert not out.exists()and not r.exists();s=p.read_text()
needle="def polys(s):return[s]if s.geom_type=='Polygon'else[q for q in getattr(s,'geoms',[])if q.geom_type=='Polygon']";assert s.count(needle)==1
s=s.replace(needle,"def polys(s):return[q for q in ([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[]))if q.geom_type=='Polygon'and not q.is_empty and q.area>1e-12]")
compile(s,str(out),'exec');out.write_text(s)
failed=H/'field-ground-bare-ordinary-nomination-r7';assert failed.exists()and not(failed/'proposed-discrete.pkl').exists()and not(failed/'receipt.json').exists()
(failed/'failure-receipt.json').write_text(json.dumps({'verdict':'PLANNER_EXCEPTION_BEFORE_ANY_ACCEPTED_DOGBONE','failed_script_sha256':sha(p),'stage':'source-only R78 plus snapshot4 projected; empty direct-source polygon passed to nearest_points','exception':'ValueError first input geometry empty','accepted_new_Cu':0,'native_jobs':0,'source_board_or_native_files_changed':False,'all_failed_output_preserved':True},indent=1)+'\n')
r.write_text(json.dumps({'prior_script_sha256':sha(p),'derived_script_sha256':sha(out),'failed_output_preserved':str(failed.resolve()),'change':'Exclude empty or zeroarea polygons before nearest point nomination; unchanged physical/source clearance gates and ordinary hole sizes','finite_nomination_failure_is_not_global_no_path_proof':True,'no_native_jobs_or_live_board_edits':True},indent=1)+'\n');print(json.dumps({'script':str(out),'sha256':sha(out)}))
