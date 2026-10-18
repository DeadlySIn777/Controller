"""Derive r15 verifier with an exact reconstruction of the1nm crossing carve.

The first strict no-added-area failure is retained. Tiny positive areas caused
by quantizing boolean intersection vertices remain explicit; matching the
declared carve algorithm, raw WKB hashes and coordinate envelope is required.
"""
from pathlib import Path
path=Path(__file__).resolve().parent/'audit_field_io3_crossings_r15.py'
code=path.read_text()
code=code.replace("OUT=HERE/'field-io3-crossing-contact-audit-r15'","OUT=HERE/'field-io3-crossing-contact-audit-r15b'")
code=code.replace('from shapely.ops import unary_union','from shapely.ops import unary_union\nfrom shapely import set_precision\nimport hashlib')
old="new=byid[q['uuid']];removed=q['shape'].difference(new['shape']);added=new['shape'].difference(q['shape']);assert added.area<1e-8"
new="""new=byid[q['uuid']];removed=q['shape'].difference(new['shape']);added=new['shape'].difference(q['shape'])
        if q['uuid'] in carves:
            c=carves[q['uuid']];assert hashlib.sha256(q['shape'].wkb).hexdigest()==c['old_sha256'];assert hashlib.sha256(new['shape'].wkb).hexdigest()==c['new_sha256'];expected=q['shape']
            for finger in [z for z in zones if z.get('label','').startswith('IO3-r15-field-crossing-')]:expected=set_precision(expected.difference(finger['shape'].buffer(.625)),1e-6)
            assert expected.equals_exact(new['shape'],0),('declared1nm carve does not reconstruct',q['uuid']);assert q['shape'].buffer(.000001).covers(new['shape']),('grid rounding outside1nm envelope',q['uuid'])
        else:assert added.area<1e-8
        addedfile=OUT/(q['uuid']+'-quantized-positive-delta.wkb');addedfile.write_bytes(added.wkb)"""
assert old in code;code=code.replace(old,new)
code=code.replace("'no_added_shape_area_mm2':added.area","'explicit_quantized_positive_area_mm2':added.area,'quantized_positive_delta_file':str(addedfile.resolve()),'quantized_positive_delta_sha256':sha(addedfile),'declared_carve_algorithm_exactly_reconstructed':q['uuid'] in carves")
code=code.replace("'input_r15_cache_sha256':sha(cache),","'input_r15_cache_sha256':sha(cache),'first_failed_frozen_shape_precheck_sha256':sha(HERE/'field-io3-crossing-contact-audit-r15/first-shape-precheck-failure.json'),'carved_In2_raw_WKB_and_declared_sequential_1nm_boolean_algorithm_exact':True,'explicit_positive_quantization_deltas_are_reported_not_waived':True,")
exec(compile(code,str(path),'exec'))
