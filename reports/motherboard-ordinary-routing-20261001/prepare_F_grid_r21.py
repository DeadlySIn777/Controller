"""Prepare actual F-only routing with unchanged ordinary Source/return geometry guards."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'route_In2_extended_search_r20.py').read_text()
s=s.replace('import sys,json,math,copy,shutil,itertools,time','import sys,json,math,copy,shutil,itertools,time,heapq')
s=s.replace('if 0<length<=90:', 'if 0<length<=45:')
marker='for length,name,p,q in sorted(jobs,key=lambda x:x[0]):'
prefix,suffix=s.split(marker,1)
function='''
def grid_front(start,end,name,max_nodes=3500,step=.5):
    # A search only. Every emitted edge still passes the original actual
    # clearance, keepout and Source-owned filled-reference corridor check.
    limit=min(100.,1.8*math.dist(start,end)+10.)
    if not clear([start,start],name,pcbnew.F_Cu)or not clear([end,end],name,pcbnew.F_Cu):return None
    point=lambda k:(round(start[0]+step*k[0],6),round(start[1]+step*k[1],6))
    queue=[(math.dist(start,end),0.,(0,0))];cost={(0,0):0.};previous={};memo={}
    while queue and len(cost)<max_nodes:
        _,travelled,k=heapq.heappop(queue)
        if travelled>cost[k]+1e-8:continue
        at=point(k)
        if math.dist(at,end)<=step*1.5 and travelled+math.dist(at,end)<=limit and clear([at,end],name,pcbnew.F_Cu):
            result=[end,at]
            while k!=(0,0):k=previous[k];result.append(point(k))
            result.reverse();simple=[]
            for point_mm in result:
                if simple and math.dist(simple[-1],point_mm)<1e-7:continue
                while len(simple)>1:
                    a,z=simple[-2:]
                    if abs((z[0]-a[0])*(point_mm[1]-z[1])-(z[1]-a[1])*(point_mm[0]-z[0]))>1e-8:break
                    simple.pop()
                simple.append(point_mm)
            assert clear(simple,name,pcbnew.F_Cu)
            return simple
        for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nxt=(k[0]+dx,k[1]+dy);dest=point(nxt);new=travelled+step*math.hypot(dx,dy)
            if new+math.dist(dest,end)>limit or new>=cost.get(nxt,float('inf'))-1e-8:continue
            if not(bounds[0]<=dest[0]<=bounds[2]and bounds[1]<=dest[1]<=bounds[3]):continue
            key=tuple(sorted((k,nxt)))
            if key not in memo:memo[key]=clear([at,dest],name,pcbnew.F_Cu)
            if not memo[key]:continue
            cost[nxt]=new;previous[nxt]=k;heapq.heappush(queue,(new+math.dist(dest,end),new,nxt))
    return None

grid_attempts=0
'''
keep,oldtail=suffix.split('    row=m[\'nets\'][name];starts=escapes(p,row);ends=escapes(q,row);chosen=None',1)
_,save=oldtail.split("\ndest=OUT/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'",1)
loop='''    direct=next((line for line in enhanced_paths(start,end)if sum(math.dist(s,t)for s,t in zip(line,line[1:]))<=100 and clear(line,name,pcbnew.F_Cu)),None)
    if direct is None and grid_attempts<24 and clear([start,start],name,pcbnew.F_Cu)and clear([end,end],name,pcbnew.F_Cu):
        grid_attempts+=1;print(json.dumps(dict(grid_source_pair=pair,attempt=grid_attempts)),flush=True)
        direct=grid_front(start,end,name)
    if direct is None:
        blocked.append(dict(net=name,source_pair=pair,span_mm=length,reason='No Source-covered F-only bounded native path'))
        continue
    signal=[add_segment(s,t,name,pcbnew.F_Cu)for s,t in zip(direct,direct[1:])];signal=[u for u in signal if u]
    groups.append(dict(net=name,source_pair=pair,source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],signal_UUIDs=signal,ground_UUIDs=[],new_copper_UUIDs=signal,front_path_mm=direct,no_new_vias=True))
    print(json.dumps(dict(added_pair=pair,net=name,newCu=len(signal),path_mm=sum(math.dist(s,t)for s,t in zip(direct,direct[1:])))),flush=True)
    if len(groups)>=12:break
'''
s=prefix+function+marker+keep+loop+"\ndest=OUT/'motherboard-ordinary-F-batch-candidate.kicad_pcb'"+save
s=s.replace('actual_signal_layers=["F.Cu","In2.Cu"]','actual_signal_layers=["F.Cu"]')
out=p/'route_F_grid_r21.py';assert not out.exists();out.write_text(s)
