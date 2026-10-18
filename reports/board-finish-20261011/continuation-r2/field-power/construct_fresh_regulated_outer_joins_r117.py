"""Close remaining local regulated pads against the fresh R116 source graph."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'regulated_outer_joins_r51.py').read_text()
s=s.replace("OUT=HERE/'regulated-outer-source-joins-r51'","OUT=HERE/'regulated-fresh-short-outer-source-joins-r117'\nimport guarded_power_projection_r44 as P")
start=s.index(" assert not OUT.exists();OUT.mkdir();bp=HERE/'logic-core-split-repair-r53'")
stop=s.index("rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'})",start)
setup=" assert not OUT.exists();OUT.mkdir();bp=HERE/'regulated-source-contact-reference-audit-r116';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'model.pkl')==br['model_sha256'];g,h,binding,planes,after=pickle.loads((bp/'model.pkl').read_bytes());\n peer=HERE.parent/'sbc-power/core1v2-local-outer-join-nominees-r106/proposed-tracks.pkl';assert sha(peer)=='ebce5be3f82d0c2de9bf6ee303d287efa78a9f85bc19358ee5249f01152b3073';peertracks=pickle.loads(peer.read_bytes());hardh={**h,'tracks':h['tracks']+peertracks};\n "
s=s[:start]+setup+s[stop:]
s=s.replace("rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'})","rec,trees=F.build({**hardh,'zones':[]},layers={'F.Cu','B.Cu'})")
s=s.replace("if a.distance(b)<40.","if a.distance(b)<100.").replace("line.length>60","line.length>120")
s=s.replace("ss=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in planes if q['layer']==l and C.norm(q['net'])!=net]","ss=[]\n   vmap={q['uuid']:q for q in hardh['vias']};tmap={q['uuid']:q for q in hardh['tracks']}\n   for q in rec[l]:\n    if C.norm(q['net'])==net:continue\n    req=gap(q['net'])+.025\n    if q['kind']=='via':v=vmap[q['uuid']];ss.append(P.bounded_disk(v,v['d']/2+req))\n    elif q['kind']=='track':t=tmap[q['uuid']];ss.append(P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+req))\n    else:ss.append(P.bounded_buffer(q['shape'],req))\n   ss += [P.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in planes if q['layer']==l and C.norm(q['net'])!=net]")
s=s.replace("Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=64)","P.bounded_disk(v,v['drill']/2+.275)")
s=s.replace("s.buffer(.275)","P.bounded_buffer(s,.275)").replace("s.buffer(.025)","P.bounded_buffer(s,.025)")
s=s.replace("C.body(t).buffer(gap(t['net'])+.025)","P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(t['net'])+.025)")
s=s.replace("part.buffer(-.00002).intersection(src)","part.buffer(-.00002).intersection(src)")
s=s.replace("core=line.buffer(width/2,quad_segs=32)","core=P.bounded_buffer(line,width/2)").replace("not legal.buffer(.000001).covers(core)","not legal.covers(core)")
s=s.replace("controller-regulated-outer-r51/","controller-regulated-outer-r117/")
s=s.replace("write(OUT/'outward-round-cutters.json',roundcuts)","write(OUT/'outward-round-cutters.json',[])")
s=s.replace("sha(rp/'receipt.json')","br['R114_delta_receipt_sha256']")
s=s.replace("'input_R41_receipt_sha256'","'input_R114_delta_receipt_sha256'").replace("'input_R53_receipt_sha256'","'input_R116_audit_receipt_sha256'")
s=s.replace("'protected_R7_not_composed':True","'final_protected_R9_already_composed':True,'peer_J7_body_hard_hash':sha(peer),'literal_free_coverage_no_buffer_expansion':True")
# This frozen successor requires its actual base receipt, not the old r53
# cache or old quantized projector. Every new track still needs native/current
# and independent source/reference checks before integration.
exec(compile(s,str(p/'regulated_outer_joins_r51.py'),'exec'))
