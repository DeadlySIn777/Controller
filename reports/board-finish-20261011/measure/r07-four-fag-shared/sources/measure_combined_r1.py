"""Measure exact four-signal/FAG addition; dual native guards and original source parity."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import shutil
import sysconfig
import time
sys.dont_write_bytecode = True

STAGE = Path(__file__).resolve().parent
HERE = STAGE.parent.parent.parent
PREVIOUS = HERE.parent / "routing-resume-20261011"
sys.path.insert(0, str(PREVIOUS))
import importlib.util
guard_spec = importlib.util.spec_from_file_location("composite_partition_guard", HERE / "gate-repair/partition_guard.py")
guard_module = importlib.util.module_from_spec(guard_spec)
guard_spec.loader.exec_module(guard_module)
compare, check_board = guard_module.compare, guard_module.check_board
from finish_bridge_proof import (ReadSet, digest, manifest, library_inventory,
                                 footprint_fingerprint, check_summary, PROJECT_NAMES, require)
sys.path.insert(0, str(STAGE))
from validate_combined import validate_construction, construction_hashes, R07_SHA
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


ROOT = Path("Z:/pcb-runs/claude-finish")
TOOL_NAMES = ("step_measure.sh", "step_summary.py", "net_partitions.py", "heavy.sh")
NATIVE_BINARIES = {
    "kicad_cli": Path("C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"),
    "native_python": Path("C:/Program Files/KiCad/10.0/bin/python.exe"),
    "pcbnew_python": Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/pcbnew.py"),
    "pcbnew_extension": Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/_pcbnew.pyd"),
    "host_python": Path(sys.executable),
    "slot_shell": Path("C:/Program Files/Git/usr/bin/sh.exe"),
}


def write(path, value):
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def status(out, phase, **extra):
    record = {"phase": phase, "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "pid": os.getpid(), "adopted": False, **extra}
    write(out / "status.json", record)
    print(json.dumps(record), flush=True)


def binary_identities(reads):
    identities = {}
    for role, path in NATIVE_BINARIES.items():
        require(path.is_file(), "expected native binary unavailable: " + str(path))
        identities[role] = {"path": str(path.resolve()), "sha256": digest(reads.read(path))}
    return identities


def verify_inputs(out, inputs, inputs_sha256, reads):
    raw = reads.read(out / "inputs.json")
    require(digest(raw) == inputs_sha256, "saved inputs.json bytes changed during native run")
    require(json.loads(raw) == inputs, "saved inputs.json disagrees with run inputs")
    require(binary_identities(reads) == inputs["native_binaries"], "native binary identity changed during run")


def combined_verdict(live_guard, r06_guard, drc_errors):
    return "PASS" if live_guard["verdict"] == "PASS" and r06_guard["verdict"] == "PASS" and drc_errors == 0 else "FAIL"


def evaluate(args, inputs, inputs_sha256):
    out, bm = args.out, args.before_measure
    reads = ReadSet()
    verify_inputs(out, inputs, inputs_sha256, reads)
    boards = {"before": reads.read(args.before_board), "after": reads.read(args.candidate)}
    for role in boards:
        require(digest(boards[role]) == inputs[role + "_sha256"], "source board changed during native run")
    construction = validate_construction(args.construction, args.candidate)
    require(reads.read(args.construction) == reads.read(out / "construction.json"), "construction receipt changed")
    for path, expected in inputs["construction_file_hashes"].items():
        require(digest(reads.read(path)) == expected, "construction input changed: " + path)
    for path, expected in inputs["baseline_file_hashes"].items():
        require(digest(reads.read(path)) == expected, "frozen baseline evidence changed: " + path)
    footprints = {role: footprint_fingerprint(data) for role, data in boards.items()}
    require(footprints["before"] == footprints["after"], "pure-add candidate changes footprints/pads/poses")
    b, a = reads.json(out / "baseline-partitions.json"), reads.json(out / "partitions.json")
    check_board(b, args.before_board)
    check_board(a, args.candidate)
    guard = compare(b, a)
    r06 = reads.json(out / "r06-partitions.json")
    check_board(r06, args.r06_board)
    r06_guard = compare(r06, a)
    require(digest(reads.read(args.r06_board)) == inputs["r06_sha256"], "r06 source board changed")
    require(digest(reads.read(args.live_board)) == inputs["before_sha256"], "actual live board changed")
    for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
        require(reads.read(out / ("r06-" + name)) == reads.read(args.r06_measure / name), "r06 evidence changed")
    r06_manifest = manifest(reads.read(out / "r06-sha256.txt"))
    require(r06_manifest["board.kicad_pcb"] == inputs["r06_sha256"], "r06 manifest board differs")
    for name in PROJECT_NAMES | {"board.kicad_pcb"}:
        require(digest(reads.read(args.r06_measure / "copy" / name)) == r06_manifest[name], "r06 measured copy changed")
    manifests = {"before": manifest(reads.read(out / "baseline-sha256.txt")),
                 "after": manifest(reads.read(out / "sha256.txt"))}
    for role, directory in (("before", bm / "copy"), ("after", out / "copy")):
        require(manifests[role]["board.kicad_pcb"] == inputs[role + "_sha256"], "manifest board differs")
        for name in PROJECT_NAMES | {"board.kicad_pcb"}:
            require(digest(reads.read(directory / name)) == manifests[role][name], "measured copy changed: " + name)
    for name in PROJECT_NAMES:
        require(manifests["before"][name] == manifests["after"][name] == r06_manifest[name], "native rules/source changed: " + name)
    for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
        require(reads.read(out / ("baseline-" + name)) == reads.read(bm / name), "baseline evidence changed")
    before_libs = library_inventory(bm / "copy", reads)
    after_libs = library_inventory(out / "copy", reads)
    require(before_libs == after_libs == library_inventory(args.r06_measure / "copy", reads), "effective footprint resources differ")
    require(after_libs == inputs["library_inventory_at_start"], "footprint resources changed during run")
    drcs = {}
    for role, prefix, parts in (("before", "baseline-", b), ("after", "", a)):
        drcs[role] = check_summary(reads.json(out / (prefix + "drc.json")), parts,
                                  reads.json(out / (prefix + "summary.json")), inputs[role + "_sha256"])
    require(drcs["before"]["kicad"] == drcs["after"]["kicad"], "KiCad versions differ")
    drcs["r06"] = check_summary(reads.json(out / "r06-drc.json"), r06,
                                reads.json(out / "r06-summary.json"), inputs["r06_sha256"])
    require(drcs["r06"]["kicad"] == drcs["after"]["kicad"], "r06 KiCad version differs")
    for path, expected in inputs["tools"].items():
        require(digest(reads.read(path)) == expected, "tool changed during native run: " + path)
        require(digest(reads.read(out / "sources" / Path(path).name)) == expected, "tool snapshot differs")
    start = (out / "inputs.json").stat().st_mtime_ns
    for name in ("partitions.json", "drc.json", "summary.json", "sha256.txt"):
        require((out / name).stat().st_mtime_ns >= start, "receipt predates this native run")
    cli_log = reads.read(out / "drc.log").decode("utf-8", errors="replace")
    cli_parity = ("NOT_EXECUTED" if "Failed to fetch schematic netlist" in cli_log
                  or "Schematic parity tests require" in cli_log else "NO_REPORTED_DIAGNOSTIC; execution needs independent source/API proof")
    source_proof = reads.json(out / 'source-proof.json')
    require(source_proof['verdict'] == 'PASS', 'Fresh hierarchy/API proof failed')
    verify_source(args, inputs['source_parity_precheck'])
    for path, expected in source_proof['observed_output_hashes'].items():
        require(digest(reads.read(path)) == expected, 'Source/API output changed')
    verify_helpers(inputs['imported_helpers'])
    validate_construction(args.construction, args.candidate)
    reads.verify()
    passed = combined_verdict(guard, r06_guard, drcs["after"]["errors"]) == "PASS"
    return {"verdict": "PASS" if passed else "FAIL", "adopted": False, "manufacturing_ready": False,
            "candidate_sha256": inputs["after_sha256"], "connectivity": guard, "connectivity_r07_live": guard, "connectivity_r06": r06_guard, "drc": drcs,
            "inputs_sha256": inputs_sha256, "native_binaries": inputs["native_binaries"],
            "footprints": footprints["after"], "project_hashes": manifests["after"],
            "exact_reconstructed_source_contract": construction,
            "cli_schematic_parity": cli_parity,
            "explicit_native_netlist_parity": source_proof['native_api'],
            "fresh_hierarchy_export": source_proof['fresh_export'],
            "source_proof": source_proof, "imported_helpers": inputs['imported_helpers'],
            "capacitor_C11061_rating_correction": "OPEN; exact original r07/source still 16V",
            "observed_file_hashes": reads.hashes, "evidence_class": "native KiCad refill/DRC/connectivity",
            "limits": ["No electrical/current/thermal/SI or physical qualification",
                       "Native unconnected report is capped; use uncapped pad partitions/API",
                       "Final manufacture and source adoption gates remain open"]}



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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("before-board", "before-measure", "candidate", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--construction", type=Path, required=True)
    for name in ("r06-board", "r06-measure", "live-board"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    try:
        ready = json.loads((STAGE / 'ready-r1.json').read_bytes())
        require(ready['verdict'] == 'READY_SOURCE_ONLY_NATIVE_OPEN', 'Ready source contract differs')
        for path, expected in ready['files'].items():
            require(digest(Path(path).read_bytes()) == expected, 'Ready input changed before native launch: ' + path)
        require(binary_identities(ReadSet()) == ready['native_binaries'], 'Ready native binary changed before launch')
        construction = validate_construction(args.construction, args.candidate)
        receipt = json.loads(args.construction.read_text(encoding="utf-8"))
        require(digest(args.before_board.read_bytes()) == R07_SHA, "baseline is not frozen actual r07")
        require(digest(args.live_board.read_bytes()) == R07_SHA, "actual live board is not frozen r07")
        require(digest(args.r06_board.read_bytes()) == "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53", "r06 source differs")
        records = []
        def collect(value):
            if isinstance(value, dict):
                if {"path", "sha256"} <= set(value):
                    records.append(value)
                else:
                    for item in value.values(): collect(item)
            elif isinstance(value, list):
                for item in value: collect(item)
        collect(receipt)
        construction_pins = construction_hashes(args.construction)
        construction_pins.update(json.loads((STAGE / "combined-audit.json").read_bytes())["source_files_sha256"])
        construction_pins[str((STAGE / "combined-audit.json").resolve())] = digest((STAGE / "combined-audit.json").read_bytes())
        for path, expected in construction_pins.items():
            require(digest(Path(path).read_bytes()) == expected, "construction binding changed")
        (args.out / "construction.json").write_bytes(args.construction.read_bytes())
        source_check = prepare_source(args)
        helper_start = helper_identities()
        sources = [ROOT / 'tools' / n for n in TOOL_NAMES] + [ROOT / 'tools/heavyt.sh', Path(__file__),
                   STAGE / 'validate_combined.py', STAGE / 'native_entry.py', STAGE / 'combined-audit.json',
                   STAGE / 'ready-r1.json', STAGE / 'runner-derivation-r1.json',
                   HERE / 'gate-repair/partition_guard.py', PARSER, PCBTEXT,
                   PREVIOUS / 'finish_bridge_proof.py']
        require(len({p.name for p in sources}) == len(sources), "source snapshot names collide")
        (args.out / "sources").mkdir()
        for p in sources:
            (args.out / "sources" / p.name).write_bytes(p.read_bytes())
        for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
            (args.out / ("baseline-" + name)).write_bytes((args.before_measure / name).read_bytes())
            (args.out / ("r06-" + name)).write_bytes((args.r06_measure / name).read_bytes())
        initial_reads = ReadSet()
        libs = library_inventory(args.before_measure / "copy", initial_reads)
        native_binaries = binary_identities(initial_reads)
        baseline_file_hashes = {}
        for directory in (args.before_measure, args.r06_measure):
            paths = [directory / name for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json")]
            paths += [directory / "copy" / name for name in PROJECT_NAMES | {"board.kicad_pcb"}]
            for path in paths:
                baseline_file_hashes[str(path.resolve())] = digest(initial_reads.read(path))
        initial_reads.verify()
        verify_helpers(helper_start)
        inputs = {"before_sha256": digest(args.before_board.read_bytes()),
                  "after_sha256": digest(args.candidate.read_bytes()),
                  "r06_sha256": digest(args.r06_board.read_bytes()),
                  "live_board": str(args.live_board.resolve()),
                  "before_board": str(args.before_board.resolve()), "after_board": str(args.candidate.resolve()),
                  "tools": {str(p): digest(p.read_bytes()) for p in sources},
                  "library_inventory_at_start": libs, "slot": "shared-kicad (one, isolated copy)", "new_gpu_jobs": 0,
                  "native_binaries": native_binaries,
                  "baseline_file_hashes": baseline_file_hashes,
                  "construction_file_hashes": construction_pins, "construction_check": construction,
                  "source_parity_precheck": source_check, "imported_helpers": helper_start}
        check_board(json.loads((args.out / "baseline-partitions.json").read_text()), args.before_board)
        check_board(json.loads((args.out / "r06-partitions.json").read_text()), args.r06_board)
        write(args.out / "inputs.json", inputs)
        inputs_sha256 = digest((args.out / "inputs.json").read_bytes())
        env = os.environ.copy()
        env["HEAVY"] = "heavy.sh"
        env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
        env.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
        status(args.out, "NATIVE_MEASUREMENT_RUNNING", candidate_sha256=inputs["after_sha256"])
        with (args.out / "measure.log").open("w", encoding="utf-8") as log:
            cmd = ["C:/Program Files/Git/usr/bin/sh.exe", str(ROOT / "tools/step_measure.sh"),
                   args.candidate.resolve().as_posix(), args.out.resolve().as_posix(), (STAGE / "inputs/project").resolve().as_posix()]
            native = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
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
        require(parity_error is None, 'Source/API proof failed: ' + str(parity_error))
        status(args.out, "EVALUATING_NATIVE_RECEIPTS")
        receipt = evaluate(args, inputs, inputs_sha256)
        write(args.out / "proof.json", receipt)
        status(args.out, "COMPLETE", verdict=receipt["verdict"], completed=receipt["connectivity"]["completed"],
               lost=receipt["connectivity"]["lost"], r06_lost=receipt["connectivity_r06"]["lost"], drc_errors=receipt["drc"]["after"]["errors"])
        return 0 if receipt["verdict"] == "PASS" else 1
    except Exception as exc:
        status(args.out, "FAILED", reason=str(exc), traceback=traceback.format_exc())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
