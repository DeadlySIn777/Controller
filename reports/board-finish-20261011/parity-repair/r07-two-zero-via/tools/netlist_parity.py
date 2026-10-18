# Netlist parity audit: KiCad S-expression netlist (sch.net, "Export netlist" from Eeschema) against a board.
# Evidence class: SOURCE INSPECTION of the board file (pcbnew API load of a snapshot) and of the netlist file.
# No DRC, no zone refill, no physical measurement. Unconnected (unrouted) items are counted for information
# only: a mid-route board is expected to have them and they are not parity defects.
#
# Checks (net names compared after .replace("{slash}", "/"); the board's own spelling is kept for lookups):
#   components  every netlist component is on the board with the same footprint id and value (plus the
#               sheet path, DNP and exclude-from-BOM flags as informational checks); every board footprint is
#               in the netlist, extras (fiducials, mounting holes, board-only parts) listed separately;
#   pads        every netlist node (ref, pin) has a board pad whose net equals the node's net; board pads with
#               no netlist node (numbered and unnumbered) are listed, those carrying a net flagged;
#   nets        netlist nets with no board pad; board nets that have pads but are absent from the netlist;
#               board nets with copper only (no pad, not in the netlist); normalisation collisions;
#   no-net pads pads with no net that carry copper (not NPTH-without-copper), and those that a track end,
#               arc end or via actually touches (geometric hit test on a shared copper layer).
# Usage (KiCad's python.exe, pcbnew API; the board load takes about a minute on a large board):
#   python.exe tools/quality/netlist_parity.py board.kicad_pcb [--netlist sch.net] [--no-connectivity]
#                                               [--examples N] out.json
# Prints a one-line JSON summary; out.json holds every finding with net names, refs and mm positions.
import collections
import datetime
import hashlib
import json
import os
import re
import sys
import time

import pcbnew

TOKEN = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)
MECHANICAL_PREFIXES = ("FID", "H", "MH", "LOGO", "G", "REF", "NPTH", "MP")
UNCONNECTED = "unconnected-"


def sexpr_parse(text):
    """Parse an S-expression file into nested lists; quoted atoms are unescaped strings."""
    stack = [[]]
    pos, n = 0, len(text)
    while pos < n:
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"netlist parse error at offset {pos}: {text[pos:pos + 40]!r}")
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            done = stack.pop()
            stack[-1].append(done)
        elif m.group(3) is not None:
            s = m.group(3)[1:-1]
            stack[-1].append(s.replace('\\"', '"').replace("\\\\", "\\"))
        else:
            stack[-1].append(m.group(4))
    if len(stack) != 1 or not stack[0]:
        raise ValueError("netlist: unbalanced parentheses")
    return stack[0][0]


def child(node, key):
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def atom(node, key, default=""):
    c = child(node, key)
    if c is None or len(c) < 2 or isinstance(c[1], list):
        return default
    return c[1]


