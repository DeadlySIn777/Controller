from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r560.py');t=p.read_text();t=t.replace('r560','r562').replace("at=child(x,'at');at[3]='180'if r=='C11091'else'0'","at=child(x,'at');at.append('180'if r=='C11091'else'0')if len(at)==3 else at.__setitem__(3,'180'if r=='C11091'else'0')")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r562.py').write_text(t)
