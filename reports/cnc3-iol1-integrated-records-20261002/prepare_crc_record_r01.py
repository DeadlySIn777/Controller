from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
D=H/'crc-share-record-candidate-r01';src=H/'timer-share-record-candidate-r02'
if D.exists():raise RuntimeError('fresh candidate required')
shutil.copytree(src,D,ignore=shutil.ignore_patterns('__pycache__'))
target=D/'cnc_iol1_record_master.v';old=sha(target);shutil.copyfile(H/'crc-share-stage-r01/cnc_iol1_record_master.v',target)
delta={'prior_candidate':str(src),'old_master_sha256':old,'new_master_sha256':sha(target),'scope':'one shared byte CRC datapath across mutually exclusive PREP/SHIFT states; no frame/state/timing/authority delta','formal_induction_stage':str(H/'crc-share-formal-r01'),'formal_proof_status_at_preparation':'NOT_RUN','adoption_or_vendor_fit':False}
(D/'crc-sharing-provenance.json').write_text(json.dumps(delta,indent=2)+'\n',newline='\n')
m=json.loads((D/'bundle-manifest.json').read_text());m['files']={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p not in (D/'bundle-manifest.json',D/'freeze-receipt.json')};(D/'bundle-manifest.json').write_text(json.dumps(m,indent=2)+'\n',newline='\n')
print(D,sha(D/'bundle-manifest.json'))
