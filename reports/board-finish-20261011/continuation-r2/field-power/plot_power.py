import json,pickle,hashlib
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from shapely.ops import unary_union
from shapely.geometry import Point
from contact_layout import HERE,load,poly
from inventory import sha
b=json.loads((HERE/'power-groups-r1-binding.json').read_text(encoding='utf-8'));raw=(HERE/'power-groups-r1.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==b['cache_sha256'];groups=pickle.loads(raw);r=json.loads((HERE/'power-groups-r1.json').read_text(encoding='utf-8'));g,_=load()
fig,ax=plt.subplots(2,1,figsize=(16,15))
for a,(net,layer) in zip(ax,[('FBG','In1.Cu'),('FAG','In1.Cu')]):
 for i,xs in enumerate(groups[net]):
  fills=[x['shape'] for x in xs if x['kind']=='fill' and x['layer']==layer];root=i==r['nets'][net]['source_root_group'];sh=unary_union(fills)
  for p in ([sh] if sh.geom_type=='Polygon' else getattr(sh,'geoms',[])):
   if p.is_empty:continue
   xx,yy=p.exterior.xy;a.fill(xx,yy,color='seagreen' if root else 'goldenrod',alpha=.35);a.plot(xx,yy,color='seagreen' if root else 'goldenrod',linewidth=.5)
  if not sh.is_empty and sh.area>40:
   pt=sh.representative_point();a.text(pt.x,pt.y,str(i)+(' ROOT' if root else ''),fontsize=8)
 for p in g['pads']:
  if (p['ref'],p['num']) in [('J11003','2'),('J11005','2'),('U11018','9'),('U19028','7')]:a.plot(p['x'],p['y'],'ko');a.text(p['x']+2,p['y'],p['ref']+'.'+p['num'],fontsize=9)
 a.plot(80,206,'r+');a.text(82,206,'new U11038',fontsize=9,color='red')
 for sh in poly(g['outline']):xx,yy=sh.exterior.xy;a.plot(xx,yy,color='black',linewidth=1)
 a.set_aspect('equal');a.invert_yaxis();a.set_title(net+' fresh In1 copper: green source-rooted, yellow isolated; labels = physical group IDs');a.set_xlabel('mm');a.set_ylabel('mm');a.grid(alpha=.15)
fig.tight_layout();fig.savefig(HERE/'source-rooted-field-planes-r1.png',dpi=140)
