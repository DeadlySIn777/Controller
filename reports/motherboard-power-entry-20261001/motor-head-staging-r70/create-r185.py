from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r184.py').read_text().replace('ROOT94-health-U20-cell-r184','ROOT94-health-U20-cell-r185')
s=s.replace("fs['U11020'].SetPosition(xy((339,175)));fs['C11079'].SetPosition(xy((339.8375,174.225)))","fs['U11020'].SetPosition(xy((339,175)));fs['U11020'].SetOrientationDegrees(180);fs['C11079'].SetPosition(xy((338.1625,174.225)))")
s=s.replace('pv=(340.5875,175);gv=(341.1875,175.6);og=(337.4125,175)','pv=(337.4125,175);gv=(337.4125,174.15);og=(340.5875,175)')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r185.py').write_text(s)
