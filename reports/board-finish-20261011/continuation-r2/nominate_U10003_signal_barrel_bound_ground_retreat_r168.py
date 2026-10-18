"""Consider only the one actual ground-role withdrawal needed by a signal via."""
from pathlib import Path
H=Path(__file__).resolve().parent;wrapper=H/'nominate_U10003_existing_signal_barrel_relocation_face_r167.py';code=wrapper.read_text()
needle="compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))";assert code.count(needle)==1
extra="""code=code.replace('signal-barrel-relocation-legal-faces-r167','signal-barrel-bound-ground-retreat-faces-r168')
old=\"('9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9')\"
new=\"('9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9','bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a')\"
assert code.count(old)==1;code=code.replace(old,new)
code=code.replace(\"'exact_new_ground_two_band_local_negative_withdrawal_qualification':'OPEN'\",\"'exact_new_ground_two_bands_and_one_old_bde_In1_local_negative_withdrawal_qualification':'OPEN; proposed only, no physical operation or old-reference waiver'\")
"""
code=code.replace(needle,extra+needle)
compile(code,str(wrapper),'exec');exec(compile(code,str(wrapper),'exec'))
