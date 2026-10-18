"""Preserve alarm history and schedule an unchanged next watch."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=H/'arm_resource_watch_r10.py';target=H/'arm_resource_watch_r11.py';assert not target.exists()
    code=source.read_text(encoding='utf-8')
    replacements={"prior=H/'resource-monitor-r9'":"prior=H/'resource-monitor-r10'","out=H/'resource-monitor-r10'":"out=H/'resource-monitor-r11'","'prior_watch':'resource-monitor-r9'":"'prior_watch':'resource-monitor-r10'","source=H/'schedule_resource_watch_r9.py';target=H/'schedule_resource_watch_r10.py'":"source=H/'schedule_resource_watch_r10.py';target=H/'schedule_resource_watch_r11.py'","out=HERE/'resource-monitor-r9'":"out=HERE/'resource-monitor-r10'","out=HERE/'resource-monitor-r10'\"),encoding":"out=HERE/'resource-monitor-r11'\"),encoding"}
    # Derive scheduler replacement expression separately, since its old/new
    # literals overlap the folder names in the arm script.
    expr="target.write_text(code.replace(\"out=HERE/'resource-monitor-r9'\",\"out=HERE/'resource-monitor-r10'\"),encoding='utf-8')"
    assert code.count(expr)==1
    code=code.replace(expr,"target.write_text(code.replace(\"out=HERE/'resource-monitor-r10'\",\"out=HERE/'resource-monitor-r11'\"),encoding='utf-8')")
    for old,new in list(replacements.items())[:4]:
        assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
    old="code.count(\"out=HERE/'resource-monitor-r9'\")";assert code.count(old)==1;code=code.replace(old,"code.count(\"out=HERE/'resource-monitor-r10'\")")
    compile(code,str(target),'exec');target.write_text(code,encoding='utf-8')
    (H/'resource-watch-r11-derivation.json').write_text(json.dumps({'prior_arm_sha256':sha(source),'derived_arm_sha256':sha(target),'thresholds_unchanged':True,'new_heavy_slots':0},indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
