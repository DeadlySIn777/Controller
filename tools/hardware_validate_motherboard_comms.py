"""Independent full manufacturer pin/default/rail/native checks; no device execution claim."""
import argparse,collections,json,math
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_comms'

def validate(d,netlist=None,erc=None):
 errors=[]
 def ck(v,msg):
  if not v:errors.append(msg)
 try:
  p=d['components'];b=d['blocks'];ck(len(p)==d['fitted_component_count']==95,'95 real communication source parts')
  ck(sum(len(q['pins']) for q in p.values())==d['fitted_pad_count']==304,'304 exact electrical pads')
  ck(not any(d[k] for k in ['manufacturing_ready','physical_qualification','firmware_implemented','target_image_compiled']),'native source not target/physical/manufacture proof')
  def exact(key,mpn,fp,pins):
   q=p[b[key]];ck(q['mpn']==mpn and q['footprint']==fp and q['pins']=={str(k):v for k,v in pins.items()},'exact independently reviewed fullpin/MPN/package '+key)
  def rr(a,z,v):return [q for q in p.values() if q['kind']=='R' and q['pins']=={'1':a,'2':z} and q['resistance_ohm']==v]
  def cc(a,z,nf):return [q for q in p.values() if q['kind']=='C' and q['pins']=={'1':a,'2':z} and math.isclose(q['capacitance_f'],nf*1e-9)]
  exact('load_switch','TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6',{1:'IO_3V3',2:'LOGIC_GND',3:'COMPUTE_3V3_GOOD',4:'CAN_CTRL_CT',5:'CAN_CTRL_QOD',6:'CAN_CTRL_3V3'})
  ck(len(rr('COMPUTE_3V3_GOOD','LOGIC_GND',4700))==len(rr('CAN_CTRL_3V3','CAN_CTRL_QOD',100))==len(cc('CAN_CTRL_CT','LOGIC_GND',1))==len(cc('CAN_CTRL_3V3','LOGIC_GND',22000))==1,'actual LOWdefault, discharge and slew/storage paths')
  exact('controller_supervisor','TPS3839K33DBZR','CNC_MB_Comms:TPS3839_DBZ3_TI',{1:'LOGIC_GND',2:'CAN_CTRL_READY',3:'CAN_CTRL_3V3'})
  exact('link_ready_gate','SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'CAN_CTRL_READY',2:'COMPUTE_3V3_GOOD',3:'LOGIC_GND',4:'CAN_CTRL_LINK_READY',5:'IO_3V3'})
  exact('ready_inverter','SN74LVC1G14DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:'CAN_CTRL_LINK_READY',3:'LOGIC_GND',4:'CAN_CTRL_OE_N',5:'IO_3V3'})
  ck(len(rr('CAN_CTRL_READY','LOGIC_GND',10000))==1,'below POR valid range observation really LOW')
  exact('spi_buffer','74LVC125APW,118','Package_SO:TSSOP-14_4.4x5mm_P0.65mm',{1:'CAN_CTRL_OE_N',2:'CAN_SPI_SCLK_HOST',3:'CAN_CTRL_SCLK_RAW',4:'CAN_CTRL_OE_N',5:'CAN_SPI_MOSI_HOST',6:'CAN_CTRL_MOSI_RAW',7:'LOGIC_GND',8:'CAN_CTRL_CS_RAW',9:'CAN_SPI_CS_N_HOST',10:'CAN_CTRL_OE_N',11:'CAN_INT_N_HOST',12:'CAN_CTRL_INT_RAW',13:'CAN_CTRL_OE_N',14:'CAN_CTRL_3V3'})
  for a,z in [('CAN_CTRL_SCLK_RAW','CAN_CTRL_SCLK'),('CAN_CTRL_MOSI_RAW','CAN_CTRL_MOSI'),('CAN_CTRL_CS_RAW','CAN_CTRL_CS_N'),('CAN_CTRL_CLOCK_RAW','CAN_CTRL_OSC')]:ck(len(rr(a,z,22))==1,'actual source termination '+a)
  for net,rail in [('CAN_CTRL_SCLK','LOGIC_GND'),('CAN_CTRL_MOSI','LOGIC_GND'),('CAN_CTRL_CS_N','CAN_CTRL_3V3'),('CAN_CTRL_INT_RAW','CAN_CTRL_3V3'),('CAN_CTRL_XSTBY','CAN_CTRL_3V3'),('CAN_CTRL_TX','CAN_CTRL_3V3'),('CAN_CTRL_RX','CAN_CTRL_3V3')]:ck(len(rr(net,rail,10000))==1,'correct controller-rail reset/missing default '+net)
  exact('controller','MCP2518FDT-E/SL','Package_SO:SOIC-14_3.9x8.7mm_P1.27mm',{1:'CAN_CTRL_TX',2:'CAN_CTRL_RX',3:None,4:'CAN_CTRL_INT_RAW',5:None,6:'CAN_CTRL_OSC',7:'LOGIC_GND',8:None,9:'CAN_CTRL_XSTBY',10:'CAN_CTRL_SCLK',11:'CAN_CTRL_MOSI',12:'CAN_SPI_MISO_HOST',13:'CAN_CTRL_CS_N',14:'CAN_CTRL_3V3'})
  exact('clock','ASV-40.000MHZ-LC-T','Oscillator:Oscillator_SMD_Abracon_ASV-4Pin_7.0x5.1mm',{1:'CAN_CTRL_3V3',2:'LOGIC_GND',3:'CAN_CTRL_CLOCK_RAW',4:'CAN_CTRL_3V3'})
  exact('can_tx_buffer','SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'CAN_CTRL_OE_N',2:'CAN_CTRL_TX',3:'LOGIC_GND',4:'CAN_TXD',5:'IO_3V3'})
  exact('can_rx_buffer','SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'CAN_CTRL_OE_N',2:'CAN_RXD',3:'LOGIC_GND',4:'CAN_CTRL_RX',5:'CAN_CTRL_3V3'})
  exact('standby_gate','SN74LVC1G32DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'CAN_CTRL_XSTBY',2:'CAN_CTRL_OE_N',3:'LOGIC_GND',4:'CAN_STANDBY',5:'IO_3V3'})
  ck(len(rr('CAN_TXD','IO_3V3',10000))==len(rr('CAN_STANDBY','IO_3V3',4700))==1,'actual CAN recessive and standby HIGH defaults')
  exact('rs_de_gate','SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'RS485_DE_HOST',2:'COMPUTE_3V3_GOOD',3:'LOGIC_GND',4:'RS485_DE_QUALIFIED',5:'IO_3V3'})
  ck(len(rr('RS485_DE_HOST','LOGIC_GND',10000))==len(rr('RS485_DE_QUALIFIED','LOGIC_GND',4700))==len(rr('RS485_UART_TX_HOST','IO_3V3',10000))==1,'real RS485 idle HIGH and DE LOW')
  exact('rs_transceiver','ISOW1432DFMR','CNC_MB_Comms:ISOW_DFM20_TI',{1:'IO_3V3',2:'RS485_UART_TX_HOST',3:'RS485_DE_QUALIFIED',4:'RS485_UART_RX_HOST',5:'LOGIC_GND',6:'LOGIC_GND',7:'RS485_FIELD_GOOD_HOST',8:'RS485_CONVERTER_GOOD_N',9:'CORE_5V',10:'LOGIC_GND',11:'RS485_ISO_RETURN_RAW',12:'RS485_ISO_3V3_RAW',13:'RS485_ISO_RETURN_RAW',14:'RS485_POWER_GOOD_FIELD',15:'RS485_COM',16:'RS485_FIELD_3V3',17:'RS485_B',18:'RS485_A',19:'RS485_A',20:'RS485_B'})
  exact('can_transceiver','ISOW1044DFMR','CNC_MB_Comms:ISOW_DFM20_TI',{1:'IO_3V3',2:'LOGIC_GND',3:'CAN_TXD',4:'CAN_STANDBY',5:'CAN_RXD',6:'LOGIC_GND',7:None,8:'CAN_CONVERTER_GOOD_N',9:'CORE_5V',10:'LOGIC_GND',11:'CAN_ISO_RETURN_RAW',12:'CAN_ISO_5V_RAW',13:'CAN_ISO_5V_RAW',14:None,15:'CAN_GND',16:'CAN_GND',17:'CAN_GND',18:'CAN_L',19:'CAN_H',20:'CAN_FIELD_5V'})
  for tag,rv,rg,sv,sg,lo,hi in [('RS485','RS485_ISO_3V3_RAW','RS485_ISO_RETURN_RAW','RS485_FIELD_3V3','RS485_COM',68100,78700),('CAN','CAN_ISO_5V_RAW','CAN_ISO_RETURN_RAW','CAN_FIELD_5V','CAN_GND',107000,123000)]:
   exact(tag+'_power_bead','BLM15EX331SN1D','Inductor_SMD:L_0402_1005Metric',{1:rv,2:sv});exact(tag+'_return_bead','BLM15EX331SN1D','Inductor_SMD:L_0402_1005Metric',{1:rg,2:sg})
   pg=tag+'_POWER_GOOD_FIELD';uv=tag+'_FIELD_UV';ov=tag+'_FIELD_OV'
   exact(tag+'_window','TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6',{1:pg,2:sg,3:uv,4:ov,5:sv,6:pg})
   for a,z,v in [(sv,uv,lo),(uv,sg,10000),(sv,ov,hi),(ov,sg,10000)]:
    qs=rr(a,z,v);ck(len(qs)==1 and qs[0]['tolerance']==.001 and qs[0]['tcr_ppm_K']==25,'actual precision window divider '+a)
   ck(len(rr(pg,sv,10000))==len(rr(tag+'_CONVERTER_GOOD_N','IO_3V3',10000))==1,'converter fault-only mode and actual field PG pullup')
   # CORE5 supply bypasses are duplicated intentionally, one bank per physical converter.
   ck(len(cc(rv,rg,10))==len(cc(rv,rg,1000))==1 and len(cc(rv,rg,22000))==2,'actual converter HF/bulk bypass '+tag)
   exact(tag+'_health_gate','SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:tag+'_FIELD_GOOD_HOST',2:tag+'_CONVERTER_GOOD_N',3:'LOGIC_GND',4:tag+'_POWER_GOOD_HOST',5:'IO_3V3'})
  ck(len(cc('CORE_5V','LOGIC_GND',10))==len(cc('CORE_5V','LOGIC_GND',1000))==2 and len(cc('CORE_5V','LOGIC_GND',22000))==4,'distinct local CORE5 banks at both ISOWs')
  exact('can_health_isolator','ISO7720FDWR','CNC_MB_Comms:ISO7720_DW16_TI_HV',{1:'CAN_GND',2:None,3:'CAN_FIELD_5V',4:'CAN_POWER_GOOD_FIELD',5:'CAN_GND',6:None,7:'CAN_GND',8:None,9:'LOGIC_GND',10:None,11:None,12:None,13:'CAN_FIELD_GOOD_HOST',14:'IO_3V3',15:None,16:'LOGIC_GND'})
  exact('can_tvs','PESD2CANFD24V-T','Package_TO_SOT_SMD:SOT-23',{1:'CAN_H',2:'CAN_L',3:'CAN_GND'})
  for key,a,z in [('rs_termination','RS485_A','RS485_TERM'),('can_termination','CAN_L','CAN_TERM')]:
   q=p[b[key]];ck(q['pins']=={'1':a,'2':z} and q['mpn']=='CRCW2512120RFKEG' and q['resistance_ohm']==120 and q['footprint']=='Resistor_SMD:R_2512_6332Metric' and q['power_rating_w']==1,'actual separately linkable120ohm1W termination '+key)
  # No resistor/return ferrite is allowed to erase isolated bus regions.
  for q in p.values():
   ck(q['physical'] and q['mpn'] and q['footprint'],'no placeholder purchased parts')
   if q['kind'] in ['R','BEAD']:ck(not ({'RS485_COM','CAN_GND'}&set(q['pins'].values()) and 'LOGIC_GND' in q['pins'].values()),'no field-return DC bond')
  li=d['limits'];ck(li['RS485_part_max_bps']==12000000 and li['RS485_target_bps']==1000000 and li['RS485_common_mode_v']==[-7,12] and li['RS485_abs_bus_v']==[-12,15],'real12Mbps part and bounded RS485 voltage')
  ck(li['CAN_target_data_bps']==2000000 and li['CAN_part_max_bps']==5000000 and li['CAN_abs_bus_v']==[-58,58] and li['controller_external_clock_hz']==40000000 and li['controller_SPI_hz_candidate']==10000000<=li['controller_SPI_part_max_hz']==20000000,'actual CAN controller/physical limits')
  ck(not li['RS485_external_TVS_fitted'] and not li['RS485_board_surge_claim'],'do not promise mismatched19V SM712 clamp protection')
  ck(d['defaults']=={'missing_compute_powers_off_CAN_controller':True,'CAN_controller_has_no_reset_pin':True,'CAN_standby_until_real_ready_and_XSTBY_LOW':True,'RS485_DE_LOW_when_missing_compute':True,'separate_isolated_COMs':True,'native_health_not_synthetic':True,'automatic_motion_rearm':False},'bounded hardware defaults')
  pb=d['power_budget'];ck(math.isclose(pb['IO_3V3_bypass_nominal_uf'],2.0) and math.isclose(pb['CAN_CTRL_bypass_nominal_uf'],22.5),'real parent2.0uF plus actualswitched22.5uF')
  ck(pb['MCP2518FD_max_at40MHz_SYSCLK_20MHzSPI_a']==.020 and pb['ASV_max_at40MHz_a']==.025 and pb['RS485_IO3_max_12Mbps_loopback_a']==.0072 and pb['CAN_IO3_max_5Mbps_a']==.0062,'exact max IC facts do not become dynamic system budget')
  ck(set(d['boundaries']['J14802']['pins'].values())=={'RS485_UART_TX_HOST','RS485_UART_RX_HOST','RS485_DE_HOST','CAN_SPI_SCLK_HOST','CAN_SPI_MOSI_HOST','CAN_SPI_MISO_HOST','CAN_SPI_CS_N_HOST','CAN_INT_N_HOST'},'exacteight agreed compute bus endpoints')
  ck(all(not q['physical'] and not q['mpn'] and not q['footprint'] for q in d['boundaries'].values()),'no fake boundary sockets')
  if netlist:
   n=native(netlist);ck(set(n)==set(p)|set(d['boundaries']),'native exact population')
   for ref,q in {**p,**d['boundaries']}.items():ck(n.get(ref)=={k:q[k] for k in ['mpn','footprint','value','pins']},'native exact fullpin agreement '+ref)
  if erc:
   e=json.loads(Path(erc).read_text());vs=[v for s in e['sheets'] for v in s['violations']];ck(not e['ignored_checks'] and len(vs)==2 and all(v['type']=='ground_pin_not_ground' and v['severity']=='warning' for v in vs),'native ERC0errors2 isolated-return labelwarnings, no ignored')
   ck({v['items'][0]['description'].split()[1] for v in vs}=={b['rs_transceiver'],b['can_transceiver']},'only two exact isolated rawreturn name warnings')
 except (KeyError,ValueError,TypeError,OSError,IndexError) as e:errors.append('invalid source/evidence '+str(e))
 return {'ok':not errors,'errors':errors,'physical_footprints':95,'electrical_pads':304,'manufacturing_ready':False,'physical_qualification':False,'target_image_compiled':False}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args();r=validate(json.loads((OUT/'design.json').read_text()),OUT/'netlist.xml',OUT/'erc.json')
 if a.write:(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
