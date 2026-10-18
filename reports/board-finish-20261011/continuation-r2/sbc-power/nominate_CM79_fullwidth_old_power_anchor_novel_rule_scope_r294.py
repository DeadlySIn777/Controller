"""Coupled full-width CORE5 nomination retains exact old reserved anchor Cu.

Frozen native/routing reservations are applied to all genuinely novel Cu.
No old keepout exception is created; the exact prior body is the sole anchor.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM79_coupled_fullwidth_CORE5_wall_r288.py').read_text()
s=s.replace('CM79-coupled-fullwidth-single-CORE5-wall-nominations-r288','CM79-fullwidth-exact-old-anchor-only-novel-native-rule-nomination-r294')
s=s.replace("cases=[];winner=None;oldlength=", "ra=H/'sbc-power/CM79-power-terminal-exact-native-frozen-rule-area-diagnosis-r292/receipt.json';assert sha(ra)=='0c0ab17cd9cf8571d712d16265b9774909d6c7392086805aad82d73abcd1ed4f';cases=[];winner=None;oldlength=")
s=s.replace("oldlength=math.dist(old['a'],old['b'])","oldlength=math.dist(old['a'],old['b']);oldbody=buf(LineString([old['a'],old['b']]),.625);anchor_start=[131.4,202.35];anchor={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R294-exact-unchanged-original-CORE5-anchor')),'net':old['net'],'layer':'F.Cu','w':1.25,'a':anchor_start,'b':old['b']};anchorbody=buf(LineString([anchor['a'],anchor['b']]),.625);assert anchorbody.difference(oldbody).is_empty")
s=s.replace("ff.covers(Point(old['b']))","ff.covers(Point(anchor_start))")
s=s.replace("TR.route(faces[0],old['a'],old['b'])","TR.route(faces[0],old['a'],anchor_start)")
s=s.replace("trial={**c,'tracks'", "pt.append(anchor);powerbody=unary_union([buf(LineString([t['a'],t['b']]),.625)for t in pt]);novel=powerbody.difference(oldbody);rule_rows=[];rule_bad=[]\n   for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):\n    for rule in rules:\n     if'F.Cu'not in rule['layers']or(not ex and not rule.get('no_tracks'))or(ex and L.norm(old['net'])in exempt.get(rule['name'],set())):continue\n     for sh in L.poly(rule['outline']):\n      if powerbody.distance(sh)<.025:\n       row0={'rule':rule.get('name',rule.get('uuid')),'full_new_body_overlap_mm2':powerbody.intersection(sh).area,'exact_unchanged_old_body_overlap_mm2':oldbody.intersection(sh).area,'true_novel_body_overlap_mm2':novel.intersection(sh).area,'true_novel_body_rule_gap_mm':novel.distance(sh),'no_new_native_or_frozen_exception':True};rule_rows.append(row0)\n       if novel.distance(sh)<.025:rule_bad.append(row0)\n   rrow['exact_old_anchor_novel_rule_rows']=rule_rows\n   if rule_bad:rrow['failure']='Novel power body enters exact frozen rule reserve';continue\n   trial={**c,'tracks'")
s=s.replace("'new_CORE5_full1p25_track_count':len(pt)","'new_CORE5_full1p25_track_count':len(pt),'original_native_reserved_anchor_Cu_is_exact_subset_only':True,'exact_old_anchor_novel_rule_rows':rule_rows,'true_novel_power_WKB_sha256':__import__('hashlib').sha256(novel.wkb).hexdigest()")
s=s.replace("if winner:(O/'only-coupled-CM79", "put(O/'finite-fullwidth-current-preserving-matrix.json',cases)\n if winner:(O/'only-coupled-CM79")
s=s.replace('R288','R294')
exec(compile(s,str(__file__),'exec'))