def norm(name):
    return (name or "").replace("{slash}", "/")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_identity(path):
    st = os.stat(path)
    return {"path": os.path.abspath(path), "size": st.st_size,
            "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            "sha256": sha256(path)}


def mm(v):
    return round(pcbnew.ToMM(v), 3)


def ref_prefix(ref):
    m = re.match(r"[A-Za-z]+", ref)
    return m.group(0) if m else ref


def is_mechanical_ref(ref):
    p = ref_prefix(ref).upper()
    return any(p == x or (x in ("FID",) and p.startswith(x)) for x in MECHANICAL_PREFIXES)


# ----------------------------------------------------------------------------------------------- netlist
def read_netlist(path):
    text = open(path, encoding="utf-8").read()
    root = sexpr_parse(text)
    if not root or root[0] != "export":
        raise ValueError("not a KiCad netlist export")
    design = child(root, "design") or []
    info = {"source": atom(design, "source"), "date": atom(design, "date"), "tool": atom(design, "tool"),
            "version": atom(root, "version")}
    comps = collections.OrderedDict()
    duplicate_refs = []
    for c in children(child(root, "components") or [], "comp"):
        ref = atom(c, "ref")
        sp = child(c, "sheetpath") or []
        ts = child(c, "tstamps") or []
        props = {}
        for p in children(c, "property"):
            props[atom(p, "name")] = atom(p, "value", default="")
        entry = {"ref": ref, "value": atom(c, "value"), "footprint": atom(c, "footprint"),
                 "sheet_names": atom(sp, "names"), "sheet_tstamps": atom(sp, "tstamps"),
                 "tstamps": [t for t in ts[1:] if isinstance(t, str)], "properties": props,
                 "dnp": "dnp" in props, "exclude_from_board": "exclude_from_board" in props,
                 "exclude_from_bom": "exclude_from_bom" in props,
                 "pins": sorted({atom(p, "num") for u in children(child(c, "units") or [], "unit")
                                 for p in children(child(u, "pins") or [], "pin")})}
        if ref in comps:
            duplicate_refs.append(ref)
        comps[ref] = entry
    nets = collections.OrderedDict()
    node_net = {}
    node_conflicts = []
    name_collisions = collections.defaultdict(set)
    for n in children(child(root, "nets") or [], "net"):
        raw = atom(n, "name")
        name = norm(raw)
        name_collisions[name].add(raw)
        nodes = []
        for nd in children(n, "node"):
            ref, pin = atom(nd, "ref"), atom(nd, "pin")
            nodes.append({"ref": ref, "pin": pin, "pinfunction": atom(nd, "pinfunction"),
                          "pintype": atom(nd, "pintype")})
            if (ref, pin) in node_net and node_net[(ref, pin)] != name:
                node_conflicts.append({"ref": ref, "pin": pin, "nets": [node_net[(ref, pin)], name]})
            node_net[(ref, pin)] = name
        if name in nets:
            nets[name]["nodes"].extend(nodes)
            nets[name]["raw_names"].append(raw)
        else:
            nets[name] = {"name": name, "raw_names": [raw], "code": atom(n, "code"), "class": atom(n, "class"),
                          "nodes": nodes}
    collisions = [{"normalised": k, "raw_names": sorted(v)} for k, v in name_collisions.items() if len(v) > 1]
    return {"info": info, "components": comps, "nets": nets, "node_net": node_net,
            "duplicate_refs": duplicate_refs, "node_conflicts": node_conflicts, "name_collisions": collisions}


# ----------------------------------------------------------------------------------------------- board
def read_board(path, want_connectivity):
    t0 = time.time()
    b = pcbnew.LoadBoard(path)
    load_s = round(time.time() - t0, 1)
    copper = set(b.GetEnabledLayers().CuStack())
    attr_names = {"PTH": pcbnew.PAD_ATTRIB_PTH, "SMD": pcbnew.PAD_ATTRIB_SMD, "CONN": pcbnew.PAD_ATTRIB_CONN,
                  "NPTH": pcbnew.PAD_ATTRIB_NPTH}
    attr_of = {v: k for k, v in attr_names.items()}
    fps = collections.OrderedDict()
    duplicate_refs = []
    pads = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        pos = f.GetPosition()
        attrs = f.GetAttributes()
        entry = {"ref": ref, "fpid": f.GetFPIDAsString(), "value": f.GetValue(), "x": mm(pos.x), "y": mm(pos.y),
                 "layer": f.GetLayerName(), "path": f.GetPath().AsString(),
                 "board_only": bool(attrs & pcbnew.FP_BOARD_ONLY), "dnp": bool(attrs & pcbnew.FP_DNP),
                 "exclude_from_bom": bool(attrs & pcbnew.FP_EXCLUDE_FROM_BOM), "pads": []}
        for p in f.Pads():
            pp = p.GetPosition()
            layers = [b.GetLayerName(l) for l in p.GetLayerSet().Seq() if l in copper]
            has_copper = bool(layers) and p.IsOnCopperLayer() and not p.IsNPTHWithNoCopper()
            pad = {"ref": ref, "number": p.GetNumber(), "net": p.GetNetname(), "netcode": p.GetNetCode(),
                   "x": mm(pp.x), "y": mm(pp.y), "attribute": attr_of.get(p.GetAttribute(), str(p.GetAttribute())),
                   "copper_layers": layers, "has_copper": has_copper, "_obj": p}
            entry["pads"].append(pad)
            pads.append(pad)
        if ref in fps:
            duplicate_refs.append(ref)
            fps[ref + f"#dup{len(duplicate_refs)}"] = entry
        else:
            fps[ref] = entry
    nets_raw = {}
    for code, n in b.GetNetsByNetcode().items():
        if code > 0:
            nets_raw[n.GetNetname()] = code
    copper_by_code = collections.defaultdict(lambda: collections.Counter())
    endpoints = []  # (item, point, layers)
    for t in b.GetTracks():
        cls = t.GetClass()
        code = t.GetNetCode()
        if cls == "PCB_VIA":
            copper_by_code[code]["vias"] += 1
            endpoints.append((t, t.GetPosition(), set(t.GetLayerSet().Seq()) & copper))
        else:
            copper_by_code[code]["tracks" if cls == "PCB_TRACK" else "arcs"] += 1
            lay = {t.GetLayer()}
            endpoints.append((t, t.GetStart(), lay))
            endpoints.append((t, t.GetEnd(), lay))
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        copper_by_code[z.GetNetCode()]["zones"] += 1
    unconnected = None
    conn = None
    if want_connectivity:
        t1 = time.time()
        b.BuildConnectivity()
        conn = b.GetConnectivity()
        unconnected = int(conn.GetUnconnectedCount(False))
        load_s = {"load_s": load_s, "connectivity_s": round(time.time() - t1, 1)}
    return {"board": b, "footprints": fps, "pads": pads, "duplicate_refs": duplicate_refs, "nets_raw": nets_raw,
            "copper_by_code": copper_by_code, "endpoints": endpoints, "copper_layers": copper,
            "unconnected_items": unconnected, "conn": conn, "timing": load_s, "layer_name": b.GetLayerName,
            "track_count": sum(c["tracks"] + c["arcs"] for c in copper_by_code.values()),
            "via_count": sum(c["vias"] for c in copper_by_code.values()),
            "zone_count": sum(c["zones"] for c in copper_by_code.values())}


# ----------------------------------------------------------------------------------------------- compare
def pad_public(pad, **extra):
    d = {k: v for k, v in pad.items() if k != "_obj" and k != "netcode"}
    d.update(extra)
    return d


def expected_path(comp):
    sheet = comp["sheet_tstamps"] or "/"
    if not sheet.endswith("/"):
        sheet += "/"
    return [sheet + t for t in comp["tstamps"]] or [sheet]


def touching_copper(board_data, pad):
    """Track/arc ends and via centres that lie on the pad on a shared copper layer (geometric check)."""
    p = pad["_obj"]
    pad_layers = set(p.GetLayerSet().Seq()) & board_data["copper_layers"]
    bb = p.GetBoundingBox()
    x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    hits = []
    for item, pt, layers in board_data["_grid_lookup"](x0, y0, x1, y1):
        if not (layers & pad_layers):
            continue
        if x0 <= pt.x <= x1 and y0 <= pt.y <= y1 and p.HitTest(pt, 0):
            hits.append({"item": item.GetClass(), "net": item.GetNetname(), "x": mm(pt.x), "y": mm(pt.y),
                         "layers": sorted(board_data["layer_name"](l) for l in layers)})
    return hits


def build_grid(endpoints, cell=1000000):
    grid = collections.defaultdict(list)
    for item, pt, layers in endpoints:
        grid[(pt.x // cell, pt.y // cell)].append((item, pt, layers))

    def lookup(x0, y0, x1, y1):
        out = []
        for cx in range(x0 // cell, x1 // cell + 1):
            for cy in range(y0 // cell, y1 // cell + 1):
                out.extend(grid.get((cx, cy), ()))
        return out
    return lookup


def compare(nl, bd, examples):
    comps, fps = nl["components"], bd["footprints"]
    report = {"components": {}, "pads": {}, "nets": {}, "no_net_pads": {}, "informational": {}}
    C, P, N, Z = report["components"], report["pads"], report["nets"], report["no_net_pads"]

    # ---- components
    C["netlist_components_missing_on_board"] = [
        {"ref": r, "value": c["value"], "footprint": c["footprint"], "sheet": c["sheet_names"],
         "pins": len(c["pins"])} for r, c in comps.items() if r not in fps and not c["exclude_from_board"]]
    C["netlist_components_excluded_from_board"] = [
        {"ref": r, "value": c["value"], "footprint": c["footprint"], "on_board": r in fps}
        for r, c in comps.items() if c["exclude_from_board"]]
    extra_mech, extra_board_only, extra_unexpected = [], [], []
    for r, f in fps.items():
        if r in comps:
            continue
        row = {"ref": r, "fpid": f["fpid"], "value": f["value"], "x": f["x"], "y": f["y"], "layer": f["layer"],
               "pads": len(f["pads"]), "pads_with_net": sum(1 for p in f["pads"] if p["netcode"] > 0),
               "board_only_attr": f["board_only"]}
        if f["board_only"]:
            extra_board_only.append(row)
        elif is_mechanical_ref(r):
            extra_mech.append(row)
        else:
            extra_unexpected.append(row)
    C["board_footprints_not_in_netlist"] = {"mechanical_by_ref": extra_mech, "board_only_attr": extra_board_only,
                                            "unexpected": extra_unexpected}
    fp_mis, fp_case, val_mis, path_mis, dnp_mis, bom_mis = [], [], [], [], [], []
    for r, c in comps.items():
        f = fps.get(r)
        if f is None:
            continue
        where = {"ref": r, "x": f["x"], "y": f["y"], "layer": f["layer"]}
        if c["footprint"] != f["fpid"]:
            row = dict(where, netlist_footprint=c["footprint"], board_fpid=f["fpid"])
            (fp_case if c["footprint"].lower() == f["fpid"].lower() else fp_mis).append(row)
        if c["value"] != f["value"]:
            val_mis.append(dict(where, netlist_value=c["value"], board_value=f["value"]))
        if f["path"] not in expected_path(c):
            path_mis.append(dict(where, netlist_path=expected_path(c), board_path=f["path"]))
        if c["dnp"] != f["dnp"]:
            dnp_mis.append(dict(where, netlist_dnp=c["dnp"], board_dnp=f["dnp"]))
        if c["exclude_from_bom"] != f["exclude_from_bom"]:
            bom_mis.append(dict(where, netlist_exclude_from_bom=c["exclude_from_bom"],
                                board_exclude_from_bom=f["exclude_from_bom"]))
    C["footprint_id_mismatch"] = fp_mis
    C["footprint_id_mismatch_case_only"] = fp_case
    C["value_mismatch"] = val_mis
    C["path_mismatch_informational"] = path_mis
    C["dnp_flag_mismatch_informational"] = dnp_mis
    C["exclude_from_bom_flag_mismatch_informational"] = bom_mis
    C["duplicate_refs"] = {"netlist": nl["duplicate_refs"], "board": bd["duplicate_refs"]}

    # ---- pads vs nodes
    pads_by_key = collections.defaultdict(list)
    for pad in bd["pads"]:
        pads_by_key[(pad["ref"], pad["number"])].append(pad)
    node_without_pad, net_mismatch = [], []
    kinds = collections.Counter()
    matched_pads = 0
    nodes_of_missing = 0
    for (ref, pin), net in nl["node_net"].items():
        if ref not in fps:
            nodes_of_missing += 1
            continue
        plist = pads_by_key.get((ref, pin))
        if not plist:
            f = fps[ref]
            node_without_pad.append({"ref": ref, "pin": pin, "net": net, "fpid": f["fpid"], "x": f["x"], "y": f["y"],
                                     "board_pad_numbers": sorted({p["number"] for p in f["pads"]})[:examples]})
            continue
        for pad in plist:
            bn = norm(pad["net"])
            if bn == net:
                matched_pads += 1
                continue
            if bn == "":
                kind = "board_pad_has_no_net"
            elif net.startswith(UNCONNECTED) and bn.startswith(UNCONNECTED):
                kind = "both_unconnected_name_differs"
            elif net.startswith(UNCONNECTED):
                kind = "netlist_unconnected_board_has_net"
            elif bn.startswith(UNCONNECTED):
                kind = "board_unconnected_netlist_has_net"
            else:
                kind = "different_net"
            kinds[kind] += 1
            net_mismatch.append(pad_public(pad, netlist_net=net, board_net=pad["net"], kind=kind))
    pads_without_node, pads_without_node_with_net = [], []
    unnumbered, unnumbered_with_net = 0, []
    unnumbered_by_ref = collections.Counter()
    pads_of_extra = 0
    for pad in bd["pads"]:
        if pad["ref"] not in comps:
            pads_of_extra += 1
            continue
        if pad["number"] == "":
            unnumbered += 1
            unnumbered_by_ref[pad["ref"]] += 1
            if pad["netcode"] > 0:
                unnumbered_with_net.append(pad_public(pad))
            continue
        if (pad["ref"], pad["number"]) not in nl["node_net"]:
            row = pad_public(pad)
            pads_without_node.append(row)
            if pad["netcode"] > 0:
                pads_without_node_with_net.append(row)
    P["pad_net_mismatch"] = net_mismatch
    P["pad_net_mismatch_kinds"] = dict(kinds)
    P["netlist_nodes_without_board_pad"] = node_without_pad
    P["netlist_nodes_of_missing_components"] = nodes_of_missing
    P["board_pads_without_netlist_node"] = pads_without_node
    P["board_pads_without_netlist_node_with_net"] = pads_without_node_with_net
    P["board_pads_unnumbered"] = {"count": unnumbered, "with_net": unnumbered_with_net,
                                  "by_ref": dict(sorted(unnumbered_by_ref.items()))}
    P["pads_of_footprints_not_in_netlist"] = pads_of_extra
    P["pads_matched"] = matched_pads
    P["netlist_node_conflicts"] = nl["node_conflicts"]

    # ---- nets
    board_norm_to_raw = collections.defaultdict(set)
    for raw in bd["nets_raw"]:
        board_norm_to_raw[norm(raw)].add(raw)
    board_collisions = [{"normalised": k, "raw_names": sorted(v)} for k, v in board_norm_to_raw.items() if len(v) > 1]
    pads_by_net = collections.defaultdict(list)
    for pad in bd["pads"]:
        if pad["netcode"] > 0:
            pads_by_net[norm(pad["net"])].append(pad)
    code_of_raw = bd["nets_raw"]

    def copper_of(net_norm):
        tot = collections.Counter()
        for raw in board_norm_to_raw.get(net_norm, ()):
            tot.update(bd["copper_by_code"].get(code_of_raw[raw], {}))
        return dict(tot)

    nl_no_pads = []
    for name, net in nl["nets"].items():
        if pads_by_net.get(name):
            continue
        nl_no_pads.append({"net": name, "netlist_raw_names": net["raw_names"], "class": net["class"],
                           "nodes": [f'{n["ref"]}.{n["pin"]}' for n in net["nodes"]][:examples], "node_count": len(net["nodes"]),
                           "on_board_as": sorted(board_norm_to_raw.get(name, ())), "board_copper": copper_of(name)})
    bd_pads_not_in_nl = []
    for name, plist in pads_by_net.items():
        if name in nl["nets"]:
            continue
        bd_pads_not_in_nl.append({"net": name, "board_spelling": sorted({p["net"] for p in plist}),
                                  "pad_count": len(plist),
                                  "pads": [f'{p["ref"]}.{p["number"]}@({p["x"]},{p["y"]})' for p in plist][:examples],
                                  "board_copper": copper_of(name)})
    copper_only = []
    for raw, code in bd["nets_raw"].items():
        name = norm(raw)
        if name in nl["nets"] or pads_by_net.get(name):
            continue
        cu = bd["copper_by_code"].get(code)
        if cu:
            copper_only.append({"net": name, "board_spelling": raw, "board_copper": dict(cu)})
    membership = []
    for name, net in nl["nets"].items():
        sch_pins = {f'{n["ref"]}.{n["pin"]}' for n in net["nodes"]}
        pcb_pins = {f'{p["ref"]}.{p["number"]}' for p in pads_by_net.get(name, ()) if p["number"] != ""}
        if sch_pins != pcb_pins:
            membership.append({"net": name, "board_spelling": sorted(board_norm_to_raw.get(name, ())),
                               "netlist_only": sorted(sch_pins - pcb_pins)[:examples],
                               "board_only": sorted(pcb_pins - sch_pins)[:examples],
                               "netlist_pins": len(sch_pins), "board_pads": len(pcb_pins)})
    N["netlist_nets_without_board_pads"] = nl_no_pads
    N["board_nets_with_pads_not_in_netlist"] = bd_pads_not_in_nl
    N["board_nets_copper_only_not_in_netlist_informational"] = copper_only
    N["net_membership_differences"] = membership
    N["normalisation_collisions"] = {"netlist": nl["name_collisions"], "board": board_collisions}
    N["netlist_nets_in_board_net_table"] = sum(1 for n in nl["nets"] if n in board_norm_to_raw)
    N["board_net_table_size"] = len(bd["nets_raw"])

    # ---- pads with no net that carry copper
    bd["_grid_lookup"] = build_grid(bd["endpoints"])
    copper_pads, npth_no_copper, touching = [], 0, []
    no_copper_by_ref = collections.Counter()
    for pad in bd["pads"]:
        if pad["netcode"] > 0 or norm(pad["net"]) != "":
            continue
        if not pad["has_copper"]:
            npth_no_copper += 1
            no_copper_by_ref[f'{pad["ref"]}:{pad["attribute"]}'] += 1
            continue
        row = pad_public(pad, in_netlist=pad["ref"] in comps,
                         netlist_net=nl["node_net"].get((pad["ref"], pad["number"])))
        copper_pads.append(row)
        hits = touching_copper(bd, pad)
        if hits:
            touching.append(dict(row, touching=hits[:12], touching_count=len(hits)))
    Z["pads_no_net_with_copper"] = copper_pads
    Z["pads_no_net_without_copper_count"] = npth_no_copper
    Z["pads_no_net_without_copper_by_ref_attribute"] = dict(sorted(no_copper_by_ref.items()))
    Z["pads_no_net_touched_by_track_or_via"] = touching
    Z["method"] = ("pad has copper = on a copper layer and not NPTH-without-copper; touched = a track/arc end "
                   "or via centre inside the pad shape on a shared copper layer (zone fills not tested)")

    report["informational"] = {
        "unconnected_items_api": bd["unconnected_items"],
        "unconnected_note": "KiCad connectivity ratsnest count on the stored zone fills (no refill); the board is "
                            "mid-route, this is information, not a parity defect",
        "timing_s": bd["timing"]}
    return report


def summarise(report, nl, bd, netlist_info):
    C, P, N, Z = report["components"], report["pads"], report["nets"], report["no_net_pads"]
    extra = C["board_footprints_not_in_netlist"]
    real_kinds = {k: v for k, v in P["pad_net_mismatch_kinds"].items() if k != "both_unconnected_name_differs"}
    s = collections.OrderedDict()
    s["netlist_components"] = len(nl["components"])
    s["board_footprints"] = len(bd["footprints"])
    s["netlist_nets"] = len(nl["nets"])
    s["netlist_nodes"] = len(nl["node_net"])
    s["board_pads"] = len(bd["pads"])
    s["board_pads_with_net"] = sum(1 for p in bd["pads"] if p["netcode"] > 0)
    s["board_nets_in_table"] = N["board_net_table_size"]
    s["components_missing_on_board"] = len(C["netlist_components_missing_on_board"])
    s["components_excluded_from_board"] = len(C["netlist_components_excluded_from_board"])
    s["board_extra_mechanical"] = len(extra["mechanical_by_ref"])
    s["board_extra_board_only_attr"] = len(extra["board_only_attr"])
    s["board_extra_unexpected"] = len(extra["unexpected"])
    s["footprint_id_mismatch"] = len(C["footprint_id_mismatch"])
    s["footprint_id_mismatch_case_only"] = len(C["footprint_id_mismatch_case_only"])
    s["value_mismatch"] = len(C["value_mismatch"])
    s["path_mismatch_informational"] = len(C["path_mismatch_informational"])
    s["dnp_flag_mismatch_informational"] = len(C["dnp_flag_mismatch_informational"])
    s["exclude_from_bom_flag_mismatch_informational"] = len(C["exclude_from_bom_flag_mismatch_informational"])
    s["duplicate_refs"] = len(C["duplicate_refs"]["netlist"]) + len(C["duplicate_refs"]["board"])
    s["pads_matched"] = P["pads_matched"]
    s["pad_net_mismatch"] = len(P["pad_net_mismatch"])
    s["pad_net_mismatch_kinds"] = P["pad_net_mismatch_kinds"]
    s["pad_net_mismatch_excluding_unconnected_renames"] = sum(real_kinds.values())
    s["netlist_nodes_without_board_pad"] = len(P["netlist_nodes_without_board_pad"])
    s["board_pads_without_netlist_node"] = len(P["board_pads_without_netlist_node"])
    s["board_pads_without_netlist_node_with_net"] = len(P["board_pads_without_netlist_node_with_net"])
    s["board_pads_unnumbered"] = P["board_pads_unnumbered"]["count"]
    s["board_pads_unnumbered_with_net"] = len(P["board_pads_unnumbered"]["with_net"])
    s["netlist_nets_without_board_pads"] = len(N["netlist_nets_without_board_pads"])
    s["board_nets_with_pads_not_in_netlist"] = len(N["board_nets_with_pads_not_in_netlist"])
    s["board_nets_copper_only_not_in_netlist_informational"] = len(N["board_nets_copper_only_not_in_netlist_informational"])
    s["net_membership_differences"] = len(N["net_membership_differences"])
    s["normalisation_collisions"] = len(N["normalisation_collisions"]["netlist"]) + len(N["normalisation_collisions"]["board"])
    s["pads_no_net_with_copper"] = len(Z["pads_no_net_with_copper"])
    s["pads_no_net_without_copper"] = Z["pads_no_net_without_copper_count"]
    s["pads_no_net_touched_by_track_or_via"] = len(Z["pads_no_net_touched_by_track_or_via"])
    s["unconnected_items_api_informational"] = report["informational"]["unconnected_items_api"]
    defects = (s["components_missing_on_board"] + s["board_extra_unexpected"] + s["footprint_id_mismatch"]
               + s["value_mismatch"] + s["pad_net_mismatch"] + s["netlist_nodes_without_board_pad"]
               + s["board_pads_without_netlist_node_with_net"] + s["board_pads_unnumbered_with_net"]
               + s["netlist_nets_without_board_pads"] + s["board_nets_with_pads_not_in_netlist"]
               + s["pads_no_net_touched_by_track_or_via"] + s["duplicate_refs"] + s["normalisation_collisions"])
    s["parity_defects"] = defects
    s["status"] = "parity_ok" if defects == 0 else "mismatches"
    s["evidence_class"] = "source inspection of the board file (pcbnew load) and the netlist file; no DRC, no refill"
    return s


def top_findings(report, s, limit=15):
    C, P, N, Z = report["components"], report["pads"], report["nets"], report["no_net_pads"]
    out = []

    def add(text):
        if len(out) < limit:
            out.append(text)

    for r in C["netlist_components_missing_on_board"][:3]:
        add(f'netlist component {r["ref"]} ({r["value"]}, {r["footprint"]}) is not on the board')
    for r in C["board_footprints_not_in_netlist"]["unexpected"][:3]:
        add(f'board footprint {r["ref"]} ({r["fpid"]}) at ({r["x"]}, {r["y"]}) mm is not in the netlist '
            f'({r["pads_with_net"]} of {r["pads"]} pads carry a net)')
    for r in C["footprint_id_mismatch"][:3]:
        add(f'{r["ref"]} at ({r["x"]}, {r["y"]}) mm: footprint id netlist={r["netlist_footprint"]} board={r["board_fpid"]}')
    for r in C["value_mismatch"][:3]:
        add(f'{r["ref"]} at ({r["x"]}, {r["y"]}) mm: value netlist={r["netlist_value"]!r} board={r["board_value"]!r}')
    for r in P["pad_net_mismatch"][:4]:
        add(f'pad {r["ref"]}.{r["number"]} at ({r["x"]}, {r["y"]}) mm: net netlist={r["netlist_net"]} '
            f'board={r["board_net"]} [{r["kind"]}]')
    for r in P["netlist_nodes_without_board_pad"][:3]:
        add(f'netlist node {r["ref"]}.{r["pin"]} (net {r["net"]}) has no pad on {r["fpid"]} at ({r["x"]}, {r["y"]}) mm')
    for r in P["board_pads_without_netlist_node_with_net"][:3]:
        add(f'board pad {r["ref"]}.{r["number"]} at ({r["x"]}, {r["y"]}) mm carries {r["net"]} but has no netlist node')
    for r in P["board_pads_unnumbered"]["with_net"][:2]:
        add(f'unnumbered pad of {r["ref"]} at ({r["x"]}, {r["y"]}) mm carries net {r["net"]}')
    for r in N["netlist_nets_without_board_pads"][:3]:
        add(f'netlist net {r["net"]} ({r["node_count"]} nodes: {", ".join(r["nodes"][:4])}) has no board pad')
    for r in N["board_nets_with_pads_not_in_netlist"][:3]:
        add(f'board net {r["net"]} has {r["pad_count"]} pads ({", ".join(r["pads"][:3])}) but is not in the netlist')
    for r in Z["pads_no_net_touched_by_track_or_via"][:3]:
        t = r["touching"][0]
        add(f'no-net pad {r["ref"]}.{r["number"] or "(unnumbered)"} at ({r["x"]}, {r["y"]}) mm is touched by '
            f'{t["item"]} of net {t["net"] or "(none)"} at ({t["x"]}, {t["y"]}) mm')
    for r in N["normalisation_collisions"]["board"][:2]:
        add(f'board net names collide after {{slash}} normalisation: {r["raw_names"]}')
    if not out:
        add(f'parity clean: {s["pads_matched"]} pads match their netlist node net, {s["netlist_components"]} components '
            f'matched by ref/footprint/value; extras: {s["board_extra_mechanical"]} mechanical, '
            f'{s["board_extra_board_only_attr"]} board-only')
    add(f'no-net pads with copper: {s["pads_no_net_with_copper"]} ({s["pads_no_net_touched_by_track_or_via"]} touched '
        f'by a track or via); unconnected items (informational, mid-route): {s["unconnected_items_api_informational"]}')
    return out[:limit]


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--netlist", "--examples"):
            opts[a] = argv[i + 1]
            args.remove(argv[i + 1])
            i += 2
            continue
        if a.startswith("--"):
            opts[a] = True
        i += 1
    if len(args) != 2:
        print("usage: netlist_parity.py board.kicad_pcb [--netlist sch.net] [--no-connectivity] [--examples N] out.json",
              file=sys.stderr)
        return 2
    board_path, out_path = args
    netlist_path = opts.get("--netlist") or os.path.join(os.path.dirname(os.path.abspath(board_path)), "sch.net")
    examples = int(opts.get("--examples", 40))
    nl = read_netlist(netlist_path)
    bd = read_board(board_path, want_connectivity="--no-connectivity" not in opts)
    report = compare(nl, bd, examples)
    s = summarise(report, nl, bd, nl["info"])
    findings = top_findings(report, s)
    out = collections.OrderedDict()
    out["tool"] = "netlist_parity"
    out["evidence_class"] = s["evidence_class"]
    out["generated"] = datetime.datetime.now().isoformat(timespec="seconds")
    out["inputs"] = {"board": file_identity(board_path), "netlist": dict(file_identity(netlist_path), **nl["info"])}
    out["board_copper"] = {"tracks_and_arcs": bd["track_count"], "vias": bd["via_count"], "zones": bd["zone_count"],
                           "copper_layers": sorted(bd["layer_name"](l) for l in bd["copper_layers"])}
    out["summary"] = s
    out["top_findings"] = findings
    out.update(report)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    line = collections.OrderedDict((k, v) for k, v in s.items() if k not in ("evidence_class",))
    line["out"] = os.path.abspath(out_path)
    print(json.dumps(line, default=str))
    return 0  # the result is the "status" field; exit 0 so pipeline scripts under set -e keep going


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
