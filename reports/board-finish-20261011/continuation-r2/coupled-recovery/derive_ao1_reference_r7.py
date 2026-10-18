"""Create a fresh paired nomination; older bounded evidence stays immutable."""
from pathlib import Path
import py_compile

here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r6.py').read_text()
source=source.replace("OUT=HERE/'ao1-reference-coupled-r6.json'", "OUT=HERE/'ao1-reference-coupled-r7.json'")
source=source.replace("('ao1-r6-initial-'", "('ao1-r7-initial-'")
old="""    attempts=[];success=None;S.STEP=.025
    parts="""
new="""    # Every candidate is first tested for continuous source-to-via and
    # via-to-actual-target reachability with only its own transition void.
    # This avoids a nearest-prefix silently rejecting every pair by pitch.
    single={};single_diagnostics={}
    for net,sites,jobs in ((VREF,vsite,[('F.Cu',[vstart]),('B.Cu',vtargets)]),(SDI,ssites,[('F.Cu',[sstart]),('In3.Cu',target_seeds)])):
        rows=[];failed=[]
        for at in sites:
            case=body_refs(refs,[at],gaps,initial);valid=True;stages=[]
            for layer,seeds in jobs:
                shape=path_shape(physical_free[net,layer],case,layer,at,initial,gaps)
                components=P.K.D.components(shape)
                connected=[p for p in components if p.covers(Point(at)) and any(p.covers(Point(s)) for s in seeds)]
                stages.append({'layer':layer,'connected':bool(connected),'via_present':shape.covers(Point(at))})
                if not connected:valid=False
            (rows if valid else failed).append(at if valid else {'at_mm':at,'stages':stages})
        single[net]=rows;single_diagnostics[net]={'individually_continuous_sites':rows,'rejected':failed}
    pairs=sorted([(vat,sat) for vat in single[VREF] for sat in single[SDI] if math.dist(vat,sat)>=.81-1e-9],key=lambda pair:(math.dist(pair[0],vstart)+math.dist(pair[1],sstart),pair))
    diagnostic['reference_aware_site_nomination']=single_diagnostics
    diagnostic['ordinary_pitch_compatible_individually_reachable_pairs']=len(pairs)
    attempts=[];success=None;S.STEP=.025
    parts="""
assert old in source
source=source.replace(old,new)
old="""    for vat in vsite[:20]:
        for sat in ssites[:20]:
            if math.dist(vat,sat)<.81:continue
"""
new="""    for vat,sat in pairs[:120]:
        for _one_case in (0,):
"""
assert old in source
source=source.replace(old,new)
source=source.replace("# Nominate conservative full-disk source-connected ordinary returns.", "# Nominate finite .15-mm-interior source-rooted annular contact.\n            # Exact final drilled graph and native gates still apply.")
old="""                        disk=Point(ret).buffer(.275,resolution=128)
                        if not all(case_refs[layer].covers(disk) for layer in ('F.Cu','B.Cu')) or not via_legal(temp,COM,ret,smd,centres,all_positions):continue
"""
new="""                        body=Point(ret).buffer(.25,resolution=128);hole=Point(ret).buffer(.1,resolution=128);ann=body.difference(hole)
                        if not all(case_refs[layer].buffer(-.075).intersection(ann).area>=.004 for layer in ('F.Cu','B.Cu')) or not via_legal(temp,COM,ret,smd,centres,all_positions):continue
"""
assert old in source
source=source.replace(old,new)
source=source.replace("'No finite all6/SMD/full-rooted-annulus return'", "'No finite all6/SMD/source-rooted .15mm-interior annular return'")
old="""            attempt.update(clearance_errors=errors,pad_losses=losses,surviving_contact_losses=contacts,fill_errors=fillerrors,reference_errors=ref_errors,returns=returns)
            if errors or losses or contacts or fillerrors or ref_errors:continue
"""
new="""            paired=[]
            for ret in returns:
                p=Point(ret['at_mm']);ann=p.buffer(.25,resolution=128).difference(p.buffer(.1,resolution=128))
                contact={layer:frefs[layer].buffer(-.075).intersection(ann).area for layer in ('F.Cu','B.Cu')}
                paired.append(dict(ret,distance_mm=math.dist(ret['signal_at_mm'],ret['at_mm']),source_rooted_finite_annular_contacts_mm2=contact,pass_=all(a>=.004 for a in contact.values())))
            attempt.update(clearance_errors=errors,pad_losses=losses,surviving_contact_losses=contacts,fill_errors=fillerrors,reference_errors=ref_errors,returns=paired)
            if errors or losses or contacts or fillerrors or ref_errors or any(not r['pass_'] for r in paired):continue
"""
assert old in source
source=source.replace(old,new)
target=here/'ao1_reference_coupled_r7.py'
assert not target.exists()
target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r7-syntax-only.pyc'))
print('Created syntax-checked fresh reference-aware r7')
