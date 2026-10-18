from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r185.py').read_text().replace('ROOT94-health-U20-cell-r185','ROOT94-health-U20-cell-r186').replace('gv=(337.4125,174.15)','gv=(336.8,175.6)')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r186.py').write_text(s)
