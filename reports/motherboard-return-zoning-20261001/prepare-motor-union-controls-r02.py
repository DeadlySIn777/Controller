from pathlib import Path
import json
p=Path('reports/motherboard-return-zoning-20261001/test_motor_exact_endpoint_antipad_union_r01.py');q=p.with_name(p.name.replace('r01.py','r02.py'))
if q.exists():raise ValueError('Immutable controls revision exists')
s=p.read_text().replace('import sys,json,copy','import sys,json,copy,subprocess').replace("motor-exact-antipad-union-native-controls-r01'","motor-exact-antipad-union-native-controls-r02'")
needle="try:run(pcbnew.LoadBoard(str(p)),row)\n except ValueError as error:controls.append(dict(name=name,path=str(p),sha256=sha(p),rejected=True,reason=str(error)));return\n raise ValueError('Actual native negative unexpectedly accepted '+name)"
replacement="""declaration=out/(name+'-declaration.json');write(declaration,row)
 helper=Path(__file__).with_name('check_motor_pg_negative_fresh_process_r01.py')
 result=subprocess.run([sys.executable,str(helper),str(p),str(declaration)],capture_output=True,text=True)
 (out/(name+'-command.txt')).write_text(result.stdout+result.stderr)
 if result.returncode:raise ValueError('Actual native negative process failed '+name)
 parsed=json.loads(result.stdout.strip().splitlines()[-1])
 if not parsed['rejected']:raise ValueError('Actual native negative unexpectedly accepted '+name)
 controls.append(dict(name=name,path=str(p),sha256=sha(p),rejected=True,reason=parsed['reason'],fresh_native_process=True))"""
if needle not in s:raise ValueError('Exact negative runner drift')
q.write_text(s.replace(needle,replacement))
Path('reports/motherboard-return-zoning-20261001/motor-exact-antipad-union-native-controls-r01/failure.json').write_text(json.dumps(dict(passed=False,reason='Inline second LoadBoard produced a transient SwigPyObject rather than BOARD in the loaded process; the persisted board loads correctly in a fresh native process. All82 positive controls passed before that API failure; negatives rerun in independent processes.'),indent=2))
