"""Real isolated RS485/CAN source, controller power-cycle and default/health paths."""
from __future__ import annotations
import csv,json,uuid,shutil
from pathlib import Path
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,effects,quote
from hardware_build_motherboard_analog_output import KINDS as SHARED
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_comms'
NS=uuid.UUID('0d66a77a-85c5-4c44-9ebd-887898de00f2')
KINDS={k:SHARED[k].copy() for k in ['AND','INV','BUFFER','WINDOW','ISO2','R','C','PWR_FLAG']}
KINDS.update({
 'OR':{1:('A','input'),2:('B','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'BEAD':{1:('','passive'),2:('','passive')},
 'TVS3':{1:('K1','passive'),2:('K2','passive'),3:('CC','passive')},
 'SUP':{1:('GND','power_in'),2:('RESET_N_PUSH_PULL','output'),3:('VDD','power_in')},
 'SWITCH':{1:('VIN','power_in'),2:('GND','power_in'),3:('ON','input'),4:('CT','passive'),5:('QOD','passive'),6:('VOUT','power_out')},
 'OSC':{1:('OE','input'),2:('GND','power_in'),3:('OUT','output'),4:('VDD','power_in')},
 'BUF4':{1:('OE1_N','input'),2:('A1','input'),3:('Y1','tri_state'),4:('OE2_N','input'),5:('A2','input'),6:('Y2','tri_state'),7:('GND','power_in'),8:('Y3','tri_state'),9:('A3','input'),10:('OE3_N','input'),11:('Y4','tri_state'),12:('A4','input'),13:('OE4_N','input'),14:('VCC','power_in')},
 'CANCTL':{1:('TXCAN','output'),2:('RXCAN','input'),3:('CLKO_SOF','output'),4:('INT_N_CONFIGURABLE_PUSH_PULL','output'),5:('OSC2','output'),6:('OSC1','input'),7:('VSS','power_in'),8:('GPIO1_INT1','bidirectional'),9:('GPIO0_XSTBY','bidirectional'),10:('SCK','input'),11:('SDI','input'),12:('SDO','tri_state'),13:('CS_N','input'),14:('VDD','power_in')},
 'RSISO':{1:('VIO','power_in'),2:('D','input'),3:('DE','input'),4:('R','output'),5:('RE_N','input'),6:('GNDIO','power_in'),7:('OUT_FIELD_GPIO','output'),8:('EN_FLT_N_FAULT_MODE','open_collector'),9:('VDD','power_in'),10:('GND1','power_in'),11:('GND2','power_in'),12:('VISOOUT','power_out'),13:('MODE','input'),14:('IN_FIELD_GPIO','input'),15:('GISOIN','power_in'),16:('VISOIN','power_in'),17:('Y_NONINVERTING','output'),18:('Z_INVERTING','output'),19:('B_INVERTING','input'),20:('A_NONINVERTING','input')},
 'CANISO':{1:('VIO','power_in'),2:('IN_GPIO','input'),3:('TXD','input'),4:('STB','input'),5:('RXD','output'),6:('GNDIO','power_in'),7:('NC','no_connect'),8:('EN_FLT_N_FAULT_MODE','open_collector'),9:('VDD','power_in'),10:('GND1','power_in'),11:('GND2','power_in'),12:('VISOOUT','power_out'),13:('VSIN','power_in'),14:('OUT_GPIO','output'),15:('GISOIN','power_in'),16:('GISOIN','power_in'),17:('GISOIN','power_in'),18:('CANL','bidirectional'),19:('CANH','bidirectional'),20:('VISOIN','power_in')}
})
MPNS={
 'AND':('SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'OR':('SN74LVC1G32DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'INV':('SN74LVC1G14DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'BUFFER':('SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'WINDOW':('TPS3700DDCR','Package_TO_SOT_SMD:SOT-23-6'),
 'ISO2':('ISO7720FDWR','CNC_MB_Comms:ISO7720_DW16_TI_HV'),
 'BUF4':('74LVC125APW,118','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),
 'SUP':('TPS3839K33DBZR','CNC_MB_Comms:TPS3839_DBZ3_TI'),
 'SWITCH':('TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'OSC':('ASV-40.000MHZ-LC-T','Oscillator:Oscillator_SMD_Abracon_ASV-4Pin_7.0x5.1mm'),
 'CANCTL':('MCP2518FDT-E/SL','Package_SO:SOIC-14_3.9x8.7mm_P1.27mm'),
 'RSISO':('ISOW1432DFMR','CNC_MB_Comms:ISOW_DFM20_TI'),
 'CANISO':('ISOW1044DFMR','CNC_MB_Comms:ISOW_DFM20_TI'),
 'BEAD':('BLM15EX331SN1D','Inductor_SMD:L_0402_1005Metric'),
 'TVS3':('PESD2CANFD24V-T','Package_TO_SOT_SMD:SOT-23')}

def description():
 p={};bounds={};u=r=c=14800;b={}
 def ic(kind,pins,role):
  nonlocal u
  u+=1;ref=f'U{u}';mpn,fp=MPNS[kind];p[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role};return ref
 def res(a,z,v,role,precision=False,termination=False):
  nonlocal r
  r+=1;ref=f'R{r}';codes={22:'22R0',100:'100R',120:'120R',4700:'4K70',10000:'10K0',68100:'68K1',78700:'78K7',107000:'107K',123000:'123K'}
  mpn='CRCW2512120RFKEG' if termination else ('TNPW0603' if precision else 'CRCW0603')+codes[v]+('BEEA' if precision else 'FKEA')
  p[ref]={'kind':'R','mpn':mpn,'value':f'{v}R'+('0.1%' if precision else '1%'),'footprint':'Resistor_SMD:R_2512_6332Metric' if termination else 'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':z},'resistance_ohm':v,'tolerance':.001 if precision else .01,'tcr_ppm_K':25 if precision else 100,'power_rating_w':1 if termination else .1,'role':role};return ref
 def cap(a,z,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,size,v={1:('GRM1885C1H102JA01D','C_0603_1608Metric',50),10:('GRM155R71H103KA88D','C_0402_1005Metric',50),100:('GRM188R72A104KA35D','C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','C_0603_1608Metric',50),22000:('GCM31CR71A226KE02L','C_1206_3216Metric',10)}[nf]
  p[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF{v}V','footprint':'Capacitor_SMD:'+size,'physical':True,'pins':{'1':a,'2':z},'capacitance_f':nf*1e-9,'voltage_rating_v':v,'role':role};return ref
 def bd(ref,nets,role):bounds[ref]={'kind':'Boundary'+str(len(nets)),'mpn':'','value':'PARENT: '+role,'footprint':'','physical':False,'pins':{str(i+1):n for i,n in enumerate(nets)},'role':role}
 # Actual CAN controller power domain. MCP2518FD has NO reset pin: withdraw its supply.
 b['load_switch']=ic('SWITCH',{1:'IO_3V3',2:'LOGIC_GND',3:'COMPUTE_3V3_GOOD',4:'CAN_CTRL_CT',5:'CAN_CTRL_QOD',6:'CAN_CTRL_3V3'},'actual computed-module health power cycles controller and oscillator; no fictitious MCP reset pin')
 res('COMPUTE_3V3_GOOD','LOGIC_GND',4700,'missing module/supervisor enable request defaults LOW')
 cap('IO_3V3','LOGIC_GND',1000,'actual switched-domain input bypass');cap('CAN_CTRL_CT','LOGIC_GND',1,'real load-switch slew control');res('CAN_CTRL_3V3','CAN_CTRL_QOD',100,'real output discharge via QOD while power off');cap('CAN_CTRL_3V3','LOGIC_GND',22000,'controller-domain bulk/discharge storage')
 b['controller_supervisor']=ic('SUP',{1:'LOGIC_GND',2:'CAN_CTRL_READY',3:'CAN_CTRL_3V3'},'actual push-pull delayed rail qualification, 2.857..2.974V trip and120..350ms release; not RESET pin on CAN controller')
 cap('CAN_CTRL_3V3','LOGIC_GND',100,'supervisor bypass');res('CAN_CTRL_READY','LOGIC_GND',10000,'below0.6V supervisor output undefined held LOW by real bias')
 b['link_ready_gate']=ic('AND',{1:'CAN_CTRL_READY',2:'COMPUTE_3V3_GOOD',3:'LOGIC_GND',4:'CAN_CTRL_LINK_READY',5:'IO_3V3'},'real module-health loss inhibits SPI/TX and forces standby without waiting for controller stored-charge discharge');cap('IO_3V3','LOGIC_GND',100,'actual missing-module qualification bypass')
 b['ready_inverter']=ic('INV',{1:None,2:'CAN_CTRL_LINK_READY',3:'LOGIC_GND',4:'CAN_CTRL_OE_N',5:'IO_3V3'},'actual controller readiness, enables Ioff buffers only after real local rail delayed good');cap('IO_3V3','LOGIC_GND',100,'controller qualification inverter bypass')
 b['spi_buffer']=ic('BUF4',{1:'CAN_CTRL_OE_N',2:'CAN_SPI_SCLK_HOST',3:'CAN_CTRL_SCLK_RAW',4:'CAN_CTRL_OE_N',5:'CAN_SPI_MOSI_HOST',6:'CAN_CTRL_MOSI_RAW',7:'LOGIC_GND',8:'CAN_CTRL_CS_RAW',9:'CAN_SPI_CS_N_HOST',10:'CAN_CTRL_OE_N',11:None,12:'LOGIC_GND',13:'CAN_CTRL_3V3',14:'CAN_CTRL_3V3'},'actual Nexperia Ioff protection into power-cycled controller: three active SPI paths, fourth input LOW/output NC/OE HIGH')
 cap('CAN_CTRL_3V3','LOGIC_GND',100,'Ioff SPI buffer bypass')
 for a,z in [('CAN_CTRL_SCLK_RAW','CAN_CTRL_SCLK'),('CAN_CTRL_MOSI_RAW','CAN_CTRL_MOSI'),('CAN_CTRL_CS_RAW','CAN_CTRL_CS_N')]:res(a,z,22,'controller-side actual source series damping')
 for net,rail in [('CAN_CTRL_SCLK','LOGIC_GND'),('CAN_CTRL_MOSI','LOGIC_GND'),('CAN_CTRL_CS_N','CAN_CTRL_3V3'),('CAN_INT_N_HOST','CAN_CTRL_3V3'),('CAN_CTRL_XSTBY','CAN_CTRL_3V3')]:res(net,rail,10000,'actual controller reset/unprogrammed default')
 b['controller']=ic('CANCTL',{1:'CAN_CTRL_TX',2:'CAN_CTRL_RX',3:None,4:'CAN_INT_N_HOST',5:None,6:'CAN_CTRL_OSC',7:'LOGIC_GND',8:None,9:'CAN_CTRL_XSTBY',10:'CAN_CTRL_SCLK',11:'CAN_CTRL_MOSI',12:'CAN_SPI_MISO_HOST',13:'CAN_CTRL_CS_N',14:'CAN_CTRL_3V3'},'real CAN FD SPI controller with externally clocked OSC1; OSC2/CLKO/GPIO1 NC, real reset-push-pull IRQ (configurable open-drain) and GPIO0 transceiver standby')
 cap('CAN_CTRL_3V3','LOGIC_GND',100,'controller VDD local bypass')
 b['clock']=ic('OSC',{1:'CAN_CTRL_3V3',2:'LOGIC_GND',3:'CAN_CTRL_CLOCK_RAW',4:'CAN_CTRL_3V3'},'actual40MHz3.3V oscillator, OE HIGH only on controller rail, -40..85C/50ppm/4ms startup max')
 cap('CAN_CTRL_3V3','LOGIC_GND',100,'clock local bypass');res('CAN_CTRL_CLOCK_RAW','CAN_CTRL_OSC',22,'actual40MHz source damping')
 b['can_tx_buffer']=ic('BUFFER',{1:'CAN_CTRL_OE_N',2:'CAN_CTRL_TX',3:'LOGIC_GND',4:'CAN_TXD',5:'IO_3V3'},'TX buffer powered IO3 keeps transceiver recessive while controller supply missing');cap('IO_3V3','LOGIC_GND',100,'TX Ioff buffer bypass');res('CAN_TXD','IO_3V3',10000,'actual recessive HIGH when controller/clock missing');res('CAN_CTRL_TX','CAN_CTRL_3V3',10000,'actual controller-rail TX bias cannot backpower off controller')
 b['can_rx_buffer']=ic('BUFFER',{1:'CAN_CTRL_OE_N',2:'CAN_RXD',3:'LOGIC_GND',4:'CAN_CTRL_RX',5:'CAN_CTRL_3V3'},'Ioff receiver into power-cycled controller; input tolerant5.5V while supply OFF');cap('CAN_CTRL_3V3','LOGIC_GND',100,'RX Ioff buffer bypass');res('CAN_CTRL_RX','CAN_CTRL_3V3',10000,'receiver recessive when buffer disabled')
 b['standby_gate']=ic('OR',{1:'CAN_CTRL_XSTBY',2:'CAN_CTRL_OE_N',3:'LOGIC_GND',4:'CAN_STANDBY',5:'IO_3V3'},'real standby HIGH until controller rail ready and GPIO0/XSTBY deliberately configured LOW');cap('IO_3V3','LOGIC_GND',100,'standby gate bypass');res('CAN_STANDBY','IO_3V3',4700,'actual HIGH standby bias for start/unpowered outputs')
 b['rs_de_gate']=ic('AND',{1:'RS485_DE_HOST',2:'COMPUTE_3V3_GOOD',3:'LOGIC_GND',4:'RS485_DE_QUALIFIED',5:'IO_3V3'},'real UART driver enable AND actual compute rail, no automatic transmitter enable');cap('IO_3V3','LOGIC_GND',100,'RS485 driver qualification bypass');res('RS485_DE_HOST','LOGIC_GND',10000,'UART DE absent/unprogrammed LOW');res('RS485_DE_QUALIFIED','LOGIC_GND',4700,'actual transceiver DE off default');res('RS485_UART_TX_HOST','IO_3V3',10000,'UART idle HIGH, no transmission without qualified DE')
 b['rs_transceiver']=ic('RSISO',{1:'IO_3V3',2:'RS485_UART_TX_HOST',3:'RS485_DE_QUALIFIED',4:'RS485_UART_RX_HOST',5:'LOGIC_GND',6:'LOGIC_GND',7:'RS485_FIELD_GOOD_HOST',8:'RS485_CONVERTER_GOOD_N',9:'CORE_5V',10:'LOGIC_GND',11:'RS485_ISO_RETURN_RAW',12:'RS485_ISO_3V3_RAW',13:'RS485_ISO_RETURN_RAW',14:'RS485_POWER_GOOD_FIELD',15:'RS485_COM',16:'RS485_FIELD_3V3',17:'RS485_B',18:'RS485_A',19:'RS485_A',20:'RS485_B'},'real12Mbps isolated halfduplex RS485 with integrated3.3V secondary; terminal B is D+ and A is D-, distinct from vendor receiver pin letters')
 b['can_transceiver']=ic('CANISO',{1:'IO_3V3',2:'LOGIC_GND',3:'CAN_TXD',4:'CAN_STANDBY',5:'CAN_RXD',6:'LOGIC_GND',7:None,8:'CAN_CONVERTER_GOOD_N',9:'CORE_5V',10:'LOGIC_GND',11:'CAN_ISO_RETURN_RAW',12:'CAN_ISO_5V_RAW',13:'CAN_ISO_5V_RAW',14:None,15:'CAN_GND',16:'CAN_GND',17:'CAN_GND',18:'CAN_L',19:'CAN_H',20:'CAN_FIELD_5V'},'actual5Mbps physical CAN FD transceiver with isolated5V power; VSIN13 joins raw VISOOUT12, allGISOIN15/16/17 join same actual isolated CAN_GND')
 for tag,rv,rg,sv,sg in [('RS485','RS485_ISO_3V3_RAW','RS485_ISO_RETURN_RAW','RS485_FIELD_3V3','RS485_COM'),('CAN','CAN_ISO_5V_RAW','CAN_ISO_RETURN_RAW','CAN_FIELD_5V','CAN_GND')]:
  b[tag+'_power_bead']=ic('BEAD',{1:rv,2:sv},'actual330ohm100MHz field supply ferrite');b[tag+'_return_bead']=ic('BEAD',{1:rg,2:sg},'actualfieldreturn ferrite; no LOGIC_GND DC bond')
  for rail,gnd in [('CORE_5V','LOGIC_GND'),(rv,rg)]:
   cap(rail,gnd,10,'ISOW prescribed0402 HF bypass <1mm from pins');cap(rail,gnd,1000,'ISOW local1uF bypass');cap(rail,gnd,22000,'firstbulk of44uF nominal; combinedeffective>=10uF acrossbias must bequalified');cap(rail,gnd,22000,'secondbulk of44uF nominal; 2..4mm from HF capacitor')
  cap('IO_3V3','LOGIC_GND',100,'ISOW logic VIO bypass');cap(sv,sg,100,'actual transceiver field supply bypass after bead')
  res(tag+'_CONVERTER_GOOD_N','IO_3V3',10000,'EN/FLT strictly used as fault output with>=5kohm pull-up, not driven enable')
  uv=tag+'_FIELD_UV';ov=tag+'_FIELD_OV';pg=tag+'_POWER_GOOD_FIELD'
  b[tag+'_window']=ic('WINDOW',{1:pg,2:sg,3:uv,4:ov,5:sv,6:pg},'actual fieldrail window observed after supply/return beads; open-drain outputs wireAND')
  lo,hi=(68100,78700) if tag=='RS485' else (107000,123000)
  for a,z,v in [(sv,uv,lo),(uv,sg,10000),(sv,ov,hi),(ov,sg,10000)]:res(a,z,v,'actual .1%25ppm fieldrail monitor divider',True)
  res(pg,sv,10000,'actual monitoredfield PG pullup, never constant healthy');cap(sv,sg,100,'fieldrail monitor bypass')
 b['can_health_isolator']=ic('ISO2',{1:'CAN_GND',2:None,3:'CAN_FIELD_5V',4:'CAN_POWER_GOOD_FIELD',5:'CAN_GND',6:None,7:'CAN_GND',8:None,9:'LOGIC_GND',10:None,11:None,12:None,13:'CAN_FIELD_GOOD_HOST',14:'IO_3V3',15:None,16:'LOGIC_GND'},'actual F-defaultLOW extraisolatedCANrail observation; unusedinputLOW/outputNC')
 cap('CAN_FIELD_5V','CAN_GND',100,'actual health isolation source bypass');cap('IO_3V3','LOGIC_GND',100,'health isolation receive bypass')
 for tag in ['RS485','CAN']:
  b[tag+'_health_gate']=ic('AND',{1:tag+'_FIELD_GOOD_HOST',2:tag+'_CONVERTER_GOOD_N',3:'LOGIC_GND',4:tag+'_POWER_GOOD_HOST',5:'IO_3V3'},'real fieldrail return AND integrated converter fault, distinct from software status/commands');cap('IO_3V3','LOGIC_GND',100,'actual health AND bypass')
 b['can_tvs']=ic('TVS3',{1:'CAN_H',2:'CAN_L',3:'CAN_GND'},'actual24V stand-off6pFtyp CAN-FD ESD network;42Vmax at1A belowtransceiver58Vabs, boardpulse/ESDqualification required')
 b['rs_termination']=res('RS485_A','RS485_TERM',120,'actualoptional120ohm1W termination; external link TERMtoRS485_B only when busendpoint',termination=True)
 b['can_termination']=res('CAN_L','CAN_TERM',120,'actualoptional120ohm1W termination; external link TERMtoCAN_H only when busendpoint',termination=True)
 bd('J14801',['IO_3V3','CORE_5V','LOGIC_GND','COMPUTE_3V3_GOOD'],'actual parent powers and module-own supervisedrail, not constanthealthy')
 bd('J14802',['RS485_UART_TX_HOST','RS485_UART_RX_HOST','RS485_DE_HOST','CAN_SPI_SCLK_HOST','CAN_SPI_MOSI_HOST','CAN_SPI_MISO_HOST','CAN_SPI_CS_N_HOST','CAN_INT_N_HOST'],'exact qualified compute UART/SPI1; GPIO14contact55 ESP UART retained')
 bd('J14803',['RS485_POWER_GOOD_HOST','CAN_POWER_GOOD_HOST'],'actual ACC PD0/PD1 observations, no ACC data bus')
 bd('J14804',['RS485_B','RS485_A','RS485_COM','RS485_TERM','CAN_H','CAN_L','CAN_GND','CAN_TERM'],'actual parent field terminals; parent owns CHASSIS/HF coupling without DC return ties')
 return {'schema_version':1,'revision':'motherboard-comms-r0.1','status':'actual_source_candidate','components':p,'boundaries':bounds,'blocks':b,'fitted_component_count':len(p),'fitted_pad_count':sum(len(q['pins']) for q in p.values()),'manufacturing_ready':False,'physical_qualification':False,'firmware_implemented':False,'target_image_compiled':False,'limits':{'RS485_target_bps':1000000,'RS485_part_max_bps':12000000,'RS485_common_mode_v':[-7,12],'RS485_abs_bus_v':[-12,15],'CAN_target_data_bps':2000000,'CAN_part_max_bps':5000000,'CAN_abs_bus_v':[-58,58],'CAN_common_mode_v':[-12,12],'controller_SPI_hz_candidate':10000000,'controller_SPI_part_max_hz':20000000,'controller_external_clock_hz':40000000,'RS485_intrinsic_device_IEC_contact_v':8000,'RS485_external_TVS_fitted':False,'RS485_board_surge_claim':False},'power_budget':{'IO_3V3_bypass_nominal_uf':sum(q['capacitance_f'] for q in p.values() if q['kind']=='C' and q['pins']['1']=='IO_3V3')*1e6,'CAN_CTRL_bypass_nominal_uf':sum(q['capacitance_f'] for q in p.values() if q['kind']=='C' and q['pins']['1']=='CAN_CTRL_3V3')*1e6,'MCP2518FD_max_at40MHz_SYSCLK_20MHzSPI_a':.020,'ASV_max_at40MHz_a':.025,'RS485_CORE5_max_12Mbps54ohm_REdisabled_a':.130,'CAN_CORE5_max_dominant60ohm_a':.211,'CAN_ISO_extra_available_a':.020,'RS485_IO3_max_12Mbps_loopback_a':.0072,'CAN_IO3_max_5Mbps_a':.0062,'no_total_dynamic_budget_claim':True},'defaults':{'missing_compute_powers_off_CAN_controller':True,'CAN_controller_has_no_reset_pin':True,'CAN_standby_until_real_ready_and_XSTBY_LOW':True,'RS485_DE_LOW_when_missing_compute':True,'separate_isolated_COMs':True,'native_health_not_synthetic':True,'automatic_motion_rearm':False},'open_gates':['Compute carrier pinmux/device-tree/SocketCAN and UART driver images remain target uncompiled; CM4/CM5 RTS-only mapping must retain GPIO14 ESP UART; BTT mappings not implicitly qualified.','MCP2518FD actual power-off discharge and POR below datasheet voltage, firstclock/CS ordering, FIFO generation/reset/reconnect and XSTBY driver setup require target compile and measured startup/failure tests. SPI RESET does not erase message RAM.','ISOW intrinsic contact ESD is device evidence, not board EMC/surge qualification. External SM712 was rejected because its19Vpositiveclamp exceedsRS48515Vabs. No arbitrary24Vbusmiswire/surge rating is claimed.','CAN TVS manufacturer type/package verified; packing order suffix/stock and production procurement require outside supplier confirmation.42Vclamp at1A is not allsurge/boardfault qualification.','ISOW layout requires10nF within1mm and bulk2..4mm/effective>=10uF, rawreturn/power routing exclusions4mm and allGISOIN tied locally. Creepage/return ferrite/cable/commonmode/thermal/EMC require nativeboard andphysicalvalidation.','2MbpsCAN loaded loop/samplepoint budget,10MHzSPI route/buffer roundtrip and1MbpsRS485 hostRTSturnaround require target/board latency proof. Standby/driver disable are communications defaults and do not replace independent20msmotioninhibit.','TPS3839 supervisor120..350ms validrelease and20us typfaultdelay are not a hardware20mswatchdog. Native source/ERC does not establish manufacture readiness.']}

def footprints(out):
 lib=out/'CNC_MB_Comms.pretty';lib.mkdir(exist_ok=True)
 shutil.copyfile(ROOT/'hardware/motherboard_analog_output/CNC_MB_AO.pretty/ISO7720_DW16_TI_HV.kicad_mod',lib/'ISO7720_DW16_TI_HV.kicad_mod')
 def emit(name,body,pads,description):
  x,y=body;cx=max(x/2,max(abs(z[1])+z[3]/2 for z in pads))+.3;cy=max(y/2,max(abs(z[2])+z[4]/2 for z in pads))+.3
  raw=f'(footprint "{name}"(version 20241229)(generator "controller_hardware")(layer "F.Cu")(descr {quote(description)})(attr smd)(property "Reference" "REF**"(at 0 {-cy-1} 0)(layer "F.SilkS"){effects(.7)})(property "Value" "{name}"(at 0 {cy+1} 0)(layer "F.Fab"){effects(.7)})(fp_rect(start {-x/2} {-y/2})(end {x/2} {y/2})(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start {-cx} {-cy})(end {cx} {cy})(stroke(width .05)(type default))(layer "F.CrtYd"))(fp_text user "1"(at {-cx} {-cy-.4} 0)(layer "F.SilkS"){effects(.6)})'
  for n,px,py,w,h in pads:raw+=f'(pad "{n}" smd rect(at {px} {py})(size {w} {h})(layers "F.Cu" "F.Paste" "F.Mask"))'
  (lib/(name+'.kicad_mod')).write_text(dump(parse(raw+')'))+'\n',encoding='utf-8')
 emit('ISOW_DFM20_TI',(7.5,12.83),[(n,-4.85 if n<=10 else 4.85,(n-1)*1.27-5.715 if n<=10 else (20-n)*1.27-5.715,2.1,.6) for n in range(1,21)],'TI DFM0020A4225640/A01/2020: exact20leads2.1x.6 atx+-4.85,pitch1.27,body7.5x12.83,height3.55. Native isolation/4mmconverterpour/HFbypass geometry still parent responsibility.')
 emit('TPS3839_DBZ3_TI',(1.3,2.9),[(1,-1.05,-.95,1.3,.6),(2,-1.05,.95,1.3,.6),(3,1.05,0,1.3,.6)],'TI DBZ0003A4214838/F08/2024 land centres2.1x1.9, pads1.3x.6, TOP1GND2RESET3VDD, stockSOT transistor pin assumption prohibited.')
 (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MB_Comms")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Comms.pretty")(options "")(descr "Primary sourced communication footprints")))'))+'\n',encoding='utf-8')


def build(out=OUT):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);d=description();parts={**d['components'],**d['boundaries']};functions=dict(KINDS);uid=lambda n:str(uuid.uuid5(NS,n));root=uid('root');libs=[];layouts={}
 for p in d['boundaries'].values():functions[p['kind']]={int(k):(k,'passive') for k in p['pins']}
 for kind,table in functions.items():
  if kind in ['R','C','TVS']:layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
  elif kind=='PWR_FLAG':layout=[(1,'pwr',0,0,90,'power_out')];body=''
  else:
   keys=sorted(table);half=(len(keys)+1)//2;layout=[(n,table[n][0],sign*12.7,20.32-i*5.08,0 if sign<0 else 180,table[n][1]) for sign,nums in [(-1,keys[:half]),(1,keys[half:])] for i,n in enumerate(nums)];low=min(p[3] for p in layout)-5.08;body=f'(rectangle(start -10.16 25.4)(end 10.16 {low})(stroke(width .254)(type default))(fill(type background)))'
  layouts[kind]=layout;libs.append(symbol(kind,layout,body,'R' if kind=='R' else 'C' if kind=='C' else 'D' if kind=='TVS' else 'J' if kind.startswith('Boundary') else '#FLG' if kind=='PWR_FLAG' else 'U'))
 items=[];netmap={};ic=pas=bnd=0
 for ref,p in parts.items():
  if ref.startswith('U'):x=63.5+(ic%7)*165.1;y=83.82+(ic//7)*160.02;ic+=1
  elif p['physical']:x=40.64+(pas%17)*68.58;y=1201.42+(pas//17)*30.48;pas+=1
  else:x=63.5+(bnd%7)*165.1;y=1691.64+(bnd//7)*190.5;bnd+=1
  layout=layouts[p['kind']];small=p['kind'] in ['R','C','TVS'];rx=x+3.81 if small else x;ry=y-2.54 if small else y-max(z[3] for z in layout)-10.16
  props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hide else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
  yes='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {yes})(on_board {yes})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_comms"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for n,_,px,py,_,_ in layout:
   sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
   if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
   dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else 5.08;ex,ey=round(sx+dx,4),round(sy+dy,4)
   items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))');items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
 for i,net in enumerate(['IO_3V3','LOGIC_GND','CORE_5V','RS485_ISO_RETURN_RAW','CAN_ISO_RETURN_RAW','RS485_COM','RS485_FIELD_3V3','CAN_GND','CAN_FIELD_5V']):
  ref=f'#FLG148{i}';x=30.48+i*139.7;y=2080.26;items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "PARENT SUPPLY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_comms"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
 note='ACTUAL ISOLATED RS485 AND CAN FD / actual UART, SPI controller, clock, power-cycle and hardware rail/fault observations.\nNative source only; target image/pinmux/failure/startup/EMC and loaded timing remain qualification.'
 items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
 raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1270 2200)(title_block(title "Motherboard isolated RS485 and CAN FD")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
 (out/'motherboard_comms.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8');(out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8');(out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Analog output source")))'))+'\n',encoding='utf-8');(out/'motherboard_comms.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_comms.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n');footprints(out)
 for name,obj in [('design',d),('pin-map',netmap),('boundary-map',d['boundaries'])]:(out/(name+'.json')).write_text(json.dumps(obj,indent=2)+'\n')
 with (out/'bom.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader();w.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in d['components'].items())
 print(json.dumps({'components':len(d['components']),'pads':d['fitted_pad_count'],'manufacturing_ready':False}));return d

if __name__=='__main__':build()

