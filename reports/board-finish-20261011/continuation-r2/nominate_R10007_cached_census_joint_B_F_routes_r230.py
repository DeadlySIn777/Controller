"""Consume the completed, identical-offset R229 port census."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_R10007_joint_B_F_actual_source_routes_r228.py'
code=source.read_text().replace('r228','r230').replace('R228','R230').replace('screen-r227','screen-r229')
compile(code,str(source),'exec')
census=H/'R10007-HOST-existing-source-return-B-F-port-screen-r229/receipt.json'
assert census.is_file();read=json.loads(census.read_bytes());assert read['candidates'] and read['model_sha256']=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5'
receipt=H/'R10007-joint-route-r230-derivation.json';assert not receipt.exists()
receipt.write_text(json.dumps({'source_script_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'executed_script_sha256':hashlib.sha256(code.encode()).hexdigest(),'complete_port_census_sha256':hashlib.sha256(census.read_bytes()).hexdigest(),'only_revision_and_completed_census_path_changed':True,'native_jobs':0},indent=1)+'\n')
exec(compile(code,str(source),'exec'))
