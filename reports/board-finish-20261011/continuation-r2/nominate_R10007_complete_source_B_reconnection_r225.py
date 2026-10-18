"""Use the complete source group with unchanged full body qualification."""
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_U10003_R10007_local_source_reference_B_reconnection_r223.py';prefix=src.read_text().split("exec(compile(code,str(source),'exec'))")[0];exec(compile(prefix,str(src),'exec'))
code=code.replace('reconnection-nomination-r223','complete-source-reconnection-nomination-r225');old="H/'U10003-R10007-rigid-pose-actual-source-bodies-r215/actual-retained-SDI-B-Cu.wkb'";assert code.count(old)==1;code=code.replace(old,"H/'R10007-complete-actual-SDI-B-source-r224/complete-actual-SDI-B-Cu.wkb'")
code=code.replace("'native_jobs':0","'source_target_is_complete_actual_U13004_U10003_group':True,'complete_source_binding_receipt_sha256':sha(H/'R10007-complete-actual-SDI-B-source-r224/receipt.json'),'native_jobs':0")
exec(compile(code,str(src),'exec'))
