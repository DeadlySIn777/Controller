"""Route IO3 and a minimal source LG support shadow together; foreign Cu is hard."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
t=(H/'sbc-power/nominate_R353_IO3_existing_annulus_actual_source_fullbody_reference_r362.py').read_text(encoding='utf-8')
needle="exec(compile(s,str(__file__),'exec'))";assert t.count(needle)==1
extra=r'''
s=s.replace('r362','r366').replace('R362','R366')
s=s.replace('pairs=pairs[:48]','pairs=pairs[:48]')
s=s.replace('for width in(.5,.75,1.0):','for width in(.5,):')
s=s.replace('for radius in(1.0,3.0):','for radius in(3.0,10.0):')
s=s.replace("radius=(v['d']/2 if observed else v['drill']/2)+.25+.025;caps.append(Point(v['x'],v['y']).buffer(radius,quad_segs=128));portcaps.append({'UUID':v['uuid'],'actual_reference_layer_annulus':observed,'own_original_radius_mm':radius})", "ownradius=(v['d']/2 if observed else v['drill']/2)+.25+.025;caps.append(Point(v['x'],v['y']).buffer(ownradius,quad_segs=128));portcaps.append({'UUID':v['uuid'],'actual_reference_layer_annulus':observed,'own_original_radius_mm':ownradius})")
old="allowed=zero(unary_union([ref.intersection(clip.buffer(1)),cap]));reference_centers=allowed.buffer(-width/2-.005,quad_segs=128);"
new="""lgcuts=[];reference_layer=refmap[ly]
    for j in trees[reference_layer].query(clip.buffer(1),predicate='intersects'):
     rr=rec[reference_layer][int(j)]
     if L.norm(rr['net'])=='/LOGIC_GND':continue
     local=next((float(z['clearance_mm'])for z in c['zones']if z['uuid']==rr['uuid']),.15)if rr['kind']=='fill'else .15;lgcuts.append(Z.bounded_buffer(rr['shape'].intersection(clip.buffer(1)),max(local,gap('/LOGIC_GND',rr['net']))+.025))
    for z in q:
     if z['layer']==reference_layer and L.norm(z['net'])!='/LOGIC_GND'and z['shape'].intersects(clip.buffer(1)):lgcuts.append(Z.bounded_buffer(z['shape'].intersection(clip.buffer(1)),max(float(z['clearance_mm']),gap('/LOGIC_GND',z['net']))+.025))
    for j in ht.query(clip.buffer(1),predicate='intersects'):
     uid,net,sh=holes[int(j)]
     if L.norm(net)!='/LOGIC_GND':lgcuts.append(Z.bounded_buffer(sh,.28))
    for rr in h['rule_areas']:
     if reference_layer in rr['layers']:lgcuts.extend(Z.bounded_buffer(p,.025)for p in L.poly(rr['outline'])if p.intersects(clip.buffer(1)))
    for rr in reserve['keepouts']:
     if reference_layer in rr['layers']and '/LOGIC_GND'not in exempt.get(rr['name'],set()):lgcuts.extend(Z.bounded_buffer(p,.025)for p in L.poly(rr['outline'])if p.intersects(clip.buffer(1)))
    lgfree=clip.difference(unary_union(lgcuts));allowed=zero(unary_union([lgfree,cap]));reference_centers=allowed.buffer(-width/2-.005,quad_segs=128);"""
assert old in s;s=s.replace(old,new)
s=s.replace("'fullwidth_body_and5um_guard_hard_inside_actual_reference_plus_exact_two_terminal_caps':True", "'fullwidth_body_and5um_guard_hard_inside_prospective_LG_free_space_plus_exact_two_terminal_caps':True,'all_existing_foreign_native_and_owned_reference_layer_Cu_hard':True")
old="reference_gap=actual.difference(cap).difference(ref);row['actual_full_body_outside_exact_named_terminal_reference_gap_EMPTY']=reference_gap.is_empty;row['actual_full_body_outside_exact_named_terminal_reference_gap_mm2']=reference_gap.area;put(O/'finite-port-layer-width-window-attempts.json',attempts)\n    if not reference_gap.is_empty:continue"
new="""required=zero(actual.difference(cap));support=zero(Z.bounded_buffer(required,.005).difference(cap));supportparts=parts(support);source_contacts=[p.intersection(ref).area for p in supportparts];support_free_gap=support.difference(lgfree);reference_gap=required.difference(unary_union([ref,support]));row.update({'positive_LG_support_components':len(supportparts),'every_component_actual_J1_source_overlap_mm2':source_contacts,'positive_support_outside_fixed_foreign_LG_free_space_EMPTY':support_free_gap.is_empty,'actual_fullbody_outside_named_terminal_reference_gap_EMPTY':reference_gap.is_empty});put(O/'finite-port-layer-width-window-attempts.json',attempts)
    if not source_contacts or not all(a>0 for a in source_contacts)or not support_free_gap.is_empty or not reference_gap.is_empty:continue
    (O/'only-prospective-new-source-contacted-minimal-LG-support.wkb').write_bytes(support.wkb);put(O/'only-prospective-LG-support-role.json',{'net':'/LOGIC_GND','layer':reference_layer,'shape_WKB_sha256':sha(O/'only-prospective-new-source-contacted-minimal-LG-support.wkb'),'source_J1_actual_fill_overlap_every_component_mm2':source_contacts,'all_existing_foreign_Cu_holes_rule_areas_hard':True,'no_native_or_original_fill_operation':True,'native_zone_profile_integer_emission_fresh_full_sources_oldrefs_signed_loop':'OPEN'})"""
assert old in s;s=s.replace(old,new)
s=s.replace("'actual_fullbody_outside_exact_two_original_terminal_reference_gap_EMPTY':True", "'prospective_minimal_LG_support_fresh_source_contacted_fullbody_reference_gap_EMPTY':True")
s=s.replace("'NO_EXISTING_ANNULUS_IO3_BYPASS_INSIDE_ACTUAL_SOURCE_REFERENCE_AND_FIXED_CU_EXACT_FINITE_WINDOWS'", "'NO_EXISTING_ANNULUS_IO3_PLUS_MINIMAL_SOURCE_LG_SUPPORT_WITH_FIXED_FOREIGN_CU_EXACT_FINITE_WINDOWS'")
'''
t=t.replace(needle,extra+'\n'+needle)
exec(compile(t,str(__file__),'exec'))
