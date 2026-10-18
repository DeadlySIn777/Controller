"""Fresh AO1 ENABLE paired route; saved COM source and VREF peers unchanged."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_DAC_CS_current_ordinary_F_In3_B_pairs_r624.py';dest=H/'construct_AO1_ENABLE_current_ordinary_F_In3_B_pairs_r626.py';assert not dest.exists();text=src.read_text()
replacements={
 "Fresh paired AO1 DAC-CS constructor":"Fresh paired AO1 ENABLE constructor",
 "AO1-DAC-CS-current-ordinary-F-In3-B-two-pair-constructor-r624":"AO1-ENABLE-current-ordinary-F-In3-B-two-pair-constructor-r626",
 "NET='/motherboard_analog_output/AO1_DAC_CS_N'":"NET='/motherboard_analog_output/AO1_ENABLE_ISOLATED'",
 "p['uuid']=='5bd36a6a-0ece-4d8a-bb54-e362786d2249'":"p['uuid']=='e1c48f25-f337-46ce-9587-4b5f4df4573a'",
 "p['uuid']=='6cc6e8f2-29a9-482e-a9b7-c53dea062394'":"p['uuid']=='81cec19c-07ad-4052-81d7-07d09940c79e'",
 "('U14626','7',NET)":"('U14624','1',NET)",
 "('R14633','1',NET)":"('U14623','12',NET)",
 "win=box(368,121,389,154)":"win=box(347,137,384,160)",
 "[374.05,127.8]":"[353.9,146.0]",
 "[381.3,145.0]":"[376.15,151.2]",
 "R624_":"R626_",
 "only-NEW-AO1-DAC-CS-three-leg-two-ordinary-pair-NOMINEE.pkl":"only-NEW-AO1-ENABLE-three-leg-two-ordinary-pair-NOMINEE.pkl",
 "CURRENT_AO1_DAC_CS_":"CURRENT_AO1_ENABLE_",
}
for old,new in replacements.items():assert old in text,old;text=text.replace(old,new)
dest.write_text(text);print('R626_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
