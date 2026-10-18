from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-local-r180.py').read_text().replace('ROOT94-health-U26-local-r180','ROOT94-health-U26-local-r182').replace('pv=(329.4,191);gv=(329.25,191.8)','pv=(329.2,191.2);gv=(329.25,192.0)')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-local-r182.py').write_text(s)
