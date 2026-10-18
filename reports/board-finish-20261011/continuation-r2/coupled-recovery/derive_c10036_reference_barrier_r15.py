"""Preserve exact constructor and render its local reference obstruction."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_power_return_r13.py').read_text().replace('c10036-power-paired-return-recipe-r13.json','c10036-reference-barrier-r15.json')
insert=r'''
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Polygon as Patch
 fig,ax=plt.subplots(figsize=(11,10));vw=box(63.5,92.3,68.2,96.4)
 def draw(sh,color,alpha=.6):
  for p in pieces(sh.intersection(vw)):
   ax.add_patch(Patch(list(p.exterior.coords),facecolor=color,edgecolor=color,alpha=alpha))
   for rr in p.interiors:ax.add_patch(Patch(list(rr.coords),facecolor='white',edgecolor='white',alpha=1))
 draw(planes['In4.Cu'],'#d3e8d4',1);draw(unary_union(obstacles),'#da7c6a',.5);draw(strictlegal.buffer(-.156),'#5a9863',.5)
 for q in g['vias']:
  if Point(q['x'],q['y']).intersects(vw):
   ax.plot(q['x'],q['y'],'o',color='#aa00aa',markersize=4);ax.text(q['x']+.02,q['y']-.04,L.norm(q['net']).split('/')[-1],fontsize=7)
 ax.plot(returnxy[0],returnxy[1],'o',color='blue');ax.text(returnxy[0]+.02,returnxy[1]-.08,'proposed GND return',fontsize=8)
 ax.plot([x[0] for x in(old['a'],old['b'])],[x[1] for x in(old['a'],old['b'])],color='black',linewidth=2,label='old power .3mm')
 if nomination:ax.plot([p[0] for p in nomination['points_mm']],[p[1] for p in nomination['points_mm']],color='blue',linewidth=2,label='physical-only nomination')
 ax.set_xlim(63.5,68.2);ax.set_ylim(96.4,92.3);ax.set_aspect('equal');ax.grid();ax.legend();ax.set_title('C10036 coupled B power route: green rooted In4, red blockers, dark green centre clearance');fig.savefig(HERE/'c10036-reference-barrier-r15.png',dpi=170);plt.close(fig)
 report['strict_components']=[{'area_mm2':p.area,'bounds':p.bounds,'start_distance_mm':p.distance(Point(old['a'])),'end_distance_mm':p.distance(Point(old['b']))} for p in pieces(strictlegal.buffer(-.156))]
 (HERE/'c10036-reference-barrier-r15.pkl').write_bytes(pickle.dumps({'planes':planes,'physicallegal':physicallegal,'strictlegal':strictlegal,'obstacles':obstacles,'old':old,'g':g,'returnxy':returnxy},protocol=5))
'''
s=s.replace(" report['read_files_sha256']=A.READS;",insert+" report['read_files_sha256']=A.READS;")
t=HERE/'construct_c10036_reference_barrier_r15.py';assert not t.exists();t.write_text(s);print(t)
