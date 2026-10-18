"""Freeze distinct r1 ready contract while preserving every r0/source input."""
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import measure_combined_r1 as M
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    previous=json.loads((HERE/'ready.json').read_bytes())
    for path,expected in previous['files'].items():
        if sha(path)!=expected:raise ValueError('Prior frozen source changed:'+path)
    files=dict(previous['files'])
    for path in (HERE/'measure_combined_r1.py',HERE/'runner-derivation-r1.json',HERE/'derive_ready_r1.py',HERE/'test_combined_r1.py',Path(__file__)):
        files[str(path.resolve())]=sha(path)
    helpers=M.helper_identities()
    for identity in helpers.values():files[identity['path']]=identity['sha256']
    binaries={role:{'path':str(path),'sha256':sha(path)} for role,path in M.NATIVE_BINARIES.items()}
    if binaries!=previous['native_binaries']:raise ValueError('Native binary identity differs')
    result={**previous,'files':files,'native_binaries':binaries,'imported_helpers_at_ready':helpers,'previous_ready_sha256':sha(HERE/'ready.json'),'runner':str(HERE/'measure_combined_r1.py'),'runner_sha256':sha(HERE/'measure_combined_r1.py')}
    target=HERE/'ready-r1.json'
    if target.exists():raise ValueError('Ready r1 already frozen')
    target.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':result['verdict'],'ready_sha256':sha(target),'runner_sha256':result['runner_sha256'],'bound_files':len(files)},indent=1))
if __name__=='__main__':main()
