"""Assemble actual reviewed sheets into an electrically connected KiCad project.

Only explicitly named interface nets cross sheets. The source blocks remain intact.
This creates a review schematic, never a manufacturing or safety qualification.
KiCad syntax: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/controller_assembly'
BLOCKS = ('power_entry', 'core_converter', 'logic_power', 'field_power', 'encoder_power', 'tx_six', 'rx_abz',
          'sbc_power', 'power_sequence', 'digital_inputs')
INTERFACES = {
    'CORE_24V_PROTECTED', 'FIELD_24V_PROTECTED', 'LOGIC_GND', 'FIELD_GND',
    'CORE_5V', 'IO_3V3', 'CORE_1V2', 'ESP_3V3', 'FIELD_5V', 'C_PGOOD', 'F_PGOOD',
    'ENC0_5V_LIMITED', 'ENC1_5V_LIMITED',
    'CORE_1V2_EN', 'IO_3V3_EN', 'ESP_3V3_EN',
}
ALIASES = {'tx_six': {'SIGNAL_5V': 'CORE_5V'}}
NS = uuid.UUID('aecdb178-a206-4928-84b5-b2fe6bca40bc')


def uid(s): return str(uuid.uuid5(NS, s))
def q(s): return json.dumps(str(s), ensure_ascii=False)
def value(s): return json.loads(s) if s.startswith('"') else s
def children(n, key): return [x for x in n if isinstance(x, list) and x and x[0] == key]
def child(n, key): return next(iter(children(n, key)), None)
def dump(n): return '(' + ' '.join(dump(x) if isinstance(x, list) else x for x in n) + ')'
def point(n): return tuple(round(float(x), 4) for x in n[1:3])


def parse(text):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack, result = [], None
    for token in tokens:
        if token == '(':
            n = []
            if stack: stack[-1].append(n)
            elif result is not None: raise ValueError('Multiple root expressions')
            else: result = n
            stack.append(n)
        elif token == ')':
            if not stack: raise ValueError('Unexpected close parenthesis')
            stack.pop()
        else:
            if not stack: raise ValueError('Token outside root expression')
            stack[-1].append(token)
    if stack or result is None: raise ValueError('Incomplete expression')
    return result


def ref_property(symbol):
    return next(p for p in children(symbol, 'property') if value(p[1]) == 'Reference')


def new_ref(old, index):
    m = re.fullmatch(r'([^0-9]+)([0-9]+)', old)
    if not m: raise ValueError('Unannotated or unsupported reference: ' + old)
    return m[1] + str(index * 1000 + int(m[2]))


def remove_flag(tree, symbol):
    """Remove only this marker's wire/label stub, preserving real circuitry."""
    at = point(child(symbol, 'at'))
    endpoints = {at}
    for wire in children(tree, 'wire'):
        points = [point(p) for p in children(child(wire, 'pts'), 'xy')]
        if at in points:
            endpoints.update(points)
            tree.remove(wire)
    for label in children(tree, 'label'):
        if point(child(label, 'at')) in endpoints:
            tree.remove(label)
    tree.remove(symbol)


