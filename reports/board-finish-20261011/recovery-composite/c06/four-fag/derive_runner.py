"""Make a distinct combined runner from the immutable reviewed four-path recipe."""
from pathlib import Path
import hashlib, json
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'four-path/measure_four.py'
EXPECTED='3818c3e914217aec1c5bb9f2cb330ef3b7be94b2fe8128a8f59fa2fba082c6ca'
if hashlib.sha256(BASE.read_bytes()).hexdigest()!=EXPECTED:raise ValueError('Frozen four runner differs')
raw=BASE.read_text()
raw=raw.replace('"""Measure four pure-add r07 signals against both r07/live and r06 with unchanged native rules."""','"""Measure exact four-signal/FAG addition; dual native guards and original source parity."""')
raw=raw.replace('import traceback','import traceback\nimport shutil\nimport sysconfig\nimport time\nsys.dont_write_bytecode = True')
raw=raw.replace('from compose_four import validate_construction, R07_SHA', '''from validate_combined import validate_construction, construction_hashes, R07_SHA
import validate_combined as V
sys.path.insert(0, str(HERE / 'parity-repair'))
from host_parity import load_parser, read_board_text, compare as host_compare, source_identity
from fresh_export import canonical
from run_native_parity import gate_report
SOURCE = HERE / 'parity-repair/root106/source'
PARSER = HERE / 'parity-repair/root106/tools/netlist_parity.py'
PCBTEXT = HERE / 'parity-repair/root106/tools/pcbtext.py'
ROOT106_INPUTS = HERE / 'parity-repair/root106/inputs.json'
NETLIST_SHA = 'df5f6cc6dbc7fa5d657fde31cd516927de84e5abcdfcb8c336eebd74ae32c65c'
''')
raw=raw.replace('"pcbnew_extension": Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/_pcbnew.pyd"),','"pcbnew_extension": Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/_pcbnew.pyd"),\n    "host_python": Path(sys.executable),\n    "slot_shell": Path("C:/Program Files/Git/usr/bin/sh.exe"),')
raw=raw.replace('construction_hashes = dict(receipt["source_files_sha256"])','construction_pins = construction_hashes(args.construction)\n        construction_pins.update(json.loads((STAGE / "combined-audit.json").read_bytes())["source_files_sha256"])\n        construction_pins[str((STAGE / "combined-audit.json").resolve())] = digest((STAGE / "combined-audit.json").read_bytes())')
raw=raw.replace('for path, expected in construction_hashes.items():','for path, expected in construction_pins.items():')
raw=raw.replace('"construction_file_hashes": construction_hashes,','"construction_file_hashes": construction_pins,')
start=raw.index('        sources = [ROOT / "tools" / n for n in TOOL_NAMES]')
end=raw.index('        require(len({p.name for p in sources})',start)
raw=raw[:start]+'''        source_check = prepare_source(args)
        helper_start = helper_identities()
        sources = [ROOT / 'tools' / n for n in TOOL_NAMES] + [ROOT / 'tools/heavyt.sh', Path(__file__),
                   STAGE / 'validate_combined.py', STAGE / 'native_entry.py', STAGE / 'combined-audit.json',
                   STAGE / 'ready.json', STAGE / 'runner-derivation.json',
                   HERE / 'gate-repair/partition_guard.py', PARSER, PCBTEXT,
                   PREVIOUS / 'finish_bridge_proof.py']
'''+raw[end:]
raw=raw.replace('initial_reads.verify()\n        inputs =', 'initial_reads.verify()\n        verify_helpers(helper_start)\n        inputs =')
raw=raw.replace('"construction_file_hashes": construction_pins, "construction_check": construction}', '"construction_file_hashes": construction_pins, "construction_check": construction,\n                  "source_parity_precheck": source_check, "imported_helpers": helper_start}')
old='''            result = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        require(result.returncode == 0, f"native measurement exited {result.returncode}")'''
new='''            native = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
            parity_error = None
            try:
                # Existing test slot runs short source/API checks while one shared
                # slot refills/DRCs. The native work remains strictly sequential
                # within each slot; no extra slot or GPU work is created.
                source_receipt = run_source_checks(args, inputs, inputs_sha256, env)
                write(args.out / 'source-proof.json', source_receipt)
            except Exception as exc:
                parity_error = str(exc)
                write(args.out / 'source-proof.json', {'verdict':'FAIL','reason':parity_error,'adopted':False})
            result_code = native.wait()
        require(result_code == 0, f"native measurement exited {result_code}")
        require(parity_error is None, 'Source/API proof failed: ' + str(parity_error))'''
