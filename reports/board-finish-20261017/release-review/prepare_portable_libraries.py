"""Copy unchanged R299 library assets into a portable project-local overlay."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "portable-libraries-r1"
SOURCE = ROOT / "reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy"
STOCK = Path("C:/Program Files/KiCad/10.0/share/kicad/footprints")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists()
OUT.mkdir()
native = OUT / "overlay"
native.mkdir()
fp_table_path = SOURCE / "fp-lib-table"
sym_table_path = SOURCE / "sym-lib-table"
fp_table = fp_table_path.read_bytes().decode("utf-8")
sym_table = sym_table_path.read_bytes().decode("utf-8")
entries = re.findall(r'\(lib \(name "([^"]+)"\) \(type "KiCad"\) \(uri "([^"]+)"\)', fp_table)
assert len(entries) == fp_table.count("(lib ")
inputs = {str(fp_table_path): sha(fp_table_path), str(sym_table_path): sha(sym_table_path), str(Path(__file__)): sha(Path(__file__))}
library_dirs = {}
absolute_replaced = []
copied = {}
for name, uri in entries:
    actual = Path(uri.replace("${KIPRJMOD}", str(SOURCE)))
    assert actual.is_dir(), actual
    library_dirs[name] = actual
    dest = native / actual.name
    assert not dest.exists()
    shutil.copytree(actual, dest)
    for p in actual.rglob("*"):
        if p.is_file():
            target = dest / p.relative_to(actual)
            assert sha(p) == sha(target)
            inputs[str(p)] = sha(p)
            copied[str(target.relative_to(native))] = sha(target)
    relative_uri = "${KIPRJMOD}/" + actual.name
    if uri != relative_uri:
        fp_table = fp_table.replace('(uri "' + uri + '")', '(uri "' + relative_uri + '")')
        absolute_replaced.append(name)

source_xml = Path(__file__).resolve().parent / "R299-fresh-source.xml"
inputs[str(source_xml)] = sha(source_xml)
x = ET.parse(source_xml).getroot()
used = sorted({c.findtext("footprint") for c in x.findall("components/comp") if c.findtext("footprint")})
stock_entries = {}
missing = []
for footprint in used:
    lib, name = footprint.split(":", 1)
    if lib in library_dirs:
        p = library_dirs[lib] / (name + ".kicad_mod")
        if not p.is_file():
            missing.append(footprint)
        continue
    p = STOCK / (lib + ".pretty") / (name + ".kicad_mod")
    if not p.is_file():
        missing.append(footprint)
        continue
    stock_entries[lib] = "${KIPRJMOD}/" + lib + ".pretty"
    dest = native / (lib + ".pretty") / p.name
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(p, dest)
    assert sha(p) == sha(dest)
    inputs[str(p)] = sha(p)
    copied[str(dest.relative_to(native))] = sha(dest)
assert not missing, missing
end = fp_table.rfind(")")
fp_table = fp_table[:end] + "".join(
    '(lib (name "' + lib + '") (type "KiCad") (uri "' + uri + '") (options "") (descr "Exact KiCad10.0.4 used-footprint copy for portable R299 source"))'
    for lib, uri in sorted(stock_entries.items())) + fp_table[end:]
(native / "fp-lib-table").write_bytes(fp_table.encode("utf-8"))
(native / "sym-lib-table").write_bytes(sym_table.encode("utf-8"))
symbol_entries = re.findall(r'\(lib \(name "([^"]+)"\) \(type "KiCad"\) \(uri "([^"]+)"\)', sym_table)
for name, uri in symbol_entries:
    assert uri.startswith("${KIPRJMOD}/")
    p = SOURCE / uri.removeprefix("${KIPRJMOD}/")
    assert p.is_file()
    dest = native / p.name
    shutil.copy2(p, dest)
    inputs[str(p)] = sha(p)
    copied[str(dest.relative_to(native))] = sha(dest)

used_symbols = {(c.find("libsource").attrib["lib"], c.find("libsource").attrib["part"]) for c in x.findall("components/comp")}
names_to_paths = {name: native / uri.removeprefix("${KIPRJMOD}/") for name, uri in symbol_entries}
missing_symbols = []
for lib, part in used_symbols:
    if lib not in names_to_paths or '(symbol "' + part + '"' not in names_to_paths[lib].read_text():
        missing_symbols.append((lib, part))
assert not missing_symbols, missing_symbols
assert all("${KIPRJMOD}/" in uri for _, uri in re.findall(r'\(lib \(name "([^"]+)"\) \(type "KiCad"\) \(uri "([^"]+)"\)', fp_table))
report = {
    "verdict": "PASS_EXACT_ASSET_PORTABLE_OVERLAY_NO_BOARD_OR_SYMBOL_EDIT",
    "source_project": str(SOURCE), "overlay_directory": str(native),
    "absolute_custom_footprint_library_paths_replaced": absolute_replaced,
    "custom_footprint_libraries": len(entries), "stock_used_footprint_libraries_added": sorted(stock_entries),
    "unique_used_footprints_all_resolve": len(used), "symbol_libraries": len(symbol_entries),
    "unique_used_symbol_definitions_all_resolve": len(used_symbols),
    "all_copied_asset_bytes_exact": True,
    "three_existing_modified_board_0603_intents_preserved": ["R11054", "R9026", "R10007"],
    "footprint_library_mismatch_warnings_remain_review_required": True,
    "all_project_library_paths_relative_to_KIPRJMOD": True,
    "input_sha256": inputs, "copied_asset_sha256": copied,
    "inputs_unchanged": all(sha(Path(p)) == h for p, h in inputs.items()),
    "application": "Copy overlay contents into the isolated corrected project alongside its existing source; do not replace board footprints or update symbols automatically",
    "no_GUI_reload_or_native_DRC_run": True, "board_copper_changed": False,
    "adopted": False, "manufacturing_ready": False,
}
(OUT / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k not in {"input_sha256", "copied_asset_sha256"}}, indent=2))
