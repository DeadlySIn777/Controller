"""Native domain/mating regressions with actual destructive mutations."""
import copy,json,sys,tempfile,unittest,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'reports/motherboard-compute-20260930/staging-r05'))
from hardware_validate_motherboard_compute import validate,validate_lands,validate_hdmi,validate_usb,OUT
from hardware_build_assembly import parse,dump,children,child,value,q


class ComputeCarrierTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tree=ET.parse(OUT/'netlist.xml');cls.model=json.loads((OUT/'design.json').read_text(encoding='utf8'))
 def check(self,tree=None,model=None,source_dir=OUT):return validate(tree or self.tree,model or self.model,source_dir)
 def alter_pin(self,ref,pin,net):
  tree=copy.deepcopy(self.tree);model=copy.deepcopy(self.model);node=None
  for n in tree.findall('./nets/net'):
   for p in n.findall('node'):
    if (p.attrib['ref'],p.attrib['pin'])==(ref,str(pin)):node=copy.deepcopy(p);n.remove(p)
  target=next((n for n in tree.findall('./nets/net') if n.attrib['name'].removeprefix('/')==net),None)
  if target is None:target=ET.SubElement(tree.find('./nets'),'net',{'code':'99999','name':'/'+net})
  target.append(node);model['components'][ref]['pins'][str(pin)]=net
  return tree,model
 def test_native_source_and_exact_lands_pass(self):
  r=self.check();self.assertTrue(r['ok'],r['errors']);self.assertEqual((191,183,8,2),(r['physical_count'],r['purchased_count'],r['bare_test_pad_count'],r['socket_count']))
 def test_one_custom_carrier_has_two_purchased_sockets_not_a_duplicate_soc(self):
  self.assertEqual(['J15001','J15002'],self.model['sockets']);self.assertFalse(self.model['compute_som_fitted_on_carrier_bom'])
  m=copy.deepcopy(self.model);m['compute_som_fitted_on_carrier_bom']=True
  self.assertIn('Commodity compute module duplicated on carrierBOM',self.check(model=m)['errors'])
 def test_exact_main_power_and_module_gpio_reference_reject_external_rail_substitution(self):
  for pin in [77,79,81,83,85,87,78,84,86]:
   with self.subTest(pin=pin):
    t,m=self.alter_pin('J15001',pin,'IO_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_complete_ground_set_cannot_lose_a_contact(self):
  t,m=self.alter_pin('J15002',1,'FAKE_RETURN');self.assertFalse(self.check(t,m)['ok'])
 def test_spi_dual_cs_and_return_supply_are_checked_independently(self):
  for ref,pin,net in [('J15001',47,'CM_HOST_SPI_CS_FB_N'),('J15001',54,'CM_HOST_SPI_CS_CMD_N'),('U15010',5,'IO_3V3')]:
   with self.subTest(ref=ref,pin=pin):
    t,m=self.alter_pin(ref,pin,net);self.assertFalse(self.check(t,m)['ok'])
 def test_actual_qualification_gate_cannot_tie_good_high(self):
  for pin in [1,3,6]:
   with self.subTest(pin=pin):
    t,m=self.alter_pin('U15005',pin,'IO_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_buffer_output_cannot_drive_native_reset_or_readonly_service(self):
  for net in ['FPGA_CRESET_N','FPGA_CDONE','COMPUTE_SERVICE_TX','CM_nRPIBOOT']:
   with self.subTest(net=net):
    t,m=self.alter_pin('U15006',4,net);self.assertTrue(any('drives an observation' in e for e in self.check(t,m)['errors']))
 def test_low_default_or_auxiliary_bleed_cannot_disappear(self):
  for a,b in [('CM_AUX_3V3','LOGIC_GND'),('HOST_SPI_CS_FB_N','IO_3V3'),('HOST_SPI_SCLK','LOGIC_GND'),('FPGA_CDONE','LOGIC_GND')]:
   with self.subTest(a=a):
    m=copy.deepcopy(self.model);p=next(p for p in m['components'].values() if p.get('kind')=='R' and set(p['pins'].values())=={a,b});p['resistance_ohm']=1234
    self.assertTrue(any('default/series resistor absent' in e for e in self.check(model=m)['errors']))
 def test_module_reset_pin92_conflict_cannot_be_quietly_connected(self):
  t,m=self.alter_pin('J15001',92,'RESET_N');self.assertTrue(any('Restricted' in e for e in self.check(t,m)['errors']))
 def test_selector_cannot_grant_power_motion_or_unimplemented_identity(self):
  for key in ['DIP_controls_electrical_power_or_permission','automatic_hardware_ID_implemented','software_profile_implemented']:
   m=copy.deepcopy(self.model);m['selector'][key]=True;self.assertFalse(self.check(model=m)['ok'])
 def test_mirrored_100pin_or_renumbered_socket_land_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty/Amphenol_10164227_1001_CM_A.kicad_mod';t=parse(p.read_text());pad=next(x for x in children(t,'pad') if value(x[1])=='1');child(pad,'at')[1]='1.54';p.write_text(dump(t))
   self.assertTrue(any('land mirror/pitch/size/orientation' in e for e in validate_lands(out)))
 def test_CTS_primary_switch_land_dimensions_are_not_generic_guess(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty/CTS_219-3M_GullWing.kicad_mod';t=parse(p.read_text());child(children(t,'pad')[0],'size')[1]='1.0';p.write_text(dump(t))
   self.assertTrue(any('CTS primary land dimensions' in e for e in validate_lands(out)))
 def test_qualified_BTT_or_manufacturing_claim_is_rejected(self):
  m=copy.deepcopy(self.model);m['profiles']['CB2']['full_electrical_qualification']=True;self.assertFalse(self.check(model=m)['ok'])
  m=copy.deepcopy(self.model);m['manufacturing_ready']=True;self.assertFalse(self.check(model=m)['ok'])
 def test_blanket_socket_rating_does_not_become_2p5A_without_evidence(self):
  m=copy.deepcopy(self.model);m['socket_rating']['planned_2p5A_selective_contact_rating_or_temperature_qualification']=True;self.assertFalse(self.check(model=m)['ok'])
 def test_native_board_silkscreen_rule_rejects_prior_compute_annotation_defect(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty/Amphenol_10164227_1001_CM_A.kicad_mod';t=parse(p.read_text());label=next(x for x in children(t,'fp_text') if 'PIN1' in value(x[2]));child(child(child(label,'effects'),'font'),'size')[1:]=['.7','.7'];p.write_text(dump(t));self.assertTrue(any('below0.8mm' in e for e in validate_lands(out)))
 def test_SD_independent_manufacturer_package_pins_reject_input_output_swap(self):
  for ref,pin,net in [('U15012',1,'SD_PORT_3V3'),('U15012',6,'CM_AUX_3V3'),('U15013',5,'CM_AUX_3V3'),('J15003',9,'SD_CARD_PRESENT_N'),('U15015',1,'SD_PORT_CLK')]:
   with self.subTest(ref=ref,pin=pin):
    t,m=self.alter_pin(ref,pin,net);self.assertFalse(self.check(t,m)['ok'])
 def test_SD_raw_host_cannot_bypass_disabled_mux(self):
  t,m=self.alter_pin('J15003',3,'CM_SD_CMD');self.assertFalse(self.check(t,m)['ok'])
 def test_SD_card_supply_or_pullups_cannot_use_alwaysonIO(self):
  for ref,pin in [('U15012',1),('U15015',8),('U15014',5),('J15003',4)]:
   with self.subTest(ref=ref):
    t,m=self.alter_pin(ref,pin,'IO_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_SD_signal_enable_cannot_tie_actual_power_good_high(self):
  for pin in [1,2]:
   t,m=self.alter_pin('U15014',pin,'CM_AUX_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_SD_exact_currentcap_tolerance_cannot_raise_or_hide(self):
  m=copy.deepcopy(self.model);m['sd_port']['current_limit_max_a']=.3;self.assertFalse(self.check(model=m)['ok'])
  m=copy.deepcopy(self.model);r=next(c for c in m['components'].values() if c.get('kind')=='R' and set(c['pins'].values())=={'SD_ILIM','LOGIC_GND'});r['resistance_ohm']=59000;self.assertFalse(self.check(model=m)['ok'])
 def test_SD_actual_bleed_and_unused_port_termination_mandatory(self):
  for pair in [{'SD_PORT_3V3','LOGIC_GND'},{'SD_UNUSED_NO1','LOGIC_GND'}]:
   m=copy.deepcopy(self.model);r=next(c for c in m['components'].values() if c.get('kind')=='R' and set(c['pins'].values())==pair);r['resistance_ohm']=1e9;self.assertFalse(self.check(model=m)['ok'])
 def test_SD_card_boot_hotswap_and_diagnostic_allocation_unproved(self):
  for k in ['boot_image_verified','physical_qualification','hot_swap_qualified','diagnostics_allocated','external_injection_or_ideal_reverse_blocking_claim']:
   m=copy.deepcopy(self.model);m['sd_port'][k]=True;self.assertFalse(self.check(model=m)['ok'])
 def test_SD_ground_pads_and_unused_ESD_channels_checked(self):
  for ref,pin in [('U15016',3),('U15016',8),('U15017',4)]:
   t,m=self.alter_pin(ref,pin,'CM_AUX_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_SD_original52_complete_fitted_pins_unchanged(self):
  old=json.loads((ROOT/'reports/motherboard-compute-20260930/source-r01/design.json').read_text(encoding='utf8'))
  for ref,c in old['components'].items():
   if c.get('physical'):
    c=copy.deepcopy(c)
    if ref=='J15001':
     self.assertIsNone(c['pins']['56']);self.assertIsNone(c['pins']['58']);self.assertIsNone(c['pins']['34']);c['pins'].update({'25':'CM_CAN_SPI_SCLK','26':'CM_CAN_SPI_MISO','27':'CM_CAN_SPI_MOSI','28':'CM_RS485_RX','29':'CM_CAN_SPI_CS_N','31':'CM_RS485_TX','50':'CM_CAN_INT_N','51':'CM_RS485_DE','34':'USB_POWER_FAULT_N','56':'COMPUTE_I2C_SCL','58':'COMPUTE_I2C_SDA'})
    self.assertEqual({k:c[k] for k in ['mpn','footprint','pins']},{k:self.model['components'][ref][k] for k in ['mpn','footprint','pins']},ref)

 def test_HDMI_PW_graphic_polarity_cannot_follow_grouped_table_guess(self):
  for pin,net in [(15,'CM_HDMI0_CLK_P'),(16,'CM_HDMI0_CLK_N'),(17,'CM_HDMI0_TX0_P'),(22,'CM_HDMI0_TX2_P')]:
   t,m=self.alter_pin('U15018',pin,net);self.assertTrue(any('PW/port pinpolarity' in e for e in self.check(t,m)['errors']))
 def test_HDMI_control_cannot_tiehigh_or_use_externalIO_rail(self):
  for ref,pin,net in [('U15018',5,'CM_AUX_3V3'),('U15018',12,'SBC_5V'),('U15019',5,'IO_3V3'),('U15018',24,'IO_3V3'),('U15018',11,'CM_AUX_3V3')]:
   t,m=self.alter_pin(ref,pin,net);self.assertFalse(self.check(t,m)['ok'])
 def test_HDMI_shells_and_compound_reference_are_actual_separate_nets(self):
  for ref,pin,net in [('J15004','SH1','LOGIC_GND'),('U15018',6,'CHASSIS'),('J15004',2,'CHASSIS')]:
   t,m=self.alter_pin(ref,pin,net);self.assertFalse(self.check(t,m)['ok'])
 def test_HDMI_55mA_normal_cannot_hide_200mA_short_or_claimmode(self):
  for key,v in [('companion_5v_fault_short_max_a',.055),('max_mode_qualified','4k60'),('physical_qualified',True),('local_logic_chassis_ESD_return_coupling_implemented',True)]:
   m=copy.deepcopy(self.model);m['hdmi_port'][key]=v;self.assertFalse(self.check(model=m)['ok'])
 def test_HDMI_issue5_shell_holes_reject_old_officialCAD_rear_1p7mm(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty/EDAC_690-019-298-412_HDMI.kicad_mod';t=parse(p.read_text());pad=next(x for x in children(t,'pad') if value(x[1])=='SH3');child(pad,'drill')[3]='1.7';p.write_text(dump(t));self.assertTrue(any('issue5 shellhole/land' in e for e in validate_hdmi(self.tree,self.model,out)))
 def test_HDMI_pin1_signal_width_y_and_orientation_are_source_backed(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty/EDAC_690-019-298-412_HDMI.kicad_mod';t=parse(p.read_text());pad=next(x for x in children(t,'pad') if value(x[1])=='1');child(pad,'at')[1]='-4.5';p.write_text(dump(t));self.assertTrue(any('primaryland/pinorientation' in e for e in validate_hdmi(self.tree,self.model,out)))
 def test_HDMI_exact89_previous_fitted_pins_and_footprints_preserved(self):
  old=json.loads((ROOT/'reports/motherboard-compute-20260930/source-r02p1/design.json').read_text(encoding='utf8'))
  for ref,c in old['components'].items():
   if c.get('physical'):
    c=copy.deepcopy(c)
    if ref=='J15001':
     self.assertIsNone(c['pins']['56']);self.assertIsNone(c['pins']['58']);self.assertIsNone(c['pins']['34']);c['pins'].update({'25':'CM_CAN_SPI_SCLK','26':'CM_CAN_SPI_MISO','27':'CM_CAN_SPI_MOSI','28':'CM_RS485_RX','29':'CM_CAN_SPI_CS_N','31':'CM_RS485_TX','50':'CM_CAN_INT_N','51':'CM_RS485_DE','34':'USB_POWER_FAULT_N','56':'COMPUTE_I2C_SCL','58':'COMPUTE_I2C_SDA'})
    self.assertEqual({k:c[k] for k in ['mpn','footprint','pins']},{k:self.model['components'][ref][k] for k in ['mpn','footprint','pins']},ref)

 def test_USB_actual_one_host_recovery_and_independent_pins_pass(self):
  self.assertEqual([],validate_usb(self.tree,self.model,OUT));self.assertEqual(1,self.model['usb_port']['host_ports']);self.assertEqual(1,self.model['usb_port']['recovery_ports'])
 def test_USB_MSOP_mux_cannot_use_UQFN_map_or_exchange_data_polarity(self):
  for pin,net in [(1,'USB_RECOVERY_MODE'),(3,'CM_USB2_N'),(6,'USB_HOST_P'),(8,'USB_RECOVERY_P')]:
   with self.subTest(pin=pin):
    t,m=self.alter_pin('U15021',pin,net);self.assertFalse(self.check(t,m)['ok'])
  m=copy.deepcopy(self.model);m['components']['U15021']['mpn']='FSUSB42UMX';self.assertFalse(self.check(model=m)['ok'])
 def test_USB_S0IC_monitor_cannot_use_SOT23_pin_order_or_reverse_shunt(self):
  for pin,net in [(1,'USB_SWITCHED_5V'),(7,'USB_SWITCHED_5V'),(8,'USB_PORT_5V'),(5,'IO_3V3')]:
   t,m=self.alter_pin('U15027',pin,net);self.assertFalse(self.check(t,m)['ok'])
 def test_USB_role_permission_cannot_bypass_real_good_or_connect(self):
  for ref,pin in [('U15023',1),('U15023',3),('U15023',6),('U15025',1),('U15026',3)]:
   t,m=self.alter_pin(ref,pin,'CM_AUX_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_USB_recovery_VBUS_never_joins_an_internal_supply(self):
  for pin in ['A4','A9','B4','B9']:
   t,m=self.alter_pin('J15006',pin,'SBC_5V');self.assertFalse(self.check(t,m)['ok'])
 def test_USB_real_CC_Rd_default_off_and_ILIM_cannot_be_removed(self):
  for ref in ['R15049','R15051','R15058','R15059']:
   m=copy.deepcopy(self.model);m['components'][ref]['resistance_ohm']=1e9;self.assertFalse(self.check(model=m)['ok'])
 def test_USB_shunt_and_current_limit_are_hardware_not_a_metadata_claim(self):
  m=copy.deepcopy(self.model);m['components']['R15053']['resistance_ohm']=0;self.assertFalse(self.check(model=m)['ok'])
  m=copy.deepcopy(self.model);m['usb_port']['hardware_limit_max_a']=.51;self.assertFalse(self.check(model=m)['ok'])
 def test_USB_driver_monitor_live_role_or_power_capacity_not_unproved(self):
  for k in ['current_monitor_calibration_firmware_implemented','USB_IF_compliance_claim','role_switching_live_qualified','upstream_power_from_recovery_VBUS','BTT_I2C_transport_or_aux_current_qualified']:
   m=copy.deepcopy(self.model);m['usb_port'][k]=True;self.assertFalse(self.check(model=m)['ok'])
  m=copy.deepcopy(self.model);m['aux_load_budget']['SBC_3A_compute2p5_USB0p5_simultaneous_profile_closed']=True;self.assertFalse(self.check(model=m)['ok'])
 def test_USB_OTG_role_buffer_has_module_own_supply(self):
  t,m=self.alter_pin('U15028',5,'IO_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_USB_only_three_reviewed_genuine_socketNC_promotions(self):
  t,m=self.alter_pin('J15001',60,'COMPUTE_I2C_SDA');self.assertTrue(any('unbounded retained physical pin' in e for e in self.check(t,m)['errors']))
  for pin,net in [(56,'COMPUTE_I2C_SDA'),(58,'COMPUTE_I2C_SCL')]:
   t,m=self.alter_pin('J15001',pin,net);self.assertFalse(self.check(t,m)['ok'])
 def test_USB_manufacturer_shell_pitch_and_typeC_orientation_reject_guess(self):
  for fname,pin,target in [('Wurth_614004134726_USB_A','SH',1),('GCT_USB4105_GF_A_USB_C','A6',0)]:
   with tempfile.TemporaryDirectory() as d:
    out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty'/(fname+'.kicad_mod');t=parse(p.read_text());pad=next(x for x in children(t,'pad') if value(x[1])==pin);child(pad,'at')[1+target]='2.72' if pin=='SH' else '.25';p.write_text(dump(t));self.assertTrue(any('USB-' in e and ('primary' in e or 'pitch' in e) for e in validate_usb(self.tree,self.model,out)))
 def test_USB_polarized_cap_exact_F_case_cannot_use_E_case_land(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty/Panasonic_FK_F_8x10p2.kicad_mod';t=parse(p.read_text());pad=next(x for x in children(t,'pad') if value(x[1])=='1');child(pad,'at')[1]='-3.1';p.write_text(dump(t));self.assertTrue(any('powerland/case/polarity' in e for e in validate_usb(self.tree,self.model,out)))
 def test_USB_previous97_fitted_pin_and_land_contract_preserved_except34_56_58(self):
  old=json.loads((ROOT/'reports/motherboard-compute-20260930/source-r03/design.json').read_text(encoding='utf8'))
  for ref,c in old['components'].items():
   if not c.get('physical'):continue
   c=copy.deepcopy(c)
   if ref=='J15001':
    self.assertIsNone(c['pins']['56']);self.assertIsNone(c['pins']['58']);self.assertIsNone(c['pins']['34']);c['pins'].update({'25':'CM_CAN_SPI_SCLK','26':'CM_CAN_SPI_MISO','27':'CM_CAN_SPI_MOSI','28':'CM_RS485_RX','29':'CM_CAN_SPI_CS_N','31':'CM_RS485_TX','50':'CM_CAN_INT_N','51':'CM_RS485_DE','34':'USB_POWER_FAULT_N','56':'COMPUTE_I2C_SCL','58':'COMPUTE_I2C_SDA'})
   self.assertEqual({k:c[k] for k in ['mpn','footprint','pins']},{k:self.model['components'][ref][k] for k in ['mpn','footprint','pins']},ref)


 def test_comms_exact_native_contacts_and_gpio14_remain_exclusive(self):
  for pin in [25,26,27,28,29,31,50,51,55]:
   with self.subTest(pin=pin):
    t,m=self.alter_pin('J15001',pin,'FAKE_COMMS');self.assertFalse(self.check(t,m)['ok'])
 def test_comms_gate_uses_real_module_health_without_FPGA_dependency(self):
  for bad in ['IO_3V3','FPGA_CDONE','FPGA_CRESET_N']:
   t,m=self.alter_pin('U15032',2,bad);self.assertFalse(self.check(t,m)['ok'])
 def test_comms_return_buffers_cannot_backpower_absent_module(self):
  for ref in ['U15038','U15039','U15040']:
   t,m=self.alter_pin(ref,5,'IO_3V3');self.assertFalse(self.check(t,m)['ok'])
 def test_comms_DE_CS_and_receiver_defaults_are_actual_parts(self):
  for ref in ['R15061','R15065','R15066','R15074','R15075','R15077','R15083']:
   m=copy.deepcopy(self.model);m['components'][ref]['resistance_ohm']=123;self.assertFalse(self.check(model=m)['ok'])
 def test_Ethernet_true_phy_pairs_not_connector_position_guess(self):
  for pin in range(2,10):
   t,m=self.alter_pin('J15007',pin,'CM_Ethernet_Pair0_P');
   if pin!=2:self.assertFalse(self.check(t,m)['ok'])
 def test_Ethernet_CT_is_AC_return_not_direct_power(self):
  t,m=self.alter_pin('J15007',1,'CM_AUX_3V3');self.assertFalse(self.check(t,m)['ok'])
  m=copy.deepcopy(self.model);m['components']['C15047']['capacitance_f']=0;self.assertFalse(self.check(model=m)['ok'])
 def test_Ethernet_ESD_actual_package_and_shell_return_cannot_swap(self):
  for ref,pin,net in [('U15041',3,'CHASSIS'),('U15042',8,'CM_AUX_3V3'),('J15007',10,'LOGIC_GND'),('J15007','SH','LOGIC_GND')]:
   t,m=self.alter_pin(ref,pin,net);self.assertFalse(self.check(t,m)['ok'])
 def test_Ethernet_pin1_and_LED_holes_match_primary_not_similar_part(self):
  for pin,kind,valuebad in [('1','at','11.43'),('11','drill','1.02')]:
   with tempfile.TemporaryDirectory() as d:
    out=Path(d);shutil.copytree(OUT/'CNC_COMPUTE.pretty',out/'CNC_COMPUTE.pretty');p=out/'CNC_COMPUTE.pretty/Wurth_7499111446_Gigabit.kicad_mod';f=parse(p.read_text());pad=next(x for x in children(f,'pad') if value(x[1])==pin);child(pad,kind)[1]=valuebad;p.write_text(dump(f));self.assertFalse(self.check(source_dir=out)['ok'])
 def test_Ethernet_no_unproved_duplicate_PHY_PoE_or_targetqualification(self):
  for group,key in [('ethernet_port','duplicate_PHY'),('ethernet_port','PoE_power_implemented'),('ethernet_port','carrier_impedance_ESD_link_or_temperature_qualified'),('compute_comms','target_baud_pinmux_or_image_qualified'),('compute_comms','depends_on_FPGA_configuration')]:
   m=copy.deepcopy(self.model);m[group][key]=True;self.assertFalse(self.check(model=m)['ok'])
 def test_r04_retained142_physical_pins_change_only_exact8_previousNC(self):
  old=json.loads((ROOT/'reports/motherboard-compute-20260930/source-r04/design.json').read_text(encoding='utf8'));allowed={'25':'CM_CAN_SPI_SCLK','26':'CM_CAN_SPI_MISO','27':'CM_CAN_SPI_MOSI','28':'CM_RS485_RX','29':'CM_CAN_SPI_CS_N','31':'CM_RS485_TX','50':'CM_CAN_INT_N','51':'CM_RS485_DE'}
  for ref,c in old['components'].items():
   if not c.get('physical'):continue
   c=copy.deepcopy(c)
   if ref=='J15001':
    for pin in allowed:self.assertIsNone(c['pins'][pin])
    c['pins'].update(allowed)
   self.assertEqual({k:c[k] for k in ['mpn','footprint','pins']},{k:self.model['components'][ref][k] for k in ['mpn','footprint','pins']},ref)

if __name__=='__main__':unittest.main()

