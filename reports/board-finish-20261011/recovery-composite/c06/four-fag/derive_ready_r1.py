"""Distinct runner refinement: enforce ready file/native pins before any native call."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
original=HERE/'measure_combined.py'
if hashlib.sha256(original.read_bytes()).hexdigest()!='b6c2846c3e353147a03ea1cef9ebaafb3c3dea27b2bed1de8b20d663a75cc8e2':raise ValueError('Prior runner identity differs')
raw=original.read_text()
raw=raw.replace('STAGE / \'ready.json\', STAGE / \'runner-derivation.json\'','STAGE / \'ready-r1.json\', STAGE / \'runner-derivation-r1.json\'')
raw=raw.replace('        construction = validate_construction(args.construction, args.candidate)', '''        ready = json.loads((STAGE / 'ready-r1.json').read_bytes())
        require(ready['verdict'] == 'READY_SOURCE_ONLY_NATIVE_OPEN', 'Ready source contract differs')
        for path, expected in ready['files'].items():
            require(digest(Path(path).read_bytes()) == expected, 'Ready input changed before native launch: ' + path)
        require(binary_identities(ReadSet()) == ready['native_binaries'], 'Ready native binary changed before launch')
        construction = validate_construction(args.construction, args.candidate)''')
target=HERE/'measure_combined_r1.py'
if target.exists():raise ValueError('Distinct r1 runner exists')
target.write_text(raw,encoding='utf-8')
receipt={'schema':'four-fag-runner-ready-enforcement-r1','previous_runner':str(original),'previous_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'runner':str(target),'runner_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'delta':'Require all frozen ready files and native binaries unchanged before starting any native phase','native_jobs':0,'adopted':False}
(HERE/'runner-derivation-r1.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
test=(HERE/'test_combined.py').read_text().replace('import measure_combined as M','import measure_combined_r1 as M').replace("   (args.out/'source/sch.net').write_bytes", "   (args.out/'source/sch.net').chmod(0o600)\n   (args.out/'source/sch.net').write_bytes")
(HERE/'test_combined_r1.py').write_text(test,encoding='utf-8')
print(json.dumps(receipt,indent=1))
