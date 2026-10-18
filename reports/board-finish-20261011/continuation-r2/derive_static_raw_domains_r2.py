import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=H/'audit_static_raw_domains_r1.py';target=H/'audit_static_raw_domains_r2.py'
    assert not target.exists()
    s=source.read_text();old="hit=[r for r in patterns if fnmatch.fnmatchcase(raw,r['pattern'])]"
    new="hit=[r for r in patterns if raw==r['pattern'] or fnmatch.fnmatchcase(raw,r['pattern'])]"
    assert s.count(old)==1
    s=s.replace(old,new).replace('static-raw-domain-contract-r1','static-raw-domain-contract-r2')
    s=s.replace('Exact raw assignment plus case-sensitive glob diagnostic','Exact raw assignment and literal pattern first, plus case-sensitive glob diagnostic')
    target.write_text(s,encoding='utf-8')
    record={'parent_sha256':sha(source),'derived_sha256':sha(target),'reason':'All90 R1 missing rows have exact literal project patterns containing square brackets; generic glob-only matching misinterpreted those literal names. Preserve R1 failure; use exact literal match before glob diagnostic, without mutating raw names/project/source. Native effective class remains a separate obligation.'}
    (H/'static-raw-domain-derivation-r2.json').write_text(json.dumps(record,indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
