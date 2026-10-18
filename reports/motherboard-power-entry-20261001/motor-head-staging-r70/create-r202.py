from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r200.py').read_text().replace('ROOT94-health-U20-cell-r200','ROOT94-health-U20-cell-r202')
s=s.replace("ret-={'8b76be20", "hh=json.loads(Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json').read_text());ret|={r['uuid']for r in hh['exact_added_copper']if r['role']=='C11079_actual_CORE_source'}\nret-={'8b76be20")
s=s.replace("route(mm(ps['U11020','5'].GetPosition()),(345.3375,175),pg,pcbnew.F_Cu,'U11020_actual_CORE_source_reconnection',.3)","route(pv,mm(ps['C11078','1'].GetPosition()),pg,pcbnew.B_Cu,'U11020_actual_CORE_source_from_C11078',.3)")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r202.py').write_text(s)
