"""Compare real external symbol libraries with every frozen embedded definition."""
import decimal
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "parity-repair"))
from host_parity import load_parser


def canonical(value, numeric=False):
    if isinstance(value, list):
        # S-expression parser removes quotes. Only known geometry fields contain
        # numbers; pin names/numbers and property strings must stay exact.
        field_numeric = bool(value) and value[0] in {"at", "offset", "start", "end", "mid", "center", "xy", "size", "length", "width", "thickness", "radius", "angle"}
        return [canonical(v, field_numeric and i > 0) for i, v in enumerate(value)]
    if numeric and re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", value):
        return str(decimal.Decimal(value).normalize())
    return value


def inventory(source, library_root, parser_path, reads):
    parser = load_parser(parser_path)
    table = parser["sexpr_parse"](reads.read(source / "sym-lib-table").decode())
    definitions, files, mismatches, missing = {}, {}, [], []
    for lib in parser["children"](table, "lib"):
        name, uri = parser["atom"](lib, "name"), parser["atom"](lib, "uri")
        if not uri.startswith("${KIPRJMOD}/") or "/" in uri.removeprefix("${KIPRJMOD}/"):
            raise ValueError("Unsupported source symbol URI: " + uri)
        path = library_root / uri.removeprefix("${KIPRJMOD}/")
        if not path.is_file():
            missing.append({"name": name, "uri": uri, "searched_path": str(path)})
            continue
        raw = reads.read(path)
        root = parser["sexpr_parse"](raw.decode())
        if root[0] != "kicad_symbol_lib":
            raise ValueError("Not a native symbol library: " + str(path))
        files[path.name] = {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest(), "uri": uri}
        for symbol in parser["children"](root, "symbol"):
            identity = name + ":" + symbol[1]
            if identity in definitions:
                raise ValueError("Duplicate symbol library identity: " + identity)
            definitions[identity] = canonical([symbol[0], *symbol[2:]])
    embedded = {}
    for path in sorted(source.glob("*.kicad_sch")):
        root = parser["sexpr_parse"](reads.read(path).decode())
        group = parser["child"](root, "lib_symbols")
        for symbol in parser["children"](group or [], "symbol"):
            identity = symbol[1]
            definition = canonical([symbol[0], *symbol[2:]])
            if identity in embedded and embedded[identity] != definition:
                raise ValueError("Conflicting embedded symbol definitions: " + identity)
            embedded[identity] = definition
            if definitions.get(identity) != definition:
                mismatches.append({"file": path.name, "lib_id": identity,
                                   "external_definition_present": identity in definitions})
    return {"verdict": "PASS" if not missing and not mismatches else "OPEN_RESOURCE_MISMATCH",
            "evidence_class": "host parsed comparison of complete symbol definitions; known geometry numeric spelling normalised only, all names/pin numbers/property strings exact",
            "source_hierarchy_files": len(list(source.glob("*.kicad_sch"))),
            "embedded_unique_symbols": len(embedded), "external_symbols": len(definitions),
            "files": files, "missing_libraries": missing, "definition_mismatches": mismatches,
            "native_library_reload_or_export_after_copy": "NOT RUN"}


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parent.parent / "routing-resume-20261011"))
    from finish_bridge_proof import ReadSet
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=HERE / "symbol-resources.json")
    args = ap.parse_args()
    source = HERE.parent / "parity-repair/root106/source"
    reads = ReadSet()
    result = inventory(source, Path("Z:/pcb-runs/claude-finish/review/schematic/erc_full"),
                       HERE.parent / "parity-repair/root106/tools/netlist_parity.py", reads)
    reads.verify()
    result["observed_file_hashes"] = reads.hashes
    out = args.out.resolve()
    if not out.is_relative_to(HERE):
        raise ValueError("Output must stay in isolated final-bundle directory")
    if out.exists():
        raise ValueError("Refusing to overwrite existing resource receipt")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"files", "observed_file_hashes", "definition_mismatches"}}))
    print("definition_mismatches=" + str(len(result["definition_mismatches"])))
