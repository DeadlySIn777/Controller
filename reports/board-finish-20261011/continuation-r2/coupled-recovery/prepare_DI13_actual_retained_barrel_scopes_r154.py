"""Inspect real native upstream/target barrels, not the deleted bare junction."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_actual_attachments_r138.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r138','r154').replace('R138','R154')
old="  if not any(math.dist([v['x'],v['y']],p)<.000002 for p in([123.95,102.15],[130.549999,109.65])):continue\n"
assert old in s;s=s.replace(old,'')
s=s.replace('win=box(120,99,134,112)','win=box(117,94,136,115)')
s=s.replace("r124['best_nominations'][:12]","r124['best_nominations'][:1]")
s=s.replace("row.update({'exact_retained_DI13_transition_witnesses':oldviawitness","print(json.dumps({'phase':'actual_retained_DI13_barrels','witnesses':oldviawitness}),flush=True);row.update({'exact_retained_DI13_transition_witnesses':oldviawitness")
s=s.replace("'max_signal_layer_segments':3","'max_signal_layer_segments':3,'actual_existing_native_source_target_barrels_inspected_instead_of_deleted_bare_junction':True,'new_DI13_signal_vias':0,'all_exact_old_unused_layer_flags_and_native_flashes_preserved':True")
dst=H/'construct_DI15_DI13_actual_barrel_scopes_r154.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI13-actual-retained-barrel-scopes-r154.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Remove nomination-only restriction to the two deleted bare junction coordinates. Every actual retained DI13 In3 barrel in the local window gets exact raw native pose/dia/drill/flash identity, finite real current In1/In4 paired-source contact checks within1mm, and only an unchanged own disk if qualified before and after. No new DI13 signal vias or full-layer-limit bypass.'},indent=1)+'\n');print(sha(dst.read_bytes()))
