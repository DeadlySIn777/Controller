"""Tighten all positive Cu hardware envelopes; leave the rejected r3 frozen."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'construct_bounded_current_In2_widening_r2.py'
s=SOURCE.read_text().replace("OUT=HERE/'bounded-current-In2-widening-construction-r2'","OUT=HERE/'bounded-current-In2-widening-construction-r4'")
s=s.replace('from shapely.geometry import Point','from shapely.geometry import Point,LineString')
s=s.replace("if q['kind']=='via':shape=covercircle(vias[q['uuid']],vias[q['uuid']]['d']/2)","if q['kind']=='via':shape=covercircle(vias[q['uuid']],vias[q['uuid']]['d']/2)\n        if q['kind']=='pad'or(q['kind']=='track'and q['source'].get('m')is not None):shape=shape.buffer(.005,quad_segs=128)\n        if q['kind']=='track'and q['source'].get('m')is None:\n            t=q['source'];shape=LineString([t['a'],t['b']]).buffer((t['w']/2+1e-8)/math.cos(math.pi/512),quad_segs=128)")
s=s.replace('gap+.0251','gap+.0321').replace('for amount in(.05,.10,.15):','for amount in(.05,):')
s=s.replace("put('exact-hard-geometry-constraints.json',constraints);rows=[];proposals=[]","put('exact-hard-geometry-constraints.json',constraints);(OUT/'exact-robust-allowed-positive-area.wkb').write_bytes(allowed.wkb);rows=[];proposals=[]")
exec(compile(s,str(SOURCE),'exec'),globals())
