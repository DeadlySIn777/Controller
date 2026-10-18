from pathlib import Path
p=Path('reports/motherboard-return-zoning-20261001/inspect-motor-r04-six-control-gaps-r01.py')
q=p.with_name('inspect-motor-r05-two-control-gaps-r01.py')
if q.exists():raise ValueError('Immutable inspection revision exists')
s=p.read_text().replace('motor-bank-A-r120-logic-reference-collars-r04','motor-bank-A-r128-logic-reference-collars-r05').replace('motor-bank-A-reference-ready-r121','motor-bank-A-reference-ready-r129').replace('actual82-control-segment-reference-reviews.json','actual-control-segment-reference-reviews.json').replace('motor-bank-A-r04-six-control-gap-inspection-r01.json','motor-bank-A-r05-two-control-gap-inspection-r01.json')
q.write_text(s)
