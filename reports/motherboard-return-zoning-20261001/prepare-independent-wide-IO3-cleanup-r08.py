from pathlib import Path
p=Path('reports/motherboard-return-zoning-20261001/review-IO3-literal-tip-cleanup-independent-r03.py');q=p.with_name('review-IO3-literal-tip-cleanup-independent-r08.py')
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace("IO3-literal-unused-tip-cleanup-r01'","IO3-literal-unused-tip-cleanup-r02'").replace("IO3-literal-tip-cleanup-independent-r03'","IO3-literal-tip-cleanup-independent-r08'").replace('[91.05,211.075,91.225,211.325]','[90.3,210.25,91.75,212.025]')
q.write_text(s)
