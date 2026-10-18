"""Jointly screen a real source-connected In1 support and the coupled signal reconnect."""
from pathlib import Path
P=Path(__file__).resolve().parent
source=(P/'exact-expanded-coupled-F-reconnect-actual-native-antipad-r393.py').read_text(encoding='utf-8').replace('CM79-R371-coupled-both-functions-F-reconnect-native-antipad-bound-r393','CM79-R371-coupled-F-reconnect-joint-minimal-source-LG-support-r394').replace('R393','R394')
old="attempts=[];winner=None;fixed={};holefixed={}"
new="""attempts=[];winner=None;fixed={};holefixed={};additionalLGSupport=[]
 allrec,alltrees=F.build(base,layers={'In1.Cu'});lgcuts=[]
 for j in alltrees['In1.Cu'].query(env.buffer(1),predicate='intersects'):
  rr=allrec['In1.Cu'][int(j)]
  if L.norm(rr['net'])=='/LOGIC_GND':continue
  local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;lgcuts.append(Z.bounded_buffer(rr['shape'].intersection(env.buffer(1)),max(local,gap('/LOGIC_GND',rr['net']))+.025))
 for z in q:
  if z['layer']=='In1.Cu'and L.norm(z['net'])!='/LOGIC_GND'and z['shape'].intersects(env.buffer(1)):lgcuts.append(Z.bounded_buffer(z['shape'].intersection(env.buffer(1)),max(float(z['clearance_mm']),gap('/LOGIC_GND',z['net']))+.025))
 for j in ht.query(env.buffer(1),predicate='intersects'):lgcuts.append(Z.bounded_buffer(holes[int(j)][1],.28))
 for rules,ex in[(h['rule_areas'],False),(reserve['keepouts'],True)]:
  for rr in rules:
   if 'In1.Cu'not in rr['layers']or(ex and '/LOGIC_GND'in exempt.get(rr['name'],set())):continue
   lgcuts.extend(Z.bounded_buffer(sh,.025)for sh in L.poly(rr['outline'])if sh.intersects(env.buffer(1)))
 prospectiveLGfree=env.difference(unary_union(lgcuts))"""
assert source.count(old)==1;source=source.replace(old,new)
old="ref=fullref.difference(sig.buffer(actualNativeRadius,quad_segs=128)); allowed=ref if cap is None else unary_union([ref,cap]);"
new="ref=unary_union([fullref]+additionalLGSupport).difference(sig.buffer(actualNativeRadius,quad_segs=128)); lgfree=prospectiveLGfree.difference(Z.bounded_buffer(sig,.425)); referenceDomain=lgfree if request['label']=='R7035-ENC3_A_P-to-one-ordinary-dive'else ref; allowed=referenceDomain if cap is None else unary_union([referenceDomain,cap]);"
assert source.count(old)==1;source=source.replace(old,new)
old="return nt if rg.is_empty and oldOverlap>0 and padOverlap>0 else None"
new="""if request['label']=='R7035-ENC3_A_P-to-one-ordinary-dive':
   required=zero(remaining); support=zero(Z.bounded_buffer(required,.005)); contacts=[ss.intersection(ref).area for ss in parts(support)]; supportGap=support.difference(lgfree); newReferenceGap=required.difference(unary_union([ref,support])); row.update({'joint_positive_LG_support_area_mm2':support.area,'every_support_component_actual_J1_source_fill_overlap_mm2':contacts,'new_LG_support_foreign_hole_rule_gap_EMPTY':supportGap.is_empty,'new_actual_body_source_reference_gap_EMPTY':newReferenceGap.is_empty})
   if not contacts or not all(a>0 for a in contacts)or not supportGap.is_empty or not newReferenceGap.is_empty or oldOverlap<=0 or padOverlap<=0:return None
   additionalLGSupport.append(support);return nt
  return nt if rg.is_empty and oldOverlap>0 and padOverlap>0 else None"""
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace("sig=Point(*pose['selected_ordinary_ENC_port']['new_signal_xy']);done=[];directRows=[];requests=", "sig=Point(*pose['selected_ordinary_ENC_port']['new_signal_xy']);additionalLGSupport.clear();done=[];directRows=[];requests=")
source=source.replace("'new_F_reconnect_tracks':done,", "'new_F_reconnect_tracks':done,'only_new_positive_source_LG_In1_support_shapes':list(additionalLGSupport),")
source=source.replace("'wholebody_actual_source_refs_exact_terminal_guards_only':True", "'wholebody_actual_source_refs_exact_terminal_guards_only':True,'minimal_new_LG_In1_role_all_foreign_reference_layer_Cu_holes_rules_hard':True,'new_LG_profile_emission_fresh_current_source_proof_native_fill_DRC':'OPEN'")
E=P/'exact-expanded-coupled-F-reconnect-joint-source-LG-r394.py';assert not E.exists();E.write_text(source,encoding='utf-8');exec(compile(source,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
