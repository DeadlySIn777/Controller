"""DI15 exact entry, using R114 immutable masks and exact track obligations."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'diagnose_DIC_return_coupled_track_sites_r114.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n');s=s.replace('DIC-return-coupled-track-site-diagnostic-r114','DI15-entry-return-coupled-track-diagnostic-r124').replace('DIC_REAL_RETURN_MINIMAL','DI15_ENTRY_REAL_RETURN_MINIMAL').replace('DIC_TERMINAL_RETURN','DI15_ENTRY_RETURN')
start=s.index("rp=HERE/'fresh-partial-annular-return-nomination-r108.json'")
end=s.index(";domains=h['domains_normalized']",start)
new="rp=HERE/'di15-safe-root-r42-DI6-bind-r118.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='bb171905c94a5795d7ae3e3ded2a367c4d02a4b463bf9c82b4c6c962126c69c6';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];g=cur['after'];cache={'planes':{l:cur['source_planes'][l] for l in('In1.Cu','In4.Cu')}}"
s=s[:start]+new+s[end:]
s=s.replace("marker=[q['signal_or_handoff_at_mm'] for q in r['queries'] if q['kind']=='DIC_CS_F_B_target_pair']","marker=[[123.675923416,103.211090311]]")
s=s.replace("for radius in(.83,.875,.925,.975,1.):","for radius in(.55,.6,.65,.7,.75,.8,.85,.9,.95,1.):")
s=s.replace("'R108_receipt_sha256'","'R118_receipt_sha256'").replace("r['source_model_sha256']","r['model_sha256']")
dst=H/'diagnose_DI15_entry_return_coupled_tracks_r124.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI15-entry-return-blockers-r124.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Fresh R118 source, actual central In3 entry handoff, .55–1mm annulus nomination. Immutable all6 pads/SMD/.275 drills/.815 pitch/native/power unchanged. Existing tracks only nominate exact future ownership; no deletion.'},indent=1)+'\n');print(sha(dst.read_bytes()))
