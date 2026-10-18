"""Verify and preserve the accepted r03 source before a bounded CORE edit."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=HERE/'prior-r03';receipt=HERE.parent/'receipt-r03.json'
 if old.exists():raise SystemExit('Archive already exists')
 d=json.loads(receipt.read_text());records=d['source_hashes'] if 'source_hashes' in d else d['hashes']
 for name,h in records.items():assert sha(ROOT/name)==h,name
 for name,h in records.items():
  dest=old/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest);assert sha(dest)==h
 shutil.copy2(receipt,old/'receipt-r03.json')
 (old/'archive-receipt.json').write_text(json.dumps({'verified_prior_source_files':len(records),'source_hashes':records,'read_only_originals_preserved_by_copy':True},indent=2)+'\n')
 print(json.dumps({'verified_archived_files':len(records),'archive':old.relative_to(ROOT).as_posix()}))
if __name__=='__main__':main()
