from pathlib import Path
import json
p=Path('reports/motherboard-return-zoning-20261001/review-IO3-literal-tip-cleanup-independent-r04.py');q=p.with_name(p.name.replace('r04.py','r05.py'))
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace('and211.075','and 211.075').replace("IO3-literal-tip-cleanup-independent-r04'","IO3-literal-tip-cleanup-independent-r05'");q.write_text(s)
p.with_suffix('.failure.json').write_text(json.dumps(dict(passed=False,reason='Syntax-only missing space after and before numeric literal; no reviewer executed and no geometry mutated.'),indent=2))
