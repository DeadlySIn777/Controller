"""Fresh separate three-net auditor; old two-net audit remains preserved."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
gd=(here/'ao1_reference_gap_diagnostic_r1.py').read_text()
gd=gd.replace("plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';v=signals[z['net']]", "plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';v=signals.get(z['net'])")
gd=gd.replace("ownbase=Point(v['at']).buffer(v['d']/2,resolution=128)", "ownbase=Point(v['at']).buffer(v['d']/2,resolution=128) if v else A.shape(z)")
gd=gd.replace("own=Point(v['at']).buffer(v['d']/2+local+.025,resolution=128)", "own=Point(v['at']).buffer(v['d']/2+local+.025,resolution=128) if v else Point().buffer(0)")
gd=gd.replace("q['uuid']==v['uuid']", "(v and q['uuid']==v['uuid'])")
target=here/'ao1_reference_gap_diagnostic_r2.py';assert not target.exists();target.write_text(gd)
source=(here/'audit_ao1_reference_coupled_r1.py').read_text().replace('import ao1_reference_gap_diagnostic_r1 as GD','import ao1_reference_gap_diagnostic_r2 as GD')
source=source.replace("VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM", "VREF,SDI,COM=Q.VREF,Q.SDI,Q.COM\nMON='/motherboard_analog_output/AO1_MON_12V'\nMON_REMOVED={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41'}")
source=source.replace("path.stem+'-independent-r1.json'", "path.stem+'-independent-mon-r2.json'")
source=source.replace("path.stem+'-independent-reference-gaps-r1'", "path.stem+'-independent-reference-gaps-mon-r2'")
source=source.replace("removed!=set(original['deletes'])", "removed!=set(original['deletes'])|MON_REMOVED")
source=source.replace("    chunks={u:ch for u,ch in now[4].items() if u not in removed};", "    for uid in MON_REMOVED:\n        item=G.parse(uid,now[4][uid],{})\n        if item['kind']!='segment' or item['net']!=MON or item['layer']!='F.Cu' or item['w']!=.2:raise ValueError('Exact native monitor wall differs')\n    monitor_policy=policies.get(MON)\n    if monitor_policy is not None and monitor_policy.get('class')!='NONE':raise ValueError('Monitor controlled assignment requires separate profile')\n    chunks={u:ch for u,ch in now[4].items() if u not in removed};")
source=source.replace("for n in (VREF,SDI,COM)", "for n in (VREF,SDI,MON,COM)")
old="""        elif z['kind']!='segment' or z['w']!=.2 or z['net'] not in signals or z['layer'] not in (('F.Cu','B.Cu') if z['net']==VREF else ('F.Cu','In3.Cu')):raise ValueError('Unowned or unqualified geometry')
"""
new="""        elif z['kind']!='segment' or z['w']!=.2 or z['net'] not in (VREF,SDI,MON) or z['layer'] not in (('F.Cu','B.Cu') if z['net']==VREF else ('F.Cu','In3.Cu') if z['net']==SDI else ('F.Cu',)):raise ValueError('Unowned or unqualified geometry')
"""
assert old in source;source=source.replace(old,new)
source=source.replace("parts,(VREF,SDI))", "parts,(VREF,SDI,MON))")
source=source.replace("    for net in (VREF,SDI):", "    for net in (VREF,SDI,MON):")
old="""        v=signals[z['net']];plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';body=Point(v['at']).buffer(.25,resolution=128)
"""
new="""        v=signals.get(z['net']);plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';body=Point(v['at']).buffer(.25,resolution=128) if v else A.shape(z)
"""
assert old in source;source=source.replace(old,new)
source=source.replace("radius=.25+required+.025;own=Point(v['at']).buffer(radius,resolution=128)", "radius=.25+required+.025 if v else 0.;own=Point(v['at']).buffer(radius,resolution=128) if v else Point().buffer(0)")
source=source.replace("'own_transition_uuid':v['uuid']", "'own_transition_uuid':v['uuid'] if v else None")
source=source.replace("'exact_frozen_SDI_policy':policies[SDI]", "'exact_frozen_SDI_policy':policies[SDI],'exact_monitor_policy':monitor_policy,'owned_exact_MON_F_segments':sorted(MON_REMOVED),'new_MON_vias':0,'MON_original_width_mm':.2")
target=here/'audit_ao1_reference_coupled_mon_r2.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-independent-mon-r2-syntax-only.pyc'))
print('Separate MON/VREF/SDI coupled auditor syntax PASS; not launched')
