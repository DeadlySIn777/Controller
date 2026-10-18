"""Render exact local native-bound copper and source-return geometry for inspection."""
import json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
from shapely import from_wkb
from shapely.geometry import Point
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
d=H/'field-health-local-context-r37';r=json.loads((d/'inventory.json').read_bytes());fig,ax=plt.subplots(figsize=(10,8));source=from_wkb((d/'In1.Cu-actual-J3-source-local.wkb').read_bytes())
def draw(s,color,alpha):
 for p in ([s]if s.geom_type=='Polygon'else getattr(s,'geoms',[])):
  if p.geom_type=='Polygon'and not p.is_empty:ax.add_patch(Patch(list(p.exterior.coords),facecolor=color,edgecolor=color,alpha=alpha))
draw(source,'#88bbee',.35)
for t in r['tracks']:
 col='#e35d23'if '/FIELD_HEALTH_B_N'in t['net']else('#b833b8'if 'AO1_MON_12V'in t['net']else'#666666');draw(C.body(t),col,.7)
for p in r['pads']:
 col='#168045'if 'FIELD_GND'in p['net']else'#555555'
 for s in C.poly(p['layers'].get('F.Cu',[])):draw(s,col,.65)
 if p['ref']=='U11025':ax.text(p['x'],p['y']+.09,p['num'],fontsize=9,ha='center',color='black')
for v in r['vias']:draw(Point(v['x'],v['y']).buffer(v['d']/2), '#333333',.8)
ax.plot([311.8315,313.05,311.8315],[155.408,154.558,153.708],color='#f22b16',linestyle='--',label='Possible health detour; unverified')
ax.scatter([312.0],[154.558],marker='x',s=100,color='#128b32',label='Possible .5/.2 ground via; unverified')
ax.set_xlim(309,314.5);ax.set_ylim(152.5,156.6);ax.invert_yaxis();ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(loc='lower left');ax.set_title('U11025 local routing: actual F copper; blue = J3-rooted In1 return\nExploratory geometry only; no board change');ax.set_xlabel('mm');ax.set_ylabel('mm');fig.tight_layout();out=H/'field-health-local-r38.png';assert not out.exists();fig.savefig(out,dpi=150);print(str(out))
