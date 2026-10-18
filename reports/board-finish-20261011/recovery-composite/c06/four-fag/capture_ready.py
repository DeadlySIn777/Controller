"""Freeze the original native project and exact runner identities; no native work."""
import hashlib, json, shutil, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import measure_combined as M

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ready=HERE/'ready.json'
    if ready.exists():raise ValueError('Ready receipt already frozen')
    project=HERE/'inputs/project'
    if project.exists():raise ValueError('Native project clone already exists')
    shutil.copytree(HERE.parent/'four-path/inputs/project',project)
    originals={p.relative_to(HERE.parent/'four-path/inputs/project').as_posix():sha(p) for p in (HERE.parent/'four-path/inputs/project').rglob('*') if p.is_file()}
    clones={p.relative_to(project).as_posix():sha(p) for p in project.rglob('*') if p.is_file()}
    if originals!=clones:raise ValueError('Native project byte clone differs')
    construction=M.V.FAG/'staged/construction.json';candidate=M.V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb'
    contract=M.validate_construction(construction,candidate)
    audit=json.loads((HERE/'combined-audit.json').read_bytes())
    if audit['verdict']!='HOST_PASS_NATIVE_ELECTRICAL_OPEN' or audit['failures']:raise ValueError('Combined reference audit did not pass')
    helpers=M.helper_identities()
    files={str(p.resolve()):sha(p) for p in [HERE/'measure_combined.py',HERE/'native_entry.py',HERE/'validate_combined.py',HERE/'derive_runner.py',HERE/'runner-derivation.json',HERE/'combined-audit.json',Path(__file__)]}
    files.update(M.construction_hashes(construction));files.update(audit['source_files_sha256'])
    for path in project.rglob('*'):
        if path.is_file():files[str(path.resolve())]=sha(path)
    for path in M.SOURCE.rglob('*'):
        if path.is_file():files[str(path.resolve())]=sha(path)
    for path in [M.ROOT/'tools'/n for n in M.TOOL_NAMES]+[M.ROOT/'tools/heavyt.sh',M.PARSER,M.PCBTEXT,M.ROOT106_INPUTS,M.HERE/'gate-repair/partition_guard.py',M.PREVIOUS/'finish_bridge_proof.py']:
        files[str(path.resolve())]=sha(path)
    for item in helpers.values():files[item['path']]=item['sha256']
    binaries={role:{'path':str(path),'sha256':sha(path)} for role,path in M.NATIVE_BINARIES.items()}
    result={'schema':'four-fag-original-source-ready-v1','verdict':'READY_SOURCE_ONLY_NATIVE_OPEN','contract':contract,'candidate':str(candidate),'construction':str(construction),'files':files,'native_binaries':binaries,'imported_helpers_at_ready':helpers,'original_native_project_clone_exact':True,'root106_original_source':True,'capacitor_C11061_rating_correction':'OPEN; original16V unchanged','native_jobs':0,'adopted':False,'manufacturing_ready':False}
    ready.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':result['verdict'],'ready_sha256':sha(ready),'runner_sha256':sha(HERE/'measure_combined.py'),'candidate_sha256':sha(candidate),'bound_files':len(files)},indent=1))

if __name__=='__main__':main()
