"""Bounded two-ball addition; no parent, RTL or PCB edits."""
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_package_reader',ROOT/'tools/hardware_validate_fpga_core.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
official=reader.primary_pins()
proposal=json.loads((ROOT/'hardware/motherboard/fpga-allocation-proposal.json').read_text(encoding='utf8'))
base=proposal['candidates']['base_preserve_all_current']
xml=ET.parse(ROOT/'hardware/motherboard/netlist.xml')
nodes={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'] for net in xml.findall('.//nets/net')for n in net.findall('node')}
signals=[]
for signal,ball,name,row in [('FAST_PORTS_ENABLE','M4','GPIOB_TXP00',192),('XF_POWER_ENABLE','M6','GPIOB_TXP05',197)]:
    assert ball in base['unused_gpio_balls']
    assert not any(r['ball']==ball for r in base['signals'])
    pin=official[ball]
    assert (pin['name'],pin['bank'],pin['config'],pin['row'])==(name,'BANK4B','',row),pin
    old='unconnected-(U1001-'+name+'-Pad'+ball+')'
    assert nodes['U1001',ball]==old
    signals.append(dict(signal=signal,reference='U1001',ball=ball,manufacturer_pin=name,
                        bank='BANK4B',worksheet='T20F256',worksheet_row=row,direction='output',
                        mode='LVDS_resource_as_single_ended_GPIO',io_standard='3.3_V_LVCMOS',
                        vccio_net='IO_3V3',vccio_nominal_v=3.3,
                        old_native_net=old,new_native_net='/fpga_core/'+signal,
                        external_low_default_ohm=4700,external_low_default_tolerance_percent=1,
                        source_implemented=False,pcb_implemented=False,gateware_implemented=False,
                        vendor_fit=False,timing_qualified=False))

rpmax=4700*1.01;rpu=27000;vmax=3.47;leakage_budget=20e-6
weakpull=(vmax/rpu+leakage_budget)/(1/rpu+1/rpmax)
reset=leakage_budget*rpmax
assert weakpull<.8 and reset<.8
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(schema_version=1,revision='motherboard-slow-enable-addition-r01',date='2026-09-30',
    status='datasheet_reviewed_candidate_adopted_by_root; native_source_and_vendor_fit_pending',
    original_allocation_unchanged=True,promoted_existing_free_nc_balls=2,
    base_assigned_with_addition=163,base_remaining_free_gpio=20,signals=signals,
    exact_primary_inputs=dict(
        datasheet_url='https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf',
        datasheet_local='sources/trion20-ds-v6.0.pdf',datasheet_sha256=sha(REPORT/'sources/trion20-ds-v6.0.pdf'),
        pinout_workbook='inputs/research/fpga-core/t20-pinout.xlsx',
        pinout_workbook_sha256=sha(REPORT/'inputs/research/fpga-core/t20-pinout.xlsx'),
        live_native_xml_sha256=sha(ROOT/'hardware/motherboard/netlist.xml'),
        reviewed_rendered_pages=['sources/slow-enable-primary-p14.png','sources/slow-enable-primary-p23.png',
                                 'sources/slow-enable-primary-p59.png','sources/slow-enable-primary-p86.png']),
    primary_electrical_review=dict(
        table_76_printed_page=59,applicability='W80/Q100F3/Q144/F169/F256 DC section',
        lvcmos_input=dict(vil_min_v=-.3,vil_max_v=.8,vih_min_v=2,vih_max='VCCIO+0.3'),
        lvcmos_output=dict(vol_max_v=.2,voh_min='VCCIO-0.2'),
        lvttl_output_not_selected=dict(vol_max_v=.4,voh_min_v=2.4),
        table_77_caution='Drive figures are typical at 25 C, nominal supply and TT process; no guaranteed drive-current inference.',
        table_78=dict(input_leakage_uA=10,tristate_output_leakage_uA=10),
        table_79=dict(internal_weak_pullup_min_ohm=27000,typ_ohm=40000,max_ohm=65000),
        table_129_printed_page=86,
        reset='Input tri-state with NO weak pull-up or pull-down while CRESET_N is LOW.',
        unconfigured='Input tri-state with NO weak pull-up or pull-down while CRESET_N is HIGH and CDONE is LOW.',
        unused_user_mode='Input tri-state with weak pull-up by default.',
        page_86_footnotes='34 affects ordinary GPIO pull-down selection; 35/36 concern CSO/NSTATUS, not M4/M6.',
        page_14_features='No LVDS-resource GPIO DDIO, Schmitt or pulldown; adjustable drive and slew are unavailable in F256.',
        page_14_output_budget='Recommended <=16 output/bidirectional LVDS-resource GPIO per bank. This addition uses two.',
        page_23_separation='At least two unused LVDS pairs between GPIO and native LVDS when mixing. No native LVDS mode used here.'),
    low_default_calculation=dict(
        engineering_assumption='At most 20 uA aggregate upward leakage, including FPGA plus external receiving gate.',
        external_gate_leakage_budget_uA=10,fpga_leakage_uA=10,
        resistance_max_ohm=rpmax,vccio_max_v=vmax,
        reset_unconfigured_no_internal_pull_worst_v=reset,
        unused_user_mode_weakpull_worst_v=weakpull,
        reference_low_limit_v=.8,external_gate_threshold_and_leakage_must_be_checked=True,
        high_output_nominal_pulldown_load_mA=3.3/4700*1000,
        high_output_worst_min_resistor_load_mA=vmax/(4700*.99)*1000,
        no_output_frequency_or_loaded_drive_guarantee=True),
    required_independent_gates=[
        'Qualified CDONE/configuration state and actual IO supply supervision must force power enables OFF independently of FPGA application state.',
        'FAST_PORTS_ENABLE requests protected base encoder/MPG power only after actual board qualification.',
        'XF power requires BOTH controls and the actual XF-present Schmitt output; no simulated presence or constant HIGH.',
        'Independent gate output and load-switch input must default LOW with all compute/ESP modules missing.',
        'No selector, status scan, LED command or service module may bypass this hardware AND.'],
    bounded_deviation='Two slow power-enable requests use manufacturer-supported 3.3 V LVDS-resource GPIO instead of the prior ordinary-output preference. All previous balls and functions remain untouched.',
    remaining=['Parent schematic/pin-map/PCB exact two-pin reconciliation and source tests.',
               '14xxx actual default-off qualifier AND and load-switch circuit review.',
               'Native Efinity interface fit, synthesis/timing/bitstream and full final RTL.',
               'Physical loaded HIGH/LOW, power-ramp/reset/unconfigured and absent-module output measurements.'],
    manufacturing_ready=False,physical_validation=False)
(REPORT/'slow-enable-allocation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(signals=signals,weakpull_worst_v=weakpull,reset_worst_v=reset),indent=2))
