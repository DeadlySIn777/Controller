"""Rasterize the source-data diagnostic with the standard plotting runtime."""
from pathlib import Path
source=Path(__file__).with_name('render_R10007_actual_source_reference_local_r231.py')
code=source.read_text().replace('diagnostic-r231','diagnostic-r232')
at=code.index("for layer,inner,xoff in");end=code.index("parts.append('<text x=\"35\"",at)
exec(compile(code[:at],str(source),'exec'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
from shapely.geometry.polygon import orient
fig,axs=plt.subplots(1,2,figsize=(14,7))
def path(s,xoff,color,opacity=1):
 ax=axs[0 if xoff==35 else 1]
 for p in K.RF.parts(s):
  p=orient(p,sign=1);verts=[];codes=[]
  for ring in [p.exterior,*p.interiors]:
   xy=list(ring.coords);verts.extend(xy);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY])
  ax.add_patch(PathPatch(MPath(verts,codes),facecolor=color,edgecolor='none',alpha=opacity))
exec(compile(code[at:end],str(source),'exec'))
for ax,layer in zip(axs,['F.Cu / actual In1 J1 source','B.Cu / actual In4 J1 source']):
 ax.set(xlim=(198,222),ylim=(150,126),aspect='equal',title=layer,xlabel='X mm',ylabel='Y mm');ax.grid(alpha=.12)
fig.suptitle('R10007 actual source/reference diagnostic: proposed pose only, no board adoption')
fig.text(.5,.02,'Pale green: actual J1 source fill. Magenta: HOST. Blue: LOGIC_GND. Gold: FIELD_GND. Gray: other native Cu.',ha='center')
png=OUT/'actual-source-reference.png';fig.savefig(png,dpi=150,bbox_inches='tight');plt.close(fig)
(OUT/'receipt.json').write_text(json.dumps({'model_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'plot_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'source_geometry_same_as_R231':True,'adopted':False},indent=1)+'\n');print(png.resolve(),flush=True)
