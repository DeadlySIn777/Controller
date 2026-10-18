"""Small-grid router for this isolated review candidate, followed by native DRC.

This geometric construction is NOT electrical or manufacturing validation.
Native KiCad DRC and schematic parity must be run on the actual saved board.
"""
from pathlib import Path
import heapq
import json
import math
import os
import random
import numpy as np
import pcbnew as p

ROOT = Path(__file__).resolve().parent
S = .05
NX, NY = int(15.24/S)+1, int(20.32/S)+1
CLEAR = .17
WIDTH = .15
board = p.LoadBoard(str(ROOT/'adapter.kicad_pcb'))
padlist = []
for fp in board.GetFootprints():
    for pad in fp.Pads():
        box = pad.GetBoundingBox()
        pos = pad.GetPosition()
        padlist.append(dict(ref=fp.GetReference(), pin=pad.GetNumber(),
            net=pad.GetNetname(), x=p.ToMM(pos.x)-100, y=p.ToMM(pos.y)-100,
            box=(p.ToMM(box.GetLeft())-100,p.ToMM(box.GetTop())-100,
                 p.ToMM(box.GetRight())-100,p.ToMM(box.GetBottom())-100),
            layers=[0,1] if pad.GetAttribute()==p.PAD_ATTRIB_PTH else [0 if fp.GetLayer()==p.F_Cu else 1],
            smd=pad.GetAttribute()==p.PAD_ATTRIB_SMD))

routes=[]
tracks=[]
vias=[]
gx,gy=np.meshgrid(np.arange(NX)*S,np.arange(NY)*S,indexing='ij')

def boxmask(box,r):
    a,b,c,d=box
    dx=np.maximum(np.maximum(a-gx,gx-c),0)
    dy=np.maximum(np.maximum(b-gy,gy-d),0)
    return dx*dx+dy*dy <= r*r

def linemask(a,b,r):
    dx,dy=b[0]-a[0],b[1]-a[1]
    dd=dx*dx+dy*dy
    if not dd:
        return (gx-a[0])**2+(gy-a[1])**2<=r*r
    t=np.clip(((gx-a[0])*dx+(gy-a[1])*dy)/dd,0,1)
    return (gx-a[0]-t*dx)**2+(gy-a[1]-t*dy)**2<=r*r

def obstacles(net):
    blocked=np.zeros((2,NX,NY),dtype=bool)
    vm=np.zeros((NX,NY),dtype=bool)
    edge=(gx<.4)|(gx>15.24-.4)|(gy<.4)|(gy>20.32-.4)
    blocked[:]=edge
    vm|=(gx<.6)|(gx>15.24-.6)|(gy<.6)|(gy>20.32-.6)
    for pad in padlist:
        if pad['net'] != net:
            m=boxmask(pad['box'],CLEAR+WIDTH/2)
            for layer in pad['layers']:
                blocked[layer]|=m
            vm|=boxmask(pad['box'],CLEAR+.3)
        # A drilled via never intersects a paste land, including same-net lands.
        if pad['smd']:
            vm|=boxmask(pad['box'],.25)
    for n,layer,a,b,width in tracks:
        if n!=net:
            blocked[layer]|=linemask(a,b,CLEAR+(WIDTH+width)/2)
            vm|=linemask(a,b,CLEAR+.3+width/2)
    for n,xy in vias:
        if n!=net:
            m=linemask(xy,xy,CLEAR+WIDTH/2+.3)
            blocked[0]|=m;blocked[1]|=m
            vm|=linemask(xy,xy,CLEAR+.6)
        else:
            # Don't add overlapping duplicate drilled holes.
            vm|=linemask(xy,xy,.65)
    return blocked,vm

def key(pad,layer):
    return (layer,round(pad['x']/S),round(pad['y']/S))

