"""Preserve R288; expose every actual native predicate blocking its join."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM79_coupled_fullwidth_CORE5_wall_r288.py').read_text()
s=s.replace('CM79-coupled-fullwidth-single-CORE5-wall-nominations-r288','CM79-fixed-inner-join-actual-native-predicate-diagnosis-r290')
needle="if not row['fixed_ground_legs_exact_foreign_Cu_and_hole_polygon_covered']:continue"
addition="""if not row['fixed_ground_legs_exact_foreign_Cu_and_hole_polygon_covered']:
   diagnostics=[]
   for t in gt:
    axis=LineString([t['a'],t['b']]);body=buf(axis,.1)
    for j in trees['F.Cu'].query(body.buffer(1),predicate='intersects'):
     rr=rec['F.Cu'][int(j)]
     if rr['uuid']==uid or L.norm(rr['net'])=='/LOGIC_GND':continue
     if rr['kind']=='track'and not rr['source'].get('m'):tt=rr['source'];dd=axis.distance(LineString([tt['a'],tt['b']]))-.1-tt['w']/2
     elif rr['kind']=='via':vv=rr['source'];dd=axis.distance(Point(vv['x'],vv['y']))-.1-vv['d']/2
     else:dd=axis.distance(rr['shape'])-.1
     req=gap('/LOGIC_GND',rr['net'])+.025
     if dd<req+.00001:diagnostics.append({'new_UUID':t['uuid'],'kind':rr['kind'],'other_UUID':rr['uuid'],'raw_net':rr['net'],'exact_true_gap_mm':dd,'native_mm':req-.025,'new_planner_mm':req,'introduced_actual_planner_failure':dd<req})
    for j in ht.query(body.buffer(.5),predicate='intersects'):
     hu,hn,hsh=holes[int(j)]
     if L.norm(hn)=='/LOGIC_GND':continue
     dd=axis.distance(hsh)-.1-.005
     if dd<.27501:diagnostics.append({'new_UUID':t['uuid'],'kind':'foreign_hole','other_UUID':hu,'raw_net':hn,'guarded_gap_mm':dd,'required_mm':.275,'introduced_actual_hole_failure':dd<.275})
    for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
     for rule in rules:
      if ex and'/LOGIC_GND'in exempt.get(rule['name'],set()):continue
      if'F.Cu'in rule['layers']and(ex or rule.get('no_tracks'))and any(body.distance(sh)<.02501 for sh in L.poly(rule['outline'])):diagnostics.append({'new_UUID':t['uuid'],'kind':'native_or_frozen_rule_area','rule':rule.get('name',rule.get('uuid'))})
   row['exact_actual_native_and_planner_blockers']=diagnostics;put(O/'finite-fullwidth-current-preserving-matrix.json',cases);continue"""
assert s.count(needle)==1;s=s.replace(needle,addition)
s=s.replace("if winner:(O/'only-coupled-CM79", "put(O/'finite-fullwidth-current-preserving-matrix.json',cases)\n if winner:(O/'only-coupled-CM79")
s=s.replace('R288','R290')
exec(compile(s,str(__file__),'exec'))
