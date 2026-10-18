"""Preserve R2; derive exact complete-delta reporting with no area threshold."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'physical_reference_losses_r2.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n');assert 'if loss.area>1e-9:' in s;s=s.replace('if loss.area>1e-9:','if not loss.is_empty:').replace("'threshold_mm2':1e-9","'threshold_mm2':0,'every_nonempty_intersection_reported':True");dst=H/'physical_reference_losses_r3_zero_r208.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'freeze-zero-threshold-reference-helper-r208.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Identical complete exact delta, all eligible full bodies and conservative disjoint-only bounds; report every nonempty intersection including zero-area boundary touches. Preserves R2 and its 1e-9 mm2 threshold as separate historical evidence. No buffering, source shape or policy geometry change.'},indent=1)+'\n');print(sha(dst.read_bytes()))
