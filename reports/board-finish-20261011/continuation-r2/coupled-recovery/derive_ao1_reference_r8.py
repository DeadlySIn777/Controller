"""Fresh fine-boundary paired constructor plus explicitly held diagnostic."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r7.py').read_text()
source=source.replace("OUT=HERE/'ao1-reference-coupled-r7.json'", "OUT=HERE/'ao1-reference-coupled-r8.json'")
source=source.replace("('ao1-r7-initial-'", "('ao1-r8-initial-'")
source=source.replace("result[layer]=refs[layer].difference(voids)", "result[layer]=refs[layer].intersection(WINDOW.buffer(1)).difference(voids)")
old="""    for i in range(75):
        for j in range(65):
            at=(round(370.5+i*.1,9),round(125.5+j*.1,9));point=Point(at)
            if vspace.covers(point) and via_regions[VREF].covers(point):vsite.append(at)
            if sspace.covers(point) and via_regions[SDI].covers(point):ssites.append(at)
"""
new="""    sample={(round(370.5+i*.1,9),round(125.5+j*.1,9)) for i in range(75) for j in range(65)}
    sample.update((round(373.65+i*.025,9),round(128.25+j*.025,9)) for i in range(33) for j in range(37))
    for at in sorted(sample):
        point=Point(at)
        if vspace.covers(point) and via_regions[VREF].covers(point):vsite.append(at)
        if sspace.covers(point) and via_regions[SDI].covers(point):ssites.append(at)
    for net,region in via_regions.items():
        p=HERE/('ao1-r8-legal-centres-'+net.rsplit('/',1)[-1]+'.wkb');p.write_bytes(region.wkb)
"""
assert old in source;source=source.replace(old,new)
old="""    diagnostic['ordinary_pitch_compatible_individually_reachable_pairs']=len(pairs)
    attempts=[];success=None;S.STEP=.025
"""
new="""    diagnostic['ordinary_pitch_compatible_individually_reachable_pairs']=len(pairs)
    strict_pairs=pairs[:120]
    # A frozen physical diagnostic is useful for resolving an actual removed
    # barrel's stale fill cache. It never receives reference or adoption credit.
    nominations=[((373.4,128.3),(374.2,128.5)),((373.4,128.3),(374.25,128.5)),((373.4,128.3),(374.3,128.6)),((374.0,129.0),(373.4,128.3))]
    physical_pairs=[p for p in nominations if math.dist(*p)>=.81-1e-9 and all(via_regions[n].covers(Point(a)) for n,a in zip((VREF,SDI),p))]
    cases=[(a,b,True) for a,b in strict_pairs]+[(a,b,False) for a,b in physical_pairs]
    diagnostic['physical_diagnostic_pairs_without_reference_credit']=physical_pairs
    return_region=VR.legal_centres(initial,COM,WINDOW)
    attempts=[];success=None;held=None;S.STEP=.025
"""
assert old in source;source=source.replace(old,new)
source=source.replace("    for vat,sat in pairs[:120]:", "    for vat,sat,enforce_reference in cases:")
source=source.replace("attempt={'VREF_via_mm':vat,'SDI_via_mm':sat,'paths':[],'failures':[]}", "attempt={'VREF_via_mm':vat,'SDI_via_mm':sat,'enforce_reference_during_nomination':enforce_reference,'paths':[],'failures':[]}")
old="""                        if not all(case_refs[layer].buffer(-.075).intersection(ann).area>=.004 for layer in ('F.Cu','B.Cu')) or not via_legal(temp,COM,ret,smd,centres,all_positions):continue
"""
new="""                        if not return_region.covers(Point(ret)) or any(math.dist(ret,p)<.81-1e-9 for p in all_positions):continue
                        if not all(case_refs[layer].buffer(-.075).intersection(ann).area>=.004 for layer in ('F.Cu','B.Cu')) or not via_legal(temp,COM,ret,smd,centres,all_positions):continue
"""
assert old in source;source=source.replace(old,new)
old="""                free_now=free(temp,net,layer);shape=path_shape(free_now,case_refs,layer,signals[net][1],temp,gaps)
"""
new="""                free_now=free(temp,net,layer);shape=path_shape(free_now,case_refs,layer,signals[net][1],temp,gaps) if enforce_reference else free_now
"""
assert old in source;source=source.replace(old,new)
old="""            if errors or losses or contacts or fillerrors or ref_errors or any(not r['pass_'] for r in paired):continue
            success={'new_chunks':{u:ch.decode() for u,ch in new.items()},'all_surviving_contact_obligations':ledger,'native_source_partition_checks':checks,'reference_witness':fwitness,'prospective_fill_contact_ledger':fillledger,'clearance_rows':clear,'new_antipads':anti,'selected_attempt_index':len(attempts)-1};break
        if success:break
"""
new="""            if errors or losses or contacts or fillerrors or any(not r['pass_'] for r in paired):continue
            candidate={'new_chunks':{u:ch.decode() for u,ch in new.items()},'all_surviving_contact_obligations':ledger,'native_source_partition_checks':checks,'reference_witness':fwitness,'prospective_fill_contact_ledger':fillledger,'clearance_rows':clear,'new_antipads':anti,'selected_attempt_index':len(attempts)-1,'full_body_reference_errors':ref_errors,'reference_and_adoption_credit':not bool(ref_errors)}
            if ref_errors:
                if not enforce_reference:held=candidate;break
                continue
            success=candidate;break
        if success or held:break
"""
assert old in source;source=source.replace(old,new)
source=source.replace("'verdict':'POSITIVE_HOST_REFERENCE_AWARE_OPERATION_INDEPENDENT_NATIVE_ANALOG_OPEN' if success else 'FINITE_REFERENCE_AWARE_OPERATION_INCOMPLETE'", "'verdict':'POSITIVE_HOST_REFERENCE_AWARE_OPERATION_INDEPENDENT_NATIVE_ANALOG_OPEN' if success else 'HELD_PHYSICAL_DIAGNOSTIC_REFERENCE_GATE_OPEN' if held else 'FINITE_REFERENCE_AWARE_OPERATION_INCOMPLETE'")
source=source.replace("'exact_new_chunks':success['new_chunks'] if success else {}", "'exact_new_chunks':(success or held)['new_chunks'] if success or held else {}")
source=source.replace("'attempts':attempts,'success':success,", "'attempts':attempts,'success':success,'held_diagnostic_candidate':held,")
target=here/'ao1_reference_coupled_r8.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r8-syntax-only.pyc'))
print('Created syntax-checked fine-boundary r8; any cached-reference diagnostic explicitly held')
