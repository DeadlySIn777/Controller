"""Create distinct two-baseline runner from the frozen c05 evidence method."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent.parent

def once(text,before,after):
    if text.count(before)!=1:raise ValueError('Ambiguousrunnerpatch:'+before[:80])
    return text.replace(before,after)

def main():
    original=ROOT/'recovery-composite/c05/measure_c05.py';raw=original.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='ce1dc397f7231632fef112238d1acdbdc1a66fb68c8ca02d1ac369bc4a3f19ca':raise ValueError('Frozenc05runnerchanged')
    text=raw.decode();text=once(text,'HERE = STAGE.parent.parent','HERE = STAGE.parent.parent.parent')
    text=once(text,'from compose_c05 import validate_construction','from compose_two import validate_construction, R07_SHA')
    text=text.replace('distinct c05 whole-FAG/E1 rollback','two pure-add r07 signals against both r07/live and r06')
    text=once(text,'    guard = compare(b, a)','''    guard = compare(b, a)
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
        require(digest(reads.read(args.r06_measure / "copy" / name)) == r06_manifest[name], "r06 measured copy changed")''')
    text=once(text,'        require(manifests["before"][name] == manifests["after"][name], "native rules/source changed: " + name)',
      '        require(manifests["before"][name] == manifests["after"][name] == r06_manifest[name], "native rules/source changed: " + name)')
    text=once(text,'    require(before_libs == after_libs, "effective footprint resources differ")',
      '    require(before_libs == after_libs == library_inventory(args.r06_measure / "copy", reads), "effective footprint resources differ")')
    text=once(text,'    require(footprints["before"]["count"] == footprints["after"]["count"], "footprint counts differ")',
      '    require(footprints["before"] == footprints["after"], "pure-add candidate changes footprints/pads/poses")')
    text=once(text,'    passed = guard["verdict"] == "PASS" and drcs["after"]["errors"] == 0',
      '    passed = guard["verdict"] == "PASS" and r06_guard["verdict"] == "PASS" and drcs["after"]["errors"] == 0')
    text=once(text,'"candidate_sha256": inputs["after_sha256"], "connectivity": guard, "drc": drcs,',
      '"candidate_sha256": inputs["after_sha256"], "connectivity": guard, "connectivity_r07_live": guard, "connectivity_r06": r06_guard, "drc": drcs,')
    text=once(text,'    ap.add_argument("--construction", type=Path, required=True)',
      '    ap.add_argument("--construction", type=Path, required=True)\n    for name in ("r06-board", "r06-measure", "live-board"):\n        ap.add_argument("--" + name, type=Path, required=True)')
    text=once(text,'        require(digest(args.before_board.read_bytes()) == receipt["base_bindings"]["base_bindings"]["native_sources"]["r06"]["sha256"], "baseline is not approved r06")',
      '''        require(digest(args.before_board.read_bytes()) == R07_SHA, "baseline is not frozen actual r07")
        require(digest(args.live_board.read_bytes()) == R07_SHA, "actual live board is not frozen r07")
        require(digest(args.r06_board.read_bytes()) == "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53", "r06 source differs")''')
    text=once(text,'        construction_hashes = {str(Path(r["path"]).resolve()): r["sha256"] for r in records}',
      '        construction_hashes = dict(receipt["source_files_sha256"])')
    start=text.index('        sources = [ROOT / "tools" / n for n in TOOL_NAMES]')
    end=text.index('        require(len({p.name for p in sources})',start)
    text=text[:start]+'''        sources = [ROOT / "tools" / n for n in TOOL_NAMES] + [Path(__file__), STAGE / "compose_two.py",
                   HERE / "compose_additions.py", HERE / "gate-repair/partition_guard.py",
                   PREVIOUS / "finish_bridge_proof.py", ROOT / "tools/integrate/pcbtext.py",
                   STAGE / "audit_two.py", STAGE.parent / "screen_c06.py", STAGE.parent / "screen_dive_c06.py",
                   STAGE.parent / "alternate-r07/screen_r07.py", HERE / "reconcile_dfm.py",
                   HERE / "power-audit/prepare_sbc_c05_proposal.py", HERE / "power-audit/prepare_sbc_plan.py",
                   HERE / "power-audit/prepare_sbc_hubs.py"]
'''+text[end:]
    text=once(text,'            (args.out / ("baseline-" + name)).write_bytes((args.before_measure / name).read_bytes())',
      '            (args.out / ("baseline-" + name)).write_bytes((args.before_measure / name).read_bytes())\n            (args.out / ("r06-" + name)).write_bytes((args.r06_measure / name).read_bytes())')
    text=once(text,'                  "after_sha256": digest(args.candidate.read_bytes()),',
      '                  "after_sha256": digest(args.candidate.read_bytes()),\n                  "r06_sha256": digest(args.r06_board.read_bytes()),\n                  "live_board": str(args.live_board.resolve()),')
    text=once(text,'               lost=receipt["connectivity"]["lost"], drc_errors=receipt["drc"]["after"]["errors"])',
      '               lost=receipt["connectivity"]["lost"], r06_lost=receipt["connectivity_r06"]["lost"], drc_errors=receipt["drc"]["after"]["errors"])')
    text=once(text,'        check_board(json.loads((args.out / "baseline-partitions.json").read_text()), args.before_board)',
      '        check_board(json.loads((args.out / "baseline-partitions.json").read_text()), args.before_board)\n        check_board(json.loads((args.out / "r06-partitions.json").read_text()), args.r06_board)')
    output=HERE/'measure_two.py'
    if output.exists():raise ValueError('Freshrunneronly')
    output.write_text(text,encoding='utf-8',newline='\n')
    (HERE/'runner-derivation.json').write_text(json.dumps({'original_path':str(original),'original_sha256':hashlib.sha256(raw).hexdigest(),
        'derived_path':str(output),'derived_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_launched':False},indent=1)+'\n')
    print(str(output))

if __name__=='__main__':main()
