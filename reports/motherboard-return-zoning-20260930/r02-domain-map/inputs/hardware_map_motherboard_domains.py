"""Map actual native pads to galvanic domains before creating return copper.

This is an electrical-domain map, not a DC continuity model. IC pins on each
nonisolated die are grouped to establish their voltage reference; no claim is
made that their signal pins are internally shorted. Isolation package groups,
connector contacts, SUB substrates and intentional chassis capacitors remain
separate. The physical PCB and native netlist are the only pin/net authority.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SEEDS = {
    'LOGIC': '/LOGIC_GND',
    'FIELD_A': '/motherboard_motors/FIELD_GND',
    'FIELD_B': '/motherboard_do/FIELD_B_0V',
    'AI': '/motherboard_analog_input/AI_AGND',
    'AO0': '/motherboard_analog_output/AO0_COM',
    'AO1': '/motherboard_analog_output/AO1_COM',
    'RS485': '/motherboard_comms/RS485_COM',
    'CAN': '/motherboard_comms/CAN_GND',
    'CHASSIS': '/CHASSIS',
}
RAW_RETURNS = {
    '/motherboard_comms/RS485_ISO_RETURN_RAW': ('RS485', 'U14815'),
    '/motherboard_comms/CAN_ISO_RETURN_RAW': ('CAN', 'U14818'),
}
HOST_SOCKETS = {'J15001', 'J15002', 'J16001', 'J16002'}
CHASSIS_COUPLERS = {f'C195{i:02}' for i in range(1, 10)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


class Union:
    def __init__(self, names):
        self.parent = {n: n for n in names}

    def find(self, name):
        while self.parent[name] != name:
            self.parent[name] = self.parent[self.parent[name]]
            name = self.parent[name]
        return name

    def group(self, names):
        names = list(names)
        if names:
            root = self.find(names[0])
            for name in names[1:]:
                self.parent[self.find(name)] = root


def package_groups(mpn, pins):
    """Exact adopted primary package splits; None means not an isolator."""
    numbers = set(pins)
    if mpn == 'ISO1212DBQR':
        if not numbers <= {str(i) for i in range(1, 17)}:
            raise ValueError('Unknown ISO1212 pin')
        return ({str(i) for i in range(1, 9)}, {'9', '10', '11', '14', '15', '16'})
    if mpn == 'ISO1540DR':
        return ({'1', '2', '3', '4'}, {'5', '6', '7', '8'})
    if mpn in ('ISO7720FDWR', 'ISO7760FDWR', 'ISO7761FDWR', 'ISO7762FDBQR'):
        return ({str(i) for i in range(1, 9)}, {str(i) for i in range(9, 17)})
    if mpn in ('ISOW1432DFMR', 'ISOW1044DFMR'):
        return ({str(i) for i in range(1, 11)}, {str(i) for i in range(11, 21)})
    if mpn in ('TMR 4-2412WI', 'TMR 4-2413WI', 'TMR 4-2415WI'):
        return ({'1', '2'}, {'6', '7'})
    if mpn in ('TLP3640A(TPL,E', 'TLP4176A(TP,F'):
        return ({'1', '2'}, {'3', '4'})
    if mpn.upper().startswith(('ISO', 'TMR', 'TLP', 'ADUM', 'REC')):
        raise ValueError('Unreviewed isolation package: ' + mpn)
    return None


def native(path):
    xml = ET.parse(path)
    nodes = {}; nc = set(); functions = {}
    for net in xml.findall('.//nets/net'):
        for node in net.findall('node'):
            key = node.attrib['ref'], node.attrib['pin']
            if key in nodes:
                raise ValueError('Duplicate native source pin ' + repr(key))
            nodes[key] = net.attrib['name']
            functions[key] = node.attrib.get('pinfunction', '')
            if 'no_connect' in node.attrib.get('pintype', ''):
                nc.add(key)
    return nodes, nc, functions


def classify(parts, nodes, nc):
    """Cut every actual isolation barrier, never infer domains by sheet name."""
    connected = {net for key, net in nodes.items() if key not in nc}
    union = Union(connected)
    barriers = []; coupling = []
    for ref, part in parts.items():
        pins = {str(pin): nodes[ref, str(pin)] for pin in part.get('pins', {})
                if (ref, str(pin)) in nodes and (ref, str(pin)) not in nc}
        mpn = part.get('mpn', part.get('mnp', ''))
        groups = package_groups(mpn, pins)
        if groups is not None:
            if mpn == 'ISO1212DBQR':
                for pin in ('12', '13'):
                    name = pins.get(pin, '')
                    if not ('SUB_ISLAND' in name or 'SUB_FLOAT' in name) or sum(n==name for n in nodes.values())!=1:
                        raise ValueError('SUB must remain a unique floating native net: '+ref+'.'+pin)
            for group in groups:
                union.group(pins[p] for p in pins if p in group)
            barriers.append(dict(reference=ref, mpn=mpn,
                groups=[sorted(g & set(pins)) for g in groups],
                grouping_basis='primary manufacturer pin-side allocation'))
        elif ref in CHASSIS_COUPLERS:
            if len(pins) != 2 or '/CHASSIS' not in pins.values():
                raise ValueError('Changed explicit chassis capacitor ' + ref)
            coupling.append(dict(reference=ref, mpn=mpn, pins=pins,
                role='intentional capacitive coupling; no copper ground join'))
        elif ref.startswith(('J', 'BM')) and ref not in HOST_SOCKETS:
            # External/boundary connectors have independently assigned contacts.
            pass
        elif ref.startswith(('H', 'TP')):
            pass
        else:
            union.group(pins.values())
    roots = collections.defaultdict(list)
    for domain, name in SEEDS.items():
        if name not in connected:
            raise ValueError('Required exact native return absent: ' + name)
        roots[union.find(name)].append(domain)
    conflicts = {r: v for r, v in roots.items() if len(v) != 1}
    if conflicts:
        raise ValueError('Distinct seeded galvanic returns became joined: ' + repr(conflicts))
    groups = collections.defaultdict(list)
    for name in connected:
        groups[union.find(name)].append(name)
    domains = {}; floating = []
    for root, nets in groups.items():
        nets = sorted(nets)
        if root in roots:
            domain = roots[root][0]
        elif len(nets) == 1 and ('SUB_ISLAND' in nets[0] or 'SUB_FLOAT' in nets[0]):
            domain = 'SUB:' + nets[0]
            floating.append(dict(domain=domain, kind='independent_substrate', nets=nets,
                copper_target_mm=[2, 2], ground_or_other_substrate_join_allowed=False))
        elif any('/EN' in n or '/PEN' in n or '/PERMIT_OUT_' in n for n in nets):
            domain = 'CONTACT:' + nets[0]
            floating.append(dict(domain=domain, kind='floating_contact', nets=nets,
                grounded_reference_required=False, ground_join_allowed=False))
        else:
            raise ValueError('Unclassified non-NC galvanic group: ' + repr(nets))
        for name in nets:
            domains[name] = domain
    for key in nc:
        domains[nodes[key]] = 'NC'
    for name, (domain, bead) in RAW_RETURNS.items():
        if domains.get(name) != domain or parts[bead].get('mpn') != 'BLM15EX331SN1D':
            raise ValueError('Changed reviewed filtered comm return ' + name)
        beadnets = {nodes[bead, p] for p in ('1', '2')}
        if beadnets != {name, SEEDS[domain]}:
            raise ValueError('Ferrite return endpoints differ ' + bead)
    return domains, barriers, floating, coupling


def bounds_points(bounds):
    a, b, c, d = bounds
    return [(a, b), (a, d), (c, b), (c, d)]


def barrier_geometry(rows):
    """Pad-edge-derived no-route/pour band, not a safety insulation rating."""
    centers = [[(p['position_mm'][0], p['position_mm'][1]) for p in side] for side in rows]
    means = [(sum(p[0] for p in g)/len(g), sum(p[1] for p in g)/len(g)) for g in centers]
    dx, dy = means[1][0]-means[0][0], means[1][1]-means[0][1]
    length = math.hypot(dx, dy)
    if length < 1:
        raise ValueError('Cannot determine an actual package isolation axis')
    axis = dx/length, dy/length; cross = -axis[1], axis[0]
    points = [[v for p in side for v in bounds_points(p['copper_aabb_mm'])] for side in rows]
    projections = [[x*axis[0]+y*axis[1] for x,y in side] for side in points]
    low, high = max(projections[0]), min(projections[1])
    if high <= low:
        raise ValueError('Actual package sides have overlapping projected copper')
    orth = [x*cross[0]+y*cross[1] for side in points for x,y in side]
    left, right = min(orth)-.5, max(orth)+.5
    poly = [[round(a*axis[0]+b*cross[0], 6), round(a*axis[1]+b*cross[1], 6)]
            for a,b in [(low,left),(high,left),(high,right),(low,right)]]
    return dict(polygon_mm=poly, pad_edge_projection_gap_mm=round(high-low, 6),
        package_axis=list(axis), cross_axis=list(cross),
        copper_route_via_pour_exclusion_layers='all six copper layers',
        fitted_package_pads_preserved=True,
        meaning='geometric pad-row barrier only; creepage/insulation certification is not established')


def positioned(board, parts, nodes, nc, functions, domains, barriers):
    import pcbnew
    mm = lambda v: [pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)]
    pads = []; per_ref = collections.defaultdict(list); pieces = set()
    board_refs = set(); errors = []; stencils = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference(); board_refs.add(ref)
        if ref not in parts:
            errors.append('Board footprint absent from source: '+ref)
        for pad in fp.Pads():
            if not pad.GetNumber() or not pad.IsOnCopperLayer():
                if pad.GetNumber() or pad.IsOnCopperLayer():
                    errors.append('Undeclared copper/electrical pad ' + ref)
                else:
                    stencils += 1
                continue
            key = ref, pad.GetNumber(); uuid = pad.m_Uuid.AsString()
            if uuid in pieces: raise ValueError('Duplicated physical copper pad UUID')
            pieces.add(uuid)
            if pad.GetNetname() != nodes.get(key):
                errors.append('Native pin/net mismatch: ' + repr(key))
            box = pad.GetBoundingBox()
            row = dict(reference=ref, pin=key[1], uuid=uuid, net=pad.GetNetname(),
                domain=domains.get(pad.GetNetname(), 'UNCLASSIFIED'),
                pin_function=functions.get(key), native_nc=key in nc,
                position_mm=mm(pad.GetPosition()),
                copper_aabb_mm=mm(box.GetOrigin())+mm(box.GetEnd()),
                copper_layers=[board.GetLayerName(i) for i in board.GetEnabledLayers().Seq()
                               if pcbnew.IsCopperLayer(i) and pad.IsOnLayer(i)])
            pads.append(row); per_ref[ref].append(row)
    missing = sorted(set(parts)-board_refs)
    if missing: errors.append('Source physical footprints missing: '+repr(missing))
    enriched = []
    for barrier in barriers:
        row = dict(barrier)
        side = [[p for p in per_ref[row['reference']] if p['pin'] in group] for group in row['groups']]
        if not all(side): raise ValueError('Isolation side absent from actual PCB ' + row['reference'])
        row['side_domains'] = [sorted({p['domain'] for p in group}) for group in side]
        row['side_pins'] = side
        # Unused NC pins remain real lands. Determine the physical row axis
        # using complete rows, rather than tilt it towards whichever signals
        # happen to be used. SUB pins influence the row geometry only; they
        # retain their independent floating domain in the electrical map.
        if row['mpn'].startswith('ISO'):
            split = 4 if row['mpn'].startswith('ISO1540') else 10 if row['mpn'].startswith('ISOW') else 8
            geometric = [[p for p in per_ref[row['reference']] if int(p['pin']) <= split],
                         [p for p in per_ref[row['reference']] if int(p['pin']) > split]]
        else:
            geometric = side
        row.update(barrier_geometry(geometric))
        enriched.append(row)
    counts = collections.Counter(p['domain'] for p in pads)
    envelopes = []
    for ref, rows in per_ref.items():
        by_domain = collections.defaultdict(list)
        for row in rows:
            if row['domain']!='NC': by_domain[row['domain']].append(row)
        for domain, group in by_domain.items():
            bounds = [min(p['copper_aabb_mm'][0] for p in group), min(p['copper_aabb_mm'][1] for p in group),
                      max(p['copper_aabb_mm'][2] for p in group), max(p['copper_aabb_mm'][3] for p in group)]
            envelopes.append(dict(reference=ref, domain=domain, copper_aabb_mm=bounds,
                pins=sorted({p['pin'] for p in group}),
                role='same-domain native component-side reference seed, not a power-current rating'))
    return dict(pads=pads, barriers=enriched, pad_domain_counts=dict(counts),
        reference_seed_envelopes=envelopes,
        footprint_count=len(board_refs), numbered_copper_pad_pieces=len(pads),
        unnumbered_stencil_only_pieces=stencils, errors=errors,
        source_physical_population_complete=not errors)


def svg_map(receipt):
    """A position-derived review view; never substitutes for native CAD."""
    colors={'LOGIC':'#475569','FIELD_A':'#f97316','FIELD_B':'#eab308','AI':'#a855f7',
            'AO0':'#22c55e','AO1':'#14b8a6','RS485':'#3b82f6','CAN':'#ec4899',
            'CHASSIS':'#ffffff','NC':'#555555'}
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1280" viewBox="-8 -22 485 388">',
         '<rect x="-8" y="-22" width="485" height="388" fill="#111827"/>',
         '<rect x="0" y="0" width="460" height="340" fill="#1e293b" stroke="#94a3b8" stroke-width=".3"/>',
         '<text x="0" y="-14" font-family="sans-serif" font-size="4.3" fill="white">Actual native galvanic pad domains — geometric review, no new planes</text>']
    for index,(domain,color) in enumerate(colors.items()):
        x=index*45
        out.append(f'<rect x="{x}" y="-9" width="2.5" height="2.5" fill="{color}"/><text x="{x+3.5}" y="-6.8" font-family="sans-serif" font-size="2.8" fill="white">{domain}</text>')
    for p in receipt['pads']:
        a,b,c,d=p['copper_aabb_mm'];domain=p['domain']
        color=colors.get(domain,'#fca5a5' if domain.startswith('SUB:') else '#c084fc')
        title=f"{p['reference']}.{p['pin']} {domain} {p['net']}".replace('&','&amp;').replace('<','&lt;')
        out.append(f'<rect x="{a}" y="{b}" width="{c-a}" height="{d-b}" fill="{color}"><title>{title}</title></rect>')
    for row in receipt['barriers']:
        points=' '.join(f'{a},{b}' for a,b in row['polygon_mm'])
        out.append(f'<polygon points="{points}" fill="#ef4444" fill-opacity=".22" stroke="#ef4444" stroke-width=".15"><title>{row["reference"]} {row["mpn"]}: {row["pad_edge_projection_gap_mm"]} mm pad-row gap</title></polygon>')
    out.append('<text x="0" y="349" font-family="sans-serif" font-size="3.3" fill="white">Red bands: package pad-row copper exclusion; pink: 44 separate floating SUB pads; purple: floating contact groups.</text>')
    out.append('<text x="0" y="355" font-family="sans-serif" font-size="3.3" fill="white">No insulation certification, whole-board creepage rating, manufactured stackup or completed routing is implied.</text></svg>')
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    a = parser.parse_args(); out = a.out.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'reports'):
        raise ValueError('A new immutable workspace report directory is required')
    out.mkdir(parents=True)
    source = a.source.resolve(); board_path = a.board.resolve()
    files = [board_path, source/'design.json', source/'netlist.xml', source/'assembly-map.json', Path(__file__)]
    hashes = {str(p):sha(p) for p in files}
    snapshots = out/'inputs'; snapshots.mkdir()
    for path in files:
        shutil.copy2(path, snapshots/path.name)
    model = json.loads((source/'design.json').read_text(encoding='utf-8'))
    parts = {r:c for r,c in model['components'].items()
             if c.get('physical', c.get('role')!='schematic_boundary_not_orderable')}
    nodes, nc, functions = native(source/'netlist.xml')
    domains, barriers, floating, coupling = classify(parts, nodes, nc)
    import pcbnew
    board = pcbnew.LoadBoard(str(board_path))
    physical = positioned(board, parts, nodes, nc, functions, domains, barriers)
    board.BuildConnectivity()
    receipt = dict(schema_version=1, input_sha256=hashes,
        copper_layers=[board.GetLayerName(i) for i in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]],
        adjacent_reference_layers={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu','B.Cu':'In4.Cu'},
        seeded_returns=SEEDS, filtered_return_nets={n:dict(domain=v[0],series_ferrite=v[1]) for n,v in RAW_RETURNS.items()},
        electrical_domain_net_counts=dict(collections.Counter(domains.values())),
        independent_floating_substrate_count=sum(r['kind']=='independent_substrate' for r in floating),
        independent_floating_contact_group_count=sum(r['kind']=='floating_contact' for r in floating),
        intentional_chassis_couplers=coupling, floating_domains=floating,
        track_via_count=len(board.GetTracks()), retained_zone_count=len(board.Zones()),
        uncapped_unconnected=board.GetConnectivity().GetUnconnectedCount(False),
        manufacturing_ready=False, physical_qualification=False,
        no_source_or_pcb_mutation=True,
        reference_routing_scope='ordinary F/In2/In3/B only, with exact same-domain adjacent filled return proof; no power/precision/high-speed routing',
        **physical)
    write(out/'domain-map.json', receipt)
    write(out/'net-domains.json', domains)
    (out/'domain-map.svg').write_text(svg_map(receipt),encoding='utf-8')
    for p,h in hashes.items():
        if sha(p)!=h: raise ValueError('Input changed during immutable map: '+p)
    print(json.dumps({k:v for k,v in receipt.items() if k in ['footprint_count','numbered_copper_pad_pieces','track_via_count','retained_zone_count','source_physical_population_complete','independent_floating_substrate_count','independent_floating_contact_group_count','errors','uncapped_unconnected']}))
    raise SystemExit(bool(physical['errors']))


if __name__ == '__main__': main()
