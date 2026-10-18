"""Actual local Freerouting run against frozen prepared DSN; never adopts PCB."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time
root=Path.cwd();ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--passes',type=int,default=4);a=ap.parse_args()
prepared=a.prepared.resolve();out=a.out.resolve();assert out.is_relative_to(root/'reports')and not out.exists();out.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
java=root/'tmp/freerouting/runtime/jdk-25.0.4.1+1-jre/bin/java.exe';jar=root/'tmp/freerouting/freerouting-2.4.1.jar'
assert sha(jar)=='251101c3eeac22d7e7dfcf6796603279e5d1000283eb82d8f093780f7afc6aa9'
prep=json.loads((prepared/'prepare.json').read_text());assert prep['manufacturing_ready']is False and prep['selection']['selected_nets']
assert sha(prepared/'selected.dsn')==prep['selected_dsn_sha256']
inputs={str(p):sha(p)for p in [prepared/'prepare.json',prepared/'selected.dsn',prepared/'native.dsn',prepared/'base.kicad_pcb',prepared/'manifest.json',java,jar,Path(__file__)]}
user=out/'router-user-data';user.mkdir()
config={'profile':{'allow_telemetry':False,'allow_contact':False},'gui':{'enabled':False},'usage_and_diagnostic_data':{'disable_analytics':True},'api_server':{'enabled':False},'mcp_server':{'enabled':False},'feature_flags':{'save_jobs':False,'multi_threading':False},'router':{'strict_drc':True,'automatic_neckdown':False,'neck_width_um':0,'copper_to_edge_clearance_um':500,'hole_clearance_um':250,'fanout':{'enabled':True},'optimizer':{'enabled':False}},'logging':{'file':{'enabled':False}}}
(user/'freerouting.json').write_text(json.dumps(config,indent=2)+'\n');initial_config=sha(user/'freerouting.json')
session=out/'actual-router.ses';cmd=[str(java),'-Xmx4g','-jar',str(jar),'-de',str(prepared/'selected.dsn'),'-do',str(session),'-mp',str(a.passes),'-mt','0','-da','--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','--user_data_path='+str(user),'--router.strict_drc=true','--router.automatic_neckdown=false','--router.neck_width_um=0','--router.copper_to_edge_clearance_um=500','--router.hole_clearance_um=250']
(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n');started=time.monotonic();error=None;code=None
try:
 with(out/'router.log').open('wb')as log:code=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=900).returncode
except Exception as exc:error=repr(exc)
unchanged=all(sha(Path(k))==v for k,v in inputs.items());log=(out/'router.log').read_text(errors='replace');unrecognized=any(s in log for s in ('Unknown command line argument','problem parsing the'))
r={'passed':code==0 and error is None and unchanged and session.is_file()and not unrecognized,'error':error,'exit_code':code,'seconds':time.monotonic()-started,'inputs_unchanged':unchanged,'input_sha256':inputs,'initial_configuration_sha256':initial_config,'selected_nets':prep['selection']['selected_nets'],'session_sha256':sha(session)if session.is_file()else None,'unrecognized_arguments':unrecognized,'original_board_changed':False,'native_reimport_or_validation_complete':False,'manufacturing_ready':False}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if r['passed']else 1)
