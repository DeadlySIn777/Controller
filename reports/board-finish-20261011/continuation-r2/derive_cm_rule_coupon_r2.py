"""Include all original board setup/version chunks in native scope coupons."""
import hashlib,json,runpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=HERE/'check_cm_terminal_native_rules_r1.py';target=HERE/'check_cm_terminal_native_rules_r2.py';old=HERE/'cm-terminal-native-rule-coupons-r1'
    if target.exists():raise ValueError('Fresh coupon correction required')
    text=source.read_text(encoding='utf-8')
    text=text.replace("OUT=HERE/'cm-terminal-native-rule-coupons-r1'","OUT=HERE/'cm-terminal-native-rule-coupons-r2'")
    anchor="    prefix=inv[0]+b''.join(edges)+area.read_bytes()"
    if text.count(anchor)!=1:raise ValueError('Exact coupon setup edit anchor differs')
    text=text.replace(anchor,"    config=[ch for ch in inv[1] if C.pcbtext.chunk_uuid(ch) is None]\n    prefix=inv[0]+b''.join(config)+b''.join(edges)+area.read_bytes()")
    target.write_text(text,encoding='utf-8')
    (old/'failure-receipt.json').write_text(json.dumps({'verdict':'NATIVE_COUPON_LOAD_FAIL','native_log_sha256':sha(old/'original-profile/native.log'),'cause':'Coupon retained opening wrapper but omitted top-level version/layers/setup chunks. No board rule verdict was produced.','source_sha256':sha(source),'corrected_sha256':sha(target),'real_board_modified':False},indent=1)+'\n',encoding='utf-8')
    runpy.run_path(str(target),run_name='__main__')
if __name__=='__main__':main()
