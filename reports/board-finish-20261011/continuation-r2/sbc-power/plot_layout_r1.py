import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch,Circle
from shapely.geometry import box,Point
import layout_r1 as L
p=L.p
def draw(ax,geom,col,alpha=1,fill=True):
    for part in p.hubs.components(geom):
        ax.add_patch(Patch(list(part.exterior.coords),closed=True,facecolor=col if fill else 'none',edgecolor=col,lw=.4,alpha=alpha))
        if fill:
            for hole in part.interiors:ax.add_patch(Patch(list(hole.coords),closed=True,facecolor='white',edgecolor='white',lw=0))
def main():
    g,h,scope,native,prior,omit=L.load();w=box(110,157,122,169)
    fig,ax=plt.subplots(figsize=(11,10))
    for t in h['tracks']:
        if t['layer']=='F.Cu':
            poly=p.base.body(t)
            if poly.intersects(w):draw(ax,poly,'#999999',.6)
    for pad in h['pads']:
        poly=L.body_pad(pad)
        if poly.intersects(w):
            draw(ax,poly,'#088c55' if 'SBC_5V' in pad['net'] else '#cba53a' if p.norm(pad['net'])=='/LOGIC_GND' else '#567999',.8)
            ax.text(pad['x'],pad['y'],pad['ref']+'.'+pad['num'],fontsize=5)
    for f in h['footprints']:
        for poly in p.base.polygons(f['courtyard'].get('F',[])):
            if poly.intersects(w):draw(ax,poly,'#c34141',.7,False)
    for v in h['vias']:
        if w.covers(Point(v['x'],v['y'])):
            ax.add_patch(Circle((v['x'],v['y']),v['d']/2,fc='#303030'))
            ax.add_patch(Circle((v['x'],v['y']),v['drill']/2,fc='white'))
    ax.set_xlim(110,122);ax.set_ylim(169,157);ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_title('Exact198b SBC local proposal — native barriers and ordinary drills')
    fig.tight_layout();fig.savefig(L.OUT/'local-proposal-r1.png',dpi=150)
    print('done',flush=True)
if __name__=='__main__':main()
