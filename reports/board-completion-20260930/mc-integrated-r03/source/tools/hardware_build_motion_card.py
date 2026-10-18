"""Connect reviewed MC circuits without modifying historical source blocks.

This is a proposed IS-2 circuit candidate. Unimplemented isolation, connector,
filter, identity and flash-restore functions are explicitly tracked as gaps.
It never emits fabrication files or treats the historical bitstream as CNC1.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import shutil
import uuid
import xml.etree.ElementTree as ET

from hardware_build_assembly import parse, dump, child, children, value, q, point, ref_property, new_ref, remove_flag

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/motion_card'
BLOCKS = (
    ('fpga_core', 'hardware/fpga_core', 'fpga_core'),
    ('mc_local_power', 'hardware/mc_local_power', 'mc_local_power'),
    ('watchdog_conditioning', 'hardware/is1_watchdogs/startup_conditioning_r0_2', 'is1_watchdogs'),
    ('mc_permission', 'hardware/mc_permission', 'mc_permission'),
    ('mc_motor_buffers', 'hardware/mc_motor_buffers', 'mc_motor_buffers'),
)
ALIASES = {
    'fpga_core': {'FPGA_PROGRESS_WDI': 'FPGA_PROGRESS_M', 'HW_WATCHDOG_OK_N': 'RAW_INHIBIT_N',
                  **{f'DRIVE_ENABLE{i}_FPGA_RESERVED': f'EN{i}_N_FPGA' for i in range(12)}},
    'mc_permission': {'MC_RAILS_OK': 'FPGA_CRESET_N', 'CDONE_QUALIFIED': 'FPGA_USER_RESET_N'},
}
PUBLIC = {'CORE_5V', 'CORE_1V2', 'IO_3V3', 'LOGIC_GND', 'FPGA_CRESET_N',
          'FPGA_USER_RESET_N', 'FPGA_MOTION_REQUEST', 'FPGA_OUTPUT_REQUEST',
          'FPGA_PROGRESS_M', 'FPGA_PROGRESS_O', 'FPGA_ENDPOINT_READY', 'TX_PERMIT',
          'WD_M_OK', 'WD_O_OK', 'WD_M_SET1_BUF', 'WD_O_SET1_BUF', 'RAW_INHIBIT_N',
          'BANK_B_BUFFER_ENABLE_QUALIFIED',
          *{f'{signal}{i}_FPGA' for signal in ('STEP', 'DIR') for i in range(12)},
          *{f'EN{i}_N_FPGA' for i in range(12)}}
NS = uuid.UUID('75189548-7d0f-4374-babf-1bd0e42d4180')


def uid(key): return str(uuid.uuid5(NS, key))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path, data): path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
def physical(c): return c.get('physical', c.get('role') != 'schematic_boundary_not_orderable')


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs, source_models, trees, namespaces, netlists = {}, {}, {}, {}, {}
    replacement_file=OUT/'component-substitutions.json'
    replacements=json.loads(replacement_file.read_text(encoding='utf-8'))['replacements']
    inputs[replacement_file.relative_to(ROOT).as_posix()]=sha(replacement_file)
    for name, relative, stem in BLOCKS:
        folder = ROOT / relative
        paths = [folder/(stem+'.kicad_sch'), folder/'design.json', folder/'bom.csv', folder/'netlist.xml']
        for path in paths: inputs[path.relative_to(ROOT).as_posix()] = sha(path)
        tree = parse(paths[0].read_text(encoding='utf-8'))
        symbols = children(child(tree, 'lib_symbols'), 'symbol')
        namespace_set = {value(s[1]).split(':')[0] for s in symbols}
        if len(namespace_set) != 1: raise ValueError('Ambiguous library: '+name)
        namespace = next(iter(namespace_set))
        lib = folder/(namespace+'.kicad_sym')
        inputs[lib.relative_to(ROOT).as_posix()] = sha(lib)
        namespaces[name] = (namespace, lib)
        source_models[name] = json.loads(paths[1].read_text(encoding='utf-8'))
        netlists[name] = ET.parse(paths[3])
        for label in children(tree, 'label'):
            label[1] = q(ALIASES.get(name, {}).get(value(label[1]), value(label[1])))
        trees[name] = tree
    interfaces = {n for n in PUBLIC if sum(any(value(l[1]) == n for l in children(t, 'label')) for t in trees.values()) > 1}
    # Remove duplicate markers only on rails actually connected between sheets.
    driven = set()
    for name, nets in netlists.items():
        for net in nets.findall('.//nets/net'):
            n = ALIASES.get(name, {}).get(net.attrib['name'].lstrip('/'), net.attrib['name'].lstrip('/'))
            if n in interfaces and any(x.attrib.get('pintype') == 'power_out' and not x.attrib['ref'].startswith('#') for x in net.findall('node')):
                driven.add(n)
    owner = {'LOGIC_GND': 'mc_local_power', 'CORE_5V': 'mc_local_power',
             'CORE_1V2': 'mc_local_power', 'IO_3V3': 'mc_local_power'}
    root_id = uid('root')
    top_items, sheets, mappings, libs, combined = [], [], {}, [], {}
    for index, (name, relative, stem) in enumerate(BLOCKS, 1):
        tree = trees[name]
        folder = ROOT/relative
        namespace, library = namespaces[name]
        sheet_id = uid(name)
        mapping = {'references': {}, 'interfaces': [], 'removed_power_flags': []}
        mappings[name] = mapping
        for sym in list(children(tree, 'symbol')):
            prop = ref_property(sym); old = value(prop[2])
            if old.startswith('#'):
                at = point(child(sym, 'at')); ends = {at}
                for wire in children(tree, 'wire'):
                    points = {point(p) for p in children(child(wire, 'pts'), 'xy')}
                    if at in points: ends |= points
                labels = {value(l[1]) for l in children(tree, 'label') if point(child(l, 'at')) in ends}
                if len(labels) != 1: raise ValueError('Ambiguous flag: '+name+'/'+old)
                net = next(iter(labels))
                if net in interfaces and (net in driven or owner.get(net) != name):
                    mapping['removed_power_flags'].append({'reference': old, 'net': net})
                    remove_flag(tree, sym); continue
            ref = new_ref(old, index); prop[2] = q(ref); mapping['references'][old] = ref
            instance = child(sym, 'instances')
            if instance is not None: sym.remove(instance)
            sym.append(['instances', ['project', q('motion_card'), ['path', q('/'+root_id+'/'+sheet_id), ['reference', q(ref)], ['unit','1']]]])
            child(sym, 'lib_id')[1] = q(value(child(sym, 'lib_id')[1]).replace(namespace+':', 'MC_'+name+':', 1))
            if old in source_models[name]['components']:
                source = source_models[name]['components'][old]
                if physical(source):
                    part = json.loads(json.dumps(source))
                    part['source_block'] = name; part['source_reference'] = old
                    part['pins'] = {p: ALIASES.get(name, {}).get(n,n) if n else None for p,n in part['pins'].items()}
                    if part.get('mpn') in replacements:
                        replacement=replacements[part['mpn']]
                        part['inherited_mpn']=part['mpn'];part['mpn']=replacement['mpn'];part['value']=replacement['value']
                        part['voltage_rating_v']=replacement['voltage_rating_v']
                        part['component_substitution']='MC-CAP-001-prototype-candidate'
                        for prop in children(sym,'property'):
                            if value(prop[1])=='MPN':prop[2]=q(part['mpn'])
                            if value(prop[1])=='Value':prop[2]=q(part['value'])
                    if name == 'fpga_core' and old == 'U1':
                        part['footprint'] = 'CNC_Motion:T20F256_Efinix_NSMD'
                        part['footprint_status'] = 'manufacturer_pad_geometry_candidate_not_process_qualified'
                        for p in children(sym,'property'):
                            if value(p[1]) == 'Footprint': p[2] = q(part['footprint'])
                    combined[ref] = part
        for libsym in children(child(tree,'lib_symbols'),'symbol'):
            libsym[1] = q(value(libsym[1]).replace(namespace+':', 'MC_'+name+':',1))
        child(tree, 'generator')[1] = q('motion_card_candidate')
        for label in children(tree,'label'):
            net = value(label[1])
            if net in interfaces and net not in mapping['interfaces']:
                label[0] = 'hierarchical_label'; label.insert(2,['shape','bidirectional'])
                mapping['interfaces'].append(net)
        filename = name+'.kicad_sch'
        (OUT/filename).write_text(dump(tree)+'\n',encoding='utf-8')
        dest = OUT/(name+'.kicad_sym'); shutil.copyfile(library,dest)
        libs.append(f'(lib (name "MC_{name}") (type "KiCad") (uri "${{KIPRJMOD}}/{dest.name}") (options "") (descr "Sourced MC circuit candidate"))')
        for fplib in folder.glob('*.pretty'):
            target = OUT/fplib.name
            if not target.exists(): target.mkdir()
            for fp in fplib.glob('*.kicad_mod'):
                dest = target/fp.name
                if dest.exists() and dest.read_bytes() != fp.read_bytes(): raise ValueError('Conflicting footprint '+str(dest))
                shutil.copyfile(fp,dest); inputs[fp.relative_to(ROOT).as_posix()] = sha(fp)
        # Five independently reviewable sheets fit within the A0 top sheet.
        x = round(292.1+((index-1)%3)*228.6,4)
        y = 76.2 if index <= 3 else 449.58
        ports = sorted(mapping['interfaces']); height = round(max(71.12, len(ports)*7.62+15.24),4)
        pins = []
        for j,net in enumerate(ports):
            py=round(y+7.62+j*7.62,4)
            pins.append(f'(pin {q(net)} bidirectional (at {x} {py} 180) (effects(font(size 1.1 1.1))) (uuid "{uid(name+net)}"))')
            top_items.append(f'(wire (pts(xy {round(x-43.18,4)} {py})(xy {x} {py})) (stroke(width 0)(type default)) (uuid "{uid(name+net+"w")}"))')
            top_items.append(f'(label {q(net)} (at {round(x-43.18,4)} {py} 0) (effects(font(size 1.1 1.1))(justify left bottom)) (uuid "{uid(name+net+"l")}"))')
        sheets.append(f'(sheet (at {x} {y}) (size 139.7 {height}) (stroke(width 0.254)(type default)) (fill(color 0 0 0 0)) (uuid "{sheet_id}") (property "Sheetname" {q(name)} (at {x} {y-3} 0) (effects(font(size 1.5 1.5))(justify left))) (property "Sheetfile" {q(filename)} (at {x} {y+height+3} 0) (effects(font(size 1 1))(justify left))) '+''.join(pins)+f'(instances(project "motion_card"(path "/{root_id}"(page "{index+1}")))))')
    notes = ('PROPOSED IS-2 MC CIRCUIT CANDIDATE: FPGA, autonomous local rails, conditioned dual watchdogs, permission/OPI/trip latches and 12-motor Ioff buffers.\n'
             '38 motor/TX paths use actual Ioff buffers; other Ioff paths, presence filters, identity, slot-status register, flash restore and connectors remain missing.\n'
             'MC_RAILS_OK uses qualified destination-rail FPGA_CRESET_N, not MC_RAILS_OK_5V. CDONE qualification uses delayed FPGA_USER_RESET_N; timing is unqualified.\n'
             'Legacy progress ball is proposed as FPGA_PROGRESS_M; A2 is the independent RAW_INHIBIT_N input. Reserved enable balls now connect to EN_N buffers; vendor fit, CNC1 pulse generation and remaining GPIO allocation are open.\n'
             'Bank-B qualified OE is the same physical net as OPI_BOE clear. Receiving cards must pull EN_N high from their own powered rail; those receivers remain separate unfinished circuits.\n'
             'Native schematic ERC is distinct from PCB DRC, vendor FPGA fit and measurements. NOT FOR MANUFACTURE.')
    top=f'(kicad_sch(version 20250114)(generator "motion_card_candidate")(uuid "{root_id}")(paper "A0")(lib_symbols)'
    top+='(title_block(title "Motion card circuit candidate")(date "2026-09-30")(rev "r0.3-proposed-IS2"))'
    top+=f'(text {q(notes)} (at 20 20 0) (effects(font(size 1.35 1.35))(justify left top)) (uuid "{uid("notes")}"))'+''.join(sheets+top_items)+'(sheet_instances(path "/"(page "1"))))'
    (OUT/'motion_card.kicad_sch').write_text(dump(parse(top))+'\n',encoding='utf-8')
    write_json(OUT/'motion_card.kicad_pro', {'meta':{'filename':'motion_card.kicad_pro','version':1}})
    (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)'+''.join(libs)+')'))+'\n',encoding='utf-8')
    fp_rows=[f'(lib(name "{p.stem}")(type "KiCad")(uri "${{KIPRJMOD}}/{p.name}")(options "")(descr "Source candidate footprint"))' for p in sorted(OUT.glob('*.pretty'))]
    (OUT/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)'+''.join(fp_rows)+')'))+'\n',encoding='utf-8')
    for p in (OUT/'CNC_Motion.pretty').glob('*.kicad_mod'): inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in (OUT/'3dmodels').glob('*'): inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    write_json(OUT/'design.json', {'schema_version':1,'revision':'motion-card-r0.3-proposed-IS2',
        'manufacturing_ready':False, 'interface_agreed':False,'frozen_IS1_unchanged':True,
        'scope':notes,'components':combined,'source_sha256':inputs,
        'physical_qualification':False,'eight_twelve_runtime_qualified':False})
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','Status','Scope'])
        for ref,c in combined.items(): w.writerow([ref,c['value'],c.get('mpn',''),c.get('footprint',''),c.get('status','candidate_not_qualified'),'physical_component_candidate'])
    write_json(OUT/'assembly-map.json',{'schema_version':1,'manufacturing_ready':False,'blocks':mappings,
        'interface_nets':sorted(interfaces),'aliases':ALIASES,'input_sha256':inputs,
        'builder_sha256':sha(Path(__file__)), 'physical_parts':len(combined)})
    changed=[p for p,h in inputs.items() if sha(ROOT/p)!=h]
    if changed: raise ValueError('Sources changed during build: '+repr(changed))
    print(json.dumps({'physical_parts':len(combined),'shared_nets':len(interfaces),'schematic':str(OUT/'motion_card.kicad_sch'),'manufacturing_ready':False}))


if __name__=='__main__': build()
