"""Source-derived package allocation proposal; never changes schematic/PCB/RTL."""
from __future__ import annotations
import collections
import csv
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = pathlib.Path(__file__).resolve().parent
OUTPUT = ROOT / 'hardware/motherboard/fpga-allocation-proposal.json'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))

spec = importlib.util.spec_from_file_location('independent_package_reader', ROOT / 'tools/hardware_validate_fpga_core.py')
package_reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package_reader)
pins = package_reader.primary_pins()
for p in load('research/fpga-core/pins-official.json'):
    assert all(p[k]==pins[p['ball']][k] for k in ('name','bank','config','row'))
    pins[p['ball']].update({k:p[k] for k in ('lvds','ddio','clock_region')})
previous = load('hardware/fpga_core/pin-allocation.json')
contract = load('hardware/motherboard/requirements.json')
assembly = load('hardware/motion_card/assembly-map.json')
model = load('hardware/fpga_core/design.json')

# Canonical logical functions may keep the old physical net label until the root
# applies its explicit rename ledger. These aliases do not add a second pad.
aliases = dict(assembly['aliases']['fpga_core'])
aliases.update({'HOST_SPI_CS_N':'HOST_SPI_CS_FB_N', 'PROBE_FPGA':'PRB0_FPGA',
                'TOOLSETTER_FPGA':'PRB1_FPGA', 'PROTECTIVE_STATUS_FPGA':'EXT_PERMIT_FPGA',
                'HW_WATCHDOG_OK_N':'RAW_INHIBIT_N'})

inventory = {}
def add(signal, direction, group, function, provenance, optional=False, full_feature=False):
    assert signal not in inventory, signal
    inventory[signal] = dict(signal=signal, direction=direction, group=group, function=function,
        provenance=provenance, optional=optional, prefer_ordinary_gpio=full_feature,
        external_voltage_domain='IO_3V3 internal logic only; protected/isolated field front end required')

for f in contract['functional_requirements']:
    for signal in f['fpga_signals']:
        direction = 'output' if signal.startswith(('STEP','DIR','PWM','PEN','ARM_LAMP')) or re.fullmatch(r'EN\d+_N_FPGA',signal) else 'input'
        rows = [r for r in contract['terminal_function_mapping'] if r['resource'].get('signal') == signal]
        add(signal,direction,f['id'],f['function'],[r['source_pointer'] for r in rows],
            optional=f['id']=='MB-ENCODER-GROWTH', full_feature=f['id']!='MB-ENCODER-GROWTH')

for n, name in enumerate(('DIC','DOA','DOB','ACC')):
    for suffix, direction in [('SCLK','output'),('MOSI','output'),('MISO','input'),('CS_N','output')]:
        add(f'IOL1_L{n}_{suffix}',direction,'base_iol1',f'Local soldered {name} controller IOL1; identity/CRC/age validated',
            ['IS-1 01 section 4; IS-2 logical-controller inheritance'])
for name, group, optional in [('FAST','base_fast_status',False),('EX8','optional_encoder_status',True),('HEALTH','onboard_health',False)]:
    for suffix, direction in [('SR_CLK','output'),('SR_LOAD_N','output'),('SR_DATA','input')]:
        add(f'{name}_{suffix}',direction,group,
            'Input-only measured status, marker plus double-read agreement; never an output command',
            ['IS-1 01 section 4.10; IS-2 onboard-health semantic delta'],optional)
for suffix,direction in [('SCLK','input'),('MOSI','input'),('MISO','output'),('CS_FB_N','input'),('CS_CMD_N','input')]:
    add('HOST_SPI_'+suffix,direction,'host_dual_cs','CNF3/CNS3 independent chip-select transport',
        ['IS-1 01 D01-1 and sections 3/5'],full_feature=True)

