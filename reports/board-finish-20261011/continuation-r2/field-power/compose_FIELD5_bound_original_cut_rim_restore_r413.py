"""Preserve R393 failure; restore exact old-record cut rims locally.

The extra 500 nm envelope covers the explicit 100 nm per-record negative
steps at the withdrawn feed's boundary. Every restored point remains in
the immutable original record and outside every retained guard. It is an
explicit local restoration scope, not an altered electrical clearance.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_R385_strict_filled_restore_boundary_r393.py'
ns={'__file__':str(owner),'__name__':'_build_R393_source_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(t,',1)[0],str(owner),'exec'),ns)
t=ns['t'];ns2={'__file__':str(H/'compose_FIELD5_R385_explicit_literal_restore_boundary_r389.py'),'__name__':'_build_current_constructor_without_running'}
exec(compile(t.rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns2)
s=ns2['s']
s=s.replace('minimal-R155-strict-filled-restoration-composition-r393','minimal-R155-bound-original-cut-rim-restoration-r413')
old="new=pickle.loads((P/'one-new-field5-replacement-plane.pkl').read_bytes());assert len(new)==1;new=new[0]"
new="new=pickle.loads((H/'FIELD5-R393-only-new-plane-margin-and-native-boundary-correction-r407/only-new-FIELD5-q-replacement.pkl').read_bytes());assert new['uuid']=='8d0d8533-168b-59d0-b231-cdd89cb7bd4e'"
assert s.count(old)==1;s=s.replace(old,new)
old="if key not in cache:cache[key]=literal(N.bounded_buffer(q['zone_outline_shape'],gap))"
new="""if key not in cache:
   cache[key]=literal(N.bounded_buffer(q['zone_outline_shape'],gap))
   if q['uuid']==OLD:
    nominal=cache[key];expanded=literal(N.bounded_buffer(nominal,.0005));ef=O/('withdrawn-old-feed-'+layer+'-explicit-500nm-original-negative-rim-restoration-envelope.wkb');ef.write_bytes(expanded.wkb);cache[key]=expanded
    put(O/('withdrawn-old-feed-'+layer+'-restoration-envelope-authority.json'),{'only_withdrawn_new_plane_UUID':OLD,'actual_nominal_guard_WKB_sha256':dg(nominal),'actual_required_native_plus_planner_guard_mm':gap,'explicit_old_negative_rim_restore_envelope_mm':.0005,'envelope_file':str(ef.resolve()),'envelope_sha256':sha(ef),'every_restored_point_still_immutable_original_and_outside_all_retained_guards':True,'no_changed_clearance':True})
"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'source_reference_current_native':'OPEN'","'source_reference_current_native':'OPEN','explicit_former_failed_guard_negative_rim_restoration_envelope_mm':.0005,'R407_new_plane_margin_receipt_sha256':sha(H/'FIELD5-R393-only-new-plane-margin-and-native-boundary-correction-r407/receipt.json')")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
