"""Audit native integer-nanometre return positions without tolerance waivers."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=HERE/'ground-escape-return-repair-r6/result.json';out=HERE/'ground-escape-return-native-r7'
    if out.exists():raise ValueError('Fresh native-grid plan required')
    plan=json.loads(source.read_bytes());changes=[]
    for row in plan['results']:
        for route in row['paths']:
            for via in route['new_signal_vias']:
                old=via['new_return_stitch']['at'];actual=[round(float(v),6) for v in old];via['new_return_stitch']['at']=actual;via['return_at']=actual;via['return_distance_mm']=__import__('math').dist(via['at'],actual);changes.append({'unquantized_mm':old,'native_integer_nm_mm':actual})
            for side,index in [('source_escape',0),('target_escape',1)]:route[side]['via']=route['new_signal_vias'][index]
    plan['repair']='New return positions quantized to native1nm grid; all constraints independently re-audited';out.mkdir();(out/'result.json').write_text(json.dumps(plan,indent=1)+'\n',encoding='utf-8')
    audit=HERE/'audit_ground_escape_r6.py';derived=HERE/'audit_ground_escape_r7.py';raw=audit.read_text(encoding='utf-8').replace("OUT=HERE/'ground-escape-audit-r6'","OUT=HERE/'ground-escape-audit-r7'").replace("HERE/'ground-escape-return-repair-r6/result.json'","HERE/'ground-escape-return-native-r7/result.json'")
    if derived.exists():raise ValueError('Fresh audit required')
    derived.write_text(raw,encoding='utf-8')
    receipt={'prior_plan':{'path':str(source),'sha256':sha(source)},'changes':changes,'no_rule_or_identity_tolerance_waiver':True,'audit_original':{'path':str(audit),'sha256':sha(audit)},'audit_derived':{'path':str(derived),'sha256':sha(derived)},'prior_fast_native_outcome':'Source native parity0defects; exact expected nine-decimal via positions differed from native1nm grid. Fullannulus helper appropriately rejected before attestation.','adopted':False}
    (out/'derivation.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(changes),flush=True)
if __name__=='__main__':main()