support_groups = [
 ('physical_health',[
  ('MOTION_A_PGOOD','input','Measured bank-A supply/receiver health; removes obsolete MIA connector contacts only'),
  ('MOTION_B_PGOOD','input','Measured bank-B supply/receiver health; all twelve motors fitted'),
  ('TAMPER_CLEAR_N','input','Real latch aggregate for installed commodity/accessory changes and qualified domain failures; no constant true'),
  ('RAILS_OK_FPGA','input','Actual qualified core/IO supply supervisor readback')]),
 ('output_path_integrity',[
  ('OPI_OK_TX','input','Latch observes the actual TX_PERMIT gate'),
  ('OPI_OK_A','input','Latch observes actual bank-A qualified output path'),
  ('OPI_OK_B','input','Latch observes actual bank-B qualified output path'),
  ('OPI_REARM_M','output','Deliberate rearm strobe, only during valid ARM'),
  ('OPI_OK_BOE','input','Latch observes actual bank-B buffer OE transition'),
  ('OPI_OK_OUT','input','Latch observes actual OUT_PERMIT gate'),
  ('OPI_REARM_O','output','Deliberate rearm strobe, only during valid IO_ENABLE')]),
 ('future_standard_accessory',[
  ('XS_SCLK','output','Reserved standardized accessory link clock'),
  ('XS_MOSI','output','Reserved standardized accessory link request'),
  ('XS_MISO','input','Reserved standardized accessory link reply'),
  ('XS_CS_N','output','Reserved standardized accessory link select'),
  ('XS_SYNC_STROBE','output','Reserved accessory timing synchronization'),
  ('XS_REFCLK','output','Reserved accessory clock; timing not qualified')]),
 ('motion_output_watchdogs',[
  ('FPGA_PROGRESS_M','output','Progress only after accepted valid motion UPDATE'),
  ('FPGA_PROGRESS_O','output','Progress only after accepted valid output command'),
  ('FPGA_MOTION_REQUEST','output','Hardware motion latch/set request'),
  ('FPGA_OUTPUT_REQUEST','output','Hardware output latch/set request'),
  ('FPGA_ENDPOINT_READY','output','Qualified runtime endpoint ready')]),
 ('permission_readback',[
  ('WD_M_OK','input','Independent motion watchdog actual readback'),
  ('WD_O_OK','input','Independent output watchdog actual readback'),
  ('TX_PERMIT','input','Actual final hardware motion permission readback'),
  ('OUT_PERMIT','input','Actual final hardware output permission readback'),
  ('PROC_PERMIT','input','Actual final hardware process permission readback'),
  ('RAW_INHIBIT_N','input','Actual asynchronous hardware inhibit; omitted from old 175-pin sum')]),
 ('watchdog_latched_faults',[
  ('WATCHDOG_TRIP_M','input','Independent motion watchdog-trip latch'),
  ('WATCHDOG_TRIP_O','input','Independent output watchdog-trip latch'),
  ('WATCHDOG_TRIP_CLEAR','output','Explicit disarmed clear/test request; no automatic rearm')]),
 ('clock_reset',[
  ('FPGA_CLK_50M','input','Existing oscillator clock into global clock-capable H3'),
  ('FPGA_USER_RESET_N','input','Qualified user reset; dedicated CRESET_N is separate')]),
 ('critical_fault_indication',[
  ('FPGA_LINK_FAULT','output','Existing critical fault observation output'),
  ('FPGA_WATCHDOG_FAULT','output','Existing critical fault observation output'),
  ('FPGA_INHIBIT_FAULT','output','Existing critical fault observation output'),
  ('FPGA_TIMING_FAULT','output','Existing critical fault observation output')]),
 ('permission_contact_request',[
  ('PERMIT_OUT_REQ','output','Independent machine permission-contact request; held low during watchdog selftest')])
]
for group, rows in support_groups:
    for signal,direction,function in rows:
        add(signal,direction,group,function,['IS-1 spec/modules.json#fpga_pin_budget; 04 sections 4/5/6; IS-2 topology delta'],
            full_feature=group not in ('physical_health','future_standard_accessory'))

assert len(inventory)==169,len(inventory)
assert sum(not r['optional'] for r in inventory.values())==142

historical = {}
existing = {}
for row in previous['user_allocations']:
    old = row['net']; signal = aliases.get(old,old)
    if signal not in inventory:
        historical[signal] = dict(signal=signal,direction='input',group='historical_extra_pad_reservation',
            function='Historical HOME/machine/debug input pad reservation; not additional required IS-2 field circuitry',
            provenance=['hardware/fpga_core/pin-allocation.json'],optional=False,prefer_ordinary_gpio=True,
            external_voltage_domain='Internal IO_3V3 only; no additional field circuitry proved')
    existing[signal] = dict(ball=row['ball'],physical_net=old,allocation_state='existing_ball_preserved')
existing['FPGA_CLK_50M'] = dict(ball='H3',physical_net='FPGA_CLK_50M',allocation_state='existing_ball_preserved')
assert len(historical)==19
all_inventory = inventory | historical

