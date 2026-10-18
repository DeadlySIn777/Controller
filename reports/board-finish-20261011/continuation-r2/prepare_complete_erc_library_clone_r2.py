"""Complete only the verified library dependencies of the exact prior ERC clone."""
import hashlib, json, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent
OLD = HERE / 'combined-source-erc-r1'
OUT = HERE / 'combined-source-erc-r2-prepared'
REPAIR = HERE.parent / 'source-library-repair/v2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    if OUT.exists(): raise ValueError('Fresh library-complete ERC preparation required')
    prior = json.loads((OLD / 'inputs.json').read_bytes())
    for p, h in prior['clone'].items():
        if sha(p) != h: raise ValueError('Prior frozen ERC clone changed: ' + p)
    recipe = json.loads((REPAIR / 'receipt.json').read_bytes())
    if recipe['verdict'] != 'EMBEDDED_LIBRARY_REPAIR_AND_NATIVE_EXPORT_PASS' or recipe['library_comparison']['verdict'] != 'PASS': raise ValueError('Original library restoration not qualified')
    files = recipe['library_comparison']['files']
    if len(files) != 27: raise ValueError('Expected 27 exact symbol libraries')
    pins = {str(Path(__file__).resolve()):sha(__file__), str((REPAIR / 'receipt.json').resolve()):sha(REPAIR / 'receipt.json'), str((OLD / 'receipt.json').resolve()):sha(OLD / 'receipt.json')}
    OUT.mkdir()
    source = OUT / 'source'
    shutil.copytree(OLD / 'source', source)
    restored = []
    for name, spec in files.items():
        p = Path(spec['path'])
        if sha(p) != spec['sha256']: raise ValueError('Library input changed: ' + name)
        pins[str(p.resolve())] = sha(p)
        target = source / name
        if target.exists():
            if sha(target) != spec['sha256']: raise ValueError('Existing cloned library differs: ' + name)
        else:
            shutil.copy2(p,target)
            restored.append(name)
    footprint_files = {rel:h for rel,h in recipe['native_design_input_hashes'].items() if '.pretty/' in rel and rel.endswith('.kicad_mod')}
    if len(footprint_files) != 15: raise ValueError('Expected 15 original local footprint dependencies')
    for rel,h in footprint_files.items():
        p = REPAIR / 'native' / rel
        if sha(p) != h: raise ValueError('Original local footprint changed: ' + rel)
        pins[str(p.resolve())] = h
        target = source / rel
        if target.exists(): raise ValueError('Unexpected prior footprint dependency: ' + rel)
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(p,target)
    for p,h in prior['clone'].items():
        relative = Path(p).relative_to(OLD / 'source')
        if sha(source / relative) != h: raise ValueError('Original ERC source clone altered: ' + str(relative))
    for p,h in pins.items():
        if sha(p) != h: raise ValueError('Preparation input changed: ' + p)
    receipt = {'verdict':'PASS_EXACT_DEPENDENCY_CLONE_ONLY','prior_ERC_receipt':str(OLD / 'receipt.json'),'original_source_files_exact':True,'all27_symbol_libraries_available':True,'newly_copied_original_symbol_libraries':restored,'copied_original_local_footprints':footprint_files,'hierarchy_error':'OPEN_PENDING_SOURCE_OWNERS_CORRECTION','netlist_export_ERC':'NOT_EXECUTED','input_hashes':pins,'clone_hashes':{str(p.resolve()):sha(p) for p in sorted(source.rglob('*')) if p.is_file()},'adopted':False}
    (OUT / 'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['input_hashes','clone_hashes','copied_original_local_footprints']}),flush=True)
if __name__ == '__main__': main()
