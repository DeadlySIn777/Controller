"""Apply unchanged actual-native source/width triage to widened R307."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'audit_short_surface_actual_before_source_and_width_r306.py';target=H/'audit_short_surface_actual_before_source_and_width_r308.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not target.exists();code=source.read_text()
assert code.count('1deac7f8a6ff3ed96c78ecfa6b8e30d26e381a306f84066b3facc64e97e5eb48')==1
code=code.replace('1deac7f8a6ff3ed96c78ecfa6b8e30d26e381a306f84066b3facc64e97e5eb48','ad00b11785d328664c575c90a895f0495eafffdf8681851f780808d5d81fee9d').replace('r305','r307').replace('R305','R307').replace('r306','r308').replace('R306','R308')
compile(code,str(target),'exec');target.write_text(code)
receipt=H/'short-surface-BEFORE-source-triage-derivation-r308.json';assert not receipt.exists()
receipt.write_text(json.dumps({'source_file':str(source),'source_SHA256':sha(source),'derived_file':str(target),'derived_SHA256':sha(target),'only_nominee_packet_pin_and_output_revision_changed':True,'all_source_width_policy_unchanged':True,'adopted':False},indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
