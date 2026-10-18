from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r198.py').read_text().replace('ROOT94-health-U20-cell-r198','ROOT94-health-U20-cell-r200').replace("and g.clear([contact,z],n,pcbnew.F_Cu,.2):candidates.append(z)","and any(g.clear(path,n,pcbnew.F_Cu,.2)for path in paths(contact,z)):candidates.append(z)")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r200.py').write_text(s)
