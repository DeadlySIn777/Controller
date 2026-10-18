"""Source-specific critical routing inventory; never an autorouter allowlist.

Differential/clock/precision classes remain outside the ordinary route manifest.
No generic impedance width, power-current rating or unmeasured timing is invented.
"""
import argparse, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('source','adoption','out'):ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.out=a.out.resolve();assert not a.out.exists();ad=json.loads(a.adoption.read_text());assert ad['passed']and ad['adopted']
 for name,h in ad['source_hashes'].items():assert sha(a.source/name)==h,name
 model=json.loads((a.source/'design.json').read_text());parts=model['components'];t=ET.parse(a.source/'netlist.xml')
 native={n.attrib['name']:[dict(reference=p.attrib['ref'],pin=p.attrib['pin'],function=p.attrib.get('pinfunction',''),type=p.attrib.get('pintype',''),mpn=parts[p.attrib['ref']]['mpn'])for p in n.findall('node')if p.attrib['ref']in parts]for n in t.findall('.//nets/net')}
 bypin={(v['reference'],v['pin']):n for n,vs in native.items()for v in vs}
 groups=[];selected=set()
 def group(name,names,domain,voltage,constraints):
  assert names and all(n in native and len(native[n])>=2 for n in names),name
  selected.update(names);groups.append(dict(name=name,return_domain=domain,maximum_nominal_signal_voltage_v=voltage,
   actual_nets={n:native[n]for n in names},constraints=constraints,ordinary_routing_permitted=False,
   native_source_proof=True,physical_signal_integrity_qualified=False))
 def node(ref,p):return bypin[ref,str(p)]
 compute='/motherboard_compute/'
 for stem,pair in [('HDMI0_TX0',[82,84]),('HDMI0_TX1',[76,78]),('HDMI0_TX2',[70,72]),('HDMI0_CLK',[88,90])]:
  group(stem,[node('J15002',p)for p in pair],'LOGIC',None,dict(differential_impedance_ohm=100,within_pair_target_mm=.15,HDMI_group_pair_to_pair_target_mm=25,
   source='Raspberry Pi CM4/CM5 datasheets, HDMI routing and module-length tables',ESD='TPD12S016PWR U15018 must be in the real pair path with minimal stub; verify exact land path',
   continuous_same_domain_reference_required=True,manufacturer_stackup_width_gap_mm=None,actual_module_internal_length_compensation_required=True,no_new_layer_change_without_same_return_stitch=True))
 for i,pins in enumerate([[12,10],[4,6],[11,9],[3,5]]):
  group('ETHERNET_PAIR'+str(i),[node('J15001',p)for p in pins],'LOGIC',None,dict(differential_impedance_ohm=100,within_pair_target_mm=.15,
   CM4_between_pair_target_mm=50,source='Raspberry Pi CM4 section Ethernet + CM5 length tables; exact module-specific profile required',
   actual_module_to_Wurth7499111446_transformer_pins_required=True,PHY_side_reference='LOGIC_GND',cable_side_shield='CHASSIS; no DC short to LOGIC_GND',
   manufacturer_stackup_width_gap_mm=None,all_ESD_and_CT_branch_stubs_need_measured_route_review=True))
 for name,pins in [('CM_USB2',[3,5])]:
  group(name,[node('J15002',p)for p in pins],'LOGIC',None,dict(differential_impedance_ohm=90,within_pair_target_mm=.15,source='CM4/CM5 USB2 routing',
   actual_FSUSB42MUX_switch_path_required=True,unused_switch_branch_separated_by_device=True,manufacturer_stackup_width_gap_mm=None,system_480Mbps_qualification=False))
 for name in ('USB_HOST','USB_RECOVERY'):
  group(name,[compute+name+'_P',compute+name+'_N'],'LOGIC',None,dict(differential_impedance_ohm=90,within_pair_target_mm=.15,
   actual_connector_and_switch_endpoints_required=True,connector_ESD_stubs_minimize=True,manufacturer_stackup_width_gap_mm=None,
   source='CM4/CM5 USB2 routing plus actual FSUSB42MUX/ESD source'))
 sd=[node('J15001',p)for p in [57,62,63,67,69,61]]+[node('J15003',p)for p in [5,3,7,8,1,2]]
 group('REMOVABLE_SD_SIGNALS',sorted(set(sd)),'LOGIC',3.3,dict(source='Actual qualified CM4 Lite/CM5 Lite source only; eMMC variants and BTT remain separate profiles',
  actual_clock_source_damping='R15026',avoid_clock_branch_stubs=True,loaded_clock_rate_and_timing_proof=False,manufacturer_stackup_single_ended_width_mm=None,
  required_signal_order=['CLK','CMD','DAT0','DAT1','DAT2','DAT3'],no_generic_max_clock_assumption=True))
 for i in range(12):
  for signal in ('STEP','DIR'):
   tag=signal+str(i);suffix='TO_MIA'if i<8 else'TO_MX4'
   group(tag+'_CHAIN',['/'+tag+'_FPGA','/mc_motor_buffers/'+tag+'_BUFFER_OUT','/mc_motor_buffers/'+tag+'_'+suffix,
      '/motherboard_motors/'+tag+'_P','/motherboard_motors/'+tag+'_N'],'LOGIC',5,
      dict(source='Actual FPGA -> reviewed LVC output buffer -> source damping -> AM26C31IPWR -> field terminal',
       independent_motor_5V_A_or_B_rail=True,motor_interface_differential=True,differential_impedance_ohm=None,
       short_local_buffer_to_driver_routes=True,paired_field_routes_same_reference=True,no_absorbing_enable_alarm_as_step=True,
       current_bringup='Six generators active; motors 6-11 safely held off',two_MHz_requirement_qualified=False,
       source_name_MX4_is_historical_logical_alias_not_physical_daughterboard=True))
 for i in range(4):
  for signal in 'ABZ':
   p='/motherboard_fast_inputs/ENC'+str(i)+'_'+signal
   group('ENC'+str(i)+'_'+signal,[p+'_P',p+'_N','/fpga_core/ENC'+str(i)+'_'+signal+'_FPGA'],'LOGIC',3.3,
    dict(source='AM26LV32EIPWR differential receiver plus exact fitted end termination',receiver_termination_location='Receiving device input lands',
     paired_field_routes=True,short_single_ended_receiver_to_FPGA=True,ten_MHz_system_qualified=False,differential_impedance_ohm=None))
 for prefix,channels in [('MPG','AB'),('FREQ0',''),('FREQ1','')]:
  for ch in channels or['']:
   name=prefix+('_'+ch if ch else'');p='/motherboard_fast_inputs/'+name
   group(name,[p+'_P',p+'_N','/fpga_core/'+name+'_FPGA'],'LOGIC',3.3,
    dict(source='Actual AM26LV32EIPWR source',do_not_fit_MPG_R7015_R7016_DNP_silently=True,paired_field_routes=True,
     no_derived_voltage_from_protected_power_connector=True,differential_impedance_ohm=None))
 for i in range(4):
  names=['/fpga_core/IOL1_L'+str(i)+'_'+s for s in ('CS_N','SCLK','MOSI','MISO')]
  controller=['U13001','U13004','U13008','U14501'][i]
  # Actual target MCU pins, not a presumed card connector or shared bus.
  mcu_pins=[15,16,17,18]if i in(0,3)else[10,11,12,13]
  actual=sorted(set(names+[node(controller,p)for p in mcu_pins]))
  group('IOL1_LANE'+str(i),actual,'LOGIC',3.3,dict(source='Frozen IOL1 four point-to-point lanes with true reset/permission/CRC/freshness',
   clock_tap_is_actual_PB5_timer_counter=True,keep_clock_count_tap_stub_local=True,source_damping_ohm=33,
   powered_off_Ioff_buffer_qualification_retained=True,target_SPI_CPHA_CPOL_and_loaded_latency_qualified=False,
   no_routing_as_shared_four_node_bus=True,simulated_protocol_pass_is_not_loaded_target_or_physical_timing=True))
 group('AI_ADC_SPI',[node('U14734',p)for p in [1,36,37,38]],'AI_AGND',5,dict(actual_ISO7761_3V3_to_5V_domain_crossing=True,
   target_profile='4 MHz planning profile; actual firmware/loaded timing distinct',series_delay_and_roundtrip_MISO_budget_required=True,
   never_route_across_ISO_body_creepage_barrier=True,source='ADS8684A + ISO7761FDWR manufacturer pin tables and frozen actual source'))
 group('AI_ADC_PRECISION',[node('U14734',p)for p in [5,7,16,18,21,23]],'AI_AGND',None,dict(
   exact_seven_cap_cell='U14734+C14740-46; AVDD/DVDD/REFCAP all-F/direct/no-via',REFIO_is_quiet_same_side_target=True,
   reference_cap_min_effective_uF=10,reference_cap_typical_uF=22,guaranteed_effective_bias_aging_ESR_production_proof=False,
   INA149_equal_REFA_REFB='Actual common low-impedance 2.5V Kelvin node; no independent series reference resistor',
   four_current_burdens_require_terminal_Kelvin_sense=True,ADC_input_RC_filter_at_receiver_required=True,
   source='ADS8684A primary recommended operation/layout; INA149 exact reference common-mode/CMRR equations'))
 a.out.mkdir(parents=True)
 inputs={str((a.source/name).resolve()):h for name,h in ad['source_hashes'].items()}
 for p in [a.adoption,Path(__file__),ROOT/'reports/board-completion-20260930/compute-bay-pin-audit/sources/cm4-datasheet.pdf',ROOT/'reports/board-completion-20260930/compute-bay-pin-audit/sources/cm5-datasheet.pdf',ROOT/'reports/motherboard-analog-input-20260930/sources/ads8684a.pdf']:
  inputs[str(p.resolve())]=sha(p)
 report=dict(passed=True,source_adoption_sha256=sha(a.adoption),input_sha256=inputs,physical_parts=len(parts),groups=groups,
  exact_selected_native_nets=len(selected),unselected_nets=len(set(native)-selected),routing_permission=False,
  ordinary_route_promotion=False,manufacturer_width_gap_unselected=True,physical_qualification=False,manufacturing_ready=False,
  remaining_required_specific_reviews=['Host SPI','AO two isolated feedback/reference/current-limiter loops','PWM/process outputs','CAN/RS485 digital and field differential paths','power/current distribution and supervision','remaining exact precision/current/timing nodes'])
 (a.out/'critical-source-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,critical_groups=len(groups),native_nets=len(selected),routing_allowed=False)))

if __name__=='__main__':main()
