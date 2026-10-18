"""Canonical equal-settings union, analytic correction, fresh SAFE projection.

All generated integer-grid tags are explicitly restored with identical WKB.
Source/native originals and all source, load and discrete ownership stay fixed.
"""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'normalize_final_owned_zones_r55.py').read_text()
s=s.replace("OUT=L.OUT/'final-owned-zone-normalization-r55'","OUT=L.OUT/'SAFE-repaired-owned-zone-normalization-r160'")
needle="    candidate,cuts=P.projected(g,h,output);model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,output,candidate),protocol=5))"
assert needle in s
replacement='''    import owned_analytic_track_guards_r75 as AT
    import owned_native_pad_guards_r98 as AP
    import SAFE_native_hole_mutual_guards_r159 as HM
    output,via_ledger=P.normalize_owned_via_guards(h,output)
    output,track_ledger,_=AT.normalize_owned_track_guards(h,output)
    output,pad_ledger,_=AP.normalize_owned_pad_guards(h,output)
    output,hole_ledger=HM.native_pad_hole_guards(h,output)
    output,mutual_ledger=HM.simultaneous_mutual_guards(h,output)
    precision=[]
    for q in output:
        for role in ('shape','zone_outline_shape'):
            before=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==before
            precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hashlib.sha256(before).hexdigest()})
        q['integer_nm_physical_rings']=[[ring_integer(part.exterior)]+[ring_integer(r) for r in part.interiors] for part in p.hubs.components(q['shape'])]
        q['integer_nm_native_outline_rings']=[[ring_integer(part.exterior)]+[ring_integer(r) for r in part.interiors] for part in p.hubs.components(q['zone_outline_shape'])]
    guard_file=OUT/'owned-analytic-margin-correction-ledger.json';guard_file.write_text(json.dumps({'via':via_ledger,'actual_full_track_caps':track_ledger,'native_pads_extra20nm':pad_ledger,'native_pad_holes_extra20nm':hole_ledger,'simultaneous_mutual_margin_extra20nm':mutual_ledger,'generated_only_explicit_unchanged_precision_tags':precision},indent=1)+'\\n')
    binding.update({'SAFE_owned_analytic_margin_correction_ledger_file':str(guard_file.resolve()),'SAFE_owned_analytic_margin_correction_ledger_sha256':sha(guard_file),'restored_generated_grid_UUIDs':[q['uuid'] for q in output],'generated_precision_state_ledger':precision,'all_fitted_current_allocations_unchanged':True,'host_all_supply_rooted':False,'all_original_contact_and_reference_gates_required_after_correction':True})
    candidate,cuts=P.projected(g,h,output);model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,output,candidate),protocol=5))'''
s=s.replace(needle,replacement)
exec(compile(s,str(p/'normalize_final_owned_zones_r55.py'),'exec'))
