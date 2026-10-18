"""Correct missing native-dump UUID reader using exact current pad poses."""
import datetime,hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'nominate_short_current_logic_surface_connections_r304.py'
target=H/'nominate_short_current_logic_surface_connections_r305.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
failure=H/'current-R753-short-logic-no-hole-surface-construction-r304/reader-failure.json'
assert not failure.exists()
failure.write_text(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'NATIVE_DUMP_HAS_NO_UUID_FIELD','error':'KeyError uuid at endpoint UID lookup','native_pad_fields':['ref','num','net','at','layers','attr','drill','poly'],'script_SHA256':sha(source),'geometry_policy_changed':False,'board_written':False,'adopted':False},indent=1)+'\n')
assert not target.exists()
old="endpoint_uids={pa['uuid'],pb['uuid']};options="
new="""endpoint_uids=set()
  for np in (pa,pb):
   matches=[p['uuid'] for p in h['pads'] if p['ref']==np['ref'] and str(p['num'])==str(np['num']) and poses[p['uuid']][1]==np['net'] and poses[p['uuid']][2:4]==[int(round(v*1e6)) for v in np['at']]]
   assert len(matches)==1,('exact current native endpoint UUID',np['ref'],np['num'],matches)
   endpoint_uids.add(matches[0])
  options="""
code=source.read_text();assert code.count(old)==1
code=code.replace(old,new).replace('r304','r305').replace('R304','R305')
compile(code,str(target),'exec');target.write_text(code)
receipt=H/'short-current-logic-surface-reader-derivation-r305.json';assert not receipt.exists()
receipt.write_text(json.dumps({'source_file':str(source),'source_SHA256':sha(source),'derived_file':str(target),'derived_SHA256':sha(target),'change':'resolve endpoint UUID from exact current pose ref/number/raw-net/integer-position, uniquely','clearance_holes_rules_body_and_no_Cu_mutation_policy_unchanged':True,'original_reader_failure_preserved':str(failure)},indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
