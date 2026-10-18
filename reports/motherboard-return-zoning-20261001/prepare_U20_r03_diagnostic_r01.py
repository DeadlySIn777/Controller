from pathlib import Path
p=Path('reports/motherboard-return-zoning-20261001/diagnose_U20_r02_exact_union_r01.py');s=p.read_text().replace('ROOT94-health-U20-control-collars-r02','ROOT94-health-U20-control-collars-r03');Path('reports/motherboard-return-zoning-20261001/diagnose_U20_r03_exact_union_r01.py').write_text(s)