gpio = {b:r for b,r in pins.items() if r['name'].startswith('GPIO')}
reserved = {b:dict(r,physical_net=previous['pin_net'][b]) for b,r in gpio.items()
            if b in previous['pin_net'] and b not in {x['ball'] for x in existing.values()}}
assert len(gpio)==195 and len(reserved)==12
available = set(gpio)-set(reserved)
assert len(available)==183
nc_gpio = [r for r in previous['unconnected'] if r['ball'] in available]
assert len(nc_gpio)==86

def decorate(signal,placement):
    source = all_inventory[signal]; pin = pins[placement['ball']]
    lvds = bool(pin['lvds'])
    return dict(source,**placement,manufacturer_pin=pin['name'],bank=pin['bank'],worksheet_row=pin['row'],
        manufacturer_configuration_function=pin['config'],manufacturer_lvds_resource=pin['lvds'],
        clock_region=pin['clock_region'],vccio_net='IO_3V3',vccio_nominal_v=3.3,
        io_standard='3.3_V_LVCMOS',mode='LVDS_as_GPIO' if lvds else 'ordinary_GPIO',
        gpio_options=dict(ddio=False,schmitt=False if lvds else source['direction']=='input',
            internal_pulldown=False,drive_strength_selectable=not lvds,slew_selectable=not lvds),
        pin_provenance='T20-PINOUT v3.5, T20F256 worksheet row '+str(pin['row']),
        boot_safe_requirement='Independent unconfigured/reset permission cuts and external receiver defaults; never rely on GPIO pull state',
        vendor_fit=False,implemented_in_parent_cad=False,implemented_full_gateware=False)

def allocate(optional,repurpose):
    wanted = {n:r for n,r in inventory.items() if optional or not r['optional']}
    e = {n:dict(r) for n,r in existing.items()}
    rename = []
    for old,new in repurpose.items():
        p=e.pop(old); e[new]=dict(p,physical_net=new,previous_physical_net=p['physical_net'],
            allocation_state='proposed_existing_pad_repurpose')
        rename.append(dict(ball=p['ball'],old_logical_signal=old,new_logical_signal=new,
            old_physical_net=p['physical_net'],reason='Legacy separate input can use existing 24 DI service; no IS-2 base function removed'))
    # Existing extra pads remain reserved. Three frozen terminal aliases merely
    # reconcile the logical function at the same physical pad.
    wanted |= {n:all_inventory[n] for n in e if n not in wanted}
    missing = [n for n in wanted if n not in e]
    normal = sorted([r for r in nc_gpio if not r['lvds']],key=lambda r:r['row'])
    lvds_a = sorted([r for r in nc_gpio if r['lvds'] and r['bank']=='BANK4A'],key=lambda r:r['row'])
    lvds_b = sorted([r for r in nc_gpio if r['lvds'] and r['bank']=='BANK4B'],key=lambda r:r['row'])
    # Prioritize all necessary outputs and precision/base inputs onto ordinary
    # GPIO. LVDS GPIO carries additional fully buffered status or optional ABZ.
    priority = lambda n:(0 if wanted[n]['direction']=='output' else 1,
                         0 if wanted[n]['prefer_ordinary_gpio'] else 1,
                         1 if wanted[n]['optional'] else 0,n)
    missing.sort(key=priority)
    overflow=[]
    for n in missing:
        d=wanted[n]['direction'];choice=None
        if normal:choice=normal.pop(0)
        elif d=='input' and lvds_a:choice=lvds_a.pop(0)
        elif lvds_b:
            # At most sixteen B-bank outputs/bidirectionals under datasheet
            # recommendation, even if a later wanted list changes directions.
            used=sum(x['direction'] in ('output','bidirectional') and x['bank']=='BANK4B'
                     for k,p in e.items() for x in [dict(wanted[k],bank=pins[p['ball']]['bank'])])
            if d=='input' or used<16:choice=lvds_b.pop(0)
            elif lvds_a:
                used_a=sum(wanted[k]['direction'] in ('output','bidirectional') and pins[p['ball']]['bank']=='BANK4A' for k,p in e.items())
                if used_a<16:choice=lvds_a.pop(0)
        elif d=='input' and lvds_a:choice=lvds_a.pop(0)
        if choice:
            e[n]=dict(ball=choice['ball'],physical_net=n,allocation_state='proposed_NC_to_named_signal')
        else:overflow.append(n)
    rows=[decorate(n,p) for n,p in e.items()]
    rows.sort(key=lambda r:r['worksheet_row'])
    unused=sorted(available-{r['ball'] for r in rows})
    return dict(required_with_retained_historical=len(wanted),assigned=len(rows),unassigned=overflow,
        source_package_capacity_pass=not overflow,unused_gpio_balls=unused,
        existing_ball_repurposes=rename,signals=rows,
        summary=dict(ordinary_gpio=sum(r['mode']=='ordinary_GPIO' for r in rows),
            lvds_gpio=sum(r['mode']=='LVDS_as_GPIO' for r in rows),
            lvds_output_count_by_bank={bank:sum(r['bank']==bank and r['direction'] in ('output','bidirectional') for r in rows)
                for bank in ('BANK4A','BANK4B')},
            promoted_NC_balls=sum(r['allocation_state']=='proposed_NC_to_named_signal' for r in rows)))

