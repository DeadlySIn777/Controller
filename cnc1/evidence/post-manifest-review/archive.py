"""Archive the previous recorded milestone without claiming changed files match."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

root=Path(__file__).resolve().parents[3]
task=Path('/root/.cache/controller-lab-linuxcnc/rootfs/work')
archive=Path(__file__).resolve().parent/'prior-recorded-milestone'
manifest=json.loads((root/'cnc1/evidence/manifest.json').read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
archive.mkdir(exist_ok=True)
copied=[];diffs=[];freeze={}
for section in ('source_sha256','evidence_sha256'):
    for name,expected in manifest[section].items():
        current=(root/name).read_bytes();original=current;origin='unchanged workspace file'
        if section=='source_sha256':freeze[name]=sha(current)
        if sha(original)!=expected:
            candidate=task/name
            if candidate.is_file() and sha(candidate.read_bytes())==expected:
                original=candidate.read_bytes();origin='actual tested task-rootfs source'
            elif name.startswith('cnc1/tools/'):
                original=current.replace(b'task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}\nexport CONTROLLER_LAB_ROOTFS="$task_root"',b'task_root=/root/.cache/controller-lab-linuxcnc/rootfs')
                original=original.replace(b'task_root=$CONTROLLER_LAB_ROOTFS',b'task_root=/root/.cache/controller-lab-linuxcnc/rootfs')
                origin='reconstructed by reversing isolated rootfs-override edits; verified against original recorded SHA256'
            elif name=='reports/CNC1_INTEGRATION.md':
                original=current.replace(b' The original `simulation.log` hashed in that archived manifest was overwritten by the later re-run and is not archived; only its hash is retained (see `ARCHIVE_NOTE.md` in that directory).',b'')
                origin='reconstructed by removing later archive-note sentence; verified against original recorded SHA256'
            if sha(original)!=expected:raise SystemExit('Cannot recover recorded bytes: '+name)
            diffs.extend(difflib.unified_diff(original.decode().splitlines(True),current.decode().splitlines(True),fromfile='recorded/'+name,tofile='current/'+name))
        target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(original)
        copied.append({'path':name,'sha256':expected,'source':origin})
binary=(root/'cnc1/build/cnc1_sim.so').read_bytes()
assert sha(binary)==manifest['module_sha256']
(archive/'cnc1_sim.so').write_bytes(binary)
shutil.copy2(root/'cnc1/evidence/manifest.json',archive/'manifest.json')
(archive/'archive-inventory.json').write_text(json.dumps(copied,indent=2)+'\n')
(archive.parent/'post-manifest-diff.patch').write_text(''.join(diffs))
(archive.parent/'pre-rerun-source-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
print(json.dumps({'archived_files':len(copied),'module_sha256':sha(binary),'changed_sources':sum(1 for v in copied if v['source']!='unchanged workspace file')}))
