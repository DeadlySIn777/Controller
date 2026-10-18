"""Exercise the local offline router only on the disconnected software fixture."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=Path(__file__).resolve().parent/'native-fixture-r05'
java=ROOT/'tmp/freerouting/runtime/jdk-25.0.4.1+1-jre/bin/java.exe';jar=ROOT/'tmp/freerouting/freerouting-2.4.1.jar'
args=[str(java),'-Djava.awt.headless=true','-jar',str(jar),'--user_data_path='+str(p/'router-user-data'),
 '--gui.enabled=false','--profile.allow_telemetry=false','--profile.allow_contact=false',
 '--usage_and_diagnostic_data.disable_analytics=true','-de',str(p/'prepared/selected.dsn'),'-do',str(p/'actual-router.ses'),'-mp','2','-mt','1']
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
(p/'router-argv.json').write_text(json.dumps(args,indent=2)+'\n')
r=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=45)
(p/'router.txt').write_text(r.stdout,encoding='utf8');(p/'router-errors.txt').write_text(r.stderr,encoding='utf8')
if r.returncode or not (p/'actual-router.ses').is_file():raise RuntimeError('Local fixture router failed')
if 'Unknown settings property' in r.stdout+r.stderr:raise RuntimeError('Offline/privacy settings not recognized')
cmd=['C:/Program Files/KiCad/10.0/bin/python.exe','-u',str(ROOT/'tools/hardware_route_selected_additive.py'),'import','--prepared',str(p/'prepared'),'--session',str(p/'actual-router.ses'),'--out',str(p/'actual-router-import')]
v=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=45)
(p/'native-import.txt').write_text(v.stdout+v.stderr,encoding='utf8')
if v.returncode:raise RuntimeError('Native additive fixture rejected')
(p/'router-fixture-receipt.json').write_text(json.dumps(dict(test_only=True,actual_local_autorouter_executed=True,
 no_controller_board_uploaded=True,live_PCB_or_source_mutated=False,jar_sha256=sha(jar),java_sha256=sha(java),selected_dsn_sha256=sha(p/'prepared/selected.dsn'),
 session_sha256=sha(p/'actual-router.ses'),router_exit_code=r.returncode,native_import_exit_code=v.returncode,
 native_acceptance_receipt='actual-router-import/receipt.json',router_advisories_not_suppressed=True,
 scope='Disconnected four-resistor software fixture. Netless retained obstacles cause router advisories; actual retained native geometry is independently DRC-checked.'),indent=2)+'\n')
print(v.stdout)
