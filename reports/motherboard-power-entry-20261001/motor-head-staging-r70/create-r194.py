from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r193.py').read_text().replace('ROOT94-health-U20-cell-r193','ROOT94-health-U20-cell-r194').replace('(347.6,173.635)','(347.6,172.9)').replace('(271.6,234.635)','(271.6,235.37)')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r194.py').write_text(s)
