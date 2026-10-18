"""Exact nanometre terminal A*; source helper rounds terminal points to um."""
import heapq,math,time
from shapely.geometry import Point,LineString
from shapely.prepared import prep
STEP=.025
def astar(free,start,goals,deadline,node_cap=50000):
    prepared=prep(free);starts=[];targets={};cache={}
    def allowed(node):
        if node not in cache:cache[node]=prepared.covers(Point(node[0]*STEP,node[1]*STEP))
        return cache[node]
    def nearby(p):
        nx,ny=[round(x/STEP) for x in p];choices=[]
        for dx in range(-3,4):
            for dy in range(-3,4):
                n=(nx+dx,ny+dy);q=(n[0]*STEP,n[1]*STEP)
                if allowed(n) and prepared.covers(LineString([p,q])):choices.append((math.dist(p,q),n))
        return [n for _,n in sorted(choices)[:2]]
    for p,r in goals:
        for n in nearby(p):targets.setdefault(n,(p,r))
    for p,r in start:
        for n in nearby(p):starts.append((n,p,r))
    if not starts or not targets:return None,{'reason':'No exact grid attachment','nodes':0}
    xs=[n[0] for n in targets];ys=[n[1] for n in targets];bounds=min(xs),min(ys),max(xs),max(ys)
    def h(n):return math.hypot(max(bounds[0]-n[0],0,n[0]-bounds[2]),max(bounds[1]-n[1],0,n[1]-bounds[3]))
    queue=[];cost={};previous={};origin={}
    for n,p,r in starts:
        value=math.dist(p,(n[0]*STEP,n[1]*STEP))/STEP
        if value<cost.get(n,math.inf):cost[n]=value;origin[n]=(p,r);heapq.heappush(queue,(value+h(n),value,n))
    while queue and len(cost)<node_cap and time.monotonic()<deadline:
        _,value,n=heapq.heappop(queue)
        if value>cost[n]+1e-9:continue
        if n in targets:
            nodes=[n]
            while nodes[-1] in previous:nodes.append(previous[nodes[-1]])
            nodes.reverse();p,r=origin[nodes[0]];q,s=targets[n]
            path=[p]+[(x*STEP,y*STEP) for x,y in nodes]+[q];merged=[path[0]];i=0
            while i<len(path)-1:
                j=len(path)-1
                while j>i+1 and not prepared.covers(LineString([path[i],path[j]])):j-=1
                if math.dist(path[i],path[j])>1e-9:merged.append(path[j])
                i=j
            exact=[[round(x,9),round(y,9)] for x,y in merged]
            if any(not free.covers(LineString([a,b])) for a,b in zip(exact,exact[1:])):return None,{'reason':'Exact serialized nanometre path escaped guarded free polygon','nodes':len(cost)}
            return {'points_mm':exact,'source_uuid':r['uuid'],'source_kind':r['kind'],'target_uuid':s['uuid'],'target_kind':s['kind']},{'reason':'Exact nanometre path','nodes':len(cost)}
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
            nxt=n[0]+dx,n[1]+dy
            if not allowed(nxt) or not prepared.covers(LineString([(n[0]*STEP,n[1]*STEP),(nxt[0]*STEP,nxt[1]*STEP)])):continue
            new=value+math.hypot(dx,dy)
            if new<cost.get(nxt,math.inf):cost[nxt]=new;previous[nxt]=n;heapq.heappush(queue,(new+h(nxt),new,nxt))
    reason='Time budget exhausted' if time.monotonic()>=deadline else 'Node budget exhausted' if len(cost)>=node_cap else 'Bounded open set exhausted'
    return None,{'reason':reason,'nodes':len(cost)}
