"""One authorized original-API c7d8 load-only graph contrast. No native/route job."""
from pathlib import Path
import hashlib,json,sys,datetime
import psutil
HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if(p/'PROJECT_MEMORY.md').exists());RR=ROOT/'reports/board-finish-20261017/release-review';H=ROOT/'reports/board-finish-20261017/global-router-handoff-r1'
ME=psutil.Process();assert 23 in ME.cpu_affinity();ME.cpu_affinity([23]);ME.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
sys.path.insert(0,str(RR/'fresh-source-forward-pipeline-r2'));import execute_fresh_case_guarded as G
SDK=Path('C:/Users/Gluis/.codex/toolchains/controller-jdk25-20261018/sdk/jdk-25.0.4.1+1/bin');SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=HERE/'actual-c7d8-native-ordinary-query-r1';OUT.mkdir(exist_ok=False);G.OUT=OUT
overlay=HERE/'freerouting-2.4.1-electrical-query-optin-r1.jar';finite=HERE/'compiled-finite-r3/finite-qualification.json';bytecode=HERE/'compiled-bytecode-review.json';source=HERE/'NativeOrdinaryPartitionGate.java';dsn=H/'three-clamp-signal-route-first-r1/signal-route-first-cached-power-only.dsn';protected=dsn.parent/'protected-raw-nets.txt';ordinary=dsn.parent/'ordinary-raw-nets.txt';expected=RR/'fresh-native-source-catalog-r1/a210-rebind-r2/expected-native-ordinary-partitions.json'
assert SHA(overlay)=='97c26511ce5f3a53c9165298ce2a6417dcf5c5d8a5b50912660b8ea451af9050';assert SHA(dsn)=='c7d855916351128825d3d847375b776443fb72e93a71cd38f54167def9b48153';assert SHA(expected)=='83d6488064fb5eb8c590aecc807e8b398bb86d2772a7d5b72d4031c8cd20f507';assert json.loads(finite.read_text())['status'].startswith('PASS');assert json.loads(bytecode.read_text())['unchanged_methods'].__len__()==103
pins={str(p.resolve()):SHA(p)for p in(Path(__file__),source,overlay,finite,bytecode,dsn,protected,ordinary,expected,Path(G.__file__))};(OUT/'provenance.json').write_text(json.dumps({'scope':'ONE_NO_ROUTING_ORIGINAL_JAVA_LOAD_ONLY_ELECTRICAL_QUERY','input_SHA256':pins,'one_core':23,'statistics_memo_enabled':False,'router_runs':0,'native_workers':0,'adopted':False},indent=1)+'\n')
classes=OUT/'classes';classes.mkdir();G.guarded('JAVAC_ACTUAL_HELPER',[str(SDK/'javac.exe'),'-J-XX:ActiveProcessorCount=1','-encoding','UTF-8','-cp',str(overlay),'-d',str(classes),str(source)])
argv=[str(SDK/'java.exe'),'-XX:ActiveProcessorCount=1','-Xmx16g','-Djava.awt.headless=true','-Dfreerouting.stats.immutableRoutingOwner=false','-cp',str(classes)+';'+str(overlay),'NativeOrdinaryPartitionGate',str(dsn),str(protected),str(ordinary),str(expected),str(OUT/'result')]
G.guarded('ACTUAL_ORIGINAL_JAVA_LOAD_ONLY',argv);assert all(SHA(p)==h for p,h in pins.items());r=json.loads((OUT/'result/acceptance.json').read_text());r['input_SHA256']=pins;r['all_input_hashes_unchanged']=True;r['resource']=json.loads((OUT/'ACTUAL_ORIGINAL_JAVA_LOAD_ONLY-process.json').read_text());(OUT/'qualification.json').write_text(json.dumps(r,indent=1)+'\n');print(json.dumps(r))
