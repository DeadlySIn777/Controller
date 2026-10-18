"""Bind a fresh native job to the fully re-audited integer-grid reset copper."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    old=HERE/'stage_cap_reset_native_r3.py';new=HERE/'stage_cap_reset_native_r4.py';audit=HERE/'ground-escape-audit-r7/audit.json';a=json.loads(audit.read_bytes())
    if a['verdict']!='HOST_READY_NATIVE_ELECTRICAL_OPEN' or a['errors']:raise ValueError('Native-grid audit failed')
    if new.exists():raise ValueError('Fresh native staging required')
    raw=old.read_text(encoding='utf-8').replace("OUT=HERE/'cap-reset-native-r3'","OUT=HERE/'cap-reset-native-r4'").replace("HERE/'ground-escape-audit-r6/audit.json'","HERE/'ground-escape-audit-r7/audit.json'")
    new.write_text(raw,encoding='utf-8');(HERE/'cap-reset-native-grid-derivation-r4.json').write_text(json.dumps({'original':str(old),'original_sha256':sha(old),'derived':str(new),'derived_sha256':sha(new),'native_grid_audit':str(audit),'native_grid_audit_sha256':sha(audit),'changes':['Use independently re-audited native1nm coordinates for two added ground vias','All source/net/size/drill/annulus exact gates retained'],'adopted':False},indent=1)+'\n',encoding='utf-8')
    print(str(new),flush=True)
if __name__=='__main__':main()