def search(net,source,targets):
    blocked,vm=obstacles(net)
    starts=[key(source,l) for l in source['layers']]
    ends={key(t,l):t for t in targets for l in t['layers']}
    goalcoords=list(ends)
    def h(v):
        z,x,y=v
        return min(abs(x-ex)+abs(y-ey)+(0 if z==ez else 12) for ez,ex,ey in goalcoords)
    heap=[];prev={};cost={}
    for start in starts:
        if blocked[start]:
            raise RuntimeError(f'Blocked source {net} {source}')
        cost[start]=0;heapq.heappush(heap,(h(start),0,start))
    found=None
    while heap:
        _,g,v=heapq.heappop(heap)
        if cost.get(v)!=g:continue
        if v in ends:
            found=v;break
        z,x,y=v
        for dz,dx,dy,step in [(0,1,0,1),(0,-1,0,1),(0,0,1,1),(0,0,-1,1),(1-2*z,0,0,16)]:
            nz,nx,ny=z+dz,x+dx,y+dy
            if not (0<=nx<NX and 0<=ny<NY) or blocked[nz,nx,ny]:continue
            if dz and vm[x,y]:continue
            nv=(nz,nx,ny);ng=g+step
            if ng<cost.get(nv,1e30):
                cost[nv]=ng;prev[nv]=v
                heapq.heappush(heap,(ng+h(nv),ng,nv))
    if found is None:return None
    path=[found]
    while path[-1] in prev:path.append(prev[path[-1]])
    path.reverse()
    return path,ends[found]

def savepath(net,path,source,target):
    segments=[];current=[(source['x'],source['y'])];layer=path[0][0]
    viapoints=[]
    for z,x,y in path:
        xy=(round(x*S,4),round(y*S,4))
        if z!=layer:
            segments.append((layer,current))
            current=[xy];layer=z;viapoints.append(xy);vias.append((net,xy))
        elif xy!=current[-1]:current.append(xy)
    current.append((target['x'],target['y']));segments.append((layer,current))
    for idx,(layer,points) in enumerate(segments):
        compact=[]
        for xy in points:
            if compact and xy==compact[-1]:continue
            if len(compact)>1:
                a,b=compact[-2:]
                if abs((b[0]-a[0])*(xy[1]-b[1])-(b[1]-a[1])*(xy[0]-b[0]))<1e-9:
                    compact[-1]=xy;continue
            compact.append(xy)
        for a,b in zip(compact,compact[1:]):tracks.append((net,layer,a,b,WIDTH))
        routes.append(dict(net=net,layer='F.Cu' if layer==0 else 'B.Cu',width=WIDTH,
            points=compact,vias=viapoints if idx==0 else []))

nets={name:[pad for pad in padlist if pad['net']==name]
    for name in sorted({pad['net'] for pad in padlist if pad['net']})}
# Fine-pitch escapes first, then the socket signals, then the two rails.
order=sorted(nets,key=lambda n:(n.lstrip('/') in ('+5V','GND','VCC_5V'),
    not any(q['ref']=='U1' for q in nets[n]),len(nets[n]),n))
seed = int(os.environ.get('ADAPTER_ROUTE_SEED','0'))
if seed:
    random.Random(seed).shuffle(order)
for net in order:
    remaining=nets[net].copy()
    remaining.sort(key=lambda q:q['ref']!='U1')
    connected=[remaining.pop(0)]
    while remaining:
        options=sorted(((abs(a['x']-b['x'])+abs(a['y']-b['y']),a,b)
            for a in connected for b in remaining),key=lambda x:x[0])
        result=None
        for _,source,target in options:
            result=search(net,source,[target])
            if result:break
        if not result:
            (ROOT/'routes.json').write_text(json.dumps(routes,indent=2)+'\n')
            raise RuntimeError(f'Could not route {net}; {len(remaining)} pads remain')
        path,target=result;savepath(net,path,source,target)
        connected.append(target);remaining.remove(target)
    print(f'Routed {net}: {len(nets[net])} pads',flush=True)
(ROOT/'routes.json').write_text(json.dumps(routes,indent=2)+'\n')
print(f'{len(routes)} paths, {len(vias)} vias; native DRC required')
