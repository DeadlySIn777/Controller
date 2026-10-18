from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'b5_source_rooted_feeds_r2.py').read_text(encoding='utf-8')
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change("OUT=HERE/'b5-source-rooted-feeds-r2'","OUT=HERE/'b5-source-rooted-feeds-r3'")
change('controller-b5-source-feeds-r2/','controller-b5-source-feeds-r3/')
change("for drill in drills:dd.append((drill['uuid'],drill['shape'] if drill['plated'] and drill['net']==raw else drill['shape'].buffer(.275)))","for drill in drills:\n                if not (drill['plated'] and drill['net']==raw):dd.append((drill['uuid'],drill['shape'].buffer(.275)))")
change("body=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]),1e-6)\n                        if not legal.buffer(.000002).covers(body) or not body.buffer(.000002).covers(core):continue", "sameholes=unary_union([q['shape'] for q in drills if q['plated'] and q['net']==raw]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in vias]+[hole]);body=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]).difference(sameholes),1e-6)\n                        if not legal.buffer(.000002).covers(body) or not body.buffer(.000002).covers(core.difference(sameholes)):continue")
out=HERE/'b5_source_rooted_feeds_r3.py';assert not out.exists();out.write_text(s,encoding='utf-8')
