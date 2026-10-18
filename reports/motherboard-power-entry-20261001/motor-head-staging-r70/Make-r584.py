from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-closer-bypass-native-proof-r574.py');t=p.read_text().replace('r574','r584').replace('r572','r582');Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-closer-bypass-native-proof-r584.py').write_text(t)
