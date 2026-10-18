import json
from shapely.geometry import Point,box
import switch_control_paths_r3 as T
L=T.L;p=T.p;R=T.R
def main():
    g,h,_=T.model();rec=json.loads((L.OUT/'switch-control-paths-r3.json').read_text());rows=[]
    nets=tuple(p.norm(z['net']) for z in g['zones'] if g['domains_normalized'].get(p.norm(z['net']))=='DOM_LOGIC')
    for row in rec['routes']:
        start,end=row['start'],row['end'];window=box(min(start[0],end[0])-10,min(start[1],end[1])-10,max(start[0],end[0])+10,max(start[1],end[1])+10);p.WINDOW=window
        for repour,guard in [(('/LOGIC_GND',),None),(nets,.025),(nets,None)]:
            free=R.free_layer(h,row['net_raw'],'In3.Cu',window,repour,reference_guard=guard,allow_own_via_connection=True)
            for w in (.2,.125):
                parts=p.hubs.components(free.buffer(-w/2));aa=[i for i,q in enumerate(parts) if q.covers(Point(start))];bb=[i for i,q in enumerate(parts) if q.covers(Point(end))];near=[min(q.distance(Point(x)) for q in parts) for x in (start,end)];shared=set(aa)&set(bb)
                rr={'pin':row['pin'],'repour':repour,'reference_guard':guard,'width':w,'start_parts':aa,'end_parts':bb,'nearest_distances':near,'shared':list(shared),'component_count':len(parts)};rows.append(rr);print('PROBE',rr,flush=True)
                if shared:(L.OUT/('control-'+row['pin']+'-free-r2.wkb')).write_bytes(parts[next(iter(shared))].wkb)
    (L.OUT/'control-component-probe-r2.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
