"""Repeat the authorized selected source trial with exact one-hole correction."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent.parent
src=H/'stage_core1v2_native_diagnostic_r132.py';dst=H/'stage_core1v2_native_diagnostic_r138.py';assert not dst.exists()
s=src.read_text().replace("OUT=H/'core1v2-native-diagnostic-r132'","OUT=H/'core1v2-native-diagnostic-r138'")
s=s.replace('selected-CORE1V2-native-recipe-r130','selected-CORE1V2-native-recipe-r136').replace('selected-CORE1V2-strict-geometry-r131','corrected-source-outline-strict-r137')
s=s.replace('d778d6118245f0846575f49bdb4e44bffa2b14437c9025bff62c07ab49e34c2c','2e8c03d7c3c064b0f0bab5e37cd76f2fd72e72e67ee4229d5147ba93b5f08bc5').replace('f2c85f9a08c763487647ed512bb0ef4d3051268730f1ef3b821ff0982431e471','7f0c0c960c640bbd52f1b4753651e58fadc990faeb34ad9293cea80d0fd20808')
dst.write_text(s);compile(s,str(dst),'exec')
(H/'sbc-power/corrected-source-native-repeat-derivation-r138.json').write_text(json.dumps({'source_driver':str(src.resolve()),'source_driver_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'derived_driver':str(dst.resolve()),'derived_driver_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'native_scope':'Same authorized test-only1 slot; exact eedf plus same J7 segment and one corrected NEW 1V2 intended outline. No old native Cu or source change.','preserved_failed_R132_R133':True,'new_heavy_slots':0,'full_native_reference_current_and_joint_no_loss':'OPEN'},indent=1)+'\n')
print('CORRECTED_SOURCE_NATIVE_REPEAT_READY',hashlib.sha256(dst.read_bytes()).hexdigest())