reuse={'SPARE_FPGA':'HOST_SPI_CS_CMD_N','SPINDLE_FAULT_FPGA':'PERMIT_OUT_REQ',
       'SPINDLE_READY_FPGA':'FPGA_OUTPUT_REQUEST','LUBE_STATUS_FPGA':'FPGA_PROGRESS_O',
       'CYCLE_START_FPGA':'OPI_REARM_O'}
candidates = dict(base_preserve_all_current=allocate(False,{}),
    full_preserve_all_current=allocate(True,{}), full_with_five_legacy_repurposes=allocate(True,reuse))
print({k:(v['assigned'],v['required_with_retained_historical'],v['unassigned']) for k,v in candidates.items()})
assert candidates['base_preserve_all_current']['assigned']==161
assert candidates['full_preserve_all_current']['required_with_retained_historical']==188
assert candidates['full_with_five_legacy_repurposes']['assigned']==183

delta = [
 dict(old_group='MIA PRESENT_A/B',old_pins=2,new_pins=0,reason='Soldered motor region has no removable custom card or presence contacts; actual MOTION_A_PGOOD remains'),
 dict(old_group='MX4 PRESENT_A/B + MOD_ID0-2',old_pins=5,new_pins=0,reason='All twelve channels soldered and fully fitted; no MX4 connector or removable custom motor-card identity exists'),
 dict(old_group='MIA PGOOD / EXP_PGOOD',old_pins=2,new_pins=2,reason='Renamed measured MOTION_A/B_PGOOD; hardware domain faults and OPI remain real'),
 dict(old_group='MX4 TAMPER_N',old_pins=1,new_pins=1,reason='Real global hardware interruption/tamper aggregate; must include actual replaceable/accessory domains and rails; never tie true'),
 dict(old_group='MC SSR',old_pins=3,new_pins=3,reason='Measured onboard-health/commodity-presence shift register, versioned replacement for nonexistent rack-card status'),
 dict(old_group='RAW_INHIBIT_N',old_pins=0,new_pins=1,reason='Mandatory current A2 asynchronous inhibit readback was omitted from the old 175-pin arithmetic'),
 dict(old_group='all remaining inherited groups',old_pins=162,new_pins=162,reason='Preserved direct fields, serial data/diagnostics, watchdogs, OPI, dual host CS, clock/reset, faults and accessory resources')
]

health_layout = [
 'FAST_5V_PGOOD','FAST_SUPPLY_FAULT_LATCH','DI_LOGIC_PGOOD','DI_FIELD_PGOOD',
 'DOA_LOGIC_PGOOD','DOA_FIELD_PGOOD','DOB_LOGIC_PGOOD','DOB_FIELD_PGOOD',
 'ANALOG_LOGIC_PGOOD','ANALOG_FIELD_PGOOD','ESP_PRESENT_MEASURED','ESP_PGOOD',
 'COMPUTE_PRESENT_A','COMPUTE_PRESENT_B','COMPUTE_5V_PGOOD','SETTINGS_PRESENT_A','SETTINGS_PRESENT_B',
 'ACCESSORY_PRESENT_A','ACCESSORY_PRESENT_B','ACCESSORY_PGOOD','CORE_ENTRY_PGOOD','FIELD_A_ENTRY_PGOOD',
 'FIELD_B_ENTRY_PGOOD','MOTION_A_PGOOD','MOTION_B_PGOOD','RAILS_OK','TAMPER_CLEAR_N',
 'DI_HEALTH_QUALIFIED','DOA_HEALTH_QUALIFIED','DOB_HEALTH_QUALIFIED','ANALOG_HEALTH_QUALIFIED']
