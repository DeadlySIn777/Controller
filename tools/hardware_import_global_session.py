"""Import a global reroute in isolation; replace only native track/via/arc records.

Run with KiCad Python. Source placement, pads, rules, outline and zone definitions
remain byte-exact. Full native refill/DRC and electrical acceptance remain required.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import sys
import os
if os.name == "nt":
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetProcessAffinityMask.argtypes = (wintypes.HANDLE, ctypes.c_size_t)
    kernel.SetPriorityClass.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), sum(1 << i for i in range(16,20)))
    assert kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000)
import pcbnew

TOKENS = re.compile(rb'"(?:\\.|[^"\\])*"|[()]')
ROUTES = {b"segment", b"via", b"arc"}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def top_nodes(data):
    depth, start, kind = 0, None, None
    for token in TOKENS.finditer(data):
        ch = token.group()
        if ch == b"(":
            depth += 1
            if depth == 2:
                start = token.start()
                kind = re.match(rb"\(\s*([^\s()]+)", data[start: start + 100]).group(1)
        elif ch == b")":
            if depth == 2:
                yield kind, start, token.end()
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced source")
    assert depth == 0

def section(data, name):
    # Both native pretty-printed and transformed single-line DSNs are used.
    match = re.search(rb"\(" + name.encode() + rb"(?=\s)", data)
    if not match:
        return None
    start = data.index(b"(", match.start())
    depth = 0
    for token in TOKENS.finditer(data, start):
        if token.group() == b"(":
            depth += 1
        elif token.group() == b")":
            depth -= 1
            if depth == 0:
                return start, token.end(), data[start:token.end()]
    raise ValueError("Unterminated section")

def placements(data, session=False):
    s = section(data, "placement")
    if not s:
        return {}
    raw = s[2]
    unit = {b"mm": 1.0, b"um": .001, b"mil": .0254, b"inch": 25.4}
    factor = .001
    if session:
        resolution = re.search(rb"\(resolution\s+(\w+)\s+([\d.]+)\)", raw)
        assert resolution
        factor = unit[resolution[1]] / float(resolution[2])
    else:
        base_unit = re.search(rb"\(unit\s+(\w+)\)", data)
        assert base_unit
        factor = unit[base_unit[1]]
    rows = {}
    for m in re.finditer(rb'\(place\s+("(?:\\.|[^"\\])*"|[^\s()]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+(front|back)\s+([-\d.eE+]+)', raw):
        name = m[1].decode()
        name = json.loads(name) if name.startswith('"') else name
        assert name not in rows
        rows[name] = (float(m[2])*factor, -float(m[3])*factor,
                      m[4].decode(), float(m[5]) % 360)
    return rows

def pose(board):
    return {
        "footprints": {f.m_Uuid.AsString(): (f.GetReference(), f.GetValue(), f.GetPosition().x,
                         f.GetPosition().y, f.GetOrientation().AsDegrees(), f.GetLayer())
                       for f in board.GetFootprints()},
        "pads": {p.m_Uuid.AsString(): (p.GetNumber(), p.GetNetname(), p.GetPosition().x,
                    p.GetPosition().y, p.GetOrientation().AsDegrees(), tuple(p.GetLayerSet().Seq()))
                 for f in board.GetFootprints() for p in f.Pads()}
    }

def remove_routes(data):
    nodes = [(k,a,b) for k,a,b in top_nodes(data) if k in ROUTES]
    out, cursor = [], 0
    for _, start, end in nodes:
        out.append(data[cursor:start])
        cursor = end
    out.append(data[cursor:])
    return b"".join(out), nodes

def import_global(args):
    source, dsn, session, out = [Path(getattr(args, n)).resolve() for n in ("board", "dsn", "session", "output")]
    original = source.read_bytes()
    assert sha(original) == args.expected_board_sha256, "Source board changed"
    assert not out.exists(), "Use a fresh output directory"
    dsn_data, ses_data = dsn.read_bytes(), session.read_bytes()
    base_places, ses_places = placements(dsn_data), placements(ses_data, session=True)
    assert base_places and ses_places and set(base_places) == set(ses_places), "Session placement inventory differs"
    for ref, a in base_places.items():
        b = ses_places[ref]
        assert a[2] == b[2] and abs((a[3]-b[3]+180)%360-180) < 1e-7, (ref, "side/rotation changed")
        assert max(abs(a[i]-b[i]) for i in (0,1)) <= .000101, (ref, "position changed")
    out.mkdir(parents=True)
    placement = section(ses_data, "placement")
    assert placement
    # Placement has already been checked; native import need not re-quantize it.
    sanitized = ses_data[:placement[0]] + ses_data[placement[1]:]
    imported_session = out / "routing-only.ses"
    imported_session.write_bytes(sanitized)
    board = pcbnew.LoadBoard(str(source))
    before_pose = pose(board)
    old_count = len(list(board.GetTracks()))
    # Explicitly clear all old routes, including locked ones. Native importer
    # behavior differs across KiCad versions; the global session supplies all.
    for track in list(board.GetTracks()):
        board.Remove(track)
    assert len(list(board.GetTracks())) == 0
    assert pcbnew.ImportSpecctraSES(board, str(imported_session)), "Native SES import failed"
    assert pose(board) == before_pose, "Native session changed pads or placement"
    assert all(t.GetNetname() for t in board.GetTracks()), "Unassigned imported route"
    donor = out / "donor.kicad_pcb"
    pcbnew.SaveBoard(str(donor), board)
    donor_data = donor.read_bytes()
    new_nodes = [(k,a,b) for k,a,b in top_nodes(donor_data) if k in ROUTES]
    assert new_nodes
    retained, old_nodes = remove_routes(original)
    assert len(old_nodes) == old_count
    close = retained.rfind(b")")
    new_copper = b"\n".join(donor_data[a:b] for _,a,b in new_nodes)
    combined = retained[:close] + b"\n" + new_copper + b"\n" + retained[close:]
    combined_without_routes, combined_nodes = remove_routes(combined)
    # Only whitespace joins accompany replacement of the top-level Cu records.
    assert re.sub(rb"\s+", b" ", combined_without_routes) == re.sub(rb"\s+", b" ", retained)
    original_noncu = [original[a:b] for k,a,b in top_nodes(original) if k not in ROUTES]
    current_noncu = [combined[a:b] for k,a,b in top_nodes(combined) if k not in ROUTES]
    assert original_noncu == current_noncu, "Non-Cu source records changed"
    dest = out / "board.kicad_pcb"
    dest.write_bytes(combined)
    # Adjacent native project and source libraries are preserved for normal GUI/CLI use.
    for p in source.parent.rglob("*"):
        rel = p.relative_to(source.parent)
        if not p.is_file() or p == source or p.suffix in {".kicad_prl", ".lck"} or p.name.startswith("~"):
            continue
        if p.suffix in {".kicad_pro", ".kicad_dru", ".kicad_sch", ".kicad_sym", ".kicad_mod"} or p.name in {"fp-lib-table", "sym-lib-table"}:
            target = out / rel
            if rel.parent == Path(".") and p.stem == source.stem and p.suffix in {".kicad_pro", ".kicad_dru"}:
                target = out / ("board" + p.suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
    reloaded = pcbnew.LoadBoard(str(dest))
    assert pose(reloaded) == before_pose
    assert len(list(reloaded.GetTracks())) == len(new_nodes)
    assert source.read_bytes() == original and dsn.read_bytes() == dsn_data and session.read_bytes() == ses_data
    receipt = {"status":"GLOBAL_SESSION_NATIVE_IMPORTED_SOURCE_RECORDS_RETAINED_REFILL_DRC_ELECTRICAL_OPEN",
       "KiCad":pcbnew.GetBuildVersion(), "source_board":str(source), "source_SHA256":sha(original),
       "dsn_SHA256":sha(dsn_data), "session_SHA256":sha(ses_data), "candidate":str(dest),
       "candidate_SHA256":sha(combined), "old_Cu_records":old_count, "new_Cu_records":len(new_nodes),
       "placement_checked_and_not_reimported":len(base_places), "all_nonCu_source_records_byte_exact":True,
       "native_pad_and_footprint_poses_unchanged":True, "source_inputs_unchanged":True,
       "native_Fill_calls":0, "native_after_join_count":None, "manufacturing_ready":False}
    (out / "import-receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))

def probe(args):
    out = Path(args.output).resolve()
    assert not out.exists()
    out.mkdir(parents=True)
    board = pcbnew.BOARD()
    net = pcbnew.NETINFO_ITEM(board, "/TEST", 1)
    board.Add(net)
    for x, locked in ((2,True),(4,False)):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(2)))
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(3)))
        t.SetWidth(pcbnew.FromMM(.2));t.SetLayer(pcbnew.F_Cu);t.SetNet(net);t.SetLocked(locked);board.Add(t)
    session = out / "fixture.ses"
    session.write_text('(session "test" (base_design "test") (routes (resolution um 1) (parser (host_cad "KiCad") (host_version "10")) (library_out) (network_out (net "/TEST" (wire (path F.Cu 200 10000 -10000 20000 -10000))))))\n', encoding="utf-8")
    for track in list(board.GetTracks()):
        board.Remove(track)
    assert not list(board.GetTracks())
    assert pcbnew.ImportSpecctraSES(board,str(session))
    tracks = list(board.GetTracks())
    assert len(tracks) == 1
    t = tracks[0]
    assert (t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth(),t.GetNetname()) == (10000000,10000000,20000000,10000000,200000,"/TEST")
    result = {"status":"INSTALLED_NATIVE_GLOBAL_REPLACEMENT_PROBE_PASS", "KiCad":pcbnew.GetBuildVersion(),
              "old_locked_and_unlocked_routes_removed":True, "only_session_Cu_imported_exactly":True, "Fill_calls":0}
    (out / "probe.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("probe"); p.add_argument("--output",required=True)
    p = sub.add_parser("import")
    for n in ("board","dsn","session","output","expected-board-sha256"):
        p.add_argument("--"+n, required=True)
    args = parser.parse_args()
    probe(args) if args.command == "probe" else import_global(args)
