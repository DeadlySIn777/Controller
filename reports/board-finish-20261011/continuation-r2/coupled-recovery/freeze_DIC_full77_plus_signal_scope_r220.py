"""Preserve R218; include affected discrete-only nets beside ALL77 planes."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'audit_DIC_C1022_actual_R214_full77_r218.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r218','r220').replace('R218','R220')
old="nets=sorted({L.norm(z['net'])for z in before['zones']}|{'/motherboard_motors/AUX_5V_B'});assert len(nets)==77;assert affected<=set(nets)"
new="plane_nets={L.norm(z['net'])for z in before['zones']}|{'/motherboard_motors/AUX_5V_B'};assert len(plane_nets)==77;nets=sorted(plane_nets|affected);assert affected<=set(nets)"
assert old in s;s=s.replace(old,new)
old="'all26_add_four_delete_exact_source_bytes_rebuilt':True"
assert old in s;s=s.replace(old,"'all77_plane_net_count':len(plane_nets),'additional_affected_discrete_signal_nets':sorted(affected-plane_nets),'full_actual_contact_net_count':len(nets),"+old)
dst=H/'audit_DIC_C1022_actual_R214_full77_and_signals_r220.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'freeze-DIC-full77-plus-signal-scope-r220.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'R218 incorrectly required discrete-only DIC/CS/RSP/CMD signal nets to belong to the 77 plane-bearing net set. R220 preserves all77 scope and additionally audits every affected discrete-only signal net, with explicit counts. No geometry/contact/reference/policy change.'},indent=1)+'\n');print(sha(dst.read_bytes()))
