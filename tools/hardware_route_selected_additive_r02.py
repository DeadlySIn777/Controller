"""Reviewed v2 selected ordinary-signal routing with actual return stitches.

Run with KiCad's bundled Python. The authoritative PCB is never SES-imported:
an isolated donor receives the session and only reviewed new segments/vias are
appended to an exact copy of the authoritative native tree. Old copper UUIDs,
all pad pieces, footprints, drawings, rules and zone definitions are retained.
Power, switching, precision and high-speed routing are excluded. Native DRC and
the independent uncapped inventory are acceptance gates, not a fab-ready claim.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from hardware_build_assembly import parse, dump, child, children, value, q

ROOT = Path(__file__).resolve().parents[1]
CLI = Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
# This is a deny guard in addition to, never instead of, an explicit reviewed
# exact-net allowlist. Ambiguous names require a separate engineering task.
DENY = re.compile(
    r'(^|[/_])(GND|GROUND|CHASSIS|PE|VCC|VDD|VSS|VIN|VBUS|POWER|SUPPLY|'
    r'RAIL|[0-9]+V[0-9]*|IO_3V3|CORE|FIELD|AUX|SW|ISNS|COMP|FB|BOOT|SS|'
    r'AI|AO|ANALOG|REF|BIAS|HDMI|USB|ETH|RGMII|MDI|SD|SDIO|EMMC|PCIE|'
    r'NVME|DDR|JTAG|HOST_SPI|CLOCK|CLK|REFCLK|SPI|CAN|RS485|STEP|DIR|ENC|MPG|FREQ|PWM)(_|/|$)', re.I)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def require_new_report(path):
    path = Path(path).resolve()
    if path.exists() or not path.is_relative_to(ROOT / 'reports'):
        raise ValueError('Use a new immutable workspace reports directory')
    path.mkdir(parents=True)
    return path


CHECKER_SHA256='ae44bbaf5ba31fb4bbe0f1bf7f532f5a07ef5f6546ca82523b760a27379c1aa7'
OLD_ROUTER_SHA256='8452a2853854d86baa88b90b2658117781b7e5c1076886a603da67b450d02b97'
EXTRA_DENY=re.compile(r'(^|[/_])(SCLK|SCK|IOL1|SDI|SDO|MOSI|MISO|SCL|SDA|UART|TXD|RXD|TCK|TDI|TDO|RC|CWD|SENSE|ISENSE|FILTER|DELAY|STROBE|PULSE|D[0-9]+|A[0-9]+)(_|/|$)',re.I)


def checked_dependencies():
    for name,expected in [('hardware_check_return_corridors.py',CHECKER_SHA256),
                          ('hardware_route_selected_additive.py',OLD_ROUTER_SHA256)]:
        if sha(ROOT/'tools'/name)!=expected:
            raise ValueError('Reviewed frozen routing dependency has changed: '+name)
    return dict(checker_sha256=CHECKER_SHA256,old_router_sha256=OLD_ROUTER_SHA256)


def _base_manifest_check_v2(manifest, board_nets, board_layers, node_inventory):
    if manifest.get('schema_version') != 2 or not manifest.get('electrical_review'):
        raise ValueError('An exact reviewed ordinary-signal manifest is required')
    rows = manifest.get('nets')
    if not isinstance(rows, dict) or not rows:
        raise ValueError('No reviewed exact nets')
    for name, row in rows.items():
        if name not in board_nets or (DENY.search(name.rsplit('/',1)[-1]) and name not in (
                '/motherboard_io_control/DOA_FIELD_POWER_GOOD','/motherboard_io_control/DOB_FIELD_POWER_GOOD',
                '/motherboard_io_control/DI_SAFETY_SUPPLY_FAULT')):
            raise ValueError('Absent, ambiguous or excluded net: ' + name)
        if row.get('type') != 'ordinary_logic' or row.get('controlled_impedance') is not False:
            raise ValueError('Only ordinary logic without impedance constraints: ' + name)
        if not 0 < row.get('maximum_voltage_v', 0) <= 5.5:
            raise ValueError('Bounded ordinary logic voltage is required: ' + name)
        if not 0 < row.get('width_mm', 0) <= .5 or not .15 <= row.get('clearance_mm', 0) <= 1:
            raise ValueError('Explicit bounded native routing dimensions required: ' + name)
        layers = row.get('layers')
        refs = row.get('reference_layers')
        if not layers or len(set(layers)) != len(layers) or not isinstance(refs, dict) or set(refs) != set(layers):
            raise ValueError('Every signal layer requires an explicit reference layer: ' + name)
        if row.get('return_net') not in board_nets or row['return_net'] == name:
            raise ValueError('Actual same-domain return net required: ' + name)
        if not .1 <= row.get('reference_corridor_margin_mm', 0) <= 2:
            raise ValueError('Explicit geometric return corridor margin required: ' + name)
        for layer in layers:
            ref = refs[layer]
            if layer not in board_layers or ref not in board_layers or abs(board_layers.index(layer) - board_layers.index(ref)) != 1:
                raise ValueError('Reference must be a physically adjacent copper layer: ' + name)
            if ref in layers:
                raise ValueError('Do not autoroute the reserved reference layer: ' + name)
        expected = sorted(tuple(p) for p in row.get('source_pins', []))
        if len(expected) < 2 or len(set(expected)) != len(expected) or expected != sorted(node_inventory.get(name, [])):
            raise ValueError('Exact full physical source-pin inventory required: ' + name)
        if row.get('allow_vias') not in (False, True):
            raise ValueError('An explicit via decision is required: ' + name)
        if row['allow_vias'] and not 0 < row.get('return_stitch_distance_mm', 0) <= 1:
            raise ValueError('Through-via return stitching bound is required: ' + name)
        if row['allow_vias'] and not (.2 <= row.get('via_drill_mm', 0) <= .4 and
                                     row.get('via_drill_mm', 0) + .15 <= row.get('via_diameter_mm', 0) <= .8):
            raise ValueError('An exact reviewed manufacturable via geometry is required: ' + name)
    return rows



def manifest_check(manifest,board_nets,board_layers,node_inventory):
    from hardware_build_ordinary_route_manifest import CLASSES
    if manifest.get('schema_version')!=2:
        raise ValueError('Version2 exact source/return/class review is required')
    rows=_base_manifest_check_v2(manifest,board_nets,board_layers,node_inventory)
    for name,row in rows.items():
        if EXTRA_DENY.search(name):raise ValueError('Clock/data/precision/timing net is excluded: '+name)
        if row.get('signal_class')not in CLASSES or row.get('return_domain')!='LOGIC' or row['return_net']!='/LOGIC_GND':
            raise ValueError('Exact reviewed ordinary class and return domain required: '+name)
        endpoints=row.get('source_endpoints',[])
        if sorted((p['reference'],p['pin'])for p in endpoints)!=sorted(tuple(p)for p in row['source_pins']):
            raise ValueError('Actual source endpoint proof must cover every physical endpoint: '+name)
        if any(not p.get('mpn')or ('function'not in p)or
               (p['reference'].startswith('U')and not p['function'])for p in endpoints):
            raise ValueError('Every endpoint needs the actual part/pin function: '+name)
        if any(p['reference'].startswith('U')and not p.get('actual_logic_return_pins')for p in endpoints):
            raise ValueError('An active endpoint lacks an actual source return pin: '+name)
    return rows


def frozen_review_check(manifest,design,netlist):
    checked_dependencies()
    for label in ('source_review','plane_review'):
        evidence=manifest.get(label,{})
        if not evidence.get('path')or not evidence.get('sha256')or sha(evidence['path'])!=evidence['sha256']:
            raise ValueError('Frozen source/plane review is required: '+label)
    review=read(manifest['source_review']['path'])
    hashes=review['source_review_sha256']
    if sha(design)not in hashes.values()or sha(netlist)not in hashes.values():
        raise ValueError('Frozen ordinary review does not cover these exact source bytes')
    for name,row in manifest['nets'].items():
        if review['nets'].get(name)!=row:raise ValueError('Ordinary source row changed or unreviewed: '+name)
    planes=read(manifest['plane_review']['path'])
    if planes.get('board_sha256')!=manifest['board_sha256']or planes.get('passed')is not True:
        raise ValueError('Plane review must pass against this exact native board')
    return dict(source_review_sha256=manifest['source_review']['sha256'],
                plane_review_sha256=manifest['plane_review']['sha256'],**checked_dependencies())


def all_pad_pieces(tree):
    """A UUID-keyed inventory preserves duplicate numbered pieces and paste pads."""
    result = {}
    for fp in children(tree, 'footprint'):
        ref = next(value(p[2]) for p in children(fp, 'property') if value(p[1]) == 'Reference')
        for pad in children(fp, 'pad'):
            ident = value(child(pad, 'uuid')[1])
            if ident in result:
                raise ValueError('Duplicate native pad-piece UUID')
            result[ident] = (ref, dump(pad))
    return result


def zone_definitions(tree):
    result = {}
    for zone in children(tree, 'zone'):
        z = copy.deepcopy(zone)
        # Refill is generated data, not a license to change electrical zones.
        for kind in ('filled_polygon', 'fill_segments'):
            for generated in list(children(z, kind)):
                z.remove(generated)
        result[value(child(zone, 'uuid')[1])] = dump(z)
    return result


def immutable_objects(tree):
    # Compare ALL top-level native objects except route additions and generated
    # zone fills, rather than selecting only familiar drawings or footprints.
    normal = [dump(n) if isinstance(n, list) else n for n in tree
              if not (isinstance(n, list) and n and n[0] in ('segment', 'via', 'arc', 'zone'))]
    return normal, zone_definitions(tree), all_pad_pieces(tree)


def route_geometry(item):
    """Native segment/via identity without UUID; net and all geometry stay exact."""
    item = copy.deepcopy(item)
    for ident in list(children(item, 'uuid')):
        item.remove(ident)
    return dump(item)


def transform_dsn(tree, rows):
    """Retain physical library/placement/structure and protect every old wire.

    The interchange copy omits excluded electrical net declarations. Their
    physical pins and retained conductors remain fixed netless obstacles. The
    native PCB and final merge keep their exact original electrical assignments.
    Freerouting v2.4.1 Wiring.java accepts protected netless wires/vias; NetClass
    and Network.java implement per-class use_layer as exact active layer lists.
    """
    tree = copy.deepcopy(tree)
    network = child(tree, 'network')
    structure = child(tree, 'structure')
    if network is None or structure is None:
        raise ValueError('Native DSN lacks physical structure/network')
    native_names = {value(n[1]) for n in children(network, 'net')}
    if not set(rows) <= native_names:
        raise ValueError('Reviewed net omitted from native DSN export')
    via = child(structure, 'via')
    if via is None or len(via) < 2:
        raise ValueError('Use the actual native via padstack, never invent one')
    for kind in ('class', 'class_class'):
        for c in list(children(network, kind)):
            network.remove(c)
    for n in list(children(network, 'net')):
        if value(n[1]) not in rows:
            network.remove(n)
    for index, (name, row) in enumerate(sorted(rows.items())):
        network.append(['class', q('Reviewed_ordinary_' + str(index)), q(name),
                        ['circuit', ['use_via'] + list(via[1:]),
                         ['use_layer'] + [q(n) for n in row['layers']]],
                        ['rule', ['width', str(row['width_mm'] * 1000)],
                         ['clearance', str(row['clearance_mm'] * 1000)]]])
    # Freerouting creates electrical nets from plane declarations even when
    # those nets were omitted from the selected network. Do not let an
    # interchange-only plane reintroduce a power/return autorouting job.
    # Actual filled copper on routable layers is emitted as fixed keepouts
    # below; native planes/reference coverage remain exact in the base PCB.
    excluded_planes = 0
    for plane in list(children(structure, 'plane')):
        if value(plane[1]) not in rows:
            structure.remove(plane)
            excluded_planes += 1
    protected = 0
    netless = 0
    wiring = child(tree, 'wiring')
    if wiring:
        for item in wiring[1:]:
            if not isinstance(item, list) or item[0] not in ('wire', 'via'):
                continue
            for t in list(children(item, 'type')):
                item.remove(t)
            item.append(['type', 'protect'])
            n = child(item, 'net')
            if n is not None and value(n[1]) not in rows:
                item.remove(n)
                netless += 1
            protected += 1
    return tree, dict(selected_nets=sorted(rows), excluded_net_count=len(native_names - set(rows)),
                      old_wires_vias_protected=protected, excluded_old_conductors_netless_obstacles=netless,
                      excluded_nominal_planes_replaced_by_native_filled_copper_keepouts=excluded_planes)


def protect_routable_filled_copper(tree, board, rows):
    """Exact filled copper is an obstacle, even when its net is not routable.

    DSN plane declarations describe nominal outlines; their native generated
    holes and islands need separate explicit geometry when routing on that
    layer. Include the actual filled polygons, with their actual holes, as fixed
    interchange keepouts. Native zone definitions are never modified.
    """
    structure = child(tree, 'structure')
    routable = {layer for row in rows.values() for layer in row['layers']}
    count = 0
    def polygon(chain, layer):
        coords = []
        for index in range(chain.PointCount()):
            point = chain.CPoint(index)
            coords.extend([str(point.x / 1000), str(-point.y / 1000)])
        return ['polygon', q(layer), '0'] + coords
    for zone in board.Zones():
        if zone.GetNetname() in rows:
            raise ValueError('Ordinary selected nets cannot also be zone/plane nets')
        for layer in routable:
            number = board.GetLayerID(layer)
            if not zone.HasFilledPolysForLayer(number):
                continue
            polys = zone.GetFilledPolysList(number)
            for outline in range(polys.OutlineCount()):
                keepout = ['keepout', polygon(polys.COutline(outline), layer)]
                for hole in range(polys.HoleCount(outline)):
                    keepout.append(['window', polygon(polys.CHole(outline, hole), layer)])
                structure.append(keepout)
                count += 1
    return count


def native_source_check(board, design, netlist):
    from hardware_populate_motherboard_pcb import native_parts_and_nets, verify_population
    from hardware_route_logic_return import identity
    _, nodes = native_parts_and_nets(netlist, design['components'])
    tracks = {t.m_Uuid.AsString(): identity(t) for t in board.GetTracks()}
    result = verify_population(board, design, nodes, tracks, {}, {}, [])
    if not result['ok']:
        raise ValueError('Complete native source population mismatch: ' + repr(result['errors']))
    by_net = {}
    for (ref, pin), name in nodes.items():
        if name.startswith('unconnected-'):
            continue
        by_net.setdefault(name, []).append((ref, pin))
    return result, by_net


def protect_actual_reference_voids(tree,board,rows):
    """Guide the donor away from actual same-domain reference-plane voids.

    This supplements, never replaces, the final exact geometric return proof.
    No nominal plane outline is treated as copper. Only this version's single
    reviewed LOGIC domain is supported; mixed-domain global obstacles would
    falsely forbid another domain's valid routes and are expressly rejected.
    """
    import pcbnew
    from hardware_check_return_corridors import ReturnCheck,copy_poly
    checker=ReturnCheck(board,rows);outline=pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(outline,False):raise ValueError('Actual closed native outline is required')
    definitions={}
    for row in rows.values():
        for signal,reference in row['reference_layers'].items():
            definitions.setdefault(signal,set()).add((row['return_net'],reference))
    structure=child(tree,'structure');records=[]
    def polygon(chain,layer):
        coords=[]
        for i in range(chain.PointCount()):
            p=chain.CPoint(i);coords.extend([str(p.x/1000),str(-p.y/1000)])
        return ['polygon',q(layer),'0']+coords
    for layer,domains in sorted(definitions.items()):
        if len(domains)!=1:raise ValueError('Mixed-domain routing needs per-net obstacle treatment')
        net,reference=next(iter(domains));void=copy_poly(outline)
        void.BooleanSubtract(checker.reference(net,board.GetLayerID(reference)))
        for i in range(void.OutlineCount()):
            obstacle=['keepout',polygon(void.COutline(i),layer)]
            for j in range(void.HoleCount(i)):obstacle.append(['window',polygon(void.CHole(i,j),layer)])
            structure.append(obstacle)
        records.append(dict(signal_layer=layer,actual_reference_layer=reference,return_net=net,
            actual_reference_void_polygons=void.OutlineCount(),nominal_outlines_used_as_copper=False))
    return records


def native_drc(board, out, name, refill=False):
    args = [str(CLI), 'pcb', 'drc', '--format', 'json', '--all-track-errors', '--severity-all']
    if refill:
        args += ['--refill-zones', '--save-board']
    path = out / (name + '.json')
    run = subprocess.run(args + ['--output', str(path), str(board)], capture_output=True,
                         text=True, encoding='utf-8', errors='replace')
    (out / (name + '.txt')).write_text(run.stdout + run.stderr, encoding='utf-8')
    if not path.is_file():
        raise ValueError('Native DRC did not run; attempt preserved')
    report = read(path)
    if run.returncode or report.get('violations') or report.get('ignored_checks'):
        raise ValueError('Native DRC rejected candidate; no suppression or live adoption')
    return dict(exit_code=run.returncode, regular_violations=0, ignored_checks=[],
                reported_unconnected_items=len(report.get('unconnected_items', [])))


def copy_board_inputs(board, out):
    dest = out / 'base.kicad_pcb'
    shutil.copyfile(board, dest)
    for suffix in ('.kicad_pro', '.kicad_dru'):
        src = board.with_suffix(suffix)
        if src.is_file():
            shutil.copyfile(src, dest.with_suffix(suffix))
    for folder in board.parent.glob('*.pretty'):
        shutil.copytree(folder, out / folder.name)
    for name in ('fp-lib-table', '3dmodels'):
        src = board.parent / name
        if src.is_dir():
            shutil.copytree(src, out / name)
        elif src.is_file():
            shutil.copyfile(src, out / name)
    return dest


def prepare(board, design, netlist, manifest_path, out):
    import pcbnew
    out = require_new_report(out)
    inputs = dict(board=str(board), design=str(design), netlist=str(netlist), manifest=str(manifest_path))
    for suffix, label in (('.kicad_pro', 'project'), ('.kicad_dru', 'rules')):
        path = board.with_suffix(suffix)
        if path.is_file():
            inputs[label] = str(path)
    hashes = {name: sha(path) for name, path in inputs.items()}
    if 'project' not in hashes:
        raise ValueError('A frozen native KiCad project with manufacturing rules is required')
    manifest = read(manifest_path)
    if manifest.get('board_sha256') != hashes['board']:
        raise ValueError('Exact reviewed board hash does not match')
    if manifest.get('design_sha256') != hashes['design'] or manifest.get('netlist_sha256') != hashes['netlist']:
        raise ValueError('Exact reviewed physical source hashes do not match')
    for label in ('project', 'rules'):
        if label in hashes and manifest.get(label + '_sha256') != hashes[label]:
            raise ValueError('Exact reviewed native project/rule hash does not match: ' + label)
    review_dependencies=frozen_review_check(manifest,design,netlist)
    base = copy_board_inputs(board, out)
    shutil.copyfile(design, out / 'design.json')
    shutil.copyfile(netlist, out / 'netlist.xml')
    shutil.copyfile(manifest_path, out / 'manifest.json')
    b = pcbnew.LoadBoard(str(base))
    population, nodes = native_source_check(b, read(design), netlist)
    layers = [b.GetLayerName(i) for i in b.GetEnabledLayers().Seq() if pcbnew.IsCopperLayer(i)]
    # KiCad's layer enums are not the physical stack ordering (B.Cu is 31).
    layers = ['F.Cu'] + sorted([n for n in layers if n.startswith('In')], key=lambda n: int(n[2:-3])) + ['B.Cu']
    rows = manifest_check(manifest, {str(n.GetNetname()) for n in b.GetNetsByName().values()}, layers, nodes)
    for row in rows.values():
        for reference in row['reference_layers'].values():
            layer = b.GetLayerID(reference)
            if not any(z.GetNetname() == row['return_net'] and z.HasFilledPolysForLayer(layer) for z in b.Zones()):
                raise ValueError('Actual filled adjacent return is absent: ' + reference + ' / ' + row['return_net'])
    baseline = native_drc(base, out, 'baseline-drc')
    raw = out / 'native.dsn'
    if not pcbnew.ExportSpecctraDSN(b, str(raw)):
        raise ValueError('Native DSN export failed')
    raw_tree = parse(raw.read_text(encoding='utf-8'))
    selected, selection = transform_dsn(raw_tree, rows)
    selection['actual_filled_copper_keepout_polygons_on_routable_layers'] = protect_routable_filled_copper(selected, b, rows)
    selection['actual_adjacent_reference_void_obstacles']=protect_actual_reference_voids(selected,b,rows)
    # Preserve every physical component/padstack, not just distinct pin numbers.
    for kind in ('library', 'placement'):
        if child(selected, kind) != child(raw_tree, kind):
            raise ValueError('Physical DSN library or placement changed')
    route = out / 'selected.dsn'
    route.write_text(dump(selected) + '\n', encoding='utf-8')
    receipt = dict(schema_version=1, inputs=inputs, input_hashes=hashes,
                   reviewed_dependencies=review_dependencies, prepared_board_sha256=sha(base), design_sha256=sha(out / 'design.json'),
                   netlist_sha256=sha(out / 'netlist.xml'), manifest_sha256=sha(out / 'manifest.json'),
                   native_dsn_sha256=sha(raw), selected_dsn_sha256=sha(route), selection=selection,
                   population=population, baseline_native_drc=baseline,
                   all_native_pad_pieces=len(all_pad_pieces(parse(base.read_text(encoding='utf-8')))),
                   physical_stack=layers, routing_run=False, manufacturing_ready=False,
                   scope='Exact selected ordinary logic; excluded physical pads and protected copper remain obstacles. Session is donor only.')
    if any(sha(path) != hashes[name] for name, path in inputs.items()):
        raise ValueError('Source input changed during preparation')
    write(out / 'prepare.json', receipt)
    return receipt


def merge_tree(base, donor, rows):
    """Never substitute imported copper for authoritative retained copper."""
    if immutable_objects(base) != immutable_objects(donor):
        raise ValueError('SES donor changed native geometry, pad pieces, rules or zone definitions')
    old_by_uuid = {}
    old_geometries = set()
    for kind in ('segment', 'via', 'arc'):
        for item in children(base, kind):
            ident = value(child(item, 'uuid')[1])
            if ident in old_by_uuid:
                raise ValueError('Duplicate old copper UUID')
            old_by_uuid[ident] = dump(item)
            old_geometries.add(route_geometry(item))
    merged = copy.deepcopy(base)
    added = []
    seen = set(old_by_uuid)
    for kind in ('segment', 'via', 'arc'):
        for item in children(donor, kind):
            ident = value(child(item, 'uuid')[1])
            if ident in old_by_uuid:
                if dump(item) != old_by_uuid[ident]:
                    raise ValueError('Donor changed retained copper UUID geometry')
                continue
            if route_geometry(item) in old_geometries:
                continue  # A DSN round trip may assign a new UUID to old geometry.
            name = value(child(item, 'net')[1])
            if name not in rows:
                raise ValueError('Session adds excluded-net copper: ' + name)
            if kind == 'arc':
                raise ValueError('Curved route donor requires a separate corridor implementation')
            row = rows[name]
            if kind == 'segment':
                layer = value(child(item, 'layer')[1])
                if layer not in row['layers'] or abs(float(child(item, 'width')[1]) - row['width_mm']) > 1e-9:
                    raise ValueError('Session used unapproved layer/width: ' + name)
            else:
                if not row['allow_vias']:
                    raise ValueError('Reviewed selected net does not permit vias: ' + name)
                if [value(n) for n in child(item, 'layers')[1:]] != ['F.Cu', 'B.Cu']:
                    raise ValueError('Reviewed donor only supports literal full-stack through vias')
                if (abs(float(child(item, 'size')[1]) - row['via_diameter_mm']) > 1e-9 or
                        abs(float(child(item, 'drill')[1]) - row['via_drill_mm']) > 1e-9):
                    raise ValueError('Session used unapproved via diameter/drill: ' + name)
            if ident in seen:
                raise ValueError('Duplicate donor route UUID')
            seen.add(ident)
            merged.append(copy.deepcopy(item))
            added.append(ident)
            old_geometries.add(route_geometry(item))
    if not added:
        raise ValueError('Session contains no new approved route geometry')
    return merged, added


def corridor_polygon(a, b, radius):
    import pcbnew
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    if length == 0:
        corners = [(ax-radius, ay-radius), (ax+radius, ay-radius), (ax+radius, ay+radius), (ax-radius, ay+radius)]
    else:
        dx, dy = (bx-ax)/length, (by-ay)/length
        nx, ny = -dy*radius, dx*radius
        corners = [(ax-dx*radius+nx, ay-dy*radius+ny), (bx+dx*radius+nx, by+dy*radius+ny),
                   (bx+dx*radius-nx, by+dy*radius-ny), (ax-dx*radius-nx, ay-dy*radius-ny)]
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for x, y in corners:
        poly.Append(round(x), round(y))
    return poly


def return_corridor_check(board,added,rows):
    checked_dependencies()
    from hardware_check_return_corridors import return_corridor_check as reviewed_check
    return reviewed_check(board,added,rows)



def normalize_new_via_bends(path,added,rows):
    """Collapse only NEW unanchored degree-two bends inside via reference voids.

    Replace a tiny new polyline with a clear direct leg to the same actual
    outside endpoint. Every source pad, branch, old copper object and signal
    net/layer/width is immutable. Exact reference polygons screen the new leg;
    actual native DRC/return/source-connectivity checks still decide acceptance.
    """
    import pcbnew
    from hardware_check_return_corridors import ReturnCheck,circle,covered,uid
    from hardware_route_logic_return import segment_hits_box,segment_distance
    tree=parse(Path(path).read_text(encoding='utf8'));ledger=[];removed=set()
    initial=pcbnew.LoadBoard(str(path));via_ids=[uid(t)for t in initial.GetTracks()if uid(t)in added and isinstance(t,pcbnew.PCB_VIA)]
    for ident in via_ids:
        board=pcbnew.LoadBoard(str(path));native={uid(t):t for t in board.GetTracks()};via=native[ident]
        row=rows[via.GetNetname()];centre=tuple(via.GetPosition());checker=ReturnCheck(board,rows)
        for layer_name in row['layers']:
            layer=board.GetLayerID(layer_name);ref=board.GetLayerID(row['reference_layers'][layer_name]);fill=checker.reference(row['return_net'],ref)
            radius=via.GetWidth(pcbnew.F_Cu)/2+checker.zone_clearance[row['return_net'],ref]+pcbnew.FromMM(.02)
            bound=radius+math.sqrt(2)*pcbnew.FromMM(row['width_mm']/2+row['reference_corridor_margin_mm'])+pcbnew.FromMM(.05)
            starts=[t for t in board.GetTracks()if uid(t)in added-removed and not isinstance(t,pcbnew.PCB_VIA)
                    and t.GetNetname()==via.GetNetname()and t.GetLayer()==layer and centre in [tuple(t.GetStart()),tuple(t.GetEnd())]]
            for first in starts:
                chain=[first];at=tuple(first.GetEnd())if tuple(first.GetStart())==centre else tuple(first.GetStart());visited={uid(first)}
                while math.dist(centre,at)<bound:
                    if any(p.IsOnLayer(layer)and p.HitTest(pcbnew.VECTOR2I(*at))for p in board.GetPads()):break
                    if any(uid(t)not in added and t.IsOnLayer(layer)and t.HitTest(pcbnew.VECTOR2I(*at))for t in board.GetTracks()):break
                    peers=[t for t in board.GetTracks()if uid(t)not in removed and not isinstance(t,pcbnew.PCB_VIA)
                           and t.GetNetname()==via.GetNetname()and t.GetLayer()==layer and at in [tuple(t.GetStart()),tuple(t.GetEnd())]]
                    if len(peers)!=2 or any(uid(t)not in added for t in peers):break
                    choices=[t for t in peers if uid(t)not in visited]
                    if len(choices)!=1:break
                    next_leg=choices[0];chain.append(next_leg);visited.add(uid(next_leg))
                    at=tuple(next_leg.GetEnd())if tuple(next_leg.GetStart())==at else tuple(next_leg.GetStart())
                if len(chain)<2 or at==centre:continue
                clear=True
                for pad in board.GetPads():
                    if pad.GetNetname()==via.GetNetname()or not pad.IsOnLayer(layer):continue
                    bb=pad.GetBoundingBox();box=(bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom())
                    if segment_hits_box(centre,at,box,pcbnew.FromMM(row['width_mm']/2+row['clearance_mm'])):clear=False;break
                if not clear:continue
                for t in board.GetTracks():
                    if t.GetNetname()==via.GetNetname()or not t.IsOnLayer(layer):continue
                    if isinstance(t,pcbnew.PCB_ARC):clear=False;break
                    width=t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth()
                    if segment_distance(centre,at,tuple(t.GetStart()),tuple(t.GetEnd()))<pcbnew.FromMM(row['width_mm']/2+row['clearance_mm'])+width/2:clear=False;break
                if not clear:continue
                projected=corridor_polygon(centre,at,pcbnew.FromMM(row['width_mm']/2+row['reference_corridor_margin_mm']))
                exception=circle(centre,radius);exception.BooleanSubtract(fill);projected.BooleanSubtract(exception)
                if not covered(projected,fill):continue
                nodes={value(child(t,'uuid')[1]):t for t in children(tree,'segment')}
                ast=nodes[uid(first)];key='end'if tuple(first.GetStart())==centre else'start'
                child(ast,key)[1:]=[str(v/1e6)for v in at]
                gone=[uid(t)for t in chain[1:]]
                for i in gone:tree.remove(nodes[i]);removed.add(i)
                ledger.append(dict(signal_via_uuid=ident,retained_new_segment_uuid=uid(first),removed_new_segment_uuids=gone,
                    same_net_layer_width_and_outside_endpoint_preserved=True,only_new_unanchored_degree_two_vertices=True,
                    actual_reference_polygon_screen_passed=True,layer=layer_name,direct_leg_mm=[[v/1e6 for v in centre],[v/1e6 for v in at]],
                    final_native_DRC_and_frozen_return_check_required=True))
        Path(path).write_text(dump(tree)+'\n',encoding='utf8')
    return ledger


def eligible_signal_vias(board,added,rows):
    """New vias and retained same-net vias touched by exact new signal endpoints."""
    import pcbnew
    from hardware_check_return_corridors import uid
    endpoints={(str(t.GetNetname()),tuple(p))for t in board.GetTracks()
        if uid(t)in added and not isinstance(t,pcbnew.PCB_VIA)
        for p in (t.GetStart(),t.GetEnd())}
    return [v for v in board.GetTracks()if isinstance(v,pcbnew.PCB_VIA)and str(v.GetNetname())in rows
            and(uid(v)in added or(str(v.GetNetname()),tuple(v.GetPosition()))in endpoints)]


def add_return_stitches(path,added,rows):
    """Append own-domain stitches beside new vias or actual new-leg endpoint vias.

    A proposal is accepted only after final native refill/DRC and the frozen
    checker's actual source-anchor, same-plane-piece and endpoint-annulus tests.
    All pads/drills, retained copper and via-forbidden areas remain obstacles.
    """
    import pcbnew
    from hardware_check_return_corridors import ReturnCheck,circle,covered,uid
    from hardware_route_logic_return import distance
    board=pcbnew.LoadBoard(str(path));board.BuildConnectivity()
    checker=ReturnCheck(board,rows);tree=parse(Path(path).read_text(encoding='utf8'));ledger=[]
    signals=eligible_signal_vias(board,added,rows)
    for signal in sorted(signals,key=uid):
        row=rows[signal.GetNetname()]
        try:
            audit=checker.via(signal,row)
            ledger.append(dict(signal_via_uuid=uid(signal),return_net=row['return_net'],
                               signal_via_was_retained=uid(signal)not in added,
                               reused_return_stitches=audit['return_stitches'],added_stitch_uuid=None))
            continue
        except ValueError:
            pass # A fresh proposal still has to pass this same final gate.
        references=checker.layers_at(signal,row);origin=tuple(signal.GetPosition())
        radius=pcbnew.FromMM(row['via_diameter_mm']/2);clearance=pcbnew.FromMM(row['clearance_mm'])
        found=None
        for ring in (.80,.90,.99):
            for index in range(16):
                angle=2*math.pi*index/16
                point=tuple(round(origin[j]+pcbnew.FromMM(ring)*(math.cos(angle)if j==0 else math.sin(angle)))for j in range(2))
                if not all(covered(circle(point,radius),checker.reference(row['return_net'],layer))for layer in references):continue
                obstacle=False
                for pad in board.GetPads():
                    if not pad.IsOnCopperLayer()and not any(pad.GetDrillSize()):continue
                    bb=pad.GetBoundingBox();guard=radius+clearance
                    if bb.GetLeft()-guard<=point[0]<=bb.GetRight()+guard and bb.GetTop()-guard<=point[1]<=bb.GetBottom()+guard:
                        obstacle=True;break
                if obstacle:continue
                for item in board.GetTracks():
                    if isinstance(item,pcbnew.PCB_VIA):
                        # Own-net drills must not overlap either. Reuse was
                        # checked above instead of placing a duplicate hole.
                        if math.dist(point,tuple(item.GetPosition()))<radius+item.GetWidth(pcbnew.F_Cu)/2+clearance:
                            obstacle=True;break
                    elif item.GetNetname()!=row['return_net']:
                        if isinstance(item,pcbnew.PCB_ARC):
                            bb=item.GetBoundingBox();guard=radius+clearance
                            if bb.GetLeft()-guard<=point[0]<=bb.GetRight()+guard and bb.GetTop()-guard<=point[1]<=bb.GetBottom()+guard:
                                obstacle=True;break
                        elif distance(point,tuple(item.GetStart()),tuple(item.GetEnd()))<radius+item.GetWidth()/2+clearance:
                            obstacle=True;break
                if obstacle:continue
                for zone in board.Zones():
                    if not zone.GetIsRuleArea()or not zone.GetDoNotAllowVias():continue
                    overlap=circle(point,radius);overlap.BooleanIntersection(zone.Outline())
                    if overlap.OutlineCount():obstacle=True;break
                if obstacle:continue
                # Real outline/milling and all remaining native rules are gates
                # in the unsuppressed full native DRC after this finite search.
                found=point;break
            if found:break
        if found is None:raise ValueError('No bounded actual return-stitch position for signal via '+uid(signal))
        v=pcbnew.PCB_VIA(board);ident=uid(v)
        item=['via',['at',str(found[0]/1e6),str(found[1]/1e6)],['size',str(row['via_diameter_mm'])],
              ['drill',str(row['via_drill_mm'])],['layers',q('F.Cu'),q('B.Cu')],
              ['net',q(row['return_net'])],['uuid',q(ident)]]
        tree.append(item)
        # Use a native object for the next search. Output remains the original
        # authoritative tree plus the exact bounded return-via AST only.
        v.SetNet(board.FindNet(row['return_net']))
        v.SetPosition(pcbnew.VECTOR2I(*found));v.SetWidth(pcbnew.FromMM(row['via_diameter_mm']))
        v.SetDrill(pcbnew.FromMM(row['via_drill_mm']));v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);board.Add(v);board.BuildConnectivity()
        checker=ReturnCheck(board,rows)
        ledger.append(dict(signal_via_uuid=uid(signal),return_net=row['return_net'],added_stitch_uuid=ident,
                           signal_via_was_retained=uid(signal)not in added,
                           position_mm=[v/1e6 for v in found],diameter_mm=row['via_diameter_mm'],
                           drill_mm=row['via_drill_mm'],distance_mm=math.dist(found,origin)/1e6,
                           physically_verified_after_final_refill_required=True))
    Path(path).write_text(dump(tree)+'\n',encoding='utf8')
    return ledger


def validate_added_stitches(board,added,rows,ledger):
    from hardware_check_return_corridors import ReturnCheck,uid
    import pcbnew
    exact={uid(t):t for t in board.GetTracks()};proof=[];seen=set()
    eligible={uid(v)for v in eligible_signal_vias(board,added,rows)}
    # Check assigned native identities BEFORE BuildConnectivity can infer a via
    # net from touching stale fill. Inference cannot replace exact source review.
    for row in ledger:
        ident=row.get('added_stitch_uuid')
        if row.get('signal_via_was_retained')is not(row['signal_via_uuid']not in added):
            raise ValueError('Exact retained/new signal-via ledger classification differs')
        if ident and (ident not in exact or str(exact[ident].GetNetname())!=row['return_net']):
            raise ValueError('Assigned native return-stitch net differs from its exact source ledger')
    checker=ReturnCheck(board,rows)
    for row in ledger:
        signal=exact.get(row['signal_via_uuid'])
        if signal is None or uid(signal)not in eligible or not isinstance(signal,pcbnew.PCB_VIA):
            raise ValueError('Return-stitch ledger must belong to a new via or an actual new-leg endpoint via')
        audit=checker.via(signal,rows[signal.GetNetname()]);ident=row.get('added_stitch_uuid')
        if ident:
            if ident in seen or ident not in exact:raise ValueError('Added return-stitch identity is absent or duplicated')
            seen.add(ident);stitch=exact[ident]
            if (not isinstance(stitch,pcbnew.PCB_VIA)or stitch.GetNetname()!=row['return_net']
                or stitch.GetViaType()!=pcbnew.VIATYPE_THROUGH
                or abs(pcbnew.ToMM(stitch.GetWidth(pcbnew.F_Cu))-row['diameter_mm'])>1e-6
                or abs(pcbnew.ToMM(stitch.GetDrillValue())-row['drill_mm'])>1e-6
                or [pcbnew.ToMM(v)for v in stitch.GetPosition()]!=row['position_mm']):
                raise ValueError('Actual return stitch differs from its bounded exact ledger')
            if ident not in [s['uuid']for s in audit['return_stitches']]:
                raise ValueError('Proposed stitch lacks real source anchoring/same-plane continuity')
        proof.append(audit)
    actual_signals={uid(v)for v in eligible_signal_vias(board,added,rows)}
    if {r['signal_via_uuid']for r in ledger}!=actual_signals:
        raise ValueError('Every new signal via or actual new-leg endpoint via needs exactly one explicit return-stitch ledger entry')
    return dict(passed=True,actual_signal_vias=len(actual_signals),new_return_stitches=len(seen),
                actual_source_anchored_stitch_proofs=proof,no_ground_autorouting=True)


def import_session(prepared, session, out):
    import pcbnew
    prepared = Path(prepared).resolve()
    receipt = read(prepared / 'prepare.json')
    session_hash = sha(session)
    for suffix, label in (('.kicad_pro', 'project'), ('.kicad_dru', 'rules')):
        path = prepared / ('base' + suffix)
        expected = receipt['input_hashes'].get(label)
        if bool(expected) != path.is_file() or (expected and sha(path) != expected):
            raise ValueError('Frozen native project/rules changed: ' + label)
    for filename, field in (('base.kicad_pcb', 'prepared_board_sha256'), ('manifest.json', 'manifest_sha256'),
                            ('design.json', 'design_sha256'), ('netlist.xml', 'netlist_sha256'),
                            ('native.dsn', 'native_dsn_sha256'), ('selected.dsn', 'selected_dsn_sha256')):
        if sha(prepared / filename) != receipt[field]:
            raise ValueError('Prepared input changed: ' + filename)
    frozen_review_check(read(prepared/'manifest.json'),prepared/'design.json',prepared/'netlist.xml')
    out = require_new_report(out)
    base = copy_board_inputs(prepared / 'base.kicad_pcb', out)
    shutil.copyfile(session, out / 'session.ses')
    for name in ('prepare.json', 'design.json', 'netlist.xml', 'manifest.json'):
        shutil.copyfile(prepared / name, out / name)
    rows = read(out / 'manifest.json')['nets']
    donor = pcbnew.LoadBoard(str(base))
    if not pcbnew.ImportSpecctraSES(donor, str(out / 'session.ses')):
        raise ValueError('Native session import failed')
    donor_path = out / 'donor.kicad_pcb'
    pcbnew.SaveBoard(str(donor_path), donor)
    before = parse(base.read_text(encoding='utf-8'))
    merged, added = merge_tree(before, parse(donor_path.read_text(encoding='utf-8')), rows)
    dest = out / 'additive-route-candidate.kicad_pcb'
    dest.write_text(dump(merged) + '\n', encoding='utf-8')
    for suffix in ('.kicad_pro', '.kicad_dru'):
        if base.with_suffix(suffix).is_file():
            shutil.copyfile(base.with_suffix(suffix), dest.with_suffix(suffix))
    # Only reviewed new ordinary signals entered via the donor. Ground vias
    # below are a separate bounded native addition, never power autorouting.
    signal_only_drc=native_drc(dest,out,'signal-only-drc',refill=True)
    new_bend_ledger=normalize_new_via_bends(dest,set(added),rows)
    removed_new={i for r in new_bend_ledger for i in r['removed_new_segment_uuids']}
    added=[i for i in added if i not in removed_new]
    if new_bend_ledger:native_drc(dest,out,'normalized-signal-drc',refill=True)
    stitch_ledger=add_return_stitches(dest,set(added),rows)
    added_stitches=[r['added_stitch_uuid']for r in stitch_ledger if r.get('added_stitch_uuid')]
    drc = native_drc(dest, out, 'merged-drc', refill=True)
    fresh_tree = parse(dest.read_text(encoding='utf-8'))
    if immutable_objects(before) != immutable_objects(fresh_tree):
        raise ValueError('DRC refill changed retained native objects or zone definitions')
    old = {value(child(t, 'uuid')[1]): dump(t) for kind in ('segment', 'via', 'arc') for t in children(before, kind)}
    current = {value(child(t, 'uuid')[1]): dump(t) for kind in ('segment', 'via', 'arc') for t in children(fresh_tree, kind)}
    if any(current.get(k) != v for k, v in old.items()) or set(current) != set(old) | set(added) | set(added_stitches):
        raise ValueError('Native refill changed retained copper or additions')
    b = pcbnew.LoadBoard(str(dest))
    population, _ = native_source_check(b, read(out / 'design.json'), out / 'netlist.xml')
    returns = return_corridor_check(b, set(added), rows)
    stitch_proof=validate_added_stitches(b,set(added),rows,stitch_ledger)
    # Native connectivity can infer/reassign a via net from touching fill. It
    # must not silently repair an incorrectly assigned source/donor conductor.
    exact_serialized_nets={value(child(t,'uuid')[1]):value(child(t,'net')[1])
        for kind in ('segment','via','arc')for t in children(fresh_tree,kind)}
    if {t.m_Uuid.AsString():str(t.GetNetname())for t in b.GetTracks()}!=exact_serialized_nets:
        raise ValueError('Native connectivity changed an exact serialized conductor net assignment')
    write(out / 'return-corridor.json', returns)
    run = subprocess.run([sys.executable, str(ROOT / 'tools/motion_card_routing_inventory.py'),
                          '--board', str(dest), '--netlist', str(out / 'netlist.xml'),
                          '--source-design', str(out / 'design.json'), '--out', str(out / 'connectivity')],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    (out / 'connectivity-command.txt').write_text(run.stdout + run.stderr, encoding='utf-8')
    inventory = read(out / 'connectivity/review.json')
    if run.returncode or not inventory['source_net_checks_pass'] or not inventory['complete_source_population_pass']:
        raise ValueError('Independent complete physical pad/cluster inventory rejected candidate')
    result = dict(schema_version=1, prepared_input=receipt, session_sha256=sha(session),
                  board_sha256=sha(dest), added_copper_uuids=added+added_stitches,
                  added_signal_copper_uuids=added, added_return_stitch_uuids=added_stitches,
                  actual_return_stitch_ledger=stitch_ledger, return_stitch_proof=stitch_proof,
                  bounded_new_only_via_bend_corrections=new_bend_ledger,
                  reviewed_checker_sha256=CHECKER_SHA256, added_items=len(added)+len(added_stitches),
                  all_old_copper_UUID_geometry_net_preserved=True, old_copper_items=len(old),
                  all_pad_pieces_preserved=len(all_pad_pieces(before)), physical_footprints=population['physical_footprints'],
                  all_native_immutable_objects_preserved=True, zone_definitions_preserved=True,
                  zone_fills_recalculated=True, native_drc=drc, population=population,
                  native_connectivity_net_inference_cannot_change_copper=True,
                  independent_connectivity=dict(uncapped_missing_joins=inventory['uncapped_unconnected_ratsnest_edges'],
                    cluster_missing_joins=inventory['independent_physical_cluster_missing_joins'],
                    fully_joined_multiple_pad_nets=inventory['fully_joined_multiple_pad_nets'],
                    incomplete_multiple_pad_nets=inventory['incomplete_multiple_pad_nets'], orphan_copper_items=[]),
                  geometric_return_corridor=returns, manufacturing_ready=False,
                  physical_EMC_SI_and_motion_validation=False, live_board_or_source_mutated=False)
    if sha(session) != session_hash or sha(out / 'session.ses') != session_hash:
        raise ValueError('Session changed during isolated import')
    for filename, field in (('base.kicad_pcb', 'prepared_board_sha256'), ('manifest.json', 'manifest_sha256'),
                            ('design.json', 'design_sha256'), ('netlist.xml', 'netlist_sha256'),
                            ('native.dsn', 'native_dsn_sha256'), ('selected.dsn', 'selected_dsn_sha256')):
        if sha(prepared / filename) != receipt[field]:
            raise ValueError('Authoritative prepared input changed during isolated import: ' + filename)
    for suffix, label in (('.kicad_pro', 'project'), ('.kicad_dru', 'rules')):
        expected = receipt['input_hashes'].get(label)
        if expected and sha(prepared / ('base' + suffix)) != expected:
            raise ValueError('Authoritative project/rules changed during isolated import: ' + label)
    frozen_review_check(read(prepared/'manifest.json'),prepared/'design.json',prepared/'netlist.xml')
    write(out / 'receipt.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    for arg in ('board', 'design', 'netlist', 'manifest', 'out'):
        p.add_argument('--' + arg, type=Path, required=True)
    p = sub.add_parser('import')
    for arg in ('prepared', 'session', 'out'):
        p.add_argument('--' + arg, type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'prepare':
        r = prepare(*(getattr(args, n).resolve() for n in ('board', 'design', 'netlist', 'manifest', 'out')))
        print(json.dumps(dict(selected=len(r['selection']['selected_nets']), routing_run=False)))
    else:
        r = import_session(*(getattr(args, n).resolve() for n in ('prepared', 'session', 'out')))
        print(json.dumps(dict(added=r['added_items'], total_old=r['old_copper_items'],
                              uncapped_missing_joins=r['independent_connectivity']['uncapped_missing_joins'])))


if __name__ == '__main__':
    main()