if old not in raw:raise ValueError('Exact measurement invocation absent')
raw=raw.replace(old,new)
raw=raw.replace('    validate_construction(args.construction, args.candidate)\n    reads.verify()', '''    source_proof = reads.json(out / 'source-proof.json')
    require(source_proof['verdict'] == 'PASS', 'Fresh hierarchy/API proof failed')
    verify_source(args, inputs['source_parity_precheck'])
    for path, expected in source_proof['observed_output_hashes'].items():
        require(digest(reads.read(path)) == expected, 'Source/API output changed')
    verify_helpers(inputs['imported_helpers'])
    validate_construction(args.construction, args.candidate)
    reads.verify()''')
raw=raw.replace('"explicit_native_netlist_parity": "SEPARATE_SAME_HASH_RECEIPT_REQUIRED",', '''"explicit_native_netlist_parity": source_proof['native_api'],
            "fresh_hierarchy_export": source_proof['fresh_export'],
            "source_proof": source_proof, "imported_helpers": inputs['imported_helpers'],
            "capacitor_C11061_rating_correction": "OPEN; exact original r07/source still 16V",''')
helpers=r'''
def tree(folder):
    return {str(path.resolve()):digest(path.read_bytes()) for path in sorted(Path(folder).rglob('*')) if path.is_file()}

def helper_identities():
    stdlib=Path(sysconfig.get_path('stdlib')).resolve()
    sites={Path(sysconfig.get_path(role)).resolve() for role in ('purelib','platlib')}
    result={}
    for name,module in sorted(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        path=Path(filename).resolve()
        if path.is_relative_to(stdlib) and not any(path.is_relative_to(site) for site in sites):continue
        if path.suffix=='.pyc':path=Path(importlib.util.source_from_cache(str(path))).resolve()
        require(path.is_file(),'Loaded helper source unavailable:'+name)
        result[name]={'path':str(path),'sha256':digest(path.read_bytes())}
    required={'validate_combined','construct','whole_group_r3','compose_four','finish_bridge_proof',
              'host_parity','fresh_export','run_native_parity','prepare_parity','project_clone'}
    require(required<=set(result),'Loaded helper closure incomplete')
    return result

def verify_helpers(expected):
    require(helper_identities()==expected,'At-run loaded helper identities changed')

def prepare_source(args):
    expected=json.loads(ROOT106_INPUTS.read_bytes())
    for relative,sha in expected['snapshots'].items():
        if relative.startswith('source/'):
            require(digest((SOURCE.parent/relative).read_bytes())==sha,'Original ROOT106 source changed:'+relative)
    require(len(list(SOURCE.glob('*.kicad_sch')))==27,'Original source hierarchy count differs')
    require(digest((SOURCE/'sch.net').read_bytes())==NETLIST_SHA,'Original source netlist differs')
    source_copy=args.out/'source';shutil.copytree(SOURCE,source_copy)
    parser_initial=digest(PARSER.read_bytes());parser=load_parser(PARSER)
    require(digest(PARSER.read_bytes())==parser_initial,'AST parser changed while loading')
    netlist=parser['read_netlist'](source_copy/'sch.net')
    identities=source_identity(source_copy,netlist,parser)
    board=read_board_text(args.candidate,parser,PCBTEXT)
    host=host_compare(netlist,board,parser)
    require(identities['verdict']==host['verdict']=='PASS','Original hierarchy/candidate portable parity failed')
    write(args.out/'host-parity.json',host);write(args.out/'source-identity.json',identities)
    write(args.out/'host-board-table.json',board)
    require(len(netlist['components'])==2717 and len(netlist['nets'])==2384 and len(netlist['node_net'])==9590,'Original hierarchy inventory differs')
    copper=V.C.P.R.composition.inventory(args.candidate.read_bytes())
    r07=V.C.P.R.composition.inventory(args.before_board.read_bytes())
    vias=[]
    for uid,ch in copper[4].items():
        if uid in r07[4]:continue
        row=V.C.W.parse_copper(uid,ch)
        if row['kind']=='via':vias.append({key:row[key] for key in ('uuid','net','at','d','drill')})
    require(len(vias)==7,'Expected five FIELD/two signal vias')
    write(args.out/'native-via-spec.json',{'board_sha256':digest(args.candidate.read_bytes()),'added_vias':vias})
    api=args.out/'parity-copy';shutil.copytree(STAGE/'inputs/project',api)
    (api/'board.kicad_pro').write_bytes((api/'board.kicad_pro.good').read_bytes());(api/'board.kicad_pro.good').unlink()
    (api/'board.kicad_pcb').write_bytes(args.candidate.read_bytes())
    result={'source_original':tree(SOURCE),'source_copy':tree(source_copy),'api_copy':tree(api),
            'original_root106_inputs':{'path':str(ROOT106_INPUTS),'sha256':digest(ROOT106_INPUTS.read_bytes())},
            'saved_export_sha256':NETLIST_SHA,'parser_sha256':parser_initial,'pcbtext_sha256':digest(PCBTEXT.read_bytes()),
            'host_parity':host,'source_identity':identities,'native_via_spec_sha256':digest((args.out/'native-via-spec.json').read_bytes()),
            'capacitor_C11061_rating_correction':'OPEN; retained original 16V source/board',
            'limits':'Original embedded source cache. Symbol reload/resource reconciliation, ERC, electrical and timing remain OPEN'}
    return result

def verify_source(args,expected):
    require(tree(SOURCE)==expected['source_original'],'Original source tree changed')
    require(tree(args.out/'source')==expected['source_copy'],'Source hierarchy clone changed')
    require(tree(args.out/'parity-copy')==expected['api_copy'],'Native API project clone changed')
    require(digest(ROOT106_INPUTS.read_bytes())==expected['original_root106_inputs']['sha256'],'Original source receipt changed')
    require(digest(PARSER.read_bytes())==expected['parser_sha256'] and digest(PCBTEXT.read_bytes())==expected['pcbtext_sha256'],'Parser/text helper changed')
    require(digest((args.out/'native-via-spec.json').read_bytes())==expected['native_via_spec_sha256'],'Native via spec changed')

def run_source_checks(args,inputs,inputs_sha256,env):
    out=args.out; context=inputs['source_parity_precheck']; wrapper=ROOT/'tools/heavyt.sh'
    verify_inputs(out,inputs,inputs_sha256,ReadSet());verify_source(args,context);verify_helpers(inputs['imported_helpers'])
    parser=load_parser(PARSER)
    command=['C:/Program Files/Git/usr/bin/sh.exe',wrapper.as_posix(),'kicad',str(NATIVE_BINARIES['kicad_cli']),
             'sch','export','netlist','--format','kicadsexpr','--output',(out/'fresh.net').as_posix(),(out/'source/motherboard.kicad_sch').as_posix()]
    start=time.time()
    with (out/'source-export.log').open('w',encoding='utf-8') as log:
        run=subprocess.run(command,env=env,cwd=out/'source',stdout=log,stderr=subprocess.STDOUT,check=False)
    require(run.returncode==0 and (out/'fresh.net').stat().st_mtime>=start-1,'Fresh hierarchy export failed/stale')
    old=parser['read_netlist'](out/'source/sch.net');fresh=parser['read_netlist'](out/'fresh.net')
    require(canonical(old)==canonical(fresh),'Fresh hierarchy semantics differ')
    export={'verdict':'PASS','command':command,'native_exit_code':run.returncode,'fresh_sha256':digest((out/'fresh.net').read_bytes()),
            'saved_sha256':NETLIST_SHA,'components':len(fresh['components']),'nets':len(fresh['nets']),'nodes':len(fresh['node_net']),
            'semantic_components_nets_nodes_exact':True,'cli_DRC_schematic_parity':'NOT_RUN_BY_EXPORT','ERC':'NOT_RUN'}
    verify_inputs(out,inputs,inputs_sha256,ReadSet());verify_source(args,context);verify_helpers(inputs['imported_helpers'])
    command=['C:/Program Files/Git/usr/bin/sh.exe',wrapper.as_posix(),'kicad',str(NATIVE_BINARIES['native_python']),
             str(STAGE/'native_entry.py'),str(PARSER),str(out/'native-via-spec.json'),(out/'parity-copy/board.kicad_pcb').as_posix(),
             '--netlist',(out/'source/sch.net').as_posix(),'--no-connectivity','--examples','40',(out/'native-parity.json').as_posix()]
    start=time.time()
    with (out/'native-parity.log').open('w',encoding='utf-8') as log:
        run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
    require(run.returncode==0 and (out/'native-parity.json').stat().st_mtime>=start-1,'Native API parity failed/stale')
    report=json.loads((out/'native-parity.json').read_bytes())
    api=gate_report(report,{'board_sha256':inputs['after_sha256'],'netlist_sha256':NETLIST_SHA},context['host_parity'])
    require(report['project_settings_binding']['explicit_board_set_project'] is True,'Native project binding absent')
    require(report['added_via_annuli']['verdict']=='PASS' and len(report['added_via_annuli']['rows'])==7,'Native added via annulus gate failed')
    api.update(command=command,native_exit_code=run.returncode,added_via_annuli=report['added_via_annuli'])
    verify_inputs(out,inputs,inputs_sha256,ReadSet());verify_source(args,context);verify_helpers(inputs['imported_helpers'])
    outputs={str((out/name).resolve()):digest((out/name).read_bytes()) for name in ('fresh.net','native-parity.json','host-parity.json','source-identity.json','host-board-table.json','native-via-spec.json')}
    return {'verdict':'PASS','candidate_sha256':inputs['after_sha256'],'original_hierarchy':True,
            'fresh_export':export,'native_api':api,'observed_output_hashes':outputs,'adopted':False,
            'limits':['Explicit source/API parity; CLI DRC parity execution is separately labelled','C11061 original16V correction OPEN','No ERC/electrical/timing/thermal/SI/physical qualification']}

'''
raw=raw.replace('\ndef main():','\n'+helpers+'\ndef main():')
out=HERE/'measure_combined.py'
if out.exists():raise ValueError('Distinct derivation already exists')
out.write_text(raw,encoding='utf-8')
receipt={'schema':'four-fag-dual-native-source-runner-v1','baseline_runner':str(BASE),'baseline_sha256':EXPECTED,
         'runner':str(out),'runner_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'native_jobs':0,
         'changes':['Frozen combined replay/manifest plus prospective reference audit binding','Original ROOT106 hierarchy clone and fresh exact semantic SCH export','Same-candidate explicitly bound API parity and seven native via annuli','Existing shared board slot plus existing test slot in parallel, no new slots','All loaded nonstdlib imported helpers bound before/after; AST parser/text helper separately pinned','Both r07/live and r06 strict guards remain fatal; full footprint preservation retained']}
(HERE/'runner-derivation.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=1))
