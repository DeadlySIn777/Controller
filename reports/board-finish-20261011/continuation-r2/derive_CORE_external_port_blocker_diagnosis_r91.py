"""Derive a read-only attribution run with the exact R90 geometry predicates."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'nominate_CORE_ordinary_external_fill_ports_r90.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=base.read_text()
changes=[]
def replace(old,new):
 global source
 assert source.count(old)==1,(old,source.count(old))
 source=source.replace(old,new);changes.append({'old':old,'new':new})
insert='''
class AuditedObstacles(list):
 def __init__(self):super().__init__();self.rows=[];self.family=None;self.meta={}
 def label(self,family,**meta):self.family=family;self.meta=meta
 def append(self,shape):
  assert self.family is not None
  super().append(shape);self.rows.append({'family':self.family,**self.meta,'shape':shape})
 def extend(self,shapes):
  for shape in shapes:self.append(shape)
 def audit(self,candidate,region,out,side):
  from collections import defaultdict
  grouped=defaultdict(list)
  for row in self.rows:grouped[row['family']].append(row['shape'])
  unions={key:unary_union(values)for key,values in grouped.items()}
  stages=[];remaining=candidate
  for family,shape in unions.items():
   before=remaining;remaining=remaining.difference(shape)
   other=unary_union([sh for key,sh in unions.items()if key!=family])
   only=candidate.difference(shape);without=candidate.difference(other)
   (out/(side+'-family-'+family+'.wkb')).write_bytes(shape.wkb)
   stages.append({'family':family,'primitive_count':len(grouped[family]),'initial_candidate_intersection_mm2':candidate.intersection(shape).area,'candidate_area_after_this_family_alone_mm2':only.area,'remaining_after_ordered_family_mm2':remaining.area,'ordered_removed_area_mm2':before.difference(remaining).area,'candidate_area_without_this_family_mm2':without.area})
  ranks=[]
  for row in self.rows:
   area=candidate.intersection(row['shape']).area
   if area>0:ranks.append({k:v for k,v in row.items()if k!='shape'}|{'candidate_intersection_mm2':area})
  ranks.sort(key=lambda x:-x['candidate_intersection_mm2'])
  original=H/'CORE-ordinary-external-fill-port-nominations-r90'/(side+'-ordinary-site-region.wkb')
  assert original.read_bytes()==region.wkb,('R90 geometry changed',side)
  (out/(side+'-initial-candidate.wkb')).write_bytes(candidate.wkb)
  report={'side':side,'initial_source_fill_contained_candidate_area_mm2':candidate.area,'exact_R90_final_region_WKB_unchanged':True,'final_legal_area_mm2':region.area,'families':stages,'largest_literal_blockers':ranks[:80],'attribution_only_no_predicate_or_geometry_changes':True}
  put(out/(side+'-blocker-attribution.json'),report)
  print('R91_BLOCKERS',side,candidate.area,[(x['family'],round(x['candidate_area_after_this_family_alone_mm2'],6),round(x['candidate_area_without_this_family_mm2'],6))for x in stages],flush=True)
'''
replace('\ndef main():',insert+'\ndef main():')
replace("CORE-ordinary-external-fill-port-nominations-r90';assert", "CORE-ordinary-external-fill-port-blocker-diagnosis-r91';assert")
replace('candidate=set_precision(window.intersection(actual.buffer(-.25-.000100)),1e-6);obs=[]','candidate=set_precision(window.intersection(actual.buffer(-.25-.000100)),1e-6);obs=AuditedObstacles()')
replace('    obs.append(sh)','    obs.label("actual_foreign_discrete",layer=l,raw_net=q["net"],kind=q["kind"],UUID=q["source"].get("uuid"));obs.append(sh)')
replace("gap=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6;obs.append", "gap=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6;obs.label('held_owned_foreign_power_planes',raw_net=q['net'],layer=q['layer'],UUID=q['uuid']);obs.append")
replace("for rings in native['fills'].values():", "for native_layer,rings in native['fills'].items():")
replace('if search.intersects(sh):obs.append(N.bounded_buffer(sh,.25+', "if search.intersects(sh):obs.label('native_foreign_power_filled_Cu',raw_net=native['net'],layer=native_layer,UUID=native['uuid']);obs.append(N.bounded_buffer(sh,.25+")
replace("if search.intersects(Point(v['x'],v['y'])):obs.append", "if search.intersects(Point(v['x'],v['y'])):obs.label('every_existing_drill',raw_net=v['net'],UUID=v['uuid']);obs.append")
replace("if pad.get('smd'):obs.extend", "if pad.get('smd'):obs.label('source_SMD_hole_edge',raw_net=pad['net'],UUID=pad['uuid'],ref=pad['ref'],pin=pad['pin']);obs.extend")
replace("   obs.extend(N.bounded_buffer(sh,.1+.275+.000100)for sh in C.poly(pad.get('hole')or[])", "   obs.label('source_plated_pad_hole_edge',raw_net=pad['net'],UUID=pad['uuid'],ref=pad['ref'],pin=pad['pin']);obs.extend(N.bounded_buffer(sh,.1+.275+.000100)for sh in C.poly(pad.get('hole')or[])")
replace("if rule.get('no_vias')or rule.get('no_pads'):obs.extend", "if rule.get('no_vias')or rule.get('no_pads'):obs.label('native_via_pad_keepouts',UUID=rule.get('uuid'));obs.extend")
replace('if shadows:obs.append',"if shadows:obs.label('actual_before_source_supported_old_reference_shadows');obs.append")
replace("region=set_precision(candidate.difference(unary_union(obs)),1e-6);(out/(label+'-ordinary-site-region.wkb'))", "region=set_precision(candidate.difference(unary_union(obs)),1e-6);obs.audit(candidate,region,out,label);(out/(label+'-ordinary-site-region.wkb'))")
replace("'verdict':'PROSPECTIVE_ORDINARY_CORE_EXTERNAL_FILL_PORTS_ONLY'", "'verdict':'EXACT_R90_ORDINARY_SITE_BLOCKER_ATTRIBUTION_ONLY'")
replace("'selected_pair_layer_feed_all77_contacts_full_source_current_return_drop_thermal_stability_native_DRC':'OPEN'", "'selected_pair_layer_feed_all77_contacts_full_source_current_return_drop_thermal_stability_native_DRC':'OPEN','no_geometry_predicate_changed':True,'blocker_attributions_files':['main-blocker-attribution.json','source-blocker-attribution.json']")
replace("'R90_PORT_NOMINATION_FROZEN'", "'R91_EXACT_BLOCKER_ATTRIBUTION_FROZEN'")
compile(source,'diagnose_CORE_external_port_blockers_r91.py','exec')
output=H/'diagnose_CORE_external_port_blockers_r91.py';assert not output.exists();output.write_text(source)
(H/'CORE-external-port-blocker-diagnosis-r91-derivation.json').write_text(json.dumps({'base_script_sha256':sha(base),'derived_script_sha256':sha(output),'changes':changes,'geometry_predicates_unchanged':True,'independent_exact_R90_final_region_WKB_assertions':True},indent=1)+'\n')
print('R91_ATTRIBUTION_DERIVED',sha(output),flush=True)
