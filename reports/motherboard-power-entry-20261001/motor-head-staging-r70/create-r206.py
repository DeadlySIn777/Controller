from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-cell-r204.py').read_text().replace('ROOT94-health-U26-cell-r204','ROOT94-health-U26-cell-r206').replace("route(pv,(332.5875,191),pg,pcbnew.B_Cu,'U11026_actual_field_supply_from_U11025',.25)","route(pv,mm(ps['C11080','1'].GetPosition()),pg,pcbnew.B_Cu,'U11026_actual_field_supply_from_C11080',.25)")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-cell-r206.py').write_text(s)
