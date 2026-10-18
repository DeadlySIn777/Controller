"""Repair r20's local candidate-list name collision; retain its failed output."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'assess_real48pad_FG_group_and_stitch_electrodes_r20.py').read_text().replace("'actual48-FG-floor-and-bridge-electrodes-r20'","'actual48-FG-floor-and-bridge-electrodes-r21'")
s=s.replace(';layer=[]',';cands=[]').replace('layer.append(','cands.append(').replace('layer.sort(','cands.sort(').replace('candidates.extend(layer[:40])','candidates.extend(cands[:40])').replace("'best_real_Cu_electrodes':layer[:4]","'best_real_Cu_electrodes':cands[:4]")
exec(compile(s,str(HERE/'assess_real48pad_FG_group_and_stitch_electrodes_r20.py'),'exec'),globals())
