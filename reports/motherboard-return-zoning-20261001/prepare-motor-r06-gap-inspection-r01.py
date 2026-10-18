from pathlib import Path
p=Path('reports/motherboard-return-zoning-20261001/inspect-motor-r05-two-control-gaps-r01.py');q=p.with_name('inspect-motor-r06-one-control-gap-r01.py')
if q.exists():raise ValueError('Immutable inspection revision exists')
s=p.read_text().replace('motor-bank-A-r128-logic-reference-collars-r05','motor-bank-A-r138-logic-reference-collars-r06').replace('motor-bank-A-reference-ready-r129','motor-bank-A-reference-ready-r141').replace('motor-bank-A-r05-two-control-gap-inspection-r01.json','motor-bank-A-r06-one-control-gap-inspection-r01.json');q.write_text(s)
