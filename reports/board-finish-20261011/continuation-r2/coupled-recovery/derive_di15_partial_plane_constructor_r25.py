from pathlib import Path
HERE=Path(__file__).resolve().parent
src=HERE/'construct_di15_reference_escape_r17.py';dst=HERE/'construct_di15_reference_escape_r25.py';assert not dst.exists();t=src.read_text().replace("out=HERE/'di15-reference-B-escape-nomination-r17.json'","out=HERE/'di15-partial-annulus-reference-B-nomination-r25.json'")
assert 'via[NET]=via[NET].intersection(rooted.buffer(-.530))' in t;t=t.replace('via[NET]=via[NET].intersection(rooted.buffer(-.530))','via[NET]=via[NET].intersection(rooted.buffer(-.105))')
t=t.replace("'selected_transport':'B.Cu'", "'selected_transport':'B.Cu','signal_site_full_GND_disk_containment_not_required':True,'every_new_route_full_body_must_be_prior_source_rooted':True,'old_DI17_void_never_credited_as_own_void':True,'all_retained_reference_body_protection_preserved':True")
t=t.replace("A.read(__file__);A.read(BIND.__file__)", "A.read(__file__);A.read(BIND.__file__);A.read(HERE/'di15-target-reference-cut-obligations-r23.json')")
assert t!=src.read_text();dst.write_text(t);print(dst)
