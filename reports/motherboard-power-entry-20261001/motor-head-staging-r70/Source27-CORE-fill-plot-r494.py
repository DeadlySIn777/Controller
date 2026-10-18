import json
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle
P=Path('reports/motherboard-power-entry-20261001/Source27-CORE-fill-inspection-r494');d=json.loads((P/'geometry.json').read_text());fig,axs=plt.subplots(1,2,figsize=(16,8))
for ax,r in zip(axs,d['Core5_fills']):
 for i,p in enumerate(r['fills']):
  ax.add_patch(Polygon(p['outer'],facecolor=['#e2bb45','#93cbe0'][i%2],edgecolor='black',lw=.5))
  for h in p['holes']:ax.add_patch(Polygon(h,facecolor='white',edgecolor='black',lw=.3))
 for v in d['new_actual_barrels']:
  x,y=v['position_mm'];ax.add_patch(Circle((x,y),.4,fill=False,color='red',lw=1));ax.text(x+.3,y-.3,v['uuid'][:6],fontsize=6,color='darkred')
 ax.set_xlim(249,280);ax.set_ylim(169,137);ax.set_aspect('equal');ax.set_title(r['name']);ax.grid(alpha=.3)
fig.tight_layout();fig.savefig(P/'actual-core-fill-comparison.png',dpi=140)
