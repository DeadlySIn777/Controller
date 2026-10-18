"""Independent native source22 domains, primary pin functions and PG levels."""
from __future__ import annotations
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_diagnostics'


def native(path):
 tree=ET.parse(path);parts={}
 for c in tree.findall('./components/comp'):
  if c.attrib['ref'].startswith('#'):continue
  parts[c.attrib['ref']]={'mpn':c.findtext("./fields/field[@name='MPN']",''),'footprint':c.findtext('footprint',''),'pins':{},'functions':{}}
 for e in tree.findall('./nets/net'):
  name=e.attrib['name'].removeprefix('/')
  for n in e.findall('node'):
   ref,pin=n.attrib['ref'],n.attrib['pin']
   if ref not in parts:continue
   assert pin not in parts[ref]['pins'],(ref,pin)
   parts[ref]['pins'][pin]=None if name.startswith('unconnected-') else name
   parts[ref]['functions'][pin]=n.attrib.get('pinfunction')
 return parts


def level_screen():
 # Existing FA divider tolerance+TCR envelope is explicit; no new pullup on
 # that analog EN node. PG sink max130ohm, input leakage150nA; TPS INA6nA.
 drift=.01+100e-6*30
 lo,hi=1-drift,1+drift
 fa_high_min=17.7*(10000*lo)/(100000*hi+10000*lo)-6e-9*(100000*hi)
 fa_high_max=30.3*(10000*hi)/(100000*lo+10000*hi)
 fa_low_max=130*(30.3/(100000*lo)+150e-9+6e-9)
 own_low,own_high=3.3*.97,3.3*1.03
 pg_b_low_max=130*(own_high/(10000*lo)+150e-9+10e-6)
 good_a_min=own_low-(10e-6+300e-9)*10000*hi
 # Both comparator output and existing MCU-load ISO output testpoints exceed
 # this circuit's declared continuous load; transition/capacitive proof is not
 # supplied by these DC conditions.
 return {'FA_existing_analog_node_high_min_v':fa_high_min,'FA_existing_analog_node_high_max_v':fa_high_max,
  'FA_existing_analog_node_low_max_v':fa_low_max,'TPS3700_INA_rise_max_v':.404,'TPS3700_INA_fall_min_v':.387,
  'FA_level_translator_high_min_v':good_a_min,'FA_level_translator_low_max_v':.250,
  'FB_PGOOD_low_max_v':pg_b_low_max,'ISO_required_high_max_v':.7*own_high,'ISO_allowed_low_min_v':.3*own_low,
  'ISO_logic_output_high_min_v':3.14-.3,'ISO_logic_output_low_max_v':.3,
  'MCU_required_high_screen_v':.7*3.6,'MCU_allowed_low_screen_v':.3*2.7,
  'guaranteed_normal_interface_DC_conditions_closed':True,
  'assumptions':['FA protected input17.7–30.3V screen; resistors1% plus100ppm/K×30K','ownTPS7A1633 regulated3.3V±3% steady range','ISO7720 electrical table3.3V±10%, output2mA test load; MCU voltage2.7–3.6V'],
  'partial_power_startup_transients_qualified':False,
  'new_IO3_ISO_quiescent_max_a_at_DC_test_conditions':.0042,
  'existing_two10k_DOWN_load_high_max_a':2*3.6/(10000*lo),
  'new_each_field_ISO_quiescent_max_a_at_DC_test_conditions':.0042,
  'new_A_monitor_max_supply_a_at_datasheet_test_conditions':13e-6,
  'local_3V3_voltage_window_proven_by_entry_PG':False}