nonfpga = [
 dict(function='24 DI, 16 smart DO, 4 AI, 2 AO and smart-switch ADC/current/fault diagnostics',destination='Four soldered local IOL1 controllers L0-L3',fpga_gpio_added=0,evidence='Existing 16 IOL1 paths carry these fields; controller circuits/firmware remain to implement; no hidden per-channel GPIO assumption'),
 dict(function='Power INA238 entry monitor, identity EEPROM, settings storage, temperature/diagnostic records',destination='Compute host I2C and local controller serial telemetry',fpga_gpio_added=0,evidence='Inherited host resources retained; measured health faults also feed hardware/HEALTH_SR, with no fabricated IDs'),
 dict(function='RS485 / CAN',destination='Compute UART / separate host SPI CAN controller; isolated field transceivers',fpga_gpio_added=0,evidence='Frozen XB1/XB2 host resource map, outside precision motion SPI'),
 dict(function='ESP service / compute selector / boot storage / display / USB / Ethernet',destination='Commodity compute and replaceable ESP interfaces',fpga_gpio_added=0,evidence='Not FPGA motion resources; exact module profile electrical/boot routes still unqualified'),
 dict(function='Seven RGB = 21 emitters, 24 DI + 16 DO + 12 ALM = 52 single emitters; separate WDT',destination='Dedicated LED driver bus on service ESP/compute I2C, independent hardware fault override',fpga_gpio_added=0,evidence='Explicit engineering candidate, LED drivers/override circuits not fitted or qualified. The four retained FPGA fault outputs and real hardware inhibit/watchdog/power nets supply critical observations. Ordinary DI/ALM LEDs may observe qualified receivers; actual DO observations require valid diagnostics. No direct 73-GPIO assumption and no source-complete claim'),
]

files=['hardware/fpga_core/pin-allocation.json','hardware/fpga_core/design.json','hardware/fpga_core/netlist.xml',
 'hardware/motion_card/assembly-map.json','hardware/motherboard/requirements.json','hardware/mc_permission/design.json',
 'research/fpga-core/pins-official.json','research/fpga-core/t20-pinout.xlsx','research/fpga-core/an006.pdf',
 'research/fpga-core/trion20-ds-v6.0.pdf','docs/MOTHERBOARD_IS2.md','docs/STATUS_INDICATORS.md',
 'reports/motherboard-is2-contract-20260930/inputs/spec/modules.json',
 'reports/motherboard-is2-contract-20260930/inputs/docs/interface-spec/01-protocol-and-schedule.md',
 'reports/motherboard-is2-contract-20260930/inputs/docs/interface-spec/04-safety-power-timing.md',
 'gateware/rtl/cnc_endpoint.v']
frozen=REPORT/'inputs';frozen.mkdir(exist_ok=True)
hashes={}
for n in files:
    p=ROOT/n;h=digest(p);hashes[n]=h
    dest=frozen/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    assert digest(dest)==h

