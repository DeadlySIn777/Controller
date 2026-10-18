"""Preserve rejected R130/R132 and emit only the corrected new outline."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;root=H.parent
s=(H/'emit_selected_CORE1V2_native_r130.py').read_text()
s=s.replace("selected-CORE1V2-native-recipe-r130","selected-CORE1V2-native-recipe-r136")
s=s.replace("qf=sf.parent/'new-feed-zones.pkl';assert sha(qf)==sr['new_feed_zones_sha256']", "qf=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/new-feed-zones.pkl';assert sha(qf)=='0d7fea4cd6f0abf399a2f86ac614554b86bad127a46c51c8a0575ae87b5f7aa5'")
s=s.replace("'physical_drill_holes_intentionally_preserved_as_native_zone_holes':True", "'physical_drill_holes_intentionally_preserved_as_native_zone_holes':'Only source f6 drill void is restored in intended outline by exact R135; physical shape unchanged. Native own drill subtraction mandatory.'")
s=s.replace("(O/'receipt.json').write_text", "receipt.update({'exact_source_outline_operation_file':str((H/'sbc-power/CORE1V2-source-native-outline-correction-r135/exact-outline-operation-ledger.json').resolve()),'exact_source_outline_operation_sha256':sha(H/'sbc-power/CORE1V2-source-native-outline-correction-r135/exact-outline-operation-ledger.json'),'corrected_host_model_file':str((H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl').resolve()),'corrected_host_model_sha256':'729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca'})\n (O/'receipt.json').write_text")
s=s.replace('SELECTED_CORE1V2_NATIVE_R130','SELECTED_CORE1V2_NATIVE_R136')
out=H/'emit_selected_CORE1V2_native_r136.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
print('CORRECTED_SELECTED_EMITTER_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
