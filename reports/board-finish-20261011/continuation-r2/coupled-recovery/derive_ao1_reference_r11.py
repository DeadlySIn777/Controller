"""Create minimal monitor-wall coupled exploratory constructor."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r10.py').read_text().replace('import ao1_continuous_return_r1 as CR','import ao1_continuous_return_r1 as CR\nimport ao1_scoped_cache_nomination_r1 as SC')
source=source.replace("OUT=HERE/'ao1-reference-coupled-r10.json'", "OUT=HERE/'ao1-reference-coupled-r11.json'")
source=source.replace("VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM", "VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM\nMON='/motherboard_analog_output/AO1_MON_12V'\nMON_REMOVED={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41'}")
source=source.replace("('ao1-r10-initial-'", "('ao1-r11-initial-'").replace("('ao1-r10-legal-centres-'", "('ao1-r11-legal-centres-'")
source=source.replace("parts,(VREF,SDI))", "parts,(VREF,SDI,MON))")
source=source.replace("    for net in (VREF,SDI):\n        uf,after", "    for net in (VREF,SDI,MON):\n        uf,after")
source=source.replace("removed=set(recipe['deletes']);withdrawn=set(recipe['restores'])", "removed=set(recipe['deletes'])|MON_REMOVED;withdrawn=set(recipe['restores'])\n    for uid in MON_REMOVED:\n        item=G.parse(uid,now[4][uid],{})\n        if item['kind']!='segment' or item['net']!=MON or item['layer']!='F.Cu' or item['w']!=.2:raise ValueError('Exact original monitor ownership differs')\n    monitor_policy=policies.get(MON)\n    if monitor_policy is not None and monitor_policy.get('class')!='NONE':raise ValueError('Monitor has a controlled assignment; separate constructor required')")
source=source.replace("    return_region=VR.legal_centres(initial,COM,WINDOW)", "    return_region=VR.legal_centres(initial,COM,WINDOW)\n    provisional_refs,cache_scope=SC.provisional(initial,refs,native,now)\n    diagnostic['strictly_exploratory_scoped_withdrawn_SDI_cache_nomination']=cache_scope")
old="""                chosen=(reuse['x'],reuse['y']) if reuse else shared[0] if shared else None
"""
new=old+"""                preferred=(373.5,129.15)
                pann=Point(preferred).buffer(.25,resolution=128).difference(Point(preferred).buffer(.1,resolution=128))
                if chosen is None and all(.81-1e-9<=math.dist(preferred,q)<=1.+1e-9 for q in (vat,sat)) and all(case_refs[layer].buffer(-.075).intersection(pann).area>=.004 for layer in ('F.Cu','B.Cu')) and via_legal(temp,COM,preferred,smd,centres,all_positions):chosen=preferred
"""
assert old in source;source=source.replace(old,new)
old="""            jobs=[(VREF,'F.Cu',[vstart],[vat]),(VREF,'B.Cu',[vat],vtargets),(SDI,'F.Cu',[sstart],[sat]),(SDI,'In3.Cu',[sat],target_seeds)]
"""
new="""            nomination_refs=body_refs(provisional_refs,[vat,sat],gaps,initial)
            nomination_refs={layer:shape.difference(return_holes) for layer,shape in nomination_refs.items()}
            jobs=[(VREF,'F.Cu',[vstart],[vat]),(VREF,'B.Cu',[vat],vtargets),(SDI,'F.Cu',[sstart],[sat]),(SDI,'In3.Cu',[sat],target_seeds),(MON,'F.Cu',[(369.35,125.15)],[(374.55,130.049999)])]
"""
assert old in source;source=source.replace(old,new)
old="""                free_now=free(temp,net,layer);shape=path_shape(free_now,case_refs,layer,signals[net][1],temp,gaps) if enforce_reference else free_now
"""
new="""                free_now=free(temp,net,layer)
                if net==MON:shape=free_now.intersection(case_refs[layer].buffer(-.11))
                else:shape=path_shape(free_now,case_refs if enforce_reference else nomination_refs,layer,signals[net][1],temp,gaps)
"""
assert old in source;source=source.replace(old,new)
source=source.replace("'own_transition_mm':signals[net][1]", "'own_transition_mm':signals[net][1] if net in signals else None")
old="""                start_rows=[(p,{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['U14626.9#0' if net==VREF else 'U14626.8#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'}) for p in starts]
                goal_rows=[(p,next((r for q,r in target_records+vtarget_records if q==p),{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['C14643.1#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'})) for p in goals]
"""
new="""                if net==MON:
                    start_rows=[(p,{'uuid':'036f4f5d-d8f0-4b5f-bd20-72e5cdeecb36','kind':'track'}) for p in starts]
                    goal_rows=[(p,{'uuid':'6a7a6862-5b3a-4764-bead-1acf9ac7b861','kind':'track'}) for p in goals]
                else:
                    start_rows=[(p,{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['U14626.9#0' if net==VREF else 'U14626.8#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'}) for p in starts]
                    goal_rows=[(p,next((r for q,r in target_records+vtarget_records if q==p),{'uuid':signals[net][0] if p==signals[net][1] else initial.pads['C14643.1#0']['uuid'],'kind':'via' if p==signals[net][1] else 'pad'})) for p in goals]
"""
assert old in source;source=source.replace(old,new)
old="""                own=Point(signals[z['net']][1]).buffer(.25+maximum+.025,resolution=128);gap=A.shape(z).difference(own).difference(frefs[z['layer']]).area
                if gap>1e-9:ref_errors.append({'uuid':u,'net':z['net'],'layer':z['layer'],'full_copper_uncovered_mm2':gap})
"""
new="""                own=Point(signals[z['net']][1]).buffer(.25+maximum+.025,resolution=128) if z['net'] in signals else Point().buffer(0)
                gap=A.shape(z).difference(own).difference(frefs[z['layer']])
                if gap.area>1e-9:ref_errors.append({'uuid':u,'net':z['net'],'layer':z['layer'],'full_copper_uncovered_mm2':gap.area,'uncovered_bounds_mm':list(gap.bounds),'exact_gap_WKB_sha256':C.sha(gap.wkb)})
"""
assert old in source;source=source.replace(old,new)
source=source.replace("'SCLK_all_source_geometry_exact':True", "'owned_original_MON_F_segments':sorted(MON_REMOVED),'exact_monitor_policy':monitor_policy,'monitor_width_mm':.2,'new_monitor_vias':0,'monitor_current_r06_and_surviving_contact_obligations_mandatory':True,'SCLK_all_source_geometry_exact':True")
target=here/'ao1_reference_coupled_r11.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r11-syntax-only.pyc'))
print('Fresh r11 syntax PASS; exact monitor-wall ownership and scoped cache nomination only')