def validate(model,parts,parent=None):
 errors=[];checks=0
 def ck(test,msg):
  nonlocal checks
  checks+=1
  if not test:errors.append(msg)
 def exact(ref,mpn,pins):
  ck(ref in parts and parts[ref]['mpn']==mpn,'Exact manufacturer MPN '+ref)
  if ref in parts:
   for pin,want in pins.items():ck(parts[ref]['pins'].get(str(pin),'ABSENT')==want,'Actual native pin '+ref+'.'+str(pin))
 physical={r:c for r,c in parts.items() if c['footprint']}
 ck(set(physical)==set(model['components']),'Exactly20 source physical references; boundaries are nonphysical')
 for ref,c in model['components'].items():
  if ref not in physical:continue
  ck(physical[ref]['footprint']==c['footprint'],'Source/native footprint '+ref)
  ck(physical[ref]['pins']==c['pins'],'All source/native electrical pins including NC '+ref)
 # Datasheet DDC exact pins, not DSE alternate numbering.
 exact('U22001','TPS3700DDCR',{1:'FA_PGOOD_LEVEL_3V3',2:'FIELD_GND',3:'FA_PGOOD',4:'FIELD_GND',5:'DOA_FIELD_3V3',6:None})
 ck(parts.get('U22001',{}).get('functions',{}).get('3')=='INA+_3','TPS3700 DDC pin3 INA+ is exact primary function')
 for ref,ground,rail,raw,good in [('U22002','FIELD_GND','DOA_FIELD_3V3','FA_PGOOD_LEVEL_3V3','DOA_FIELD_POWER_GOOD'),('U22003','FIELD_B_0V','DOB_FIELD_3V3','FB_PGOOD','DOB_FIELD_POWER_GOOD')]:
  exact(ref,'ISO7720FDWR',{1:ground,2:None,3:rail,4:raw,5:ground,6:None,7:None,8:ground,9:'LOGIC_GND',10:None,11:None,12:None,13:good,14:'IO_3V3',15:None,16:'LOGIC_GND'})
  ck(parts.get(ref,{}).get('functions',{}).get('4')=='INA_4' and parts.get(ref,{}).get('functions',{}).get('13')=='OUTA_13','ISO primary actual forward lane '+ref)
 exact('R22001','CRCW060310K0FKEA',{1:'FA_PGOOD_LEVEL_3V3',2:'DOA_FIELD_3V3'})
 exact('R22002','CRCW060310K0FKEA',{1:'FB_PGOOD',2:'DOB_FIELD_3V3'})
 ck(not any(c['kind']=='R' and 'FA_PGOOD' in c['pins'].values() for c in model['components'].values()),'No new loading/bias resistor on original FA analog converterEN divider')
 for ref in ('R22001','R22002'):ck(model['components'][ref].get('resistance_ohm')==10000,'Actual10k pullup '+ref)
 supplies=[('C22001','DOA_FIELD_3V3','FIELD_GND'),('C22002','DOA_FIELD_3V3','FIELD_GND'),('C22003','IO_3V3','LOGIC_GND'),('C22004','DOB_FIELD_3V3','FIELD_B_0V'),('C22005','IO_3V3','LOGIC_GND')]
 for ref,rail,ground in supplies:
  exact(ref,'GRM188R72A104KA35D',{1:rail,2:ground});ck(model['components'][ref].get('capacitance_f')==100e-9,'Actual100nF bypass '+ref)
 for i,signal in enumerate(['FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT'],1):
  ref=f'TP2200{i}';exact(ref,'PCB_COPPER_TEST_PAD_D1.0',{1:signal});ck(model['components'][ref].get('purchased') is False,'Bare test-only geometry '+ref)
 for i in range(1,7):
  ref=f'H2200{i}';c=model['components'][ref];ck(c['pins']=={} and physical[ref]['pins']=={},'Mount has zero fake electrical pins '+ref)
  ck(c['footprint']=='MountingHole:MountingHole_3.2mm_M3' and c.get('purchased') is False and c.get('drill_mm')==3.2 and c.get('conductive_pad') is False,'Exact bare M3NPTH '+ref)
 for key,want in [('physical_footprints',20),('purchased_fitted_components',10),('bare_testpads',4),('bare_NPTH_mounts',6),('native_pad_count',56)]:ck(model.get(key)==want,'Exact source inventory '+key)
 screen=level_screen();ck(screen['FA_existing_analog_node_high_min_v']>screen['TPS3700_INA_rise_max_v'],'FA comparator guaranteed HIGH margin')
 ck(screen['FA_existing_analog_node_low_max_v']<screen['TPS3700_INA_fall_min_v'],'FA comparator guaranteed LOW margin')
 ck(screen['FA_level_translator_high_min_v']>screen['ISO_required_high_max_v'],'FA translated input VIH margin')
 ck(screen['FB_PGOOD_low_max_v']<screen['ISO_allowed_low_min_v'],'FB real PGOOD VIL margin')
 if parent is not None:
  ck(parent['U10003']['pins']['9']==parent['U11017']['pins']['4']==parent['U11004']['pins']['8'],'Actual parent DOA isolator/regulator/eFuse return agrees')
  ck(parent['U10016']['pins']['9']==parent['U11018']['pins']['4']==parent['U11006']['pins']['8'],'Actual parent DOB isolator/regulator/eFuse return agrees')
  ck(parent['U11004']['pins']['8']!=parent['U11006']['pins']['8'],'Actual parent fieldA/B ground domains remain distinct')
  ck(parent['U11004']['pins']['16'].rsplit('/',1)[-1]=='FA_PGOOD' and parent['U11006']['pins']['16'].rsplit('/',1)[-1]=='FB_PGOOD','Actual eFuse physical endpoints')
  for ref,res,net in [('U13004','R13027','DOA_FIELD_POWER_GOOD'),('U13008','R13045','DOB_FIELD_POWER_GOOD')]:
   ck(parent[ref]['pins']['16']==parent[res]['pins']['1'] and parent[ref]['pins']['16'].rsplit('/',1)[-1]==net,'Actual readonly PB1 endpoint '+ref)
   ck(parent[res]['pins']['2']=='LOGIC_GND','Preserved existing LOW bias '+res)
 return {'passed':not errors,'errors':errors,'checks':checks,'level_screen':screen,'source_only':True,'physical_qualification':False,'manufacturing_ready':False}


if __name__=='__main__':
 d=json.loads((OUT/'design.json').read_text(encoding='utf-8'));p=native(OUT/'netlist.xml');r=validate(d,p)
 (OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:r[k] for k in ['passed','errors','checks']}));raise SystemExit(0 if r['passed'] else 1)
