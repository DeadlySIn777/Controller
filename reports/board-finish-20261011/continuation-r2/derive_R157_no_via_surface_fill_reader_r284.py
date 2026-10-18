"""Preserve the failed fill reader and correct only native zone attribution."""
import hashlib,json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'nominate_R157_two_actual_no_via_surface_signal_bridges_r283.py';target=H/'nominate_R157_two_actual_no_via_surface_signal_bridges_r284.py';assert not target.exists();out=H/'R157-two-actual-no-via-surface-signal-bridge-constructive-screen-r283';assert out.exists()and not(out/'only-constructively-cleared-no-via-new-surface-tracks-NOT_MODEL.pkl').exists()
failure=out/'failure.json';assert not failure.exists();failure.write_text(json.dumps({'stage':'FILL_RECORD_LOCAL_CLEARANCE_READER','exception':'KeyError: source','source_file_SHA256':sha(source),'no_routes_or_model_emitted':True,'native_inputs_not_changed':True,'adopted':False},indent=1)+'\n')
code=source.read_text();assert code.count("r['source'].get('clearance_mm',0)")==2 and code.count("dom=h['domains_normalized'];attempts=[]")==1
code=code.replace("r['source'].get('clearance_mm',0)","owners[r['uuid']].get('clearance_mm',0)").replace("dom=h['domains_normalized'];attempts=[]","dom=h['domains_normalized'];owners={z['uuid']:z for z in actual['zones']};attempts=[]").replace('r283','r284').replace('R283','R284');compile(code,str(target),'exec');target.write_text(code)
receipt=H/'R284-native-fill-local-clearance-reader-derivation.json';assert not receipt.exists();receipt.write_text(json.dumps({'source_file':str(source),'source_SHA256':sha(source),'new_file':str(target),'new_SHA256':sha(target),'only_reader_and_fresh_output_namespace_changes':True,'native_zone_UUID_binds_clearance':True,'geometry_rules_source_holes_routes_UNCHANGED':True,'native_jobs':0,'adopted':False},indent=1)+'\n');raise SystemExit(subprocess.call([sys.executable,str(H/'launch_confined_host.py'),str(target)]))