proposal = dict(schema_version=1,revision='motherboard-fpga-allocation-proposal-r01',date='2026-09-30',
 status='source_reviewed_candidate_not_applied_to_CAD_or_vendor_fitted',package='T20F256I4',
 manufacturing_ready=False,vendor_fit=False,physical_qualification=False,
 inherited_contract='MOTHERBOARD-IS2-20260930',source_sha256=hashes,
 package_count=dict(gpio_advertised=195,ordinary_gpio=141,lvds_as_gpio=54,
    reserved_dual_purpose_gpio=12,user_function_gpio_including_clock=183,
    current_user_allocations=96,current_50mhz_clock=1,current_unconnected_user_gpio=86,
    reserved_non_gpio_ref_res=1,base_direct_fields=77,base_iol1_fast_status=19,
    optional_abz_fields=24,optional_abz_status=3,
    old_IS1_usable_claim=189,old_IS1_full_feature_claim=137,
    actual_ordinary_user_gpio_including_clock=129,
    old_claim_correction='The exact workbook plus currently wired configuration reservations supersede generic IS-1 arithmetic; six omitted reserved pads reduce 189 to 183. The worksheet has 141 ordinary GPIO plus 54 LVDS GPIO, not 143 plus 52.'),
 alias_reconciliation=[dict(old_physical_net=k,logical_signal=v,
    evidence='Current MC assembly alias or explicit frozen terminal codex_net/ball; exact same pad, no second GPIO')
    for k,v in aliases.items()],
 reserved_gpio_balls=reserved,semantic_topology_delta=delta,required_signal_inventory=list(inventory.values()),
 historical_extra_pad_inventory=list(historical.values()),candidates=candidates,
 health_register_candidate=dict(wires=['HEALTH_SR_CLK','HEALTH_SR_LOAD_N','HEALTH_SR_DATA'],
    length_bits=40,measured_bits={str(i):s for i,s in enumerate(health_layout)},
    unused_positions=list(range(len(health_layout),36)),marker_positions={'36':0,'37':1,'38':0,'39':1},
    marker_numeric=10,marker_packing='Bits39..36 as MSB..LSB = 0b1010; serial bit order must be checked against the physical register chain',
    validity='Marker and double-read agreement; explicit versioned service/ABI delta required. Missing monitored source remains invalid/inhibited, never a tied healthy bit.',
    gate_path='Necessary rail/interruption/DI health terms cut permission directly in hardware as well; shift-register data is diagnostic, never sole 20 ms inhibit path',
    implemented=False),
 non_fpga_resources=nonfpga,
 source_review_constraints=dict(all_user_vccio_v=3.3,no_native_lvds=True,ref_res='R2 remains NC under DS table123',
    fpga_core_v=1.2,bank4_only_v=3.3,lvds_gpio_output_recommendation_per_bank=16,
    lvds_ddio=False,lvds_schmitt=False,lvds_internal_pulldown=False,
    lvds_variable_drive=False,lvds_variable_slew=False,
    lvds_boot='Tri-state without internal pull; external defaults and independent output permission required',
    native_lvds_mixing='None used; two-unused-pair rule would consume resources if native LVDS introduced later',
    signal_integrity='No native fit/timing, IBIS, capacitive-load or physical noise qualification; source direction counts alone cannot prove edge-rate/return-path behavior'),
 remaining_engineering_gates=[
    'Root must choose the base or full optional allocation and apply exact native schematic/PCB/net/pin/driver/RTL rename ledger; proposal changes none of them.',
    'Full optional candidate reuses five legacy non-IS2-specific pads and consumes every user GPIO; preserving all legacy pads plus all optional resources is five pins over.',
    'HOST/ESP LED bus and independent fault override are explicit destinations but lack selected/fitted drivers; moving LED control onto the FPGA would add required pins and consume retained legacy reservations.',
    'Measured onboard health layout, hardware permission filters/latches, authentic identity records and absent-module defaults require actual circuits and software; no simulated card identity or healthy constants.',
    'Full twelve-channel CNF3/CNS3/IOL1/optional encoders gateware is not the current six-channel/two-encoder CNC1 historical RTL.',
    'Efinity installation/device database/license and real interface design for T20F256I4 required before package legality, place-and-route timing and bitstream proof.',
    'All-bank power/decoupling/SSO and LVDS fixed-edge SI must be validated with real bank loads, IBIS and a physical prototype.',
    '20 ms fault-to-inhibit is a circuit/target measurement obligation, not a pin allocation result.'
 ],hard_conclusion='Current T20F256 can support the standard base in a source-reviewed candidate while preserving all current allocated balls. Full inherited optional resources fit only after five explicit legacy-pad reuses (or release other unrequired historical reservations). No package change is forced by pin arithmetic; actual resource/timing fit remains unproved.')

OUTPUT.write_text(json.dumps(proposal,indent=2)+'\n',encoding='utf-8')
for name,c in candidates.items():
    with (REPORT/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
        keys=['signal','ball','bank','manufacturer_pin','vccio_nominal_v','direction','group','mode','allocation_state','physical_net','worksheet_row','function','pin_provenance']
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(c['signals'])
(REPORT/'input-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUTPUT),'inventory':len(inventory),'historical_extra':len(historical),
    'candidates':{n:{'required':c['required_with_retained_historical'],'assigned':c['assigned'],
       'unassigned':c['unassigned'],'summary':c['summary'],'unused':len(c['unused_gpio_balls'])} for n,c in candidates.items()}},indent=2))
