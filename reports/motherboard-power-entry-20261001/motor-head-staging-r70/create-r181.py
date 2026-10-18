from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r179.py').read_text().replace('ROOT94-health-U20-cell-r179','ROOT94-health-U20-cell-r181')
s=s.replace("[('5',(345.3375,175)),('1',(343.8625,174.35)),('3',(343.1625,176.65)),('4',(346.85,175.65)),('6',(344.85,174.135))]","[('1',(343.8625,174.35)),('3',(343.1625,176.65)),('4',(346.85,175.65)),('6',(344.85,174.135)),('5',(345.3375,175))]")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r181.py').write_text(s)
