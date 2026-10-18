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
              ('motherboard_motor_power', 9), ('motherboard_do', 10), ('motherboard_control_bridges',12),
              ('motherboard_io_control',13), ('motherboard_operator',14),
              ('motherboard_power_entry',11), ('motherboard_compute',15),
              ('motherboard_esp_socket',16), ('motherboard_process',14),
              ('motherboard_acc_control',14), ('motherboard_analog_output',14),
              ('motherboard_analog_input',14), ('motherboard_safety_sensor',19),
              ('motherboard_terminals',19), ('motherboard_comms',14),
              ('motherboard_status',17), ('motherboard_identity_io',21), ('motherboard_diagnostics',22))

# ISO1212 substrate pads are electrically isolated local thermal islands.
# They are not rack buses or connections to other motherboard regions.
# Keep their actual native nets and package lands; export no phantom root port.
LOCAL_FLOATING_SUBSTRATES=({f'DI{i}_SUB_ISLAND' for i in range(24)} |
    {f'ALM{i}_SUB_FLOAT' for i in range(12)} | {'PRB0_SUB_ISLAND','PRB1_SUB_ISLAND'} |
    {n+'_SUB_ISLAND' for n in ('PROCESS_PERMIT','EXT_PERMIT','RESET_ARM','SAFETY_STATUS','STO_FB','CONTACTOR_FB')})

