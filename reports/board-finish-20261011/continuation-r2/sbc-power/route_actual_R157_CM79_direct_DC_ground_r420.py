"""Direct DC ground attachment; keep raw signal-shadow observations separate."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'screen_actual_R157_CM79_retained_CORE_ground_ports_r417.py').read_text(encoding='utf-8')
s=s.replace('CM79-actual-R157-retained-CORE-ground-port-census-r417','CM79-actual-R157-direct-DC-ground-retained-CORE-r420')
a=s.index(' def screen(xy):');b=s.index(' # F transport',a)
new=''' policy=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');assert sha(policy)=='392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5';policytext=policy.read_text(encoding='utf-8');assert "A new signal via's return requirement"in policytext
 savedPath=P/'CM79-actual-R157-retained-CORE-ground-port-census-r417/finite-new-LG-ordinary-via-true-native-mask-census.json';saved=json.loads(savedPath.read_bytes());legal=[]
 for row in saved:
  retained=[r for r in row['deficits']if r['kind']!='real_courtyard_no_D4']
  if not retained:legal.append({**row,'deficits':retained,'removed_SIGNAL_only_courtyard_deficits':[r for r in row['deficits']if r['kind']=='real_courtyard_no_D4']})
 put('exact-saved-census-DC-ground-scope-delta.json',{'R417_census_SHA256':sha(savedPath),'operator_file':str(policy),'operator_SHA256':sha(policy),'D4_line':227,'scope_quote':"A new signal via's return requirement",'no_new_SIGNAL_via_no_D4_pair_or_spacing_use':True,'ordinary_pitch815um_all_true_Cu_SMD_drill_rules_masks_held':True,'saved_site_count':len(saved),'DC_ground_eligible_count':len(legal),'only_removed_predicate':'SIGNAL-specific courtyard rejection','raw_signal_shadow_FAILs_retained_from_R417_R418_R419':True})
 put('only-real-before-SOURCE-LG-DC-ground-ports.json',legal)
'''
s=s[:a]+new+s[b:]
old="free=allowed.buffer(-.100005,quad_segs=64).intersection(region).intersection(board).difference(hard)"
assert s.count(old)==1;s=s.replace(old,"free=region.intersection(board).difference(hard)")
old="if not missing.is_empty or body.intersection(padCu).area<=0:continue"
new="ann=Point(*xy).buffer(.25,quad_segs=128).difference(Point(*xy).buffer(.1,quad_segs=128));annContact=body.intersection(ann).area;rawCuFail=not face.covers(LineString(path));rr.update({'raw_fast_signal_shadow_gap_EMPTY':missing.is_empty,'raw_fast_signal_shadow_gap_mm2':missing.area,'fast_signal_shadow_used_as_DC_ground_rejection':False,'actual_new_ground_annulus_contact_mm2':annContact});\n   if rawCuFail or body.intersection(padCu).area<=0 or annContact<=0:continue"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("winner={'port':row,'transport':rr};(OUT/'only-nominated-CM79-F-source-connection-body.wkb').write_bytes(body.wkb)","winner={'port':row,'transport':rr};(OUT/'only-nominated-CM79-F-source-connection-body.wkb').write_bytes(body.wkb);(OUT/'raw-fast-signal-shadow-gap-not-DC-acceptance-authority.wkb').write_bytes(missing.wkb)")
s=s.replace("'status':'ACTUAL_FULL_R157_CM79_RETAINED_CORE_GROUND_PORT_SCREEN'","'status':'DIRECT_DC_GROUND_REAL_BEFORE_SOURCE_ATTACH_NOMINATION_PENDING_NATIVE_CURRENT'")
s=s.replace("'site_count':len(rows)","'site_count':len(saved)")
s=s.replace("'new_ground_via_SOURCE_annulus_bothplanes_actual':True","'new_ground_via_SOURCE_annulus_bothplanes_actual_BEFORE_positive':True,'no_native_after_flash_or_ground_source_credit_yet':True,'SIGNAL_D4_scope_operator_SHA256':sha(policy),'fast_signal_shadow_observation_is_not_DC_ground_rejection':True")
s=s.replace('R417_COMPLETE','R420_COMPLETE')
E=P/'exact-expanded-CM79-direct-DC-ground-r420.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
