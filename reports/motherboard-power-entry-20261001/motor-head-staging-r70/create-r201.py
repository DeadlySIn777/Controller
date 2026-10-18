from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-cell-r197.py').read_text().replace('ROOT94-health-U26-cell-r197','ROOT94-health-U26-cell-r201').replace('sv=(333,191.8);sg=(333,192.65)','sv=(332.5875,192.65);sg=(333.4375,192.65)')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-cell-r201.py').write_text(s)