def build(names):
    if len(set(names)) != len(names) or not set(names) <= set(BLOCKS):
        raise ValueError('Unknown or duplicate block')
    trees, nets, inputs, source_libraries = {}, {}, {}, {}
    for name in names:
        path = ROOT/'hardware'/name/(name+'.kicad_sch')
        schematic_bytes=path.read_bytes()
        netlist_bytes=path.with_name('netlist.xml').read_bytes()
        trees[name] = parse(schematic_bytes.decode('utf-8'))
        nets[name] = ET.ElementTree(ET.fromstring(netlist_bytes))
        symbols = children(child(trees[name], 'lib_symbols'), 'symbol')
        namespaces = {value(s[1]).split(':')[0] for s in symbols}
        if len(namespaces) != 1: raise ValueError('Expected one source symbol library for '+name)
        namespace=next(iter(namespaces))
        libpath=path.with_name(namespace+'.kicad_sym')
        if not libpath.exists(): raise ValueError('Missing source library '+str(libpath))
        library_bytes=libpath.read_bytes()
        source_libraries[name]=(namespace,library_bytes)
        for p,raw in ((path,schematic_bytes),(path.with_name('netlist.xml'),netlist_bytes),(libpath,library_bytes)):
            inputs[p.relative_to(ROOT).as_posix()] = hashlib.sha256(raw).hexdigest()
        for label in children(trees[name], 'label'):
            original = value(label[1])
            label[1] = q(ALIASES.get(name, {}).get(original, original))
    interfaces = {net for net in INTERFACES if sum(any(value(l[1]) == net for l in children(t, 'label')) for t in trees.values()) > 1}

    # For connected rails, a component power-output takes precedence over flags.
    driven, flag_owner = set(), {}
    for name, netlist in nets.items():
        for net in netlist.findall('.//nets/net'):
            original = net.attrib['name'].lstrip('/')
            netname = ALIASES.get(name, {}).get(original, original)
            if netname not in interfaces: continue
            if any(p.attrib.get('pintype') == 'power_out' and not p.attrib['ref'].startswith('#') for p in net.findall('node')):
                driven.add(netname)
        # KiCad omits PWR_FLAG pseudo-components from XML: use labeled geometry.
        tree = trees[name]
        for symbol in children(tree, 'symbol'):
            old = value(ref_property(symbol)[2])
            if not old.startswith('#'): continue
            at = point(child(symbol, 'at'))
            ends = {at}
            for wire in children(tree, 'wire'):
                pts = {point(p) for p in children(child(wire, 'pts'), 'xy')}
                if at in pts: ends |= pts
            labels = [value(l[1]) for l in children(tree, 'label') if point(child(l, 'at')) in ends]
            if len(set(labels)) != 1: raise ValueError('Ambiguous power flag ' + name + '/' + old)
            netname = labels[0]
            if netname in interfaces:
                flag_owner.setdefault(netname, (name, old))
                producer = {'CORE_5V':'core_converter','IO_3V3':'logic_power','CORE_1V2':'logic_power',
                            'ESP_3V3':'logic_power','FIELD_5V':'field_power'}.get(netname)
                if name == producer: flag_owner[netname] = (name, old)

    OUT.mkdir(parents=True, exist_ok=True)
    root_id = uid('assembly-root')
    sheets, top_items, mappings, library_rows, footprints = [], [], {}, [], {}
    for index, name in enumerate(names, 1):
        tree, sheet_id = trees[name], uid('sheet-'+name)
        mappings[name] = {'references': {}, 'exported_interfaces': [], 'removed_power_flags': []}
        for symbol in list(children(tree, 'symbol')):
            prop = ref_property(symbol)
            old = value(prop[2])
            if old.startswith('#'):
                owned = next((net for net, owner in flag_owner.items() if owner == (name, old)), None)
                # Any flag for a public net not owned by this sheet is redundant.
                at = point(child(symbol, 'at'))
                ends = {at}
                for wire in children(tree, 'wire'):
                    points = {point(p) for p in children(child(wire, 'pts'), 'xy')}
                    if at in points: ends |= points
                labels = [value(l[1]) for l in children(tree, 'label') if point(child(l, 'at')) in ends]
                net = labels[0]
                if net in interfaces and (owned is None or net in driven):
                    mappings[name]['removed_power_flags'].append({'reference': old, 'net': net})
                    remove_flag(tree, symbol)
                    continue
            ref = new_ref(old, index)
            mappings[name]['references'][old] = ref
            prop[2] = q(ref)
            instance = child(symbol, 'instances')
            if instance is not None: symbol.remove(instance)
            symbol.append(['instances', ['project', q('controller_assembly'), ['path', q('/'+root_id+'/'+sheet_id), ['reference', q(ref)], ['unit', '1']]]])
            lib = child(symbol, 'lib_id')
            lib[1] = q(value(lib[1]).replace(source_libraries[name][0]+':', 'CNC_'+name+':', 1))
        for sym in children(child(tree, 'lib_symbols'), 'symbol'):
            sym[1] = q(value(sym[1]).replace(source_libraries[name][0]+':', 'CNC_'+name+':', 1))
        child(tree, 'generator')[1] = q('controller_assembly')
        # One hierarchy port per public net; other local labels retain connectivity.
        for label in children(tree, 'label'):
            net = value(label[1])
            if net in interfaces and net not in mappings[name]['exported_interfaces']:
                label[0] = 'hierarchical_label'
                label.insert(2, ['shape', 'bidirectional'])
                mappings[name]['exported_interfaces'].append(net)
        filename = name+'.kicad_sch'
        (OUT/filename).write_text(dump(tree)+'\n', encoding='utf-8')
        libfile = name+'.kicad_sym'
        (OUT/libfile).write_bytes(source_libraries[name][1])
        for fp in (ROOT/'hardware'/name/'CNC_Power.pretty').glob('*.kicad_mod'):
            raw=fp.read_bytes()
            if fp.name in footprints and footprints[fp.name]!=raw:raise ValueError('Conflicting custom footprint: '+fp.name)
            footprints[fp.name]=raw
            dest=OUT/'CNC_Power.pretty'/fp.name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw)
            inputs[fp.relative_to(ROOT).as_posix()]=hashlib.sha256(raw).hexdigest()
        library_rows.append(f'(lib (name "CNC_{name}")(type "KiCad")(uri "${{KIPRJMOD}}/{libfile}")(options "")(descr "Imported {name} symbols"))')
        x, y = round(63.5+(index-1)%4*195.58,4), round(55.88+(index-1)//4*160.02,4)
        ports = sorted(mappings[name]['exported_interfaces'])
        height = round(max(55.88, len(ports)*5.08+15.24),4)
        pins = []
        for j, net in enumerate(ports):
            py = round(y+7.62+j*5.08,4)
            pins.append(f'(pin {q(net)} bidirectional (at {x} {py} 180)(effects(font(size 1.1 1.1)))(uuid "{uid(name+net)}"))')
            top_items.append(f'(wire(pts(xy {x-43.18:.4f} {py})(xy {x} {py}))(stroke(width 0)(type default))(uuid "{uid(name+net+"wire")}"))')
            top_items.append(f'(label {q(net)} (at {x-43.18:.4f} {py} 0)(effects(font(size 1.05 1.05))(justify left bottom))(uuid "{uid(name+net+"label")}"))')
        sheets.append(f'(sheet(at {x} {y})(size 101.6 {height})(stroke(width 0.254)(type default))(fill(color 0 0 0 0))(uuid "{sheet_id}")'
                      f'(property "Sheetname" {q(name)} (at {x} {y-2} 0)(effects(font(size 1.5 1.5))(justify left)))'
                      f'(property "Sheetfile" {q(filename)} (at {x} {y+height+2} 0)(effects(font(size 1 1))(justify left)))'
                      + ''.join(pins) + f'(instances(project "controller_assembly"(path "/{root_id}"(page "{index+1}")))))')
    title = 'CONNECTED POWER AND MOTION-INTERFACE REVIEW - NOT A COMPLETE CONTROLLER'
    notes = 'Real subcircuits connected through named sheet ports. Independent LOGIC / FIELD returns.\nFPGA / compute / ESP silicon, machine permission, field outputs and analog interface remain unfinished.\nBoundary connectors are retained review interfaces; connector selection and full PCB layout remain open.'
    top = f'(kicad_sch(version 20250114)(generator "controller_assembly")(uuid "{root_id}")(paper "A1")'
    top += '(title_block(title "Controller connected circuit review")(date "2026-09-28")(rev "r0.1")) (lib_symbols)'
    top += f'(text {q(title)} (at 20 15 0)(effects(font(size 2 2))(justify left top))(uuid "{uid("title")}"))'
    top += f'(text {q(notes)} (at 20 24 0)(effects(font(size 1.2 1.2))(justify left top))(uuid "{uid("notes")}"))'
    top += ''.join(sheets+top_items)+'(sheet_instances(path "/"(page "1"))))\n'
    (OUT/'controller_assembly.kicad_sch').write_text(dump(parse(top))+'\n', encoding='utf-8')
    (OUT/'controller_assembly.kicad_pro').write_text('{"meta":{"filename":"controller_assembly.kicad_pro","version":1}}\n')
    (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)'+''.join(library_rows)+')'))+'\n')
    if footprints:
        (OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "CNC_Power") (type "KiCad") (uri "${KIPRJMOD}/CNC_Power.pretty") (options "") (descr "Source-block custom footprints")))\n')
    manifest = {'schema_version':1, 'manufacturing_ready':False, 'blocks':mappings,
                'interface_nets':sorted(interfaces), 'aliases':ALIASES, 'input_sha256':inputs,
                'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'scope':'Electrically connected existing circuit blocks; absent functions are not simulated by placeholder parts'}
    (OUT/'assembly-map.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(OUT/'controller_assembly.kicad_sch')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--blocks', nargs='+', choices=BLOCKS, default=list(BLOCKS))
    build(p.parse_args().blocks)
