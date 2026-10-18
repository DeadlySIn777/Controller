"""Integrate the retained MC circuit and real motherboard peripheral sources.

This is an additive circuit integration, never a fabrication-file generator.
The five retained MC sheets remain siblings of new field-circuit sheets. Root
labels deliberately preserve their old native net names, including slashes;
the independent validator checks every retained fitted pin rather than
assuming hierarchy changes are electrically harmless.
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
MC = ROOT / 'hardware/motion_card'
OUT = ROOT / 'hardware/motherboard'
NS = uuid.UUID('14e76902-7386-4533-9ba8-f311a6588bd3')
MC_SHEETS = ('fpga_core', 'mc_local_power', 'watchdog_conditioning', 'mc_permission', 'mc_motor_buffers')
NEW_BLOCKS = (('motherboard_motors', 6), ('motherboard_fast_inputs', 7), ('motherboard_di', 8),
              ('motherboard_motor_power', 9), ('motherboard_do', 10), ('motherboard_control_bridges',12))

# Exact reviewed domain/net bindings, rather than a wildcard name flattening.
# FIELD_A/B returns stay distinct until the real power-entry source assigns
# them. Receiving motor logic uses the monitored retained 3.3 V rail.
SHARED_NEW_PORTS = {
    'MOTOR_IO_3V3':'IO_3V3',
    **{n:'motherboard_motors/'+n for n in
       ('MOTOR_5V_A','MOTOR_5V_B','AUX_5V_A','AUX_5V_B','AUX_24V_A','AUX_24V_B',
        'MOTOR_POWER_OK_A_QUALIFIED','MOTOR_POWER_OK_B_QUALIFIED','OPI_OK_A','OPI_OK_B')},
    'OPI_REARM_A':'fpga_core/OPI_REARM_M','OPI_REARM_B':'fpga_core/OPI_REARM_M',
    **{n:'fpga_core/'+n for n in ('FREQ0_FPGA','FREQ1_FPGA','MPG_A_FPGA','MPG_B_FPGA')},
    'OUT_PERMIT_A':'mc_permission/OUT_PERMIT','OUT_PERMIT_B':'mc_permission/OUT_PERMIT',
    'OPI_REARM_M':'fpga_core/OPI_REARM_M','WATCHDOG_TRIP_CLEAR':'fpga_core/WATCHDOG_TRIP_CLEAR',
    **{n:'mc_permission/'+n for n in ('OPI_REARM_TX','OPI_REARM_BOE','WD_M_TRIP_CLEAR_N','WD_O_TRIP_CLEAR_N')},
}
FPGA_REAL_ENDPOINTS = {
    'FPGA_PROGRESS_O':'watchdog_conditioning/FPGA_PROGRESS_O',
    'OPI_REARM_O':'mc_permission/OPI_REARM_OUT',
    'PERMIT_OUT_REQ':'mc_permission/PERMIT_OUT_REQ',
    **{n:'mc_permission/'+n for n in ('OPI_OK_TX','OPI_OK_BOE','OPI_OK_OUT','OUT_PERMIT','PROC_PERMIT','TAMPER_CLEAR_N')},
    'WATCHDOG_TRIP_M':'mc_permission/WD_M_TRIP_N',
    'WATCHDOG_TRIP_O':'mc_permission/WD_O_TRIP_N',
    'MOTION_A_PGOOD':'motherboard_motors/MOTOR_POWER_OK_A_QUALIFIED',
    'MOTION_B_PGOOD':'motherboard_motors/MOTOR_POWER_OK_B_QUALIFIED',
    'OPI_OK_A':'motherboard_motors/OPI_OK_A','OPI_OK_B':'motherboard_motors/OPI_OK_B',
}


def uid(key): return str(uuid.uuid5(NS, key))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path, data): path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
def native_nodes(path):
    result = {}
    for net in ET.parse(path).findall('.//nets/net'):
        for node in net.findall('node'):
            key = (node.attrib['ref'], node.attrib['pin'])
            if key in result: raise ValueError('Duplicate source pin '+repr(key))
            result[key] = net.attrib['name']
    return result


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    previous_map_path=OUT/'assembly-map.json'
    previous_inputs=json.loads(previous_map_path.read_text(encoding='utf-8')).get('input_sha256',{}) if previous_map_path.exists() else {}
    footprint_updates=[]
    inputs = {}
    def retain(path):
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
        return path
    model = json.loads(retain(MC/'design.json').read_text(encoding='utf-8'))
    old_nodes = native_nodes(retain(MC/'netlist.xml'))
    claimed_power_flags={net.lstrip('/'):ref for (ref,pin),net in old_nodes.items() if ref.startswith('#FLG')}
    # KiCad XML deliberately omits the PWR_FLAG components. The retained
    # strict-ERC local-power source owns these common declarations already.
    claimed_power_flags.update({n:'retained_mc_local_power' for n in ('IO_3V3','LOGIC_GND','CORE_1V2')})
    old_root = parse(retain(MC/'motion_card.kicad_sch').read_text(encoding='utf-8'))
    root_id = value(child(old_root, 'uuid')[1])
    original_sheets = {value(next(p[2] for p in children(s, 'property') if value(p[1])=='Sheetname')):s
                       for s in children(old_root, 'sheet')}
    if set(original_sheets) != set(MC_SHEETS): raise ValueError('Retained MC sheet inventory changed')
    old_interfaces = set(json.loads(retain(MC/'assembly-map.json').read_text(encoding='utf-8'))['interface_nets'])
    parts = json.loads(json.dumps(model['components']))
    if len(parts) != 327: raise ValueError('Expected current retained 327-part source')
    trees = {}; sheet_ids = {}; libraries = []; promotions = {}; new_maps = {}
    for name in MC_SHEETS:
        trees[name] = parse(retain(MC/(name+'.kicad_sch')).read_text(encoding='utf-8'))
        sheet_ids[name] = value(child(original_sheets[name], 'uuid')[1])
        libfile = retain(MC/(name+'.kicad_sym'))
        shutil.copyfile(libfile, OUT/libfile.name)
        libraries.append(f'(lib(name "MC_{name}")(type "KiCad")(uri "${{KIPRJMOD}}/{libfile.name}")(options "")(descr "Retained reviewed MC circuit"))')
        promotions[name] = {value(l[1]):value(l[1]) for l in children(trees[name], 'hierarchical_label')}

    # Connect the real motor field circuit to the current logic buffers without
    # renaming any retained physical net. These suffixes are historical net IDs,
    # not a promise of separate MIA/MX4 cards in the motherboard architecture.
    motor_names = {f'{signal}{i}{"_N" if signal=="EN" else ""}_TO_{"MIA" if i<8 else "MX4"}'
                   for signal in ('STEP', 'DIR', 'EN') for i in range(12)}
    motor_names |= {'TX_PERMIT_A_TO_MIA', 'TX_PERMIT_B_TO_MX4'}
    native_motor = {n.split('/')[-1]:n for n in old_nodes.values() if n.startswith('/mc_motor_buffers/') and n.split('/')[-1] in motor_names}
    if set(native_motor) != motor_names: raise ValueError('Retained 38 motor-interface names changed')
    promoted_motor = {n:'mc_motor_buffers/'+n for n in motor_names}
    promoted_alarm = {f'ALM{i}_FPGA':f'fpga_core/ALM{i}_FPGA' for i in range(12)}
    promoted_encoder = {f'ENC{i}_{signal}_FPGA':f'fpga_core/ENC{i}_{signal}_FPGA' for i in range(4) for signal in 'ABZ'}
    fpga_ports={**promoted_alarm,**promoted_encoder}
    for name, mapping in (('mc_motor_buffers',promoted_motor), ('fpga_core',fpga_ports)):
        for net, parent in mapping.items():
            labels = [l for l in children(trees[name], 'label') if value(l[1])==net]
            if not labels: raise ValueError('Missing retained interface label '+name+'/'+net)
            label = labels[0]; label[0]='hierarchical_label'; label.insert(2,['shape','bidirectional'])
            promotions[name][net]=parent

    for name, index in NEW_BLOCKS:
        source=ROOT/'hardware'/name
        source_model=json.loads(retain(source/'design.json').read_text(encoding='utf-8'))
        tree=parse(retain(source/(name+'.kicad_sch')).read_text(encoding='utf-8'))
        retain(source/'netlist.xml'); retain(source/'bom.csv')
        ns_set={value(s[1]).split(':')[0] for s in children(child(tree,'lib_symbols'),'symbol')}
        if len(ns_set)!=1: raise ValueError('Ambiguous new source symbol namespace')
        namespace=next(iter(ns_set)); libfile=retain(source/(namespace+'.kicad_sym'))
        destination=OUT/(name+'.kicad_sym'); shutil.copyfile(libfile,destination)
        libraries.append(f'(lib(name "MB_{name}")(type "KiCad")(uri "${{KIPRJMOD}}/{destination.name}")(options "")(descr "Actual motherboard circuit candidate"))')
        tree_id=uid('sheet-'+name); sheet_ids[name]=tree_id
        reference_map={}; removed_flags=[]
        boundary_nets={n for c in source_model['components'].values() if not c.get('physical',True) or c.get('role')=='schematic_boundary_not_orderable'
                       for n in c.get('pins',{}).values() if n}
        # Export only nets that have another implemented region to connect to.
        # External terminals and still-unsupplied power boundaries stay on the
        # real source sheet; unused top-sheet stubs are not useful circuitry.
        export_nets=motor_names | set(fpga_ports) | old_interfaces | set(SHARED_NEW_PORTS)
        # Shared retained logic supply, if present, is a real common net; a new
        # receiver rail remains independent and must get its own supply circuit.
        source_labels={value(l[1]) for l in children(tree,'label')}
        export_nets &= source_labels
        port_map={n:SHARED_NEW_PORTS.get(n,promoted_motor.get(n,fpga_ports.get(n,n if n in old_interfaces else name+'/'+n))) for n in export_nets}
        for symbol in list(children(tree,'symbol')):
            prop=ref_property(symbol); old=value(prop[2])
            if old.startswith('#'):
                at=point(child(symbol,'at')); ends={at}
                for wire in children(tree,'wire'):
                    points={point(p) for p in children(child(wire,'pts'),'xy')}
                    if at in points: ends|=points
                flags={value(l[1]) for l in children(tree,'label') if point(child(l,'at')) in ends}
                if len(flags)==1:
                    flagged=next(iter(flags));physical=port_map.get(flagged,name+'/'+flagged)
                    if physical in claimed_power_flags:
                        removed_flags.append({'reference':old,'net':flagged,'physical_net':'/'+physical,
                            'owner':claimed_power_flags[physical],'reason':'Single declaration for this genuinely shared incoming rail/return; no duplicate power-output flags'})
                        remove_flag(tree,symbol);continue
                    claimed_power_flags[physical]=old
            # Some source owners pre-annotate their reserved motherboard range.
            # Keep it once; never silently turn U6001 into U12001.
            import re
            match=re.fullmatch(r'([^0-9]+)([0-9]+)',old)
            if match is None:raise ValueError('Unannotated new source reference '+old)
            number=int(match[2]);ref=old if index*1000<=number<(index+1)*1000 else new_ref(old,index)
            prop[2]=q(ref);reference_map[old]=ref
            instance=child(symbol,'instances')
            if instance is not None: symbol.remove(instance)
            symbol.append(['instances',['project',q('motherboard'),['path',q('/'+root_id+'/'+tree_id),['reference',q(ref)],['unit','1']]]])
            child(symbol,'lib_id')[1]=q(value(child(symbol,'lib_id')[1]).replace(namespace+':','MB_'+name+':',1))
            c=source_model['components'].get(old)
            if c and c.get('physical',c.get('role')!='schematic_boundary_not_orderable'):
                if ref in parts: raise ValueError('New source reference collides with retained MC')
                parts[ref]={**json.loads(json.dumps(c)),'source_block':name,'source_reference':old}
        for s in children(child(tree,'lib_symbols'),'symbol'):s[1]=q(value(s[1]).replace(namespace+':','MB_'+name+':',1))
        for net in port_map:
            label=next(l for l in children(tree,'label') if value(l[1])==net)
            label[0]='hierarchical_label';label.insert(2,['shape','bidirectional'])
        trees[name]=tree;promotions[name]=port_map
        new_maps[name]={'references':reference_map,'ports':port_map,'removed_power_flags':removed_flags,'namespace_index':index}
        for library in source.glob('*.pretty'):
            target=OUT/library.name;target.mkdir(exist_ok=True)
            for fp in library.glob('*.kicad_mod'):
                retain(fp);dest=target/fp.name
                if dest.exists() and dest.read_bytes()!=fp.read_bytes():
                    # A reviewed source owner can improve its generated land
                    # pattern. Only replace the precise prior copied hash;
                    # never overwrite a hand-edited parent footprint.
                    key=fp.relative_to(ROOT).as_posix();old_hash=sha(dest)
                    if previous_inputs.get(key)!=old_hash:raise ValueError('Conflicting or edited parent footprint '+str(dest))
                    footprint_updates.append({'source':key,'old_parent_sha256':old_hash,'new_source_sha256':sha(fp)})
                shutil.copyfile(fp,dest)

    # Copy retained geometry and model artifacts without changing child sources.
    for library in MC.glob('*.pretty'):
        target=OUT/library.name;target.mkdir(exist_ok=True)
        for fp in library.glob('*.kicad_mod'):retain(fp);shutil.copyfile(fp,target/fp.name)
    models=MC/'3dmodels'
    if models.exists():
        (OUT/'3dmodels').mkdir(exist_ok=True)
        for f in models.iterdir():
            if f.is_file():retain(f);shutil.copyfile(f,OUT/'3dmodels'/f.name)
    for name,tree in trees.items():
        for symbol in children(tree,'symbol'):
            instances=child(symbol,'instances')
            if instances is not None:
                for project in children(instances,'project'):project[1]=q('motherboard')
        (OUT/(name+'.kicad_sch')).write_text(dump(tree)+'\n',encoding='utf-8')
    # Pack actual hierarchy pages, rather than drawing unconnected substitute
    # parts or allowing off-page schematic objects.
    columns=[76.2]*3;items=[];sheets=[]
    for page,name in enumerate(trees,2):
        ports=sorted(promotions[name]);left_count=(len(ports)+1)//2
        height=round(max(55.88,left_count*5.08+15.24),4)
        col=min(range(3),key=lambda i:columns[i]);x=round(101.6+col*355.6,4);y=columns[col]
        columns[col]+=height+25.4
        if columns[col]>800:raise ValueError('Actual top-level hierarchy exceeds A0; add hierarchy page')
        pins=[]
        for i,net in enumerate(ports):
            left=i<left_count;row=i if left else i-left_count
            py=round(y+7.62+row*5.08,4);parent=promotions[name][net]
            edge=x if left else round(x+177.8,4);end=round(edge+(-50.8 if left else 50.8),4)
            # A label belongs on a real wire endpoint. A generated midpoint
            # without a split wire is an ERC dangling label even if export
            # happens to infer the desired name.
            label_x=end
            pins.append(f'(pin {q(net)} bidirectional(at {edge} {py} {180 if left else 0})(effects(font(size 1 1)))(uuid "{uid(name+net+"pin")}"))')
            items.append(f'(wire(pts(xy {end} {py})(xy {edge} {py}))(stroke(width 0)(type default))(uuid "{uid(name+net+"wire")}"))')
            items.append(f'(label {q(parent)}(at {label_x} {py} 0)(effects(font(size 1 1))(justify left bottom))(uuid "{uid(name+net+"label")}"))')
        sheets.append(f'(sheet(at {x} {y})(size 177.8 {height})(stroke(width .254)(type default))(fill(color 0 0 0 0))(uuid "{sheet_ids[name]}")'
                      f'(property "Sheetname" {q(name)}(at {x} {y-3} 0)(effects(font(size 1.5 1.5))(justify left)))'
                      f'(property "Sheetfile" {q(name+".kicad_sch")}(at {x} {y+height+3} 0)(effects(font(size 1 1))(justify left)))'
                      +''.join(pins)+f'(instances(project "motherboard"(path "/{root_id}"(page "{page}")))))')
    notes='ONE CUSTOM MOTHERBOARD / TWELVE ONBOARD MOTORS\nRetained 327-part circuit plus real peripheral sources. Hierarchy pages are functional regions, not separate PCBs.\nPartial source-backed prototype engineering. Missing power, connectors, compute, full I/O and vendor fit are explicit unfinished work. NOT FOR MANUFACTURE.'
    top=f'(kicad_sch(version 20250114)(generator "motherboard_candidate")(uuid "{root_id}")(paper "A0")(lib_symbols)'
    top+='(title_block(title "One-board controller integrated circuit candidate")(date "2026-09-30")(rev "motherboard-r0.2-IS2"))'
    top+=f'(text {q(notes)}(at 20 20 0)(effects(font(size 1.35 1.35))(justify left top))(uuid "{uid("notes")}"))'+''.join(sheets+items)+'(sheet_instances(path "/"(page "1"))))'
    # Apply only the exact reviewed 64 former NC balls. Existing 96 GPIO, clock
    # and every non-FPGA retained physical net remain unchanged. Available real
    # endpoints are joined by hierarchy, never by constant-healthy substitutes.
    from hardware_apply_motherboard_fpga_allocation import apply_base_allocation, rebuild_root_geometry
    retain(ROOT/'tools/hardware_apply_motherboard_fpga_allocation.py')
    proposal=json.loads(retain(OUT/'fpga-allocation-proposal.json').read_text(encoding='utf-8'))
    root,core,allocation=apply_base_allocation(parse(top),trees['fpga_core'],proposal,ET.parse(MC/'netlist.xml'))
    trees['fpga_core']=core
    promotions['fpga_core']=dict(allocation['root_sheet_port_map'])
    for signal,parent in FPGA_REAL_ENDPOINTS.items():
        promotions['fpga_core'][signal]=parent
        for item in allocation['exact_pin_rename_ledger']:
            if item['signal']==signal:
                item['new_native_net']='/'+parent
                item['actual_endpoint_connected_in_parent']=True
                if signal in ('WATCHDOG_TRIP_M','WATCHDOG_TRIP_O'):
                    item['actual_electrical_polarity']='ACTIVE_LOW; RTL must invert for active-high logical trip status'
        leaf,net=parent.split('/',1)
        if leaf in MC_SHEETS:
            labels=[l for l in children(trees[leaf],'label') if value(l[1])==net]
            if not labels:raise ValueError('Actual retained endpoint missing '+parent)
            label=labels[0];label[0]='hierarchical_label';label.insert(2,['shape','bidirectional'])
            promotions[leaf][net]=parent
    # OUT_PERMIT is also the physical hardware permission term of both DO banks.
    if 'OUT_PERMIT' not in promotions['mc_permission']:raise ValueError('DO hardware permission endpoint missing')
    for net in ('OPI_REARM_TX','OPI_REARM_BOE','WD_M_TRIP_CLEAR_N','WD_O_TRIP_CLEAR_N'):
        labels=[l for l in children(trees['mc_permission'],'label') if value(l[1])==net]
        if not labels:raise ValueError('Retained passive fanout endpoint missing '+net)
        label=labels[0];label[0]='hierarchical_label';label.insert(2,['shape','bidirectional'])
        promotions['mc_permission'][net]='mc_permission/'+net
    rebuild_root_geometry(root,{**promotions,'_directions':allocation['desired_directions']})
    allocation['root_sheet_port_map']=promotions['fpga_core']
    allocation['source_scope']='Applied exact BASE64 NC promotions and reviewed real parent endpoint bridges; remaining peripherals/vendor fit are unfinished'
    allocation['native_export_verified']=False
    for item in allocation['exact_pin_rename_ledger']:
        parts['U1001']['pins'][item['pin']]=item['signal']
    parts['U1001']['exact_fpga_nc_promotion_native_nets']={r['pin']:r['new_native_net'] for r in allocation['exact_pin_rename_ledger']}
    write_json(OUT/'fpga-allocation-parent.json',allocation)
    (OUT/'motherboard.kicad_sch').write_text(dump(root)+'\n',encoding='utf-8')
    for name in ('fpga_core','watchdog_conditioning','mc_permission'):
        (OUT/(name+'.kicad_sch')).write_text(dump(trees[name])+'\n',encoding='utf-8')
    pro=json.loads(retain(MC/'motion_card.kicad_pro').read_text(encoding='utf-8'))
    pro['meta']['filename']='motherboard.kicad_pro';write_json(OUT/'motherboard.kicad_pro',pro)
    (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)'+''.join(libraries)+')'))+'\n',encoding='utf-8')
    entries=[f'(lib(name "{p.stem}")(type "KiCad")(uri "${{KIPRJMOD}}/{p.name}")(options "")(descr "Retained source candidate"))' for p in sorted(OUT.glob('*.pretty'))]
    (OUT/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)'+''.join(entries)+')'))+'\n',encoding='utf-8')
    write_json(OUT/'design.json',{'schema_version':1,'revision':'motherboard-r0.2-IS2','manufacturing_ready':False,
        'physical_qualification':False,'one_custom_board':True,'motor_interfaces_on_motherboard':12,
        'physical_footprints':len(parts),'assembly_fitted_parts':sum(not c.get('dnp',False) for c in parts.values()),
        'scope':notes,'components':parts,'source_sha256':inputs,'commodity_modules_fitted':False,
        'fpga_nc_promotions_applied':64,'fpga_vendor_fit':False})
    write_json(OUT/'assembly-map.json',{'schema_version':1,'manufacturing_ready':False,'retained_mc_parts':327,
        'retained_native_pin_nets':{r+'.'+p:n for (r,p),n in old_nodes.items() if r in model['components']},
        'input_sha256':inputs,'blocks':new_maps,'sheet_ports':promotions,'builder_sha256':sha(Path(__file__)),
        'native_net_renames_allowed':allocation['exact_pin_rename_ledger'],'physical_parts':len(parts)})
    write_json(OUT/'source-footprint-updates.json',{'schema_version':1,'updates':footprint_updates,
        'basis':'Only exact prior generated copies may update to the reviewed child-source footprint; no user edits or retained MC geometry replaced.'})
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','Status','DNP','Scope'])
        for ref,c in parts.items():w.writerow([ref,c['value'],c.get('mpn',''),c.get('footprint',''),c.get('status','candidate_not_qualified'),str(bool(c.get('dnp',False))).lower(),'actual_on_motherboard_component_candidate'])
    if any(sha(ROOT/p)!=h for p,h in inputs.items()):raise ValueError('Source changed during motherboard integration')
    print(json.dumps({'physical_parts':len(parts),'retained_mc_parts':327,'schematic':str(OUT/'motherboard.kicad_sch'),
                      'exact_fpga_nc_promotions':64,'manufacturing_ready':False}))


if __name__=='__main__':build()
