"""Separate native power terminal constraints from corridor disconnection."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM79_coupled_fullwidth_CORE5_wall_r288.py').read_text()
s=s.replace('CM79-coupled-fullwidth-single-CORE5-wall-nominations-r288','CM79-fullwidth-power-terminal-native-constraint-diagnosis-r291')
s=s.replace("rrow={'radius_mm':radius,'whole_fullwidth_original_endpoint_face_count':len(faces)}", "rrow={'radius_mm':radius,'whole_fullwidth_original_endpoint_face_count':len(faces),'original_terminal_A_covered':pf.covers(Point(old['a'])),'original_terminal_B_covered':pf.covers(Point(old['b']))}")
needle="cases=[];winner=None;oldlength=math.dist(old['a'],old['b'])"
replacement="""terminal_checks=[]
 for label,coord in(('A',old['a']),('B',old['b'])):
  axis=Point(coord);body=buf(axis,.625)
  for j in trees['F.Cu'].query(body.buffer(1),predicate='intersects'):
   rr=rec['F.Cu'][int(j)]
   if rr['uuid']==uid or L.norm(rr['net'])==L.norm(old['net']):continue
   if rr['kind']=='track'and not rr['source'].get('m'):tt=rr['source'];dd=axis.distance(LineString([tt['a'],tt['b']]))-.625-tt['w']/2
   elif rr['kind']=='via':vv=rr['source'];dd=axis.distance(Point(vv['x'],vv['y']))-.625-vv['d']/2
   else:dd=axis.distance(rr['shape'])-.625
   req=gap(old['net'],rr['net'])+.025
   if dd<req+.00005:terminal_checks.append({'terminal':label,'kind':rr['kind'],'other_UUID':rr['uuid'],'raw_net':rr['net'],'true_analytic_gap_mm':dd,'actual_native_mm':req-.025,'new_planner_mm':req,'native_before_deficit':dd<req-.025,'planner_before_deficit':dd<req,'terminal_matches_exact_old_native_endpoint':True})
  for j in ht.query(body.buffer(.5),predicate='intersects'):
   hu,hn,sh=holes[int(j)]
   if L.norm(hn)==L.norm(old['net']):continue
   dd=axis.distance(sh)-.625-.005
   if dd<.27505:terminal_checks.append({'terminal':label,'kind':'every_foreign_hole','other_UUID':hu,'guarded_gap_mm':dd,'required_mm':.275,'inherited_before_deficit':dd<.275})
 put(O/'exact-old-fullwidth-terminal-before-constraint-facts.json',terminal_checks)
 cases=[];winner=None;oldlength=math.dist(old['a'],old['b'])"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace("if winner:(O/'only-coupled-CM79", "put(O/'finite-fullwidth-current-preserving-matrix.json',cases)\n if winner:(O/'only-coupled-CM79")
s=s.replace('R288','R291')
exec(compile(s,str(__file__),'exec'))
