"""Create a separate runner without changing any currently frozen measurement tool."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
source = (HERE / 'measure_candidate.py').read_text(encoding='utf-8')

def replace(old, new):
    global source
    if source.count(old) != 1:
        raise ValueError('expected one exact original block: ' + old[:90])
    source = source.replace(old, new)

replace('Measure an isolated additive board with unchanged native rules and no-loss gate.',
        'Measure a reconstructed recovery/bridge/return/DFM composite with unchanged native rules.')
replace('from partition_guard import compare, check_board',
        'import importlib.util\n'
        'guard_spec = importlib.util.spec_from_file_location("composite_partition_guard", HERE / "gate-repair/partition_guard.py")\n'
        'guard_module = importlib.util.module_from_spec(guard_spec)\n'
        'guard_spec.loader.exec_module(guard_module)\n'
        'compare, check_board = guard_module.compare, guard_module.check_board')
replace('from compose_additions import inventory',
        'sys.path.insert(0, str(HERE / "recovery-composite"))\n'
        'from compose_recovery import validate_construction')
replace('"net_partitions.py", "heavyt.sh"', '"net_partitions.py", "heavym.sh"')
replace('    bi, ai = inventory(boards["before"]), inventory(boards["after"])\n'
        '    require(bi[0] == ai[0] and bi[2] == ai[2] and bi[5] == ai[5], "non-copper definitions changed")\n'
        '    require(all(ai[4].get(u) == ch for u, ch in bi[4].items()), "baseline copper changed or removed")\n'
        '    footprints = {role: footprint_fingerprint(data) for role, data in boards.items()}\n'
        '    require(footprints["before"] == footprints["after"], "footprint definitions differ")',
        '    construction = validate_construction(args.construction, args.candidate)\n'
        '    require(reads.read(args.construction) == reads.read(out / "construction.json"), "construction receipt changed")\n'
        '    for path, expected in inputs["construction_file_hashes"].items():\n'
        '        require(digest(reads.read(path)) == expected, "construction input changed: " + path)\n'
        '    footprints = {role: footprint_fingerprint(data) for role, data in boards.items()}\n'
        '    require(footprints["before"]["count"] == footprints["after"]["count"], "footprint counts differ")')
replace('    reads.verify()\n    passed = guard',
        '    cli_log = reads.read(out / "drc.log").decode("utf-8", errors="replace")\n'
        '    cli_parity = ("NOT_EXECUTED" if "Failed to fetch schematic netlist" in cli_log\n'
        '                  or "Schematic parity tests require" in cli_log else "NO_REPORTED_DIAGNOSTIC; execution needs independent source/API proof")\n'
        '    validate_construction(args.construction, args.candidate)\n'
        '    reads.verify()\n    passed = guard')
replace('            "baseline_copper_retained_exact": True, "noncopper_definitions_retained": True,',
        '            "exact_reconstructed_source_contract": construction,\n'
        '            "cli_schematic_parity": cli_parity,\n'
        '            "explicit_native_netlist_parity": "SEPARATE_SAME_HASH_RECEIPT_REQUIRED",')
replace('        ap.add_argument("--" + name, type=Path, required=True)\n    args = ap.parse_args()',
        '        ap.add_argument("--" + name, type=Path, required=True)\n'
        '    ap.add_argument("--construction", type=Path, required=True)\n'
        '    args = ap.parse_args()')
replace('        bi, ai = inventory(args.before_board.read_bytes()), inventory(args.candidate.read_bytes())\n'
        '        require(bi[0] == ai[0] and bi[2] == ai[2] and bi[5] == ai[5], "source definitions differ")\n'
        '        require(all(ai[4].get(u) == ch for u, ch in bi[4].items()), "candidate is not strictly additive")',
        '        construction = validate_construction(args.construction, args.candidate)\n'
        '        receipt = json.loads(args.construction.read_text(encoding="utf-8"))\n'
        '        require(digest(args.before_board.read_bytes()) == receipt["native_sources"]["r06"]["sha256"], "baseline is not approved r06")\n'
        '        records = []\n'
        '        def collect(value):\n'
        '            if isinstance(value, dict):\n'
        '                if set(value) == {"path", "sha256"}:\n'
        '                    records.append(value)\n'
        '                else:\n'
        '                    for item in value.values(): collect(item)\n'
        '            elif isinstance(value, list):\n'
        '                for item in value: collect(item)\n'
        '        collect(receipt)\n'
        '        construction_hashes = {str(Path(r["path"]).resolve()): r["sha256"] for r in records}\n'
        '        for path, expected in construction_hashes.items():\n'
        '            require(digest(Path(path).read_bytes()) == expected, "construction binding changed")\n'
        '        (args.out / "construction.json").write_bytes(args.construction.read_bytes())')
replace('                   PREVIOUS / "partition_guard.py", PREVIOUS / "finish_bridge_proof.py",\n'
        '                   ROOT / "tools/integrate/pcbtext.py"]',
        '                   HERE / "gate-repair/partition_guard.py", PREVIOUS / "finish_bridge_proof.py",\n'
        '                   ROOT / "tools/integrate/pcbtext.py", HERE / "recovery-composite/compose_recovery.py",\n'
        '                   HERE / "reconcile_dfm.py", HERE / "dfm_contract_v2.py"]')
replace('"library_inventory_at_start": libs, "slot": "test-kicad (one)", "new_gpu_jobs": 0}',
        '"library_inventory_at_start": libs, "slot": "main-kicad (one, isolated copy)", "new_gpu_jobs": 0,\n'
        '                  "construction_file_hashes": construction_hashes, "construction_check": construction}')
replace('env["HEAVY"] = "heavyt.sh"', 'env["HEAVY"] = "heavym.sh"')
replace('(ROOT / "integrate").as_posix()]', '(HERE / "recovery-composite/inputs/project").resolve().as_posix()]')

output = HERE / 'measure_composite.py'
if output.exists():
    raise ValueError('new runner must not overwrite an existing file')
output.write_text(source, encoding='utf-8')
print(output)
