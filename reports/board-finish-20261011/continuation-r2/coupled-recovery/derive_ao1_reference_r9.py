"""Fresh legal same-domain plane retreats and actual existing return reuse."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
vr=(here/'ao1_via_region_r1.py').read_text()
old="elif r['kind']=='fill' and r.get('net')=='/motherboard_analog_output/AO1_COM' and r.get('domain')==domain:continue"
new="elif r['kind']=='fill' and r.get('domain')==domain:continue # Prospective exact local-clearance cuts, all contacts/no-split required."
assert old in vr;vr=vr.replace(old,new)
target=here/'ao1_via_region_r2.py';assert not target.exists();target.write_text(vr)
source=(here/'ao1_reference_coupled_r8.py').read_text().replace('import ao1_via_region_r1 as VR','import ao1_via_region_r2 as VR')
source=source.replace("OUT=HERE/'ao1-reference-coupled-r8.json'", "OUT=HERE/'ao1-reference-coupled-r9.json'")
source=source.replace("('ao1-r8-initial-'", "('ao1-r9-initial-'").replace("('ao1-r8-legal-centres-'", "('ao1-r9-legal-centres-'")
source=source.replace("r['kind']=='fill' and r.get('net')==COM and r.get('domain')==domain", "r['kind']=='fill' and r.get('domain')==domain")
old="""    sample.update((round(373.65+i*.025,9),round(128.25+j*.025,9)) for i in range(33) for j in range(37))
"""
new=old+"""    sample.update((round(376.625+i*.025,9),round(127.8+j*.025,9)) for i in range(25) for j in range(57))
"""
assert old in source;source=source.replace(old,new)
old="""                shared=[r['at_mm'] for r in returns if .81-1e-9<=math.dist(at,r['at_mm'])<=1.+1e-9]
                chosen=shared[0] if shared else None
"""
new="""                existing=[]
                for oldvia in initial.g['vias']:
                    if S.norm(oldvia['net'])!=COM or not {'In1.Cu','In4.Cu'}<=smasks.get(oldvia['uuid'],set()):continue
                    oldat=(oldvia['x'],oldvia['y']);distance=math.dist(at,oldat)
                    if not .81-1e-9<=distance<=1.+1e-9:continue
                    oldann=Point(oldat).buffer(oldvia['d']/2,resolution=128).difference(Point(oldat).buffer(oldvia['drill']/2,resolution=128))
                    if all(case_refs[layer].buffer(-.075).intersection(oldann).area>=.004 for layer in ('F.Cu','B.Cu')):existing.append(oldvia)
                existing.sort(key=lambda v:(math.dist(at,(v['x'],v['y'])),v['uuid']))
                reuse=existing[0] if existing else None
                shared=[r['at_mm'] for r in returns if .81-1e-9<=math.dist(at,r['at_mm'])<=1.+1e-9]
                chosen=(reuse['x'],reuse['y']) if reuse else shared[0] if shared else None
"""
assert old in source;source=source.replace(old,new)
old="""                returns.append({'net':net,'signal_at_mm':at,'at_mm':chosen});all_positions.append(chosen);u,ch=Q.serial_via(identity,COM,chosen);new[u]=ch
"""
new="""                row={'net':net,'signal_at_mm':at,'at_mm':chosen,'existing_uuid':reuse['uuid'] if reuse else None,'diameter_mm':reuse['d'] if reuse else .5,'drill_mm':reuse['drill'] if reuse else .2,'actual_existing_flash_layers':sorted(smasks[reuse['uuid']]) if reuse else None}
                returns.append(row)
                if chosen not in all_positions:all_positions.append(chosen)
                if not reuse:u,ch=Q.serial_via(identity,COM,chosen);new[u]=ch
"""
assert old in source;source=source.replace(old,new)
source=source.replace("Point(r['at_mm']).buffer(.1,resolution=128) for r in returns", "Point(r['at_mm']).buffer(r['drill_mm']/2,resolution=128) for r in returns")
source=source.replace("p=Point(ret['at_mm']);ann=p.buffer(.25,resolution=128).difference(p.buffer(.1,resolution=128))", "p=Point(ret['at_mm']);ann=p.buffer(ret['diameter_mm']/2,resolution=128).difference(p.buffer(ret['drill_mm']/2,resolution=128))")
source=source.replace("'no_neighbor_signal_void_exemption':True", "'same_domain_fill_retreat_nominates_only_with_exact_final_local_clearance_contact_no_split_gates':True,'cross_domain_fill_and_real_hards_preserved':True,'actual_existing_source_rooted_return_reuse':True,'no_neighbor_signal_void_exemption':True")
target=here/'ao1_reference_coupled_r9.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r9-syntax-only.pyc'))
print('Fresh r9 syntax PASS; source planes are prospective cuts, no continuity/reference waiver')
