"""Portable text precheck. Native geometry and API confirmation remain separate."""
import ast
import collections
import importlib.util
import json
from pathlib import Path


def load_parser(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    wanted = {"sexpr_parse", "child", "children", "atom", "norm", "read_netlist", "expected_path"}
    keep = []
    for node in tree.body:
        if isinstance(node, ast.Import) and all(n.name in {"collections", "re"} for n in node.names):
            keep.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted:
            keep.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TOKEN" for t in node.targets):
            keep.append(node)
    tree.body = keep
    namespace = {"__name__": "host_only_export_parser"}
    exec(compile(tree, str(path), "exec"), namespace)
    if not wanted <= namespace.keys():
        raise ValueError("Frozen export parser is missing expected functions")
    return namespace


def read_board_text(path, parser, pcbtext_path):
    spec = importlib.util.spec_from_file_location("frozen_pcbtext", pcbtext_path)
    pcbtext = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pcbtext)
    data = Path(path).read_bytes()
    head, chunks, tail = pcbtext.split(data)
    if head + b"".join(chunks) + tail != data:
        raise ValueError("Board text split is not lossless")
    footprints, duplicate_refs, pads = {}, [], []
    for chunk in chunks:
        if pcbtext.chunk_kind(chunk) != "footprint":
            continue
        root = parser["sexpr_parse"](chunk.decode("utf-8"))
        props = {p[1]: p[2] for p in parser["children"](root, "property") if len(p) >= 3}
        ref = props.get("Reference", "")
        if not ref:
            raise ValueError("Footprint without a reference")
        if ref in footprints:
            duplicate_refs.append(ref)
        fp = {"ref": ref, "fpid": root[1], "value": props.get("Value", ""),
              "uuid": parser["atom"](root, "uuid"), "path": parser["atom"](root, "path"), "pads": []}
        for p in parser["children"](root, "pad"):
            if len(p) < 4:
                raise ValueError("Malformed pad")
            net = parser["child"](p, "net")
            # KiCad 10 has named nets; older numeric net syntax is refused.
            if net is not None and (len(net) != 2 or not isinstance(net[1], str)):
                raise ValueError("Unsupported pad net syntax")
            row = {"ref": ref, "number": p[1], "net": net[1] if net else "",
                   "uuid": parser["atom"](p, "uuid"), "attribute": p[2]}
            fp["pads"].append(row)
            pads.append(row)
        footprints[ref] = fp
    return {"footprints": footprints, "pads": pads, "duplicate_refs": duplicate_refs}


def compare(nl, board, parser):
    norm = parser["norm"]
    failures = {"component_missing": [], "unexpected_component": [], "footprint_mismatch": [],
                "value_mismatch": [], "node_without_pad": [], "pad_net_mismatch": [],
                "netted_pad_without_node": [], "normalisation_collisions": [], "duplicate_refs": [],
                "node_conflicts": list(nl["node_conflicts"])}
    failures["duplicate_refs"] = list(nl["duplicate_refs"]) + board["duplicate_refs"]
    failures["normalisation_collisions"] = list(nl["name_collisions"])
    comps, fps = nl["components"], board["footprints"]
    pads_by_key = collections.defaultdict(list)
    raw_names = collections.defaultdict(set)
    for p in board["pads"]:
        pads_by_key[(p["ref"], p["number"])].append(p)
        if p["net"]:
            raw_names[norm(p["net"])].add(p["net"])
    failures["normalisation_collisions"] += [{"normalised": k, "raw_names": sorted(v)}
                                            for k, v in raw_names.items() if len(v) > 1]
    for ref, c in comps.items():
        if ref not in fps:
            if not c["exclude_from_board"]:
                failures["component_missing"].append(ref)
            continue
        f = fps[ref]
        for field, source_key, board_key in [("footprint_mismatch", "footprint", "fpid"),
                                           ("value_mismatch", "value", "value")]:
            if c[source_key] != f[board_key]:
                failures[field].append({"ref": ref, "expected": c[source_key], "board": f[board_key]})
    failures["unexpected_component"] = sorted(set(fps) - set(comps))
    matched = 0
    for key, net in nl["node_net"].items():
        physical = pads_by_key.get(key, [])
        if not physical:
            failures["node_without_pad"].append({"ref": key[0], "pin": key[1], "net": net})
        for pad in physical:
            if norm(pad["net"]) != net:
                failures["pad_net_mismatch"].append(dict(pad, expected=net))
            else:
                matched += 1
    for pad in board["pads"]:
        if pad["net"] and (pad["ref"], pad["number"]) not in nl["node_net"]:
            failures["netted_pad_without_node"].append(pad)
    counts = {k: len(v) for k, v in failures.items()}
    return {"verdict": "PASS" if not any(counts.values()) else "FAIL", "counts": counts,
            "netlist_components": len(comps), "netlist_nets": len(nl["nets"]), "netlist_nodes": len(nl["node_net"]),
            "board_footprints": len(fps), "board_pads": len(board["pads"]), "physical_pads_matched": matched,
            "failures": failures, "evidence_class": "portable source inspection of exported netlist and board text",
            "native_api_confirmation": "PENDING", "no_net_pad_copper_touch": "NOT TESTED",
            "limits": "No PCB API load, source re-export, connectivity build, refill, DRC, electrical or physical measurement"}


