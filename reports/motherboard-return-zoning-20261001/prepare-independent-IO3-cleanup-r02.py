from pathlib import Path
import json
p=Path('reports/motherboard-return-zoning-20261001/review-IO3-literal-tip-cleanup-independent-r01.py')
q=p.with_name(p.name.replace('r01.py','r02.py'))
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace("rule.GetLayerSet().Seq()==[pcbnew.In2_Cu]","list(rule.GetLayerSet().Seq())==[pcbnew.In2_Cu]").replace("IO3-literal-tip-cleanup-independent-r01'","IO3-literal-tip-cleanup-independent-r02'")
q.write_text(s)
Path('reports/motherboard-return-zoning-20261001/IO3-literal-tip-cleanup-independent-r01/failure.json').write_text(json.dumps(dict(passed=False,reason='SWIG LAYER_SEQ requires explicit list conversion for exact-layer equality; no board/copper mutation occurred.'),indent=2))
