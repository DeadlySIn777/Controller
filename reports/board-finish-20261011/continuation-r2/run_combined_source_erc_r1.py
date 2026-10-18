"""Exact isolated source clone, four missing-only embedded libraries, export and native ERC."""
import collections, datetime, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
PRIOR = HERE / 'field-power/combined-power-source-r2'
REPAIR = REPORT / 'source-library-repair/v2'
OUT = HERE / 'combined-source-erc-r1'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snapshot(root): return {str(p.resolve()): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
def check(pins):
    for p, h in pins.items():
        if sha(p) != h: raise ValueError('Frozen input changed: ' + p)
def write(p, data): p.write_text(json.dumps(data, indent=1)+'\n', encoding='utf-8')
def main():
    if OUT.exists(): raise ValueError('Fresh ERC directory required')
    original = snapshot(PRIOR / 'source')
    receipt = json.loads((PRIOR / 'receipt.json').read_bytes())
    for rel, h in receipt['files'].items():
        if sha(PRIOR / rel) != h: raise ValueError('Combined source receipt changed: ' + rel)
    libraries = json.loads((REPAIR / 'receipt.json').read_bytes())['created_libraries']
    expected_names = {'motherboard_diagnostics.kicad_sym','motherboard_operator.kicad_sym','motherboard_power_entry.kicad_sym','motherboard_terminals.kicad_sym'}
    if set(libraries) != expected_names: raise ValueError('Missing-only library recipe differs')
    extra = {str(p.resolve()): sha(p) for p in [Path(__file__), PRIOR / 'receipt.json', PRIOR / 'source-export/fresh.net', PRIOR / 'source-export/receipt.json', REPAIR / 'receipt.json', Path('Z:/pcb-runs/claude-finish/tools/heavy.sh'), Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')]}
    OUT.mkdir()
    source = OUT / 'source'
    shutil.copytree(PRIOR / 'source', source)
    for name, spec in libraries.items():
        origin = REPAIR / 'native' / name
        if sha(origin) != spec['sha256'] or (source / name).exists(): raise ValueError('Missing-only library pin mismatch: ' + name)
        extra[str(origin.resolve())] = sha(origin)
        shutil.copy2(origin, source / name)
    clone = snapshot(source)
    for p, h in original.items():
        rel = Path(p).relative_to(PRIOR / 'source')
        if sha(source / rel) != h: raise ValueError('Clone differs: ' + str(rel))
    sys.path.insert(0, str(REPORT / 'parity-repair'))
    from host_parity import load_parser
    from fresh_export import canonical
    parser_path = REPORT / 'parity-repair/root106/tools/netlist_parity.py'
    for name in ['host_parity.py','fresh_export.py','prepare_parity.py','run_native_parity.py']:
        p = REPORT / 'parity-repair' / name
        extra[str(p.resolve())] = sha(p)
    extra[str(parser_path.resolve())] = sha(parser_path)
    parser = load_parser(parser_path)
    env = os.environ.copy()
    env['PATH'] = 'C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;' + env['PATH']
    prefix = ['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavy.sh','kicad','C:/Program Files/KiCad/10.0/bin/kicad-cli.exe']
    export = prefix + ['sch','export','netlist','--format','kicadsexpr','--output',str(OUT / 'fresh.net'),str(source / 'motherboard.kicad_sch')]
    erc = prefix + ['sch','erc',str(source / 'motherboard.kicad_sch'),'--output',str(OUT / 'erc.json'),'--format','json','--severity-all','--exit-code-violations']
    write(OUT / 'inputs.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'original': original, 'clone': clone, 'extra': extra, 'commands': [export, erc], 'slot': 'existing shared KiCad 2-slot pool', 'new_heavy_slots': 0})
    start = time.monotonic()
    with (OUT / 'export.log').open('w', encoding='utf-8') as log:
        exp = subprocess.run(export, env=env, cwd=source, stdout=log, stderr=subprocess.STDOUT)
    check({**original, **clone, **extra})
    if exp.returncode != 0: raise ValueError('Fresh export failed: ' + str(exp.returncode))
    baseline = canonical(parser['read_netlist'](PRIOR / 'source-export/fresh.net'))
    fresh = canonical(parser['read_netlist'](OUT / 'fresh.net'))
    if baseline != fresh: raise ValueError('Restored-library source semantics differ')
    write(OUT / 'export-receipt.json', {'verdict':'PASS_EXACT_SOURCE_SEMANTICS','components':len(fresh['components']),'nets':len(fresh['nets']),'nodes':len(fresh['node_assignments']),'fresh_export_sha256':sha(OUT / 'fresh.net'),'all_original_source_files_exact':True,'created_missing_libraries':libraries})
    print('Exact source export passed; native ERC running', flush=True)
    with (OUT / 'erc.log').open('w', encoding='utf-8') as log:
        run = subprocess.run(erc, env=env, cwd=source, stdout=log, stderr=subprocess.STDOUT)
    check({**original, **clone, **extra})
    report = json.loads((OUT / 'erc.json').read_bytes())
    violations = [v for sheet in report.get('sheets', []) for v in sheet.get('violations', [])]
    categories = collections.Counter((v.get('type','UNKNOWN'),v.get('severity','UNKNOWN')) for v in violations)
    result = {'verdict':'PASS_NATIVE_ERC' if run.returncode == 0 and not violations else 'NATIVE_ERC_VIOLATIONS','native_exit_code':run.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'violations':len(violations),'by_category':{str(k):v for k,v in sorted(categories.items())},'source_export_semantics':'PASS','source_and_libraries_unchanged':True,'ERC_report_sha256':sha(OUT / 'erc.json'),'source_only':True,'board_DRC_refill':'NOT_EXECUTED','adopted':False,'manufacturing_ready':False}
    write(OUT / 'receipt.json',result)
    print(json.dumps(result),flush=True)
    return 0 if result['verdict'] == 'PASS_NATIVE_ERC' else 1
if __name__ == '__main__': raise SystemExit(main())
