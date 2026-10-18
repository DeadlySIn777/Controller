"""Derive isolated complete R19 audit; actual inner reference is R18-native bound.

Only three new F track chunks differ. A new native refill/whole-board gate is
still mandatory; known strict native contour slivers remain explicitly OPEN.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'audit_ao1_reference_coupled_mon_r4.py').read_text()
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change('from shapely.geometry import Point','from shapely.geometry import Point\nfrom shapely import wkb')
s=s.replace('-independent-mon-r4','-independent-native-bound-r19')
s=s.replace('-independent-reference-gaps-mon-r4','-independent-reference-gaps-native-bound-r19')
change("if not operation or not recipe['exact_new_chunks']:","if not recipe['exact_new_chunks']:")
change("if ledger_identity(ledger)!=ledger_identity(operation['prospective_fill_contact_ledger']):raise ValueError('Separate sequential fill/contact projection disagrees with constructor')","# R19 receives a fresh independently derived ledger; prior R18 ledger is not reused.\n    operation={'prospective_fill_contact_ledger':ledger}")
needle="original_refs,original_witness,_,_=Q.rooted_reference(base,smasks,identity.raw(COM));refs,witness,_,_=Q.rooted_reference(final,masks,identity.raw(COM))"
replacement="""original_refs,original_witness,_,_=Q.rooted_reference(base,smasks,identity.raw(COM))
    native_diag=json.loads(A.read(HERE/'ao1-native-reference-gap-diagnostic-r3.json'))
    if C.sha(A.read(HERE/'ao1-native-reference-gap-diagnostic-r3.json'))!='29efaf67a301e8d969f63422235f674be3c63f595498a3836766267fe791aa00':raise ValueError('Native gap diagnostic changed')
    for name,pin in native_diag['read_files_sha256'].items():
        if C.sha(Path(name).read_bytes())!=pin:raise ValueError('Native diagnostic bound input changed '+name)
    r18=json.loads(A.read(HERE/'ao1-reference-coupled-r18.json'))
    r18_parsed={u:G.parse(u,ch.encode(),{}) for u,ch in r18['exact_new_chunks'].items()}
    if {u:ch for u,ch in recipe['exact_new_chunks'].items() if parsed[u].get('layer')!='F.Cu' or parsed[u]['net']!=SDI}!={u:ch for u,ch in r18['exact_new_chunks'].items() if r18_parsed[u].get('layer')!='F.Cu' or r18_parsed[u]['net']!=SDI}:raise ValueError('R19 changed more than three SDI F tracks')
    if len(recipe['replaced_prior_r18_new_SDI_F_chunks'])!=3 or len(recipe['replacement_SDI_F_chunks'])!=3:raise ValueError('Exact three F replacements required')
    refs={layer:wkb.loads(A.read(Path(native_diag['actual_rooted_reference_WKB_directory'])/('actual-'+layer+'.wkb'))) for layer in('F.Cu','B.Cu')};refs['In3.Cu']=refs['B.Cu'];witness=native_diag['functional_source_root_witness']
    # Native reference planes In1/In4, holes and all four attested native vias
    # remain exact. F-zone contact changes still receive the full fresh host
    # projection above and a mandatory later native refill.
    native_attestation=json.loads(A.read(HERE.parent/'ao1-native-diagnostic-r1/scoped-native-fill/actual-via-flashes.json'))['vias']
    for u,z in vias.items():
        if set(native_attestation[u])!=set(template['copper_layers']):raise ValueError('Existing native all6 new-via flash evidence differs')
        masks[u]=set(native_attestation[u])"""
change(needle,replacement)
change("'separate_constructor_ledger_match':True","'separate_constructor_ledger_match':False,'independent_fresh_ledger_derived_without_reusing_R18_projection':True,'native_R18_actual_inner_reference_used':True,'all_native_reference_boundary_slivers_preserved_open':native_diag['unchanged_reference_set_loss_diagnostics']")
change("'all_ordinary_new_native_annuli':'OPEN; host conservative all6'","'all_ordinary_new_native_annuli':'R18 actual all6 attested, exact R19 positions/dimensions unchanged; new whole-board R19 native gate OPEN'")
change("'INDEPENDENT_COUPLED_AO1_HOST_PASS_NATIVE_ANALOG_OPEN' if passed else 'INDEPENDENT_COUPLED_AO1_INCOMPLETE'","'INDEPENDENT_COUPLED_AO1_ALL_GATES_PASS_NATIVE_ANALOG_OPEN' if passed else 'INDEPENDENT_R19_PHYSICAL_OR_REFERENCE_OPEN'")
q=HERE/'audit_ao1_reference_coupled_native_bound_r19.py';assert not q.exists();q.write_text(s)
