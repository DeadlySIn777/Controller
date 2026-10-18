"""Preserve aborted host preparation and correct exact copper parser bindings."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    old=HERE/'stage_cap_reset_native_r2.py';new=HERE/'stage_cap_reset_native_r3.py';failed=HERE/'cap-reset-native-r2'
    if new.exists() or (failed/'aborted-host-preparation.json').exists():raise ValueError('Fresh derivation required')
    (failed/'aborted-host-preparation.json').write_text(json.dumps({'verdict':'ABORTED_HOST_PREPARATION','cause':'Used nonexistent measure-module copper parser attributes before native invocation','native_jobs_started':0,'partial_files_preserved':{str(p):sha(p) for p in failed.rglob('*') if p.is_file()},'board_adopted':False},indent=1)+'\n',encoding='utf-8')
    raw=old.read_text(encoding='utf-8').replace("OUT=HERE/'cap-reset-native-r2'","OUT=HERE/'cap-reset-native-r3'").replace('import measure_cap_signal_r1 as M','import measure_cap_signal_r1 as M\nimport ordinary_routes as F').replace("M.net(ch)","F.S.norm(F.S.overlay_tool.netname(ch))").replace("M.xy(ch,'at')","F.S.overlay_tool.numbers(ch,'at')").replace("M.scalar(ch,'size')","F.S.overlay_tool.scalar(ch,'size')").replace("M.scalar(ch,'drill')","F.S.overlay_tool.scalar(ch,'drill')")
    new.write_text(raw,encoding='utf-8');(HERE/'cap-reset-native-parser-derivation-r3.json').write_text(json.dumps({'original':str(old),'original_sha256':sha(old),'derived':str(new),'derived_sha256':sha(new),'changes':['Correct copper parser helper bindings','Fresh output directory;all previous partial bytes retained'],'native_gates_unchanged':True},indent=1)+'\n',encoding='utf-8')
    print(str(new),flush=True)
if __name__=='__main__':main()
