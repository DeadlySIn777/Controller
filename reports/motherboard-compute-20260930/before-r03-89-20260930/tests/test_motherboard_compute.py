"""Native domain/mating regressions with actual destructive mutations."""
import copy,json,sys,tempfile,unittest,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_compute import validate,validate_lands,OUT
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
  r=self.check();self.assertTrue(r['ok'],r['errors']);self.assertEqual((89,85,4,2),(r['physical_count'],r['purchased_count'],r['bare_test_pad_count'],r['socket_count']))
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
    self.assertEqual({k:c[k] for k in ['mpn','footprint','pins']},{k:self.model['components'][ref][k] for k in ['mpn','footprint','pins']},ref)
if __name__=='__main__':unittest.main()

