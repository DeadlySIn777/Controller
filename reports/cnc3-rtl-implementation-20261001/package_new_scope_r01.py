"""Only new scope paths; preserves existing source/PCB/RTL and frozen worktree."""
from pathlib import Path
import hashlib,json,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];DEST=ROOT/'gateware/v3';EXTERNAL=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not DEST.exists(),'Do not overwrite any pre-existing v3 work'
stage=BASE/'stage-r01';proof=BASE/'proof-r08'
assert json.loads((proof/'receipt.json').read_text())['status']=='PASS'
DEST.mkdir();(DEST/'rtl').mkdir();(DEST/'frozen').mkdir();(DEST/'tools').mkdir()
for f in (proof/'inputs/rtl').glob('*.v'):
 assert sha(f)==sha(stage/'rtl'/f.name);shutil.copyfile(f,DEST/'rtl'/f.name)
for f in (stage/'frozen').rglob('*'):
 if f.is_file() and '__pycache__' not in f.parts:
  dest=DEST/'frozen'/f.relative_to(stage/'frozen');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
reference=DEST/'frozen/cnc3';reference.mkdir()
for name in ['cnc3_proto.c','cnc3_proto.h','cnc3_proto_types.h','cnc3_layout.h','cnc3_rules.h']:
 src=EXTERNAL/'cnc3/src'/name;shutil.copyfile(src,reference/name)
 assert sha(src)==sha(proof/'oracle'/name),'Reference differs from tested original C oracle'
manifest={'schema_version':1,'spec_revision':'IS-1','scope':'unchanged fixed96/176-byte structural transport/codec only','original_external_root':str(EXTERNAL),'files':{str(f.relative_to(DEST/'frozen')).replace('\\','/'):sha(f) for f in (DEST/'frozen').rglob('*') if f.is_file()},'stateful_endpoint_implemented':False,'HAL_implemented':False,'hardware_qualified':False}
(DEST/'frozen/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# The rule generator operates only on packaged frozen inputs. --check is readonly;
# --write explicitly regenerates exactly the three generated RTL files.
generator=(BASE/'build_stage_r01.py').read_text()
generator=generator.replace('from pathlib import Path','from pathlib import Path\nimport argparse')
lo=generator.index('HERE =');hi=generator.index('ERRORS =')
generator=generator[:lo]+"OUT=Path(__file__).resolve().parents[1]\nWRITE=False\n"+generator[hi:]
lo=generator.index("    files =");hi=generator.index('    m=importlib',lo)
generator=generator[:lo]+'''    manifest=json.loads((frozen/'manifest.json').read_text())
    for rel,digest in manifest['files'].items():
        if sha(frozen/rel)!=digest:raise ValueError('Frozen input hash mismatch: '+rel)
    def emit(relative,text):
        destination=OUT/relative
        if WRITE:destination.write_text(text,encoding='utf8')
        elif not destination.is_file() or destination.read_text(encoding='utf8')!=text:
            raise ValueError('Generated RTL is stale: '+relative)
'''+generator[hi:]
generator=generator.replace("(rtl/'cnc3_command_validate.v').write_text('\\n'.join(lines),encoding='utf8')","emit('rtl/cnc3_command_validate.v','\\n'.join(lines))")
generator=generator.replace("(rtl/(module+'.v')).write_text('\\n'.join(text),encoding='utf8')","emit('rtl/'+module+'.v','\\n'.join(text))")
lo=generator.index("    (OUT/'frozen-inputs.json')");hi=generator.index('    return p,s',lo)
generator=generator[:lo]+generator[hi:]
generator=generator.replace("if __name__=='__main__':build()", "if __name__=='__main__':\n    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group();group.add_argument('--check',action='store_true');group.add_argument('--write',action='store_true');args=parser.parse_args();WRITE=args.write;build()")
(DEST/'tools/generate_protocol_rtl.py').write_text(generator)
# Portable actual compiler runner: original C comes only from verified frozen
# package, no external worktree or fabricated endpoint is involved.
runner=(BASE/'test_stage_r01.py').read_text()
lo=runner.index('HERE=');hi=runner.index('def sha(',lo)
runner=runner[:lo]+"ROOT=Path(__file__).resolve().parents[1]\nSTAGE=ROOT/'gateware/v3';OUT=ROOT/'reports/cnc3-rtl-validation'\nEXTERNAL=STAGE/'frozen'\n"+runner[hi:]
runner=runner.replace("EXTERNAL/'cnc3/src'","EXTERNAL/'cnc3'")
runner=runner.replace("originals={str(f):sha(f) for f in (EXTERNAL/'cnc3').glob('cnc3_proto*')}","originals={str(f):sha(f) for f in (EXTERNAL/'cnc3').glob('*') if f.is_file()}\n manifest=json.loads((EXTERNAL/'manifest.json').read_text());assert all(sha(EXTERNAL/f)==h for f,h in manifest['files'].items()),'Frozen input hash mismatch'")
# Preserve actual negative-test fixture text in a reusable simulator input file.
(ROOT/'tools/check_cnc3_rtl.py').write_text(runner)
receipt={'status':'PASS','scope':'new files only','package_source_evidence':str(proof/'receipt.json'),'new_files':{str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for f in DEST.rglob('*') if f.is_file()},'check_tool_sha256':sha(ROOT/'tools/check_cnc3_rtl.py'),'existing_source_or_PCB_changed':False,'historical_CNC1_changed':False,'external_sources_changed':False}
(BASE/'new-package-transaction-r01.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'PASS','new_files':len(receipt['new_files'])}))
