"""Preserve first per-record serialization failure and report exact types."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
src=H/'construct_CORE_R112_per_polygon_immutable_owned_r242.py'
dst=H/'construct_CORE_R112_per_polygon_immutable_owned_r244.py'
out=H/'CORE-R112-per-polygon-immutable-owned-construction-r242'
assert not dst.exists() and out.exists() and not (out/'failure.json').exists()
(out/'failure.json').write_text(json.dumps({'verdict':'PER_RECORD_SERIALIZED_GEOMETRY_EQUALS_ASSERTION_FAILED','script_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'exit_code':1,'exact_assertion':'reconstructed.equals(remaining)','no_candidate_model_emitted':True,'no_native_board_or_source_change':True,'all_failed_outputs_and_script_preserved':True},indent=1)+'\n')
t=src.read_text().replace('construction-r242','construction-r244').replace('R242_','R244_')
a="assert reconstructed.equals(remaining)"
assert t.count(a)==1
t=t.replace(a,"polygonal=unary_union(RF.parts(remaining));serialized_equal=reconstructed.equals(polygonal);geometry_state={'remaining_type':remaining.geom_type,'remaining_valid':remaining.is_valid,'polygonal_type':polygonal.geom_type,'polygonal_valid':polygonal.is_valid,'reconstructed_type':reconstructed.geom_type,'reconstructed_valid':reconstructed.is_valid,'raw_remaining_WKB_sha256':C.sha(remaining.wkb),'polygonal_WKB_sha256':C.sha(polygonal.wkb),'reconstructed_WKB_sha256':C.sha(reconstructed.wkb),'serialized_polygonal_exact':serialized_equal,'nonpolygonal_residue_never_counted_as_Cu_contact_or_reference':True};(O/(uid+'-'+str(i)+'-raw-before-record-reconstruction.wkb')).write_bytes(remaining.wkb);(O/(uid+'-'+str(i)+'-serialized-record-reconstruction.wkb')).write_bytes(reconstructed.wkb)")
t=t.replace("ok=gain.is_empty and outside_withdrawal.is_empty","ok=gain.is_empty and outside_withdrawal.is_empty and serialized_equal")
t=t.replace("'clip_only_to_exact_original_record_iterations':clip","'typed_geometry_and_serialization':geometry_state,'clip_only_to_exact_original_record_iterations':clip")
dst.write_text(t);compile(t,str(dst),'exec')
print(hashlib.sha256(dst.read_bytes()).hexdigest())
