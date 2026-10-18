from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r576.py');t=p.read_text().replace('r576','r578').replace('if math.dist(q,c)>10:continue','if math.dist(q,c)>25:continue')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r578.py').write_text(t)
