"""Create OEA r0.2 native schematic from reviewed, exact component/pin specifications.

No assumptions about parts, no old r0.1 schematic reuse, no fabrication output.
Writes only this revision directory. The local block symbols keep every package
pin visible and numbered; net names connect the functional blocks on one sheet.
"""
from pathlib import Path
import collections
import json
import math
import re
import uuid

OUT = Path(__file__).resolve().parent
LIBROOT = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
NS = uuid.UUID('b44e4fc5-9256-47a8-bf52-3a45fa44592e')
ROOT_UUID = str(uuid.uuid5(NS, 'adapter-r02-root'))


def uid(name):
    return str(uuid.uuid5(NS, name))


def q(value):
    return json.dumps(str(value), ensure_ascii=False)


def fx(size=1.0, extra=''):
    return f'(effects (font (size {size} {size})) {extra})'


def ordered(ref):
    m = re.fullmatch(r'([^0-9]+)([0-9]+)', ref)
    return (m[1], int(m[2])) if m else (ref, 0)


def normalize_spec(path):
    spec = json.loads(path.read_text(encoding='utf-8-sig'))
    values = spec['parts']
    if isinstance(values, dict):
        values = [dict(v, reference=k) for k, v in values.items()]
    result = []
    for original in values:
        p = dict(original)
        if 'reference' not in p:
            p['reference'] = p.pop('ref')
        ref = p['reference']
        for key in ['value', 'mpn', 'manufacturer', 'footprint', 'pins']:
            assert key in p, f'{path.name}: {ref} missing {key}'
        assert ':' in p['footprint'], f'{ref}: footprint library missing'
        assert p['mpn'], f'{ref}: no exact MPN'
        p['pins'] = {str(k): v for k, v in p['pins'].items()}
        p['pin_labels'] = {str(k): v for k, v in p.get('pin_labels', {}).items()}
        p['pin_types'] = {str(k): v for k, v in p.get('pin_types', {}).items()}
        p['uuid'] = uid(ref)
        p['source_specification'] = path.name
        p['functional_block'] = p.get('functional_block', 'Power conditioning' if 'power' in path.name else 'Controller and driver interface')
        result.append(p)
    return result


def local_header_footprints():
    """Copy matching stock header geometry, retaining VM physical omission."""
    folder = OUT/'Adapter.pretty'
    folder.mkdir(exist_ok=True)
    for count, mpn in [(8, '61300811121'), (7, '61300711121')]:
        base = f'PinHeader_1x{count:02d}_P2.54mm_Vertical'
        local = f'Wurth_{mpn}_1x{count:02d}_P2.54mm'
        fp = (LIBROOT/f'Connector_PinHeader_2.54mm.pretty/{base}.kicad_mod').read_text(encoding='utf-8')
        fp = fp.replace(base, local, 2)
        fp = re.sub(r'\(descr "[^"]*"\)', f'(descr "Wurth {mpn}; nominal 1.10mm finished PTH, 1.70mm pads; underside assembly; verify host fit.")', fp, count=1)
        fp, holes = re.subn(r'\(drill 1\)', '(drill 1.1)', fp)
        assert holes == count
        # Board-level orientation marks replace header body silk at flush edges.
        spans = []
        for match in re.finditer(r'\(fp_line\s', fp):
            depth = 0
            for end in range(match.start(), len(fp)):
                if fp[end] == '(':
                    depth += 1
                elif fp[end] == ')':
                    depth -= 1
                    if depth == 0:
                        if '(layer "F.SilkS")' in fp[match.start():end+1]:
                            spans.append((match.start(), end+1))
                        break
        assert len(spans) == 6
        for start, end in reversed(spans):
            fp = fp[:start] + fp[end:]
        (folder/f'{local}.kicad_mod').write_text(fp, encoding='utf-8')


