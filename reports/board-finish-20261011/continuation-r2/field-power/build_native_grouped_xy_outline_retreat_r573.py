from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;old=H/'nominate_original_IO3_TMR_exact_local_outline_retreat_r571.py';text=old.read_text(encoding='utf-8')
(H/'original-IO3-TMR-exact-local-two-notch-negative-outline-nominee-r571/failure.json').write_text(json.dumps({'status':'FAIL_SERIALIZATION_MATCH_BEFORE_PACKET_EMISSION','script_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'geometry_local_negative_full0251_margin_checks_completed':True,'cause':'Original native pts groups multiple xy atoms on each line; the first serialization matcher incorrectly required one xy per line. All failed source remains preserved; geometry and required guards are unchanged in successor.'},indent=1)+'\n',encoding='utf-8')
text=text.replace('r571','r573').replace(r'\)\r?\n[ \t]+\(xy',r'\)\s+\(xy')
new=H/'nominate_original_IO3_TMR_exact_local_outline_retreat_r573.py';assert not new.exists();new.write_text(text,encoding='utf-8');print('R573',hashlib.sha256(new.read_bytes()).hexdigest())
