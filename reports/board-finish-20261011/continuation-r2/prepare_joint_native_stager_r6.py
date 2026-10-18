"""Keep added zone UUIDs out of the ordinary-via postfill inventory."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'stage_joint_power_native_r5.py';o=H/'stage_joint_power_native_r6.py';assert not o.exists()
s=p.read_text();a="if copper[uid]['kind']=='via'";b="if uid in copper and copper[uid]['kind']=='via'";assert s.count(a)==1;s=s.replace(a,b);compile(s,str(o),'exec');o.write_text(s)
(H/'joint-native-stager-r6-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'only_filter_zone_UUIDs_before_ordinary_via_lookup':True,'R5_constructor_not_executed_before_preflight_fix':True,'all_contracts_retained':True,'native_jobs':0,'board_written':False},indent=1)+'\n')
print(json.dumps({'stager':str(o),'sha256':sha(o)}))
