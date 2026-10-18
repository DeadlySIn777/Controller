"""Read-only exact keepout/outline diagnosis for unchanged CORE5 terminals."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM79_coupled_fullwidth_CORE5_wall_r288.py').read_text()
s=s.replace('CM79-coupled-fullwidth-single-CORE5-wall-nominations-r288','CM79-power-terminal-exact-native-frozen-rule-area-diagnosis-r292')
needle="cases=[];winner=None;oldlength=math.dist(old['a'],old['b'])"
replacement="""terminal_rules=[]
 for label,coord in(('A',old['a']),('B',old['b'])):
  axis=Point(coord);body=buf(axis,.625);rows=[]
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rule in rules:
    if'F.Cu'not in rule['layers']or(not ex and not rule.get('no_tracks')):continue
    ns=exempt.get(rule['name'],set())if ex else set();allowed=L.norm(old['net'])in ns
    for sh in L.poly(rule['outline']):
     if body.distance(sh)<.02501:rows.append({'kind':'frozen_reservation'if ex else'native_no_tracks_rule','rule':rule.get('name',rule.get('uuid')),'raw_power_net':old['net'],'normalized_power_net':L.norm(old['net']),'declared_exempt_normalized_nets':sorted(ns),'existing_exact_power_net_exempt':allowed,'full_old_endpoint_cap_rule_overlap_mm2':body.intersection(sh).area,'cap_distance_mm':body.distance(sh),'only_existing_authority_reported_no_exception_added':True})
  terminal_rules.append({'terminal':label,'exact_old_native_coord':coord,'power_centre_in_inset_outline':outline.buffer(-.625003).covers(axis),'full_old_endpoint_Cu_in_outline':outline.covers(body),'native_or_frozen_rule_rows':rows})
 put(O/'exact-old-power-terminal-rule-authority-facts.json',terminal_rules)
 cases=[];winner=None;oldlength=math.dist(old['a'],old['b'])"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace("if winner:(O/'only-coupled-CM79", "put(O/'finite-fullwidth-current-preserving-matrix.json',cases)\n if winner:(O/'only-coupled-CM79")
s=s.replace('R288','R292')
exec(compile(s,str(__file__),'exec'))
