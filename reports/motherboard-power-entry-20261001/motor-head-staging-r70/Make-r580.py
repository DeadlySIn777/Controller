from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r578.py');t=p.read_text().replace('r578','r580')
t=t.replace("assert choices,('No actual own-domain Ground Source anchor',key,a);", "\n if not choices:\n  debug();print('GROUND_ORIGINAL',len(ground_original),'closest',sorted([(math.dist(a,mm(v.GetPosition())),mm(v.GetPosition()))for v in ground_original])[:8],flush=True)\n assert choices,('No actual own-domain Ground Source anchor',key,a);")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r580.py').write_text(t)