# Exact reviewed domain/net bindings, rather than a wildcard name flattening.
# FIELD_A/B returns stay distinct until the real power-entry source assigns
# them. Receiving motor logic uses the monitored retained 3.3 V rail.
SHARED_NEW_PORTS = {
    **{n:'motherboard_power_entry/'+n for n in ('FA_PGOOD','FB_PGOOD')},
    **{n:'motherboard_io_control/'+n for n in ('DOA_FIELD_POWER_GOOD','DOB_FIELD_POWER_GOOD')},
    **{n:'fpga_core/'+n for n in ('FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT')},
    'MOTOR_IO_3V3':'IO_3V3',
    **{n:'motherboard_motors/'+n for n in
       ('MOTOR_5V_A','MOTOR_5V_B','AUX_5V_A','AUX_5V_B','AUX_24V_A','AUX_24V_B',
        'MOTOR_POWER_OK_A_QUALIFIED','MOTOR_POWER_OK_B_QUALIFIED','OPI_OK_A','OPI_OK_B')},
    'OPI_REARM_A':'fpga_core/OPI_REARM_M','OPI_REARM_B':'fpga_core/OPI_REARM_M',
    **{n:'fpga_core/'+n for n in ('FREQ0_FPGA','FREQ1_FPGA','MPG_A_FPGA','MPG_B_FPGA')},
    'OUT_PERMIT_A':'mc_permission/OUT_PERMIT','OUT_PERMIT_B':'mc_permission/OUT_PERMIT',
    'OPI_REARM_M':'fpga_core/OPI_REARM_M','WATCHDOG_TRIP_CLEAR':'fpga_core/WATCHDOG_TRIP_CLEAR',
    **{n:'mc_permission/'+n for n in ('OPI_REARM_TX','OPI_REARM_BOE','WD_REARM_M','WD_REARM_O')},
    **{f'IOL1_L{i}_{suffix}':f'fpga_core/IOL1_L{i}_{suffix}'
       for i in range(4) for suffix in ('CS_N','SCLK','MOSI','MISO')},
    **{f'DI{i}_LOGIC':f'motherboard_di/DI{i}_LOGIC' for i in range(24)},
    **{f'{name}_{suffix}':f'motherboard_do/{name}_{suffix}'
       for name in ('DOA','DOB') for suffix in
       ('SCLK_HOST','SDI_HOST','SDO_HOST','CS_N_HOST','IO_ENABLE_STROBE','CARD_EN',
        'OUT_EN_LATCH','FLT_N_HOST','DO_EN_LOGIC','CONTROLLER_RESET_N')},
    **{n:'fpga_core/'+n for n in ('PROBE_FPGA','TOOLSETTER_FPGA','FAST_SR_CLK',
        'FAST_SR_LOAD_N','FAST_SR_DATA','FAST_PORTS_ENABLE','XF_POWER_ENABLE')},
    'FPGA_CDONE':'fpga_core/FPGA_CDONE',
    **{f'ENC{i}_5V':'motherboard_fast_inputs/'+f'ENC{i}_5V_LIMITED' for i in range(4)},
    **{f'ENC{i}_5V_LIMITED':'motherboard_fast_inputs/'+f'ENC{i}_5V_LIMITED' for i in range(4)},
    'MPG_5V':'motherboard_fast_inputs/MPG_5V_LIMITED',
    'MPG_5V_LIMITED':'motherboard_fast_inputs/MPG_5V_LIMITED',
    'FREQ_5V':'motherboard_fast_inputs/FREQ_5V_LIMITED',
    'FREQ_5V_LIMITED':'motherboard_fast_inputs/FREQ_5V_LIMITED',
    'MPG_VREF':'motherboard_fast_inputs/MPG_VREF_2V5',
    'MPG_VREF_2V5':'motherboard_fast_inputs/MPG_VREF_2V5',
    'MOD_PRESENT':'motherboard_fast_inputs/FREQ_MOD_PRESENT_TO_FRONTEND',
    'FREQ_MOD_PRESENT_TO_FRONTEND':'motherboard_fast_inputs/FREQ_MOD_PRESENT_TO_FRONTEND',
    'MPG_ENABLE_TO_STATUS':'motherboard_operator/MPG_ENABLE',
    'MPG_ENABLE':'motherboard_operator/MPG_ENABLE',
    'MOTION_5V_RAW':'motherboard_power_entry/MOTION_5V_RAW',
    'DOA_FIELD_3V3':'motherboard_do/DOA_FIELD_3V3',
    'FIELD_GND':'motherboard_motors/FIELD_GND',
    'FIELD_A_24V_PROTECTED':'motherboard_power_entry/FIELD_A_24V_PROTECTED',
    'FIELD_A_24V':'motherboard_power_entry/FIELD_A_24V_PROTECTED',
    'FIELD_B_24V':'motherboard_power_entry/FIELD_B_24V_PROTECTED',
    'FIELD_B_24V_PROTECTED':'motherboard_power_entry/FIELD_B_24V_PROTECTED',
    'FIELD_A_0V':'motherboard_motors/FIELD_GND',
    'FIELD_B_0V':'motherboard_do/FIELD_B_0V',
    'DOB_FIELD_3V3':'motherboard_do/DOB_FIELD_3V3',
    'FIELD_5V':'motherboard_power_entry/FIELD_5V',
    'CORE_5V':'mc_local_power/CORE_5V',
    'CORE_24V_PROTECTED':'motherboard_power_entry/CORE_24V_PROTECTED',
    'MC_RAILS_OK_5V':'mc_local_power/MC_RAILS_OK_5V',
    'WD_M_TRIP_N':'mc_permission/WD_M_TRIP_N',
    'WD_O_TRIP_N':'mc_permission/WD_O_TRIP_N',
    'TX_PERMIT':'TX_PERMIT', 'FPGA_USER_RESET_N':'FPGA_USER_RESET_N',
    'AO_I2C_SCL':'motherboard_acc_control/AO_I2C_SCL_HOST',
    'AO_I2C_SDA':'motherboard_acc_control/AO_I2C_SDA_HOST',
    'FREQ_1WIRE_DATA_HOST':'motherboard_acc_control/FREQ_1WIRE_DATA_HOST',
    'FREQ_MOD_ID_TO_FRONTEND':'motherboard_fast_inputs/FREQ_MOD_ID_TO_FRONTEND',
    **{n:'motherboard_motor_power/'+n for n in ('MOTOR_FIELD_HEALTH_A_RAW','MOTOR_FIELD_HEALTH_B_RAW')},
    **{n:'motherboard_motors/'+n for n in ('MOTOR_TX_GATE_SOURCE_A','MOTOR_TX_GATE_SOURCE_B','MOTOR_TX_GATE_A','MOTOR_TX_GATE_B')},
    **{n:'fpga_core/'+n for n in ('HOST_SPI_SCLK','HOST_SPI_MOSI','HOST_SPI_MISO','HOST_SPI_CS_CMD_N')},
    'HOST_SPI_CS_FB_N':'fpga_core/HOST_SPI_CS_N',
    'COMPUTE_SERVICE_TX':'motherboard_compute/COMPUTE_SERVICE_TX',
    'SBC_5V':'motherboard_power_entry/SBC_5V',
    'OUT_PERMIT_ACC':'mc_permission/OUT_PERMIT',
    'PROC_PERMIT':'mc_permission/PROC_PERMIT',
    **{n:'fpga_core/'+n for n in ('PWM0_FPGA','PWM1_FPGA','PEN0_CMD','PEN1_CMD')},
    **{n:'motherboard_process/'+n for n in ('ACC_CONTROLLER_RESET_N',
        'ACC_IO_ENABLE_STROBE','ACC_CARD_EN','ACC_OUT_EN_LATCH','PEN_OUT_EN_LATCH',
        'PWM_ENABLE_LOGIC','PEN_ENABLE_LOGIC','PWM_AUX_FAULT_N')},
    'ACC_CLR_N':'motherboard_process/ACC_CLR_N',
    **{n:'motherboard_acc_control/'+n for n in ('AI_SCLK_HOST','AI_SDI_HOST','AI_SDO_HOST',
        'AO_I2C_SCL_HOST','AO_I2C_SDA_HOST',
        'AO0_CS_N_HOST','AO1_CS_N_HOST','AO0_ENABLE_REQUEST','AO1_ENABLE_REQUEST',
        'AO0_POWER_GOOD_HOST','AO1_POWER_GOOD_HOST','AO0_CLAMP_ACTIVE','AO1_CLAMP_ACTIVE',
        'AI_CS_N_HOST','AI_POWER_GOOD_HOST','AI_SENSOR_FAULT_HOST')},
    **{n:'motherboard_compute/'+n for n in ('COMPUTE_3V3_GOOD','RS485_UART_TX_HOST',
        'RS485_UART_RX_HOST','RS485_DE_HOST','CAN_SPI_SCLK_HOST','CAN_SPI_MOSI_HOST',
        'CAN_SPI_MISO_HOST','CAN_SPI_CS_N_HOST','CAN_INT_N_HOST')},
    **{n:'motherboard_acc_control/'+n for n in ('RS485_POWER_GOOD_HOST','CAN_POWER_GOOD_HOST')},
    'EXT_PERMIT_3V3':'mc_permission/EXT_PERMIT_3V3',
    'PROCESS_PERMIT_EXT_3V3':'mc_permission/PROCESS_PERMIT_EXT_3V3',
    'PERMIT_OUT_DRIVE':'mc_permission/PERMIT_OUT_DRIVE',
    'EXT_PERMIT_FPGA':'fpga_core/PROTECTIVE_STATUS_FPGA',
    **{n:'fpga_core/'+n for n in ('PROCESS_PERMIT_FPGA','SAFETY_STATUS_FPGA',
        'RESET_ARM_FPGA','CONTACTOR_FB_FPGA','STO_FB_FPGA','ARM_LAMP_FPGA')},
    **{n:'motherboard_safety_sensor/'+n for n in ('FIELD_B_5V_PRE',
        'DIC_SENSOR_SCL','DIC_SENSOR_SDA')},
    **{n:'motherboard_io_control/'+n for n in ('DI_SENSOR_G0_FAULT','DI_SENSOR_G1_FAULT',
        'DI_SENSOR_G2_FAULT','DI_SAFETY_SUPPLY_FAULT','DI_SAFETY_SECONDARY_FAULT')},
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


def build(destination=None):
    global OUT
    if destination is not None:OUT=Path(destination).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    previous_map_path=OUT/'assembly-map.json'
    previous_inputs=json.loads(previous_map_path.read_text(encoding='utf-8')).get('input_sha256',{}) if previous_map_path.exists() else {}
    footprint_updates=[]
    inputs = {}
    def retain(path):
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
        return path
    if any(n=='motherboard_terminals' for n,i in NEW_BLOCKS):
        aliases=json.loads(retain(ROOT/'hardware/motherboard_terminals/parent-aliases.json').read_text(encoding='utf-8'))
        for n,physical in aliases.items():
            if n in SHARED_NEW_PORTS and SHARED_NEW_PORTS[n]!=physical:
                raise ValueError('Terminal alias conflicts with reviewed parent '+n)
            SHARED_NEW_PORTS[n]=physical
    model = json.loads(retain(MC/'design.json').read_text(encoding='utf-8'))
    old_nodes = native_nodes(retain(MC/'netlist.xml'))
    claimed_power_flags={net.lstrip('/'):ref for (ref,pin),net in old_nodes.items() if ref.startswith('#FLG')}
    # KiCad XML deliberately omits the PWR_FLAG components. The retained
    # strict-ERC local-power source owns these common declarations already.
    claimed_power_flags.update({n:'retained_mc_local_power' for n in ('IO_3V3','LOGIC_GND','CORE_1V2','mc_local_power/CORE_5V')})
    implemented_power_outputs={}
    for provider,_index in NEW_BLOCKS:
        provider_folder=ROOT/'hardware'/('motherboard_probe_limit_upgrade' if provider=='motherboard_operator' else provider)
        provider_parts=json.loads(retain(provider_folder/'design.json').read_text(encoding='utf8'))['components']
        for net in ET.parse(retain(provider_folder/'netlist.xml')).findall('.//nets/net'):
            bare=net.attrib['name'].lstrip('/')
            for node in net.findall('node'):
                component=provider_parts.get(node.attrib['ref'],{})
                if node.attrib.get('pintype')=='power_out' and component.get('physical',component.get('role')!='schematic_boundary_not_orderable') and component:
                    physical=SHARED_NEW_PORTS.get(bare,provider+'/'+bare)
                    implemented_power_outputs[physical]=node.attrib['ref']+'.'+node.attrib['pin']
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

    # Exact reviewed power correction; the original MC remains read-only.
    from hardware_apply_motherboard_io3_upgrade import apply_io3_upgrade
    from hardware_apply_motherboard_io3_window import apply_io3_monitor_window
    for file in ('tools/hardware_apply_motherboard_io3_upgrade.py',
                 'tools/hardware_apply_motherboard_io3_window.py',
                 'reports/motherboard-io3-upgrade-20260930/freeze-receipt-r02.json',
                 'reports/motherboard-io3-upgrade-20260930/voltage-window-review/freeze-receipt-r01.json'):
        retain(ROOT/file)
    trees['mc_local_power'],pm,upgrade=apply_io3_upgrade(trees['mc_local_power'],{'components':parts})
    trees['mc_local_power'],pm,window=apply_io3_monitor_window(trees['mc_local_power'],pm,'mc')
    from hardware_apply_io3_reset_bypass import apply_io3_reset_bypass
    retain(ROOT/'tools/hardware_apply_io3_reset_bypass.py')
    retain(ROOT/'reports/motherboard-io3-upgrade-20260930/reset-bypass-r02/freeze-receipt.json')
    trees['mc_local_power'],pm,reset_bypass=apply_io3_reset_bypass(trees['mc_local_power'],pm)
    parts=pm['components'];power_delta={'upgrade':upgrade,'mc_window':window,'reset_bypass':reset_bypass}
    from hardware_apply_motherboard_unused_endpoints import apply_unused_endpoints
    retain(ROOT/'tools/hardware_apply_motherboard_unused_endpoints.py')
    retain(ROOT/'reports/motherboard-diagnostics-20260930/r01/receipt.json')
    retain(ROOT/'reports/motherboard-diagnostics-20260930/r01/bounded-NC-proposals.json')
    unused_ledger=[]
    for name in ('fpga_core','mc_local_power'):
        trees[name],pm,unused=apply_unused_endpoints(trees[name],{'components':parts},name)
        parts=pm['components'];unused_ledger.extend(unused)
        for row in unused:promotions[name].pop(row['old_native_net'].split('/')[-1],None)
    lib=retain(ROOT/'hardware/motherboard_io3_upgrade/CNC_MB_IO3.kicad_sym')
    shutil.copyfile(lib,OUT/lib.name)
    libraries.append('(lib(name "CNC_MB_IO3")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_IO3.kicad_sym")(options "")(descr "Reviewed IO3 correction"))')
    folder=ROOT/'hardware/motherboard_io3_upgrade/CNC_MB_IO3.pretty'
    (OUT/folder.name).mkdir(exist_ok=True)
    for f in folder.glob('*.kicad_mod'):retain(f);shutil.copyfile(f,OUT/folder.name/f.name)

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
    fpga_ports={**promoted_alarm,**promoted_encoder,
        **{n:'fpga_core/'+n for n in ('FPGA_CDONE','HOST_SPI_SCLK','HOST_SPI_MOSI','HOST_SPI_MISO','HOST_SPI_CS_N',
            'FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT')}}
    for name, mapping in (('mc_motor_buffers',promoted_motor), ('fpga_core',fpga_ports)):
        for net, parent in mapping.items():
            labels = [l for l in children(trees[name], 'label') if value(l[1])==net]
            if not labels: raise ValueError('Missing retained interface label '+name+'/'+net)
            label = labels[0]; label[0]='hierarchical_label'; label.insert(2,['shape','bidirectional'])
            promotions[name][net]=parent

    for net in ('CORE_5V','MC_RAILS_OK_5V'):
        label=next(l for l in children(trees['mc_local_power'],'label') if value(l[1])==net)
        label[0]='hierarchical_label';label.insert(2,['shape','bidirectional'])
        promotions['mc_local_power'][net]='mc_local_power/'+net

    for name, index in NEW_BLOCKS:
        source=ROOT/'hardware'/name
        if name=='motherboard_operator':
            source=ROOT/'hardware/motherboard_probe_limit_upgrade'
            retain(ROOT/'reports/motherboard-probe-limit-20260930/receipt-r01.json')
            retain(ROOT/'reports/motherboard-probe-limit-20260930/bounded-delta.json')
        source_model=json.loads(retain(source/'design.json').read_text(encoding='utf-8'))
        tree=parse(retain(source/(name+'.kicad_sch')).read_text(encoding='utf-8'))
        helper_refs=set()
        if name=='motherboard_operator':helper_refs={'R19401','R19402','R19403','R19404'}
        source_endpoint_delta=[]
        source_unused=[]
        if name in ('motherboard_compute','motherboard_power_entry'):
            tree,source_model,source_unused=apply_unused_endpoints(tree,source_model,name)
            unused_ledger.extend(source_unused)
        if any(n=='motherboard_safety_sensor' for n,i in NEW_BLOCKS) and name in ('motherboard_power_entry','motherboard_io_control'):
            from hardware_apply_motherboard_safety_sensor import apply_safety_sensor_endpoints
            retain(ROOT/'tools/hardware_apply_motherboard_safety_sensor.py')
            retain(ROOT/'reports/motherboard-safety-sensor-20260930/receipt-r01.json')
            tree,source_model,delta=apply_safety_sensor_endpoints(tree,source_model,
                'power_entry' if name=='motherboard_power_entry' else 'io_control')
            source_endpoint_delta=delta['exact_endpoint_changes']
        if name=='motherboard_motor_power':
            tree,source_model,motor_window=apply_io3_monitor_window(tree,source_model,'motor')
            power_delta['motor_window']=motor_window;helper_refs=set(motor_window['added_refs'])
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
        export_nets-=LOCAL_FLOATING_SUBSTRATES
        implemented_names=set(MC_SHEETS)|{n for n,i in NEW_BLOCKS}
        export_nets={n for n in export_nets if not (
            SHARED_NEW_PORTS.get(n,'').startswith('motherboard_') and
            SHARED_NEW_PORTS[n].split('/',1)[0] not in implemented_names)}
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
                    if physical in implemented_power_outputs:
                        removed_flags.append({'reference':old,'net':flagged,'physical_net':'/'+physical,
                            'owner':implemented_power_outputs[physical],
                            'reason':'Incoming standalone boundary declaration replaced by actual fitted power-output device on the parent motherboard'})
                        remove_flag(tree,symbol);continue
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
            number=int(match[2]);ref=old if old in helper_refs or index*1000<=number<(index+1)*1000 else new_ref(old,index)
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
        pin_overrides=[{'reference':reference_map[r['ref']],'pin':r['pin'],
            'old_source_net':'/'+r['old'] if r['old'] else None,
            'new_native_net':'/'+SHARED_NEW_PORTS[r['new']],
            'reason':'Exact manufacturer-reviewed XS1 acquisition/B-LDO endpoint delta'} for r in source_endpoint_delta]
        if name=='motherboard_motors' and any(n=='motherboard_power_entry' for n,i in NEW_BLOCKS):
            # Exact source-preserving interposition of independently powered
            # health contacts. Only the two AND outputs change; consumers keep
            # their final inhibited net. Never rename the complete old net.
            for pin,bank in (('7','A'),('3','B')):
                symbol=next(s for s in children(tree,'symbol') if value(ref_property(s)[2])=='U6042')
                definition=next(s for s in children(child(tree,'lib_symbols'),'symbol') if value(s[1]).split(':')[-1]==value(child(symbol,'lib_id')[1]).split(':')[-1])
                pins=[p for sub in children(definition,'symbol') for p in children(sub,'pin') if value(child(p,'number')[1])==pin]
                if len(pins)!=1 or len(child(symbol,'at'))>3 and float(child(symbol,'at')[3])!=0:raise ValueError('Motor permission pin requires exact unrotated reviewed symbol')
                xy=point(child(pins[0],'at'));at=point(child(symbol,'at'));absolute=(round(at[0]+xy[0],4),round(at[1]-xy[1],4))
                wires=[w for w in children(tree,'wire') if absolute in [point(p) for p in children(child(w,'pts'),'xy')]]
                if len(wires)!=1:raise ValueError('Motor permission output is not one label stub')
                ends={point(p) for p in children(child(wires[0],'pts'),'xy')}
                labels=[l for l in children(tree,'label') if point(child(l,'at')) in ends and value(l[1])=='MOTOR_TX_GATE_'+bank]
                if len(labels)!=1:raise ValueError('Exact motor permission output label missing')
                new='MOTOR_TX_GATE_SOURCE_'+bank;labels[0][1]=q(new)
                # The newly named output becomes its own real hierarchy port.
                port_map[new]=SHARED_NEW_PORTS[new]
                parts['U6042']['pins'][pin]=new
                pin_overrides.append({'reference':'U6042','pin':pin,'old_source_net':'/MOTOR_TX_GATE_'+bank,
                    'new_native_net':'/'+SHARED_NEW_PORTS[new], 'reason':'Exact output-only hardware health-contact interposition'})
        for net in port_map:
            label=next(l for l in children(tree,'label') if value(l[1])==net)
            label[0]='hierarchical_label';label.insert(2,['shape','bidirectional'])
        trees[name]=tree;promotions[name]=port_map
        new_maps[name]={'references':reference_map,'ports':port_map,'removed_power_flags':removed_flags,'namespace_index':index,
                        'source_folder':source.relative_to(ROOT).as_posix(),
                        'exact_source_pin_overrides':pin_overrides,
                        'exact_unused_functional_pin_dispositions':source_unused}
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
        if columns[col]>3260:raise ValueError('Actual top-level hierarchy exceeds declared source page')
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
    notes='ONE CUSTOM MOTHERBOARD / TWELVE ONBOARD MOTORS\nRetained original327 with exact reviewed power/FPGA corrections plus real peripheral sources. Hierarchy pages are functional regions, not separate PCBs.\nAnalog, communications, field terminals, status indicators and identity front end are integrated source circuits. Full-board routing, vendor fit and physical qualification are incomplete. NOT FOR MANUFACTURE.'
    top=f'(kicad_sch(version 20250114)(generator "motherboard_candidate")(uuid "{root_id}")(paper "User" 1189 3300)(lib_symbols)'
    top+='(title_block(title "One-board controller integrated circuit candidate")(date "2026-09-30")(rev "motherboard-r0.2-IS2"))'
    top+=f'(text {q(notes)}(at 20 20 0)(effects(font(size 1.35 1.35))(justify left top))(uuid "{uid("notes")}"))'+''.join(sheets+items)+'(sheet_instances(path "/"(page "1"))))'
    # Apply only the exact reviewed 64 former NC balls. Existing 96 GPIO, clock
    # and every non-FPGA retained physical net remain unchanged. Available real
    # endpoints are joined by hierarchy, never by constant-healthy substitutes.
    from hardware_apply_motherboard_fpga_allocation import apply_base_allocation, apply_slow_enable_allocation, rebuild_root_geometry
    retain(ROOT/'tools/hardware_apply_motherboard_fpga_allocation.py')
    proposal=json.loads(retain(ROOT/'hardware/motherboard/fpga-allocation-proposal.json').read_text(encoding='utf-8'))
    root,core,allocation=apply_base_allocation(parse(top),trees['fpga_core'],proposal,ET.parse(MC/'netlist.xml'))
    if 'motherboard_operator' in trees:
        retain(ROOT/'reports/motherboard-fpga-allocation-20260930/slow-enable-allocation.json')
        root,core,allocation=apply_slow_enable_allocation(root,core,allocation)
    trees['fpga_core']=core
    promotions['fpga_core']=dict(allocation['root_sheet_port_map'])
    retained_aliases=[]
    if 'motherboard_operator' in trees:retained_aliases.extend(('PROBE_FPGA','TOOLSETTER_FPGA'))
    if 'motherboard_safety_sensor' in trees:retained_aliases.append('PROTECTIVE_STATUS_FPGA')
    if retained_aliases:
        for net in retained_aliases:
            label=next(l for l in children(core,'label') if value(l[1])==net)
            label[0]='hierarchical_label';label.insert(2,['shape','input'])
            promotions['fpga_core'][net]='fpga_core/'+net
            row=next(r for r in allocation['semantic_alias_exports'] if r['old_local_label']==net)
            row.update(hierarchy_port=net,hierarchy_export_applied=True,
                scope='Retained physical FPGA ball bridged to actual ISO1212 fast probe output in parent')
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
    for net in ('OPI_REARM_TX','OPI_REARM_BOE','WD_REARM_M','WD_REARM_O'):
        labels=[l for l in children(trees['mc_permission'],'label') if value(l[1])==net]
        if not labels:raise ValueError('Retained passive fanout endpoint missing '+net)
        label=labels[0];label[0]='hierarchical_label';label.insert(2,['shape','bidirectional'])
        promotions['mc_permission'][net]='mc_permission/'+net
    if 'motherboard_safety_sensor' in trees:
        for net in ('EXT_PERMIT_3V3','PROCESS_PERMIT_EXT_3V3','PERMIT_OUT_DRIVE'):
            labels=[l for l in children(trees['mc_permission'],'label') if value(l[1])==net]
            if not labels:raise ValueError('Actual safety permission endpoint missing '+net)
            label=labels[0];label[0]='hierarchical_label';label.insert(2,['shape','bidirectional'])
            promotions['mc_permission'][net]='mc_permission/'+net
    rebuild_root_geometry(root,{**promotions,'_directions':allocation['desired_directions']})
    allocation['root_sheet_port_map']=promotions['fpga_core']
    from hardware_apply_motherboard_fpga_allocation import apply_obsolete_home_deallocation
    home_receipt_path=retain(ROOT/'reports/motherboard-fpga-source-20260930/home-deallocation-r01/receipt.json')
    home_receipt=json.loads(home_receipt_path.read_text(encoding='utf-8'))
    root,core,allocation=apply_obsolete_home_deallocation(root,core,allocation,
        ET.parse(MC/'netlist.xml'),home_receipt['CAD23_copper_evidence'])
    from hardware_apply_motherboard_fpga_allocation import apply_reserved_health_reconciliation
    health_review=ROOT/'reports/motherboard-fpga-source-20260930/reserved-health-reconciliation-r01'
    retain(health_review/'receipt.json')
    health_copper=json.loads(retain(health_review/'copper-zero-evidence.json').read_text(encoding='utf8'))
    root,core,allocation=apply_reserved_health_reconciliation(root,core,allocation,
        ET.parse(retain(health_review/'inputs/netlist.xml')),health_copper)
    promotions['fpga_core']=dict(allocation['root_sheet_port_map'])
    trees['fpga_core']=core
    status_unused=[r for r in unused_ledger if r['source_block']=='fpga_core']
    if len(status_unused)!=7:raise ValueError('Exact obsolete seven status inputs required')
    allocation.update(assigned_user_pins=135,free_user_gpio=48,deallocated_user_pin_count=28,
        obsolete_machine_status_pin_rename_ledger=status_unused,
        obsolete_machine_status_functions_observed_via='all24 generalDI/IOL1; seven former dedicatedGPIO are actualNC',
        exact_unused_functional_pin_dispositions=unused_ledger)
    from hardware_apply_motherboard_fpga_allocation import reconcile_current_allocation_annotations
    core,allocation=reconcile_current_allocation_annotations(core,allocation)
    trees['fpga_core']=core
    allocation['native_export_verified']=False
    home_balls={r['pin'] for r in allocation['home_deallocation_pin_rename_ledger']}
    reserved_balls={r['pin'] for r in allocation['reserved_health_pin_rename_ledger']}
    deallocated=home_balls | {r['pin'] for r in allocation['reserved_health_pin_rename_ledger']
                            if r['reason']!='required_existing_qualified_rail_bridge'}
    # Preserve all66 original NC promotions as the first bounded source
    # transaction. The later nine NC reversals and real P4 bridge are a
    # separate transaction on ten of those same balls, not missing promotions.
    promoted_ledger=allocation['exact_pin_rename_ledger'][:allocation['promoted_nc_pin_count']]
    if len(promoted_ledger)!=66 or not all(r['old_native_net'].startswith('unconnected-(U1001-') for r in promoted_ledger):
        raise ValueError('Exact original66 promotion transaction missing')
    for item in allocation['exact_pin_rename_ledger']:
        parts['U1001']['pins'][item['pin']]=None if item['pin'] in deallocated else item['signal']
    final_native={r['pin']:r['new_native_net'] for r in allocation['exact_pin_rename_ledger']}
    parts['U1001']['exact_fpga_nc_promotion_native_nets']={r['pin']:final_native[r['pin']] for r in promoted_ledger}
    write_json(OUT/'fpga-allocation-parent.json',allocation)
    write_json(OUT/'fpga-allocation-applied.json',{**allocation,
        'canonical_parent_metadata':'fpga-allocation-parent.json',
        'scope_note':'Current metadata alias; archived older applied-source receipts remain historical and unchanged.'})
    (OUT/'motherboard.kicad_sch').write_text(dump(root)+'\n',encoding='utf-8')
    for name in ('fpga_core','mc_local_power','watchdog_conditioning','mc_permission'):
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
        'fpga_nc_promotions_applied':allocation['promoted_nc_pin_count'],'fpga_vendor_fit':False})
    write_json(OUT/'assembly-map.json',{'schema_version':1,'manufacturing_ready':False,'retained_mc_parts':327,
        'retained_native_pin_nets':{r+'.'+p:n for (r,p),n in old_nodes.items() if r in model['components']},
        'input_sha256':inputs,'blocks':new_maps,'sheet_ports':promotions,'builder_sha256':sha(Path(__file__)),
        'native_net_renames_allowed':promoted_ledger,'physical_parts':len(parts),
        'native_home_nc_deallocations_allowed':allocation['home_deallocation_pin_rename_ledger'],
        'native_reserved_health_reconciliation_allowed':allocation['reserved_health_pin_rename_ledger'],
        'native_unused_functional_dispositions_allowed':unused_ledger,
        'reviewed_power_delta':power_delta})
    write_json(OUT/'source-footprint-updates.json',{'schema_version':1,'updates':footprint_updates,
        'basis':'Only exact prior generated copies may update to the reviewed child-source footprint; no user edits or retained MC geometry replaced.'})
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','Status','DNP','Scope'])
        for ref,c in parts.items():w.writerow([ref,c['value'],c.get('mpn',''),c.get('footprint',''),c.get('status','candidate_not_qualified'),str(bool(c.get('dnp',False))).lower(),'actual_on_motherboard_component_candidate'])
    if any(sha(ROOT/p)!=h for p,h in inputs.items()):raise ValueError('Source changed during motherboard integration')
    print(json.dumps({'physical_parts':len(parts),'retained_mc_parts':327,'schematic':str(OUT/'motherboard.kicad_sch'),
                      'exact_fpga_nc_promotions':allocation['promoted_nc_pin_count'],'manufacturing_ready':False}))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path)
    build(parser.parse_args().out)
