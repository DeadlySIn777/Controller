from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/motherboard-ordinary-routing-20261001/actual-source26-root62-r01'
JAVA=ROOT/'tmp/freerouting/runtime/jdk-25.0.4.1+1-jre/bin/java.exe'
JAR=ROOT/'tmp/freerouting/freerouting-2.4.1.jar'
DSN=OUT/'prepared/selected.dsn'
SESSION=OUT/'actual-router.ses'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
cmd=[str(JAVA),'-jar',str(JAR),'-de',str(DSN),'-do',str(SESSION),'-mp','6','-mt','1','-da']
with (OUT/'actual-router.log').open('w',encoding='utf8')as log:
 result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
(OUT/'solver.json').write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,dsn_sha256=sha(DSN),session_sha256=sha(SESSION)if SESSION.is_file()else None,
 no_route_adopted=True,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(exit_code=result.returncode,session_exists=SESSION.is_file(),log=str(OUT/'actual-router.log'))))
