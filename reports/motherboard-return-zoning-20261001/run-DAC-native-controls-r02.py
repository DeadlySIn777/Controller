import sys,json,subprocess
from pathlib import Path
out=Path('reports/motherboard-return-zoning-20261001/source26-r61-AO1-DAC-return-r04');dest=out/'motherboard-AO1-DAC-return-candidate.kicad_pcb';receipt=out/'receipt.json';tool=Path('reports/motherboard-return-zoning-20261001/prove-actual-DAC-anchor-native-r01.py');cases=[]
for case in('healthy','missing-return-via','wrong-domain-via','missing-GND5-branch','wrong-GND5-source-net'):
 run=subprocess.run(['C:/Program Files/KiCad/10.0/bin/python.exe','-X','utf8',str(tool),'--board',str(dest),'--receipt',str(receipt),'--case',case],capture_output=True,text=True);(out/('actual-native-'+case+'.txt')).write_text(run.stdout+run.stderr,encoding='utf-8')
 records=[json.loads(s)for s in run.stdout.splitlines()if s.startswith('{')];cases+=records
 if run.returncode or not records:raise ValueError('Actual native negative-control process failed: '+case)
(out/'actual-native-anchor-negative-controls.json').write_text(json.dumps(dict(passed=True,independent_native_processes=True,cases=cases),indent=2)+'\n');print(json.dumps(cases))
