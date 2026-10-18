"""pcbtext.py - text-level helpers for KiCad 10 .kicad_pcb files (system python, no KiCad needed).

KiCad writes one top-level item per block that starts on a line beginning with exactly one tab and '(' and nests
deeper items with more tabs (strings escape newlines), so top-level blocks can be cut at b"\\n\\t(" without a full
S-expression parse. split() checks that the pieces re-join to the exact input bytes.

    split(data)            -> (head, [chunk, ...], tail)   bytes; head + b"".join(chunks) + tail == data
    chunk_kind(chunk)      -> 'segment' | 'via' | 'footprint' | 'zone' | 'gr_line' | ... | 'version' ...
    chunk_uuid(chunk)      -> the item's own uuid (depth-2 '(uuid "...")' line) or None
    chunk_layer(chunk)     -> the item's own depth-2 '(layer "...")' or None
    item_counts(data)      -> {kind: count}
    zone_fills(data)       -> {zone_uuid: {"name", "net", "layers": {layer: [filled_polygon block bytes, ...]}}}
    sha256_file(path)
"""
import collections
import hashlib
import re

_START = re.compile(rb"\n\t\(")
_KIND = re.compile(rb"\t\(([A-Za-z_0-9]+)")
_UUID = re.compile(rb'\n\t\t\(uuid "([^"]+)"\)')
_LAYER = re.compile(rb'\n\t\t\(layer "([^"]+)"')
_NET = re.compile(rb'\n\t\t\(net "((?:[^"\\]|\\.)*)"\)')
_NAME = re.compile(rb'\n\t\t\(name "((?:[^"\\]|\\.)*)"\)')
_FP_LAYER = re.compile(rb'\n\t\t\t\(layer "([^"]+)"\)')


def sha256_file(path, bufsize=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def split(data):
    starts = [m.start() + 1 for m in _START.finditer(data)]
    if not starts:
        raise ValueError("no top-level items found")
    tail_start = data.rfind(b"\n)") + 1
    if tail_start <= starts[-1]:
        raise ValueError("cannot find the closing parenthesis of kicad_pcb")
    head = data[:starts[0]]
    bounds = starts + [tail_start]
    chunks = [data[bounds[i]:bounds[i + 1]] for i in range(len(starts))]
    tail = data[tail_start:]
    if len(head) + sum(len(c) for c in chunks) + len(tail) != len(data):
        raise ValueError("split does not cover the file")
    return head, chunks, tail


def chunk_kind(chunk):
    m = _KIND.match(chunk)
    return m.group(1).decode() if m else "?"


def chunk_uuid(chunk):
    m = _UUID.search(chunk)
    return m.group(1).decode() if m else None


def chunk_layer(chunk):
    m = _LAYER.search(chunk)
    return m.group(1).decode() if m else None


def item_counts(data):
    _, chunks, _ = split(data)
    c = collections.Counter(chunk_kind(ch) for ch in chunks)
    return dict(sorted(c.items()))


def _depth2_blocks(chunk, token):
    """Blocks '\\t\\t(token ...' .. matching '\\t\\t)' line inside a top-level chunk (formatted output)."""
    out = []
    key = b"\n\t\t(" + token
    pos = 0
    while True:
        i = chunk.find(key, pos)
        if i < 0:
            break
        # single-line block?
        eol = chunk.find(b"\n", i + 1)
        line = chunk[i + 1:eol if eol >= 0 else len(chunk)].rstrip(b"\r")
        if line.endswith(b")") and line.count(b"(") == line.count(b")"):
            out.append(line)
            pos = eol if eol >= 0 else len(chunk)
            continue
        j = chunk.find(b"\n\t\t)", i + 1)
        if j < 0:
            raise ValueError("unterminated block " + token.decode())
        out.append(chunk[i + 1:j + 4])
        pos = j + 4
    return out


def zone_fills(data):
    _, chunks, _ = split(data)
    zones = {}
    for ch in chunks:
        if chunk_kind(ch) != "zone":
            continue
        u = chunk_uuid(ch)
        net = _NET.search(ch)
        name = _NAME.search(ch)
        layers = collections.defaultdict(list)
        for blk in _depth2_blocks(ch, b"filled_polygon"):
            m = re.search(rb'\(layer "([^"]+)"\)', blk)
            layers[m.group(1).decode() if m else "?"].append(blk)
        zones[u] = {"name": name.group(1).decode() if name else "",
                    "net": net.group(1).decode() if net else "",
                    "layers": dict(layers)}
    return zones


def polygon_points(block):
    """[(x, y), ...] in mm from one filled_polygon block."""
    return [(float(a), float(b)) for a, b in re.findall(rb"\(xy ([-0-9.eE]+) ([-0-9.eE]+)\)", block)]