def main():
    paths = [OUT/'power_spec.json', OUT/'logic_spec.json']
    parts = [p for path in paths for p in normalize_spec(path)]
    counts = collections.Counter(p['reference'] for p in parts)
    assert all(n == 1 for n in counts.values()), f'Duplicate references: {counts}'
    refs = {p['reference']: p for p in parts}
    assert refs['J3']['pins'] == {'1': 'COM_PLUS', '2': 'PUL_MINUS', '3': 'DIR_MINUS', '4': 'ENA_MINUS'}
    assert len(refs['J1']['pins']) == 8 and len(refs['J2']['pins']) == 7
    assert 'VM' not in refs['J2']['pins'].values()
    local_header_footprints()
    libraries = []
    items = []
    used_libraries = sorted({p['footprint'].split(':')[0] for p in parts})
    fplibs = '(fp_lib_table (version 7)\n'
    for lib in used_libraries:
        uri = '${KIPRJMOD}/'+lib+'.pretty' if (OUT/(lib+'.pretty')).exists() else '${KICAD10_FOOTPRINT_DIR}/'+lib+'.pretty'
        fplibs += f'(lib (name {q(lib)})(type "KiCad")(uri {q(uri)})(options "")(descr "OEA r0.2 reviewed footprint library"))\n'
    (OUT/'fp-lib-table').write_text(fplibs+')\n', encoding='utf-8')

    def line(x1, y1, x2, y2, width=.254):
        return f'(polyline (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width {width}) (type default)) (fill (type none)))'

    def rect(x1, y1, x2, y2):
        return f'(rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width .254) (type default)) (fill (type background)))'

    def note(x, y, text, size=1.1):
        items.append(f'(text {q(text)} (at {x} {y} 0) {fx(size, "(justify left top)")} (uuid {q(uid("note:"+text))}))')

    def make_symbol(p):
        ref = p['reference']
        name = 'Part_'+ref
        pins = []
        numbers = list(p['pins'])
        simple = len(numbers) == 2 and ref[0] in 'RC'
        if simple:
            # RC footprint pad 1 on left and pad 2 on right, matching numbered source.
            pins = [(numbers[0], '', -7.62, 0, 0, 'passive'), (numbers[1], '', 7.62, 0, 180, 'passive')]
            if ref[0] == 'R':
                body = rect(-5.08, 1.27, 5.08, -1.27)
            else:
                body = line(-5.08, 0, -.762, 0)+line(.762, 0, 5.08, 0)+line(-.762, 2.54, -.762, -2.54, .3)+line(.762, 2.54, .762, -2.54, .3)
        else:
            left = []
            right = []
            for n in numbers:
                kind = p['pin_types'].get(n, 'passive')
                if kind in {'output', 'power_out', 'open_collector', 'open_emitter', 'tri_state'}:
                    right.append(n)
                else:
                    left.append(n)
            # Avoid excessively tall connector and passive multi-pad blocks.
            if not right:
                split = math.ceil(len(numbers)/2)
                left, right = numbers[:split], numbers[split:]
            # Preserve output placement when practical while keeping tall IC
            # supply/control pin banks within one readable drawing cell.
            while len(left) > math.ceil(len(numbers)/2):
                movable = next((n for n in reversed(left) if p['pin_types'].get(n, 'passive') in {'passive', 'power_in', 'no_connect'}), left[-1])
                left.remove(movable)
                right.append(movable)
            rows = max(len(left), len(right))
            for side, ns, x, angle in [('left', left, -20.32, 0), ('right', right, 20.32, 180)]:
                for i, n in enumerate(ns):
                    y = ((rows-1)/2-i)*5.08
                    pins.append((n, p['pin_labels'].get(n, n), x, y, angle, p['pin_types'].get(n, 'passive')))
            half_h = max(5.08, ((rows-1)/2)*5.08+3.81)
            body = rect(-17.78, half_h, 17.78, -half_h)
        primitive = ''.join(f'(pin {kind} line (at {x} {y} {angle}) (length 2.54) (name {q(label)} {fx(.9)}) (number {q(n)} {fx(.8)}))' for n, label, x, y, angle, kind in pins)
        properties = ''.join(f'(property {q(k)} {q(v)} (at 0 0 0) {fx(extra="hide")})' for k, v in [('Reference', ref[0]), ('Value', name)])
        libraries.append(f'(symbol "Adapter:{name}" (pin_names (offset .508){" hide" if simple else ""}) (in_bom yes) (on_board yes) {properties}(symbol "{name}_0_1" {body})(symbol "{name}_1_1" {primitive}))')
        return name, pins

    def place(p, x, y):
        name, pins = make_symbol(p)
        ref = p['reference']
        half_h = max((abs(py) for _, _, _, py, _, _ in pins), default=0)+7.62
        props = ''.join(f'(property {q(k)} {q(v)} (at {px} {py} 0) {fx(size, extra)})' for k, v, px, py, size, extra in [
            ('Reference', ref, x, y-half_h-2.54, 1.27, ''),
            ('Value', p['value'], x, y-half_h, .95, ''),
            ('Footprint', p['footprint'], x, y, 1, 'hide'),
            ('MPN', p['mpn'], x, y, 1, 'hide'),
            ('Manufacturer', p['manufacturer'], x, y, 1, 'hide')])
        items.append(f'(symbol (lib_id "Adapter:{name}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {q(p["uuid"])}) {props}(instances (project "adapter" (path "/{ROOT_UUID}" (reference {q(ref)}) (unit 1)))))')
        for n, label, px, py, angle, kind in pins:
            nx, ny = round(x+px, 4), round(y-py, 4)
            net = p['pins'][n]
            if net is None:
                items.append(f'(no_connect (at {nx} {ny}) (uuid {q(uid(ref+"."+n+".nc"))}))')
                continue
            direction = -1 if px < 0 else 1
            ex = round(nx+direction*5.08, 4)
            items.append(f'(wire (pts (xy {nx} {ny}) (xy {ex} {ny})) (stroke (width 0) (type default)) (uuid {q(uid(ref+"."+n+".wire"))}))')
            justify = 'right bottom' if direction < 0 else 'left bottom'
            items.append(f'(label {q(net)} (at {ex} {ny} 0) {fx(.9, "(justify "+justify+")")} (uuid {q(uid(ref+"."+n+".label"))}))')

    # Give each component a readable, non-overlapping native schematic block.
    # Adjacent blocks are grouped by power/interface source and reference kind.
    parts.sort(key=lambda p: (p['source_specification'], ordered(p['reference'])))
    paper = 'A2'
    columns = 5
    rows = math.ceil(len(parts)/columns)
    assert rows <= 14, 'Too many components for one sheet; add hierarchy.'
    cell_w = 111.76
    y_cursor = 48.26
    for start in range(0, len(parts), columns):
        group = parts[start:start+columns]
        height = max(20.32 if len(p['pins']) == 2 and p['reference'][0] in 'RC'
                     else max(2, math.ceil(len(p['pins'])/2))*5.08+17.78
                     for p in group)
        cy = round(y_cursor+height/2, 4)
        for col, p in enumerate(group):
            place(p, 60.96+col*cell_w, cy)
        y_cursor += height
    if y_cursor > 375:
        paper = 'A1'

    # A flag identifies external supply/ground and power propagated through
    # passive protection elements. It is never used to hide output conflicts.
    driven = {p['pins'][n] for p in parts for n, t in p['pin_types'].items() if t == 'power_out' and p['pins'][n]}
    required = {p['pins'][n] for p in parts for n, t in p['pin_types'].items() if t == 'power_in' and p['pins'][n]}
    flag_nets = sorted(required-driven)
    for i, net in enumerate(flag_nets):
        ref = f'#FLG{i+1:02d}'
        name = 'PowerFlag'+str(i)
        sx, sy = 355.6+i*30.48, 40.64
        libraries.append(f'(symbol "Adapter:{name}" (pin_names hide) (in_bom no) (on_board no)(property "Reference" "#FLG" (at 0 0 0) {fx(extra="hide")})(property "Value" "PWR_FLAG" (at 0 0 0) {fx(extra="hide")})(symbol "{name}_0_1" {line(0,0,0,2.54)})(symbol "{name}_1_1" (pin power_out line (at 0 0 90)(length 0)(name "" {fx()})(number "1" {fx()}))))')
        items.append(f'(symbol (lib_id "Adapter:{name}")(at {sx} {sy} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid {q(uid(ref))})(property "Reference" {q(ref)} (at {sx} {sy} 0) {fx(extra="hide")})(property "Value" "PWR_FLAG" (at {sx} {sy} 0) {fx(extra="hide")})(instances (project "adapter" (path "/{ROOT_UUID}" (reference {q(ref)})(unit 1)))))')
        items.append(f'(label {q(net)} (at {sx} {sy} 0) {fx(.9, "(justify left bottom)")}(uuid {q(uid(ref+"label"))}))')

    note(12.7, 15.24, 'OEA r0.2 — 3.3 V / 5 V HOST TO EXTERNAL STEP/DIR/ENABLE', 2.0)
    note(12.7, 22.86, 'Engineering prototype — not validated for sale or production. Exact host/driver profiles require qualification.', 1.2)
    note(12.7, 30.48, 'EXT terminal: 5 V / 12 V / 24 V nominal. 5 V terminal input uses EXT only. 5V switch mode requires 12 V or 24 V input.', 1.1)
    note(12.7, 36.83, 'Switch changes COM+ only; power off before switching. Shared ground, no isolation. VM contact omitted; external power never powers host VIO.', 1.1)
    bottom = y_cursor+7.62
    note(12.7, bottom, 'Signal connector: 1 COM+ | 2 PUL− | 3 DIR− | 4 ENA−. Common-positive drivers only; configure voltage/current and enable semantics per exact driver manual.', 1.1)
    note(12.7, bottom+6.35, 'Native ERC checks electrical declarations; it does not establish loaded timing, startup behavior, protection performance, host fit or physical qualification.', 1.1)
    sch = f'(kicad_sch (version 20250114)(generator "eeschema")(generator_version "10.0")(uuid {q(ROOT_UUID)})(paper "{paper}")\n'
    sch += '(title_block (title "OEA external-driver adapter") (date "2026-10-06") (rev "r0.2") (company "ENGINEERING — NOT RELEASED") (comment 1 "External signal supply with 5V / EXT selector"))\n'
    sch += '(lib_symbols\n'+'\n'.join(libraries)+')\n'+'\n'.join(items)+'\n(embedded_fonts no))\n'
    (OUT/'adapter.kicad_sch').write_text(sch, encoding='utf-8')
    lib = '(kicad_symbol_lib (version 20250114)(generator "kicad_symbol_editor")\n'+'\n'.join(s.replace('(symbol "Adapter:', '(symbol "', 1) for s in libraries)+'\n)\n'
    (OUT/'Adapter.kicad_sym').write_text(lib, encoding='utf-8')
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7)(lib (name "Adapter")(type "KiCad")(uri "${KIPRJMOD}/Adapter.kicad_sym")(options "")(descr "OEA r0.2 exact package-pin symbols")))\n', encoding='utf-8')
    data = {'schema_version': 1, 'status': 'ENGINEERING PROTOTYPE — NOT RELEASED', 'root_uuid': ROOT_UUID, 'project': 'adapter', 'parts': {p['reference']: p for p in parts}, 'power_flag_nets': flag_nets}
    (OUT/'parts.json').write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'parts': len(parts), 'root_uuid': ROOT_UUID, 'paper': paper, 'power_flags': flag_nets}))


if __name__ == '__main__':
    main()
