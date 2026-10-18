from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',newline='\n')
write(H/'timer-share-record-candidate-r01/preparation-failure.json',{'status':'FAIL','reason':'Preparation expected a nested motion manifest absent from this actual frozen source. No validation run. Preserved unchanged partial candidate; r02 checks actual files.'})
D=H/'timer-share-record-candidate-r02';src=H/'constant-compare-record-candidate-r01'
if D.exists():raise RuntimeError('fresh candidate required')
shutil.copytree(src,D,ignore=shutil.ignore_patterns('__pycache__'))
target=D/'inputs/motion/cnc3_stepgen_runtime.v';old=sha(target);shutil.copyfile(H/'timer-share-stage-r01/cnc3_stepgen_runtime.v',target)
write(D/'timer-sharing-provenance.json',{'status':'PASS','prior_candidate':str(src),'old_runtime_sha256':old,'new_runtime_sha256':sha(target),'only_delta':'16-bit mutually-exclusive STEP high/low/DIR setup timers share one counter; signed count increment shares one adder','formal_receipt':str(H/'timer-share-formal-r01/receipt.json'),'actual_cycle_receipt':str(H/'timer-share-stage-r01/equivalence-receipt.json'),'compiled_mutation_receipt':str(H/'timer-share-mutations-r01/receipt.json'),'product_abi_or_rating_changed':False})
m=json.loads((D/'bundle-manifest.json').read_text());m['files']={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p not in (D/'bundle-manifest.json',D/'freeze-receipt.json')};write(D/'bundle-manifest.json',m)
print(D,sha(D/'bundle-manifest.json'))
