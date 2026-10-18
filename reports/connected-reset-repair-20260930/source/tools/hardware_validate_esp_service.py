"""Independent ESP service circuit contract and bounded arithmetic; no hardware access."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/esp_service'

MODULE={1:'LOGIC_GND',2:'ESP_3V3',3:'ESP_MODULE_EN',4:'ESP_HOST_RX',5:'ESP_RESERVED_GPIO5',6:'ESP_RESERVED_GPIO6',7:'ESP_RESERVED_GPIO7',12:'ESP_RESERVED_GPIO8',13:'ESP_USB_DM',14:'ESP_USB_DP',15:'ESP_STRAP3',16:'ESP_STRAP46',17:'ESP_RESERVED_GPIO9',18:'ESP_RESERVED_GPIO10',19:'ESP_RESERVED_GPIO11',20:'ESP_RESERVED_GPIO12',26:'ESP_STRAP45',27:'ESP_BOOT_N',36:'ESP_UART0_RX',37:'ESP_UART0_TX',40:'LOGIC_GND',41:'LOGIC_GND'}
CHIPS={
 'U2':('SN74LVC1G97DBVR',{1:'LOGIC_GND',2:'LOGIC_GND',3:'ESP_MANUAL_RESET_N',4:'ESP_MODULE_EN',5:'ESP_3V3',6:'ESP_CHIP_PU'}),
 'U3':('SN74LVC2G17DBVR',{1:'HOST_HEALTH_RX_FILTERED',2:'LOGIC_GND',3:'SERVICE_UART_RX_FILTERED',4:'ESP_UART0_RX',5:'ESP_3V3',6:'ESP_HOST_RX'}),
 'U4':('SN74LVC1G17DBVR',{1:None,2:'ESP_UART0_TX',3:'LOGIC_GND',4:'SERVICE_UART_TX_BUFFERED',5:'SERVICE_VREF_3V3'}),
 'U5':('TS3USB221ARSER',{1:'ESP_USB_DP_SWITCH',2:'ESP_USB_DM_SWITCH',3:None,4:None,5:'LOGIC_GND',6:'ESP_USB_OE_N',7:'USB_DM_CONNECTOR',8:'USB_DP_CONNECTOR',9:'LOGIC_GND',10:'ESP_3V3'}),
 'U6':('SN74LVC1G97DBVR',{1:'ESP_3V3',2:'LOGIC_GND',3:'LOGIC_GND',4:'ESP_USB_OE_N',5:'ESP_3V3',6:'USB_VBUS_SENSE'}),
 'D1':('TPD2EUSB30DRTR',{1:'USB_DP_CONNECTOR',2:'USB_DM_CONNECTOR',3:'LOGIC_GND'}),
 'D2':('TPD1E10B06DPYR',{1:'USB_VBUS',2:'LOGIC_GND'}),
 'D3':('TPD1E10B06DPYR',{1:'USB_CC1',2:'LOGIC_GND'}),
 'D4':('TPD1E10B06DPYR',{1:'USB_CC2',2:'LOGIC_GND'})}
PASSIVES={
 'R1':('10k1%','ESP_3V3','ESP_BOOT_N'),'R2':('10k1%','ESP_STRAP45','LOGIC_GND'),'R3':('10k1%','ESP_STRAP46','LOGIC_GND'),'R4':('10k1%','ESP_STRAP3','LOGIC_GND'),
 'R5':('10k1%','ESP_3V3','ESP_MANUAL_RESET_N'),'R6':('47k1%','ESP_MODULE_EN','LOGIC_GND'),
 'R7':('1k1%','HOST_HEALTH_TX_3V3','HOST_HEALTH_RX_FILTERED'),'R8':('100k1%','HOST_HEALTH_RX_FILTERED','LOGIC_GND'),
 'R9':('1k1%','SERVICE_ADAPTER_TX_3V3','SERVICE_UART_RX_FILTERED'),'R10':('100k1%','SERVICE_UART_RX_FILTERED','LOGIC_GND'),
 'R11':('100R1%','SERVICE_UART_TX_BUFFERED','SERVICE_ADAPTER_RX_3V3'),
 'R12':('22R1%','ESP_USB_DP','ESP_USB_DP_SWITCH'),'R13':('22R1%','ESP_USB_DM','ESP_USB_DM_SWITCH'),
 'R14':('10k1%','ESP_3V3','ESP_USB_OE_N'),'R15':('10k1%','USB_VBUS','USB_VBUS_SENSE'),'R16':('100k1%','USB_VBUS_SENSE','LOGIC_GND'),
 'R17':('5.1k1%','USB_CC1','LOGIC_GND'),'R18':('5.1k1%','USB_CC2','LOGIC_GND'),'R19':('0R','USB_SHIELD','LOGIC_GND'),
 'C1':('22uF16V X7R10%','ESP_3V3','LOGIC_GND'),
 'C4':('100nF16V X7R20%','SERVICE_VREF_3V3','LOGIC_GND'),
 'C7':('100nF16V X7R20%','ESP_MANUAL_RESET_N','LOGIC_GND')}
for n in (2,3,5,6,8):PASSIVES['C'+str(n)]=('100nF16V X7R20%','ESP_3V3','LOGIC_GND')
BOUNDARIES={'JRAIL1':['ESP_3V3','LOGIC_GND','ESP_CHIP_PU'],'JHOST1':['HOST_HEALTH_TX_3V3','LOGIC_GND'],'JSERIAL1':['SERVICE_VREF_3V3','SERVICE_ADAPTER_TX_3V3','SERVICE_ADAPTER_RX_3V3','LOGIC_GND'],'JRESET1':['ESP_MANUAL_RESET_N','LOGIC_GND'],'JBOOT1':['ESP_BOOT_N','LOGIC_GND'],'JRES1':['ESP_RESERVED_GPIO'+str(n) for n in range(5,13)]+['LOGIC_GND']}
USB={}
for side in ('A','B'):
 for n,net in ((1,'LOGIC_GND'),(4,'USB_VBUS'),(5,'USB_CC1' if side=='A' else 'USB_CC2'),(6,'USB_DP_CONNECTOR'),(7,'USB_DM_CONNECTOR'),(8,None),(9,'USB_VBUS'),(12,'LOGIC_GND')):USB[side+str(n)]=net
USB['S1']='USB_SHIELD'

def numeric(d,k,lo=0,hi=1e6):
 x=d[k]
 if isinstance(x,bool) or not isinstance(x,(int,float)):raise ValueError(k+': numeric required')
 try:x=float(x)
 except OverflowError as exc:raise ValueError(k+': range') from exc
 if not math.isfinite(x) or not lo<=x<=hi:raise ValueError(k+': range')
 return x
def pair(d,k,lo,hi):
 v=d[k]
 if not isinstance(v,list) or len(v)!=2:raise ValueError(k+': two corners required')
 a,b=[numeric({'v':x},'v',lo,hi) for x in v]
 if a>b:raise ValueError(k+': reversed')
 return a,b
def gate97(in0,in1,in2):
 # Datasheet Table1: selectIN1 whenIN2 low, IN0 whenIN2 high.
 return in0 if in2 else in1

def analyze(d):
 if d['module_mpn']!='ESP32-S3-WROOM-1-N8':raise ValueError('module variant unqualified')
 b=d['bounds'];vlo,vhi=pair(b,'esp_v',3,3.6);hostlo,hosthi=pair(b,'serial_vref_v',3,3.6)
 vblo,vbhi=pair(b,'usb_vbus_normal_v',4.4,5.25)
 running=numeric(b,'esp_total_running_reservation_a',0,1);supply=numeric(b,'logic_max_supply_a',0,1)
 aux=numeric(b,'support_running_reserve_a',0,.1);bulk=numeric(b,'module_bulk_nominal_f',1e-9,.001)
 bt=numeric(b,'module_bulk_initial_fraction',0,.5);temp=numeric(b,'x7r_temperature_fraction',0,.5)
 small=numeric(b,'small_cap_nominal_f',1e-12,.001);st=numeric(b,'small_cap_initial_fraction',0,.5)
 n=numeric(b,'local_esp_small_cap_count',6,6);soft=numeric(b,'logic_soft_start_screen_min_s',1e-6,1)
 eff=numeric(b,'conversion_efficiency_assumed',.1,1);core=numeric(b,'core5_min_v',4.5,5.5)
 cap=bulk*(1+bt)*(1+temp)+n*small*(1+st)*(1+temp)
 charge=cap*vhi/soft
 # Bounds below preserve the exact fitted resistor values, with2% total allowance.
 sense_min=vblo*98000/(10200+98000)-5e-6*(10200*98000/(10200+98000))
 sense_max=vbhi*102000/(9800+102000)+5e-6*(9800*102000/(9800+102000))
 serial_rx_min=hostlo*98000/(1020+98000)-5e-6*1020
 en_load=vhi/(47000*.98)+5e-6
 out={'scope':'bounded candidate arithmetic and logic only; no target measurements',
      'module_steady_reservation_a':running-aux,'support_reserve_within_total_a':aux,
      'esp_extra_cap_max_f':cap,'esp_extra_cap_charge_a_assumed':charge,
      'core5_extra_cap_charge_a_assumed':charge*vhi/(eff*core),
      'steady_plus_extra_cap_charge_a':running+charge,'fits_1a_local_regulator_assumed':running+charge<=supply,
      'usb_sense_normal_min_v':sense_min,'usb_sense_normal_max_v':sense_max,
      'usb_sense_fits5p5v_input':sense_max<=5.5,'usb_valid_high_screen_ge2p2v':sense_min>=2.2,
      'uart_rx_high_min_v_assumed':serial_rx_min,'uart_high_screen_ge2p2v':serial_rx_min>=2.2,
      'module_en_gate_load_a':en_load,'gate_100ua_voh_condition_met':en_load<=100e-6,
      'module_en_high_min_v':vlo-.1,'module_en_vih_worst_v':.75*vhi,
      'module_en_off_10ua_pd_v':10e-6*47000*1.02,
      'usb_port_power_off_leak_per_pin_a_spec':2e-6,
      'uart_buffer_power_off_leak_a_spec':10e-6,
      'all_partial_power_states_proven':False,'usb_compliance_proven':False,
      'industrial_io_implemented':False,'accessory_firmware_implemented':False,'manufacturing_ready':False}
 json.dumps(out,allow_nan=False);return out

def validate(tree,d):
 errors=[];expected=defaultdict(set);nc=set();actual={};seen=set()
 def add(ref,pin,net):
  node=(ref,str(pin))
  if net is None:nc.add(node)
  else:expected[net].add(node)
 for n in range(1,42):add('U1',n,MODULE.get(n))
 for ref,(_,pins) in CHIPS.items():
  for n,net in pins.items():add(ref,n,net)
 for ref,(_,a,b) in PASSIVES.items():add(ref,1,a);add(ref,2,b)
 for ref,nets in BOUNDARIES.items():
  for i,net in enumerate(nets,1):add(ref,i,net)
 for n,net in USB.items():add('JUSB1',n,net)
 actual_nc=set()
 for net in tree.findall('.//nets/net'):
  name=net.attrib['name'].lstrip('/');nodes=[(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')]
  if len(nodes)!=len(set(nodes)) or seen.intersection(nodes):errors.append('duplicate pin')
  seen.update(nodes)
  if name.startswith('unconnected-'):
   if len(nodes)!=1:errors.append('grouped NC')
   actual_nc.update(nodes)
  else:
   if name in actual:errors.append('duplicate net')
   actual[name]=set(nodes)
 if actual_nc!=nc:errors.append('NC population differs')
 for net in set(expected)|set(actual):
  if expected.get(net,set())!=actual.get(net,set()):errors.append('connectivity:'+net)
 rows=tree.findall('.//components/comp');cs={c.attrib['ref']:c for c in rows}
 required={'U1','JUSB1'}|set(CHIPS)|set(PASSIVES)|set(BOUNDARIES)
 if len(rows)!=len(cs) or set(cs)!=required:errors.append('population differs')
 for ref,mpn in [('U1','ESP32-S3-WROOM-1-N8')]+[(r,p[0]) for r,p in CHIPS.items()]:
  if ref not in cs or cs[ref].findtext("./fields/field[@name='MPN']")!=mpn:errors.append('MPN:'+ref)
 for ref,(value,_,_) in PASSIVES.items():
  if ref not in cs or cs[ref].findtext('value')!=value:errors.append('value:'+ref)
 for ref,c in cs.items():
  if c.findtext('footprint') not in ('',None):errors.append('unqualified footprint:'+ref)
  if any(p.attrib.get('name','').lower()=='dnp' for p in c.findall('property')):errors.append('unreviewed DNP:'+ref)
 try:
  analyze(d)
  if d['firmware']['candidate_rx_gpio']!=4 or d['firmware']['default_rx_gpio']!=-1:errors.append('firmware contract changed')
  if {int(n):v for n,v in d['module_pin_nets'].items()}!={n:MODULE.get(n) for n in range(1,42)}:errors.append('design module contract differs')
  for ref,(mpn,pins) in CHIPS.items():
   source=d['active_parts'][ref]
   if source['mpn']!=mpn or {int(n):v[1] for n,v in source['pins'].items()}!=pins:errors.append('design device contract:'+ref)
  for ref,(value,a,b) in PASSIVES.items():
   if d['passives'][ref]['value']!=value or d['passives'][ref]['nets']!=[a,b]:errors.append('design passive contract:'+ref)
 except (ValueError,KeyError,TypeError,OverflowError) as exc:errors.append('invalid envelope:'+str(exc))
 return errors

def main():
 d=json.loads((OUT/'design-envelope.json').read_text());tree=ET.parse(OUT/'netlist.xml');errors=validate(tree,d)
 erc=json.loads((OUT/'erc.json').read_text());count=sum(len(s['violations']) for s in erc['sheets'])
 if count:errors.append('ERC violations:'+str(count))
 (ROOT/'research/esp-service/analysis.json').write_text(json.dumps(analyze(d),indent=2)+'\n')
 paths=[p for p in OUT.iterdir() if p.is_file() and p.name!='validation.json']+[Path(__file__),ROOT/'tools/hardware_build_esp_service.py',ROOT/'tools/hardware_build_tx_schematic.py',ROOT/'tools/hardware_build_assembly.py',ROOT/'tests/test_esp_service_hardware.py',ROOT/'reports/ESP_SERVICE_HARDWARE.md']
 paths+=[p for p in (ROOT/'research/esp-service').iterdir() if p.is_file()]
 paths+=[ROOT/'firmware/esp32_service'/n for n in ('main/service_main.c','main/Kconfig.projbuild','sdkconfig.defaults','sdkconfig.uart-build-check.defaults')]
 result={'schema_version':1,'manufacturing_ready':False,'consistency_pass':not errors,'errors':errors,'component_count':len(tree.findall('.//components/comp')),'net_count':len(tree.findall('.//nets/net')),'erc_violations':count,'kicad_version':erc['kicad_version'],'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Source, circuitERC, connectivity and arithmetic; no PCB, RF, USBcompliance, flasheddevice or accessory firmware qualification'}
 (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print('ESP service:','PASS' if not errors else errors);return bool(errors)

if __name__=='__main__':raise SystemExit(main())
