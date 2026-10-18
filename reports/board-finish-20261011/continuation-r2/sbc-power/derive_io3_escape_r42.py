from pathlib import Path
HERE=Path(__file__).parent
s=(HERE/'repair_owned_io3_layer_escape_r41.py').read_text()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
s=s.replace('escape-repair-r41','escape-repair-r42').replace('escape-r41','escape-r42')
rep('rec=[];drills=[];smd=[];ownholes=[]','rec=[];drills=[];smd=[];ownholes=[];foreignholes=[]')
rep("if p.norm(q['net'])==NET:ownholes+=holes","if p.norm(q['net'])==NET:ownholes+=holes\n        else:foreignholes+=holes")
rep("else:\n            for layer in v['flashed']:rec.append", "else:\n            foreignholes.append(hole)\n            for layer in v['flashed']:rec.append")
rep("originalids={q['uuid'] for q in h['zones']};answer=None", """originalids={q['uuid'] for q in h['zones']};answer=None
    layer_rec={layer:[q for q in rec if q['layer']==layer] for layer in LAYERS}
    layer_trees={layer:STRtree([q['shape'] for q in rr]) for layer,rr in layer_rec.items()}
    ft=STRtree(foreignholes)
    print('IO3_ESCAPE_INITIAL',len(groups),root,target,len(foreignholes),'foreign holes',flush=True)""")
rep("blockers=[q['shape'].buffer(G.gap(h,NET,q['net'])+.025) for q in rec if q['layer']==layer and q['shape'].intersects(iw.buffer(2))]", "blockers=[layer_rec[layer][int(i)]['shape'].buffer(G.gap(h,NET,layer_rec[layer][int(i)]['net'])+.025) for i in layer_trees[layer].query(iw.buffer(2),predicate='intersects')]")
rep("blockers += [s.buffer(.275) for s in drills if s.intersects(iw.buffer(1)) and not s.intersects(point.buffer(drill/2))]", "blockers += [foreignholes[int(i)].buffer(.275) for i in ft.query(iw.buffer(1),predicate='intersects')]")
rep("if outer_route is None:continue\n                for layer", "if outer_route is None:continue\n                print('IO3_ESCAPE_OUTER_LEGAL',xy,diameter,drill,outer_route['length_mm'],flush=True)\n                for layer")
rep("test=CP.path(comp,start,end,node_cap=500000)", "print('IO3_ESCAPE_INNER_SEARCH',xy,layer,start,end,comp.area,flush=True);test=CP.path(comp,start,end,node_cap=500000)")
rep("'IO3_CM_ordinary_escape':{'via':via", "'IO3_CM_ordinary_escape':{'same_net_source_drill_annuli_not_blocked_by_foreign_hole_clearance':True,'foreign_hole_copper_clearance_mm':.275,'new_drill_to_every_existing_drill_guard_mm':.275,'via':via")
(HERE/'repair_owned_io3_layer_escape_r42.py').write_text(s);compile(s,'r42','exec');print('R42_SPATIAL_AND_ACTUAL_ANNULAR_SOURCE_FIX_SYNTAX_PASS')
