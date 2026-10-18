"""Correct helper tuple contract; fixed C geometry is never normalized away."""
import json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
failed=p/'corrected-regulated-joint-search-base-r103'
if not (failed/'receipt.json').exists():(failed/'receipt.json').write_text(json.dumps({'verdict':'FAIL_ANALYTIC_TRACK_HELPER_RETURN_ARITY','exception':'normalize_owned_track_guards returns zones, ledger, geometry; caller expected two. No projected model/source receipt or board emitted.','source_file_sha256':hashlib.sha256((p/'compose_corrected_regulated_joint_base_r103.py').read_bytes()).hexdigest(),'native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8')
s=(p/'compose_corrected_regulated_joint_base_r103.py').read_text().replace("O=H/'corrected-regulated-joint-search-base-r103'","O=H/'corrected-regulated-joint-search-base-r106'")
s=s.replace("z,guards=P.normalize_owned_via_guards(h,updates+corrected);z,trackguards=TG.normalize_owned_track_guards(h,z);", "fixedC=[q for q in updates if q['uuid']=='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'];assert len(fixedC)==1;normalize=[q for q in updates+corrected if q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'];z,guards=P.normalize_owned_via_guards(h,normalize);z,trackguards,trackgeometry=TG.normalize_owned_track_guards(h,z);z+=fixedC;\n for uid,shapes in trackgeometry.items():\n  for kind,sh in shapes.items():(O/(uid+'.'+kind+'.wkb')).write_bytes(sh.wkb)\n ")
s=s.replace("print('R103", "print('R106")
exec(compile(s,str(p/'compose_corrected_regulated_joint_base_r103.py'),'exec'))