def source_identity(project, netlist, parser):
    project = Path(project)
    todo, visited, edges, symbols, excluded = ["motherboard.kicad_sch"], set(), {}, collections.defaultdict(list), []
    while todo:
        name = todo.pop()
        if name in visited:
            continue
        path = (project / name).resolve()
        if not path.is_relative_to(project.resolve()):
            raise ValueError("Source hierarchy escapes snapshot")
        root = parser["sexpr_parse"](path.read_text(encoding="utf-8"))
        if root[0] != "kicad_sch":
            raise ValueError("Not a KiCad schematic")
        visited.add(name)
        edges[name] = []
        for sheet in parser["children"](root, "sheet"):
            targets = [p[2] for p in parser["children"](sheet, "property")
                       if len(p) > 2 and p[1].casefold() == "sheetfile"]
            if len(targets) != 1:
                raise ValueError("Source sheet does not have one file")
            edges[name].extend(targets)
            todo.extend(targets)
        for symbol in parser["children"](root, "symbol"):
            props = {p[1]: p[2] for p in parser["children"](symbol, "property") if len(p) > 2}
            ref = props.get("Reference", "")
            if not ref or ref.startswith("#"):
                continue
            if parser["atom"](symbol, "on_board") == "no":
                excluded.append({"ref": ref, "sheet": name, "value": props.get("Value", ""),
                                 "on_board": "no", "in_bom": parser["atom"](symbol, "in_bom")})
                continue
            symbols[ref].append({"uuid": parser["atom"](symbol, "uuid"), "value": props.get("Value", ""),
                                 "footprint": props.get("Footprint", ""), "sheet": name})
    defects = {"missing_ref": [], "extra_ref": [], "symbol_identity": [],
               "excluded_ref_exported": sorted({p["ref"] for p in excluded} & set(netlist["components"]))}
    for ref, comp in netlist["components"].items():
        placed = symbols.get(ref)
        if not placed:
            defects["missing_ref"].append(ref)
            continue
        if (set(comp["tstamps"]) != {p["uuid"] for p in placed}
                or any(p["value"] != comp["value"] or p["footprint"] != comp["footprint"] for p in placed)):
            defects["symbol_identity"].append({"ref": ref, "source": placed, "netlist": comp})
    defects["extra_ref"] = sorted(set(symbols) - set(netlist["components"]))
    return {"verdict": "PASS" if not any(defects.values()) else "FAIL", "reachable_files": sorted(visited),
            "hierarchy_edges": edges, "placed_component_refs": len(symbols),
            "explicitly_not_on_board": excluded,
            "defects": defects, "scope": "source hierarchy/reference/value/footprint/symbol UUID identity; wires not re-exported"}
