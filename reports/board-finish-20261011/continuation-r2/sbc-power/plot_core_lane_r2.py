import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely import from_wkb
from shapely.geometry import Point
import core_lane_r2 as R
def main():
    free=from_wkb((R.L.OUT/'CORE-In2-lane-free-r2.wkb').read_bytes());cs=R.p.hubs.components(free.buffer(-.3))
    fig,ax=plt.subplots(figsize=(16,9));source=Point(224.425,107.15).buffer(8);load=Point(116,161.4).buffer(8)
    for part in cs:
        color='lightgray'
        if part.intersects(source):color='salmon'
        if part.intersects(load):color='lightblue'
        x,y=part.exterior.xy;ax.fill(x,y,color=color,lw=0)
        for hole in part.interiors:
            x,y=hole.xy;ax.fill(x,y,color='white',lw=0)
    ax.plot([224.425],[107.15],'ro');ax.plot([116],[161.4],'bo')
    ax.set_xlim(103,250);ax.set_ylim(175,100);ax.set_aspect('equal');ax.grid(alpha=.25);fig.savefig(R.L.OUT/'CORE-In2-lane-components-r2.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
