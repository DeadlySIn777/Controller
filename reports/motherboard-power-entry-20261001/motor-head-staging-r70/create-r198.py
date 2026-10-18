from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r196.py').read_text().replace('ROOT94-health-U20-cell-r196','ROOT94-health-U20-cell-r198').replace('for d in[.75,1.,1.25,1.5,2.,2.5]:','for d in[.75,1.,1.25,1.5,2.,2.5,3.,4.,5.,6.,8.,10.]:')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r198.py').write_text(s)
