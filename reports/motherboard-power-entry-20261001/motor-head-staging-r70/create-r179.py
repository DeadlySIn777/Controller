from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r177.py').read_text().replace('ROOT94-health-U20-cell-r177','ROOT94-health-U20-cell-r179').replace('xy((340,175))','xy((339,175))').replace('xy((340.8375,174.225))','xy((339.8375,174.225))').replace('pv=(341.7375,175);gv=(341.1375,174.4);og=(338.4125,175)','pv=(340.5875,175);gv=(341.1875,175.6);og=(337.4125,175)')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r179.py').write_text(s)
