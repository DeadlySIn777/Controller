from pathlib import Path
import json
p=Path('reports/motherboard-return-zoning-20261001/inspect-IO3-three-tip-DFM-proposal-r01.py')
q=p.with_name(p.name.replace('r01.py','r02.py'))
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace('IO3-three-tip-local-native-DFM-review-r01.json','IO3-three-tip-local-native-DFM-review-r02.json')
s=s.replace("if actual_nets!=[own]:raise ValueError('Exact integrated IO3 rail name changed')","if own not in actual_nets:raise ValueError('Exact integrated IO3 rail is absent')")
q.write_text(s)
p.with_suffix('.failure.json').write_text(json.dumps(dict(passed=False,reason='The exact literal /IO_3V3 rail exists; related EN, sense and switch nodes also contain the substring. The first preflight wrongly required a substring inventory to contain only the rail. No output or mutation occurred.'),indent=2))
