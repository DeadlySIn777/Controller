"""Fresh exact substitutions of the saved DI15 continuous constructor.

R590's cache is used solely for its actual native J1 source references;
the OBS34 endpoint pad UUIDs are checked against exact current source.
"""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
source=H/'construct_DI15_current_ordinary_F_In2_F_pairs_r592.py'
dest=H/'construct_OBS34_current_ordinary_F_In2_F_pairs_r606.py'
assert not dest.exists()
text=source.read_text()
replacements={
 "Fresh paired DI15 constructor":"Fresh paired OBS34 constructor",
 "Both actual native pads are bare. No DI13/native copper is removed.":"The two retained OBS34 groups stay exact. No DOA_CARD_EN/watchdog copper is removed.",
 "OUT=H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592';NET='/motherboard_di/DI15_LOGIC'":"OUT=H/'OBS34-current-ordinary-F-In2-F-two-pair-constructor-r606';NET='/motherboard_status/OBS34_A'",
 "p['uuid']=='f5027315-3d7a-42d1-b8e2-6e07075d2842'":"p['uuid']=='cade0e04-ebe0-4bcf-bd97-c450441fb5b4'",
 "p['uuid']=='b9ed640f-51d8-4121-a94d-4a29c6058751'":"p['uuid']=='173dd601-7757-4fa2-8408-42b637f55ed8'",
 "win=box(115,86,136,118)":"win=box(134,114,156,149)",
 "[119.835668,89.798413]":"[143.975,124.0]",
 "[131.25,112.35]":"[147.175,138.5]",
 "R592_":"R606_",
 "only-NEW-DI15-three-leg-two-ordinary-pair-NOMINEE.pkl":"only-NEW-OBS34-three-leg-two-ordinary-pair-NOMINEE.pkl",
 "CURRENT_DI15_":"CURRENT_OBS34_",
 "actual_R590_native_original_endpoints_and_source_refs_SHA256":"actual_R590_native_J1_source_refs_only_SHA256",
 "all_original_DI13_FAULT_native_or_positive_current_power_Cu_fixed":"all_original_DOA_CARD_EN_watchdog_native_and_positive_current_power_Cu_fixed",
}
for old,new in replacements.items():
 assert old in text,old
 text=text.replace(old,new)
text=text.replace("+.030","+.025")
text=text.replace("identity.assert_chunks(chunks);assert set(chunks).isdisjoint(original)","identity.assert_chunks(chunks);assert set(chunks).isdisjoint(original)")
text=text.replace("start=[sourcepad['x'],sourcepad['y']];end=[targetpad['x'],targetpad['y']];", "assert (sourcepad['ref'],str(sourcepad['num']),K.L.norm(sourcepad['net']))==('R17070','1',NET);assert(targetpad['ref'],str(targetpad['num']),K.L.norm(targetpad['net']))==('D17035','2',NET);start=[sourcepad['x'],sourcepad['y']];end=[targetpad['x'],targetpad['y']];")
dest.write_text(text)
print('R606_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
