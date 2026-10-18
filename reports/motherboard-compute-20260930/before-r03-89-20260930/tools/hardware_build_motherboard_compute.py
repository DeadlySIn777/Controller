"""Source-reviewed CM4/CM5 socket pair and qualified-domain SPI carrier.

Two commodity sockets are fitted on the ONE motherboard. The compute SoM is
a separately purchased assembly, not a duplicate soldered processor. Exact
high-speed port/SD/NVMe boundaries remain visible until their circuits exist.
"""
from __future__ import annotations
import copy,csv,hashlib,json,uuid,shutil
from pathlib import Path
from hardware_build_assembly import parse,dump,children,child,value,point,q
from hardware_build_tx_schematic import symbol,effects,quote

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_compute'
REPORT=ROOT/'reports/motherboard-compute-20260930'
SOURCES=REPORT/'sources'
AUDIT=ROOT/'reports/board-completion-20260930/compute-bay-pin-audit'
OFFICIAL_FP=SOURCES/'cm5io-rev2-official/CM5IO.pretty/Raspberry-Pi-5-Compute-Module.kicad_mod'
NS=uuid.UUID('306db01a-f898-4977-bcec-e84702d7a47d')
SOCKET_MPN='10164227-1001A1RLF'
LIB='CNC_COMPUTE'

KINDS={
 'BUF':{1:('OE_N','input'),2:('A','input'),3:('GND','power_in'),4:('Y','tri_state'),5:('VCC','power_in')},
 'SCHMITT':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'NAND3':{1:('A','input'),2:('GND','power_in'),3:('B','input'),4:('Y','output'),5:('VCC','power_in'),6:('C','input')},
 'SUP':{1:('RESET_N','open_collector'),2:('GND','power_in'),3:('MR_N','input'),4:('CT','passive'),5:('SENSE','input'),6:('VDD','power_in')},
 'DIP3':{i:(str(i),'passive') for i in range(1,7)},
 'SD_SLOT':{1:('DAT2','passive'),2:('DAT3_CD','passive'),3:('CMD','passive'),4:('VDD','power_in'),5:('CLK','passive'),6:('VSS','power_in'),7:('DAT0','passive'),8:('DAT1','passive'),9:('DETECT_LEVER_VSS','passive'),10:('DETECT_SWITCH','passive'),11:('SHELL','passive')},
 'SD_PWR':{1:('IN','power_in'),2:('GND','power_in'),3:('EN','input'),4:('FAULT_N','open_collector'),5:('ILIM','passive'),6:('OUT','power_out')},
 'SD_SUP':{1:('RESET_N','open_collector'),2:('GND','power_in'),3:('MR_N','input'),4:('CT','passive'),5:('SENSE','input'),6:('VDD','power_in')},
 'NAND2':{1:('A','input'),2:('B','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
 'SD_MUX':{1:('NC2','passive'),2:('NC1','passive'),3:('NC','no_connect'),4:('COM1','passive'),5:('GND','power_in'),6:('COM2','passive'),7:('COM3','passive'),8:('VCC','power_in'),9:('COM4','passive'),10:('COM5','passive'),11:('NO1','passive'),12:('COM6','passive'),13:('NO2','passive'),14:('IN2','input'),15:('NO3','passive'),16:('NO6','passive'),17:('NO4','passive'),18:('NO5','passive'),19:('NC5','passive'),20:('EN_N','input'),21:('NC4','passive'),22:('NC6','passive'),23:('NC3','passive'),24:('IN1','input')},
 'ESD4':{1:('D1_P','passive'),2:('D1_N','passive'),3:('GND','power_in'),4:('D2_P','passive'),5:('D2_N','passive'),6:('NC','no_connect'),7:('NC','no_connect'),8:('GND','power_in'),9:('NC','no_connect'),10:('NC','no_connect')},
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},
 'TP':{1:('TP','passive')},'PWR_FLAG':{1:('pwr','power_out')}}
MPNS={'BUF':('SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'SCHMITT':('SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'NAND3':('SN74LVC1G10DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'SUP':('TPS3808G33DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'DIP3':('219-3MSTRF','CNC_COMPUTE:CTS_219-3M_GullWing'),
 'SD_PWR':('TPS2553DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'SD_SUP':('TPS3808G30DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'NAND2':('SN74LVC1G00DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'SD_MUX':('TS3A27518EPWR','Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm'),
 'ESD4':('TPD4E05U06DQAR','CNC_COMPUTE:TI_DQA0010A_TPD4E05U06')}

RAW_BUS={38:'CM_HOST_SPI_SCLK',40:'CM_HOST_SPI_MISO',44:'CM_HOST_SPI_MOSI',
         47:'CM_HOST_SPI_CS_CMD_N',54:'CM_HOST_SPI_CS_FB_N'}


def description():
 matrix=json.loads((AUDIT/'pin-matrix.json').read_text(encoding='utf8'))['pins']
 parts={};u=r=c=t=15000
 def add(kind,pins,role):
  nonlocal u
  u+=1;ref=f'U{u}';mpn,fp=MPNS[kind]
  parts[ref]=dict(kind=kind,mpn=mpn,value=mpn,footprint=fp,physical=True,dnp=False,pins={str(k):v for k,v in pins.items()},role=role)
  return ref
 def res(a,b,ohm,role):
  nonlocal r
  r+=1;ref=f'R{r}';mpn={33:'CRCW060333R0FKEA',1000:'CRCW06031K00FKEA',10000:'CRCW060310K0FKEA',47000:'CRCW060347K0FKEA',76800:'CRCW060376K8FKEA',49.9:'CRCW060349R9FKEA'}[ohm]
  parts[ref]=dict(kind='R',mpn=mpn,value=f'{ohm}R 1%',footprint='Resistor_SMD:R_0603_1608Metric',physical=True,dnp=False,pins={'1':a,'2':b},role=role,resistance_ohm=ohm,tolerance=.01)
  return ref
 def cap(net,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,fp,v={100:('GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','Capacitor_SMD:C_0603_1608Metric',50),10000:('GRM21BR61E106KA73L','Capacitor_SMD:C_0805_2012Metric',25),.13:('GRM1885C1H131JA01D','Capacitor_SMD:C_0603_1608Metric',50)}[nf]
  parts[ref]=dict(kind='C',mpn=mpn,value=f'{nf}nF {v}V',footprint=fp,physical=True,dnp=False,pins={'1':net,'2':'LOGIC_GND'},role=role,capacitance_f=nf*1e-9,voltage_rating_v=v)
  return ref
 def tp(net,role):
  nonlocal t
  t+=1;ref=f'TP{t}'
  parts[ref]=dict(kind='TP',mpn='PCB_COPPER_TEST_PAD_D1.0',value=net,footprint='TestPoint:TestPoint_Pad_D1.0mm',physical=True,dnp=False,pins={'1':net},role=role,purchased=False)
  return ref
 socket_nets={p['global_pin']:None for p in matrix}
 for p in matrix:
  if p['cm4_signal']=='GND' and p['cm5_signal']=='GND':socket_nets[p['global_pin']]='LOGIC_GND'
 for pin in [77,79,81,83,85,87]:socket_nets[pin]='SBC_5V'
 for pin in [78,84,86]:socket_nets[pin]='CM_AUX_3V3'
 socket_nets.update(RAW_BUS)
 socket_nets[55]='COMPUTE_SERVICE_TX'
 socket_nets[93]='CM_nRPIBOOT'
 # Restricted contact92 is deliberately NOT wired. CM4 RUN_PG is not CM5's
 # PWR_Button. Module-derived 1V8, fan, PMIC, EEPROM and radio controls remain NC.
 interface_groups={
  'ethernet':{pin:'CM_'+p['cm5_signal'] for p in matrix for pin in [p['global_pin']] if pin in [3,4,5,6,9,10,11,12,15,17]},
  'usb2':{101:'CM_USB_OTG_ID',103:'CM_USB2_N',105:'CM_USB2_P'},
  'sd':{57:'CM_SD_CLK',61:'CM_SD_DAT3',62:'CM_SD_CMD',63:'CM_SD_DAT0',67:'CM_SD_DAT1',69:'CM_SD_DAT2',75:'CM_SD_PWR_ON'},
  'hdmi0':{pin:'CM_'+p['cm5_signal'] for p in matrix for pin in [p['global_pin']] if pin in [151,153,170,172,176,178,182,184,188,190,199,200]},
  'pcie':{102:'CM_PCIE_CLKREQ_N',109:'CM_PCIE_PERST_N',110:'CM_PCIE_REFCLK_P',112:'CM_PCIE_REFCLK_N',116:'CM_PCIE_RX_P',118:'CM_PCIE_RX_N',122:'CM_PCIE_TX_P',124:'CM_PCIE_TX_N'}}
 for group in interface_groups.values():socket_nets.update(group)
 for index,ref in enumerate(['J15001','J15002']):
  parts[ref]=dict(kind='SocketA' if index==0 else 'SocketB',mpn=SOCKET_MPN,value=SOCKET_MPN,footprint='CNC_COMPUTE:Amphenol_10164227_1001_CM_A' if index==0 else 'CNC_COMPUTE:Amphenol_10164227_1001_CM_B',physical=True,dnp=False,
   pins={str(i):socket_nets[i+index*100] for i in range(1,101)},role='purchased100-contact carrier receptacle; not the compute SoM',
   global_contact_offset=index*100,pad_geometry_source='Raspberry Pi official CM5IO revision2 native CAD',
   manufacturer_drawing_visual_review_complete=False)
 cap('SBC_5V',10000,'bay entry local10uF bulk; full branch inrush qualification required')
 cap('SBC_5V',100,'bay power local bypass')
 cap('CM_AUX_3V3',1000,'module auxiliary local1uF; cannot feed from carrier IO rail')
 sup=add('SUP',{1:'CM_AUX_RESET_N',2:'LOGIC_GND',3:'CM_AUX_MR_N',4:None,5:'CM_AUX_3V3',6:'CM_AUX_3V3'},'actual module3V3 supervision;3.07V threshold20msnominal release; no OS identity/ready inference')
 cap('CM_AUX_3V3',100,sup+' supply bypass')
 res('CM_AUX_RESET_N','CM_AUX_3V3',10000,'module-domain open-drain reset pullup; no always-on injection')
 res('CM_AUX_MR_N','CM_AUX_3V3',10000,'supervisor manual-reset default released')
 gates=[]
 for raw,good in [('CM_AUX_RESET_N','COMPUTE_3V3_GOOD'),('FPGA_CRESET_N','CM_FPGA_RAILS_QUALIFIED'),('FPGA_CDONE','CM_FPGA_CONFIGURED')]:
  gate=add('SCHMITT',{1:None,2:raw,3:'LOGIC_GND',4:good,5:'IO_3V3'},'Ioff-rated Schmitt qualification crossing; missing source defaults LOW')
  gates.append(gate);cap('IO_3V3',100,gate+' bypass')
  # The raw module open-drain reset already has its own same-domain pullup.
  # Its ground default is at the crossing input and loads that pullup weakly;
  # use no duplicate10k divider. Below module VDD=0, internal pullup is also0.
  if raw!='CM_AUX_RESET_N':res(raw,'LOGIC_GND',47000 if raw=='FPGA_CDONE' else 10000,'missing qualification input LOW;47kCDONE avoids divider with retainedR1003 10kopen-drain pullup')
 gate=add('NAND3',{1:'COMPUTE_3V3_GOOD',2:'LOGIC_GND',3:'CM_FPGA_RAILS_QUALIFIED',4:'CM_HOST_OE_N',5:'IO_3V3',6:'CM_FPGA_CONFIGURED'},'actual SPI buffers enabled only module3V3 AND native FPGA reset released AND CDONE')
 cap('IO_3V3',100,gate+' bypass');res('CM_HOST_OE_N','IO_3V3',10000,'tri-state forward buffers during gate power ramp')
 channels=[]
 for pin,suffix,default in [(38,'SCLK','LOW'),(44,'MOSI','LOW'),(54,'CS_FB_N','HIGH'),(47,'CS_CMD_N','HIGH')]:
  raw=RAW_BUS[pin];driver=add('BUF',{1:'CM_HOST_OE_N',2:raw,3:'LOGIC_GND',4:'CM_FWD_'+suffix,5:'IO_3V3'},'Ioff-rated module to FPGA host link; source33R damping; no wired parallel driver')
  cap('IO_3V3',100,driver+' bypass');series=res('CM_FWD_'+suffix,'HOST_SPI_'+suffix,33,'source series damping; SI/rate remain unmeasured')
  res(raw,'CM_AUX_3V3' if default=='HIGH' else 'LOGIC_GND',10000,'module-domain inactive input; no IO rail to unpowered compute')
  res('HOST_SPI_'+suffix,'IO_3V3' if default=='HIGH' else 'LOGIC_GND',10000,'FPGA-domain static default while forward buffer disabled')
  channels.append(dict(contact=pin,signal='HOST_SPI_'+suffix,raw_net=raw,direction='compute_to_fpga',buffer=driver,series_resistor=series,disabled_default=default))
 driver=add('BUF',{1:'CM_HOST_OE_N',2:'HOST_SPI_MISO',3:'LOGIC_GND',4:'CM_RET_MISO',5:'CM_AUX_3V3'},'Ioff-rated FPGA to module MISO; output dies with module supply; VI/OE tolerate poweredIO whenmoduleoff')
 cap('CM_AUX_3V3',100,driver+' bypass');series=res('CM_RET_MISO','CM_HOST_SPI_MISO',33,'source series damping in module domain')
 res('HOST_SPI_MISO','LOGIC_GND',10000,'unconfigured FPGA MISO defaults LOW');res('CM_HOST_SPI_MISO','LOGIC_GND',10000,'module input default LOW while return buffer disabled')
 channels.append(dict(contact=40,signal='HOST_SPI_MISO',raw_net='CM_HOST_SPI_MISO',direction='fpga_to_compute',buffer=driver,series_resistor=series,disabled_default='LOW'))
 switch=add('DIP3',{1:'COMPUTE_PROFILE0',2:'COMPUTE_PROFILE1',3:'COMPUTE_PROFILE2',4:'IO_3V3',5:'IO_3V3',6:'IO_3V3'},'read-only cold-start profile selection, factory OFF/AUTO; no permission/reset routing')
 for bit in range(3):res('COMPUTE_PROFILE'+str(bit),'LOGIC_GND',10000,'OFF switch selects zero; selector only metadata/profile policy')
 tp('CM_nRPIBOOT','passive LOW recovery request on exact supportedPi procedure only; never ESP-driven')
 tp('LOGIC_GND','recovery request paired ground pad')
 res('CM_AUX_3V3','LOGIC_GND',1000,'actual missing-module auxiliary discharge/default reference; no assumed absentmodule zero voltage')
 # Native SD port extension. All original52 fitted pin assignments remain.
 slot='J15003'
 parts[slot]=dict(kind='SD_SLOT',mpn='503398-1892',value='503398-1892',footprint='CNC_COMPUTE:Molex_503398-1892_SD',physical=True,dnp=False,pins={str(k):v for k,v in {1:'SD_PORT_DAT2',2:'SD_PORT_DAT3',3:'SD_PORT_CMD',4:'SD_PORT_3V3',5:'SD_PORT_CLK',6:'LOGIC_GND',7:'SD_PORT_DAT0',8:'SD_PORT_DAT1',9:'LOGIC_GND',10:'SD_CARD_PRESENT_N',11:'LOGIC_GND'}.items()},role='actual purchased microSD push-push slot; Lite-only electrical profile; pin9detect leverVSS, pin10detectswitch; four numbered11shell pads')
 psw=add('SD_PWR',{1:'CM_AUX_3V3',2:'LOGIC_GND',3:'CM_SD_PWR_ON',4:'SD_POWER_FAULT_N',5:'SD_ILIM',6:'SD_PORT_3V3'},'module-aux powered SD switch;76.8k1% limits303.39..391.93mA; reverse shutdown has finite comparator delay, not ideal reverse blocking')
 cap('CM_AUX_3V3',100,psw+' input bypass');cap('CM_AUX_3V3',1000,psw+' local input reservoir')
 cap('SD_PORT_3V3',10000,'card local10uF, powerup/current anddischarge require measurement');cap('SD_PORT_3V3',100,'card local100nF')
 res('SD_ILIM','LOGIC_GND',76800,'actual programmed current cap; TI IOS equations plus resistor1%')
 res('CM_SD_PWR_ON','CM_AUX_3V3',10000,'boot defaultON module-domain; Pi Lite needs externalpullup; never ownalways-onIOrail')
 res('SD_POWER_FAULT_N','CM_AUX_3V3',10000,'switch fault open-drain same-domain observation')
 res('SD_PORT_3V3','LOGIC_GND',1000,'actual discharge for cardreset and boundedoff-leakage;~3.3mAnormal; measuredpoweroff dwell stillrequired')
 ssup=add('SD_SUP',{1:'SD_PORT_POWER_GOOD',2:'LOGIC_GND',3:'SD_PORT_MR_N',4:'SD_PORT_CT',5:'SD_PORT_3V3',6:'CM_AUX_3V3'},'actual cardpower2.79V supervision; threshold±1.25% to85C;130pFtd0.75..1.75ms; no assumedcardready/identity')
 cap('CM_AUX_3V3',100,ssup+' supply bypass');cap('SD_PORT_CT',.13,'130pF C0G5% actual supervisor CT; quotedtdcoversdevice notcap/wiring uncertainty')
 res('SD_PORT_POWER_GOOD','CM_AUX_3V3',10000,'open-drain supply-valid indication same-domainpullup')
 res('SD_PORT_MR_N','CM_AUX_3V3',10000,'actual supervisor releasedmanualreset default')
 sgate=add('NAND2',{1:'CM_SD_PWR_ON',2:'SD_PORT_POWER_GOOD',3:'LOGIC_GND',4:'SD_BUS_OE_N',5:'CM_AUX_3V3'},'SD mux can passsignals only while controller requests power AND actualSD supplygood; defaultoff during startup/off')
 cap('CM_AUX_3V3',100,sgate+' bypass');res('SD_BUS_OE_N','CM_AUX_3V3',10000,'actual mux disabled if controlgate notpowered/undefined')
 res('CM_SD_CLK','SD_CLK_DAMPED',33,'module-clock source damping before mux; actual50MHz timing/SI unqualified')
 smap={1:'SD_PORT_CMD',2:'SD_PORT_CLK',3:None,4:'SD_CLK_DAMPED',5:'LOGIC_GND',6:'CM_SD_CMD',7:'CM_SD_DAT0',8:'CM_AUX_3V3',9:'CM_SD_DAT1',10:'CM_SD_DAT2',11:'SD_UNUSED_NO1',12:'CM_SD_DAT3',13:'SD_UNUSED_NO2',14:'LOGIC_GND',15:'SD_UNUSED_NO3',16:'SD_UNUSED_NO6',17:'SD_UNUSED_NO4',18:'SD_UNUSED_NO5',19:'SD_PORT_DAT2',20:'SD_BUS_OE_N',21:'SD_PORT_DAT1',22:'SD_PORT_DAT3',23:'SD_PORT_DAT0',24:'LOGIC_GND'}
 smux=add('SD_MUX',smap,'six realSD signal paths; IN1/2 grounded selectsNC bank; EN_Npowerqualification; Ioff and poweredoff isolation; PW package exactmanufacturerpinmap')
 cap('CM_AUX_3V3',100,smux+' bypass')
 for i in range(1,7):res('SD_UNUSED_NO'+str(i),'LOGIC_GND',49.9,'mfrrecommended50R unusedanalogporttermination; unusedNO bank isnever selected')
 for suffix in ['CMD','DAT0','DAT1','DAT2','DAT3']:res('SD_PORT_'+suffix,'SD_PORT_3V3',10000,'card-side pullup dies with actualcardrail; no alwaysonmoduleauxbackpower')
 res('SD_CARD_PRESENT_N','CM_AUX_3V3',10000,'actualmechanicalcarddetect switch; no inferencefromOSorcontents')
 esd0=add('ESD4',{1:'SD_PORT_CLK',2:'SD_PORT_CMD',3:'LOGIC_GND',4:'SD_PORT_DAT0',5:'SD_PORT_DAT1',6:None,7:None,8:'LOGIC_GND',9:None,10:None},'four actualcardline ESD channels; passive5.5V standoff .5pFtyp, component12kVcontact; wholeportqualificationunproved')
 esd1=add('ESD4',{1:'SD_PORT_DAT2',2:'SD_PORT_DAT3',3:'LOGIC_GND',4:None,5:None,6:None,7:None,8:'LOGIC_GND',9:None,10:None},'two actualcardlineESD paths withtwo unusedprotectedchannelsNC; exactTI DQA0010Aground3/8')
 tp('SD_CARD_PRESENT_N','mechanicalcarddetectobservation; hostdiagnosticallocationunimplemented')
 tp('SD_POWER_FAULT_N','actualswitchfaultobservation; hostdiagnosticallocationunimplemented')
 sd=dict(slot=slot,power_switch=psw,power_supervisor=ssup,signal_mux=smux,enable_gate=sgate,esd=[esd0,esd1],limiting_resistor_ohm=76800,resistor_tolerance=.01,current_limit_min_a=25230/(76.8*1.01)**1.016/1000,current_limit_max_a=22980/(76.8*.99)**.94/1000,aux_consumption_reservation_a=.41,initial_card_profile='3.3V signalling/highspeed50MHz maximum candidate; exactcardstartup/current/temperature qualificationrequired',qualified_cards=[],boot_image_verified=False,physical_qualification=False,cardpoweroff_signal_isolation_implemented=True,hot_swap_qualified=False,external_injection_or_ideal_reverse_blocking_claim=False,diagnostics_allocated=False)
 bounds={}
 def boundary(ref,nets,role):bounds[ref]=dict(kind='Boundary'+str(len(nets)),mpn='',value=role,footprint='',physical=False,dnp=False,pins={str(i+1):n for i,n in enumerate(nets)},role=role)
 boundary('B15001',['SBC_5V','IO_3V3','LOGIC_GND','FPGA_CRESET_N','FPGA_CDONE'],'actual protected parent supplies and native FPGA qualification observations')
 boundary('B15002',['HOST_SPI_SCLK','HOST_SPI_MOSI','HOST_SPI_CS_FB_N','HOST_SPI_CS_CMD_N','HOST_SPI_MISO'],'dedicated frozen dual-CS FPGA host interface; no Ethernet in hard timing path')
 boundary('B15003',['COMPUTE_SERVICE_TX','COMPUTE_PROFILE0','COMPUTE_PROFILE1','COMPUTE_PROFILE2','COMPUTE_3V3_GOOD'],'read-only ESP service/profile/actual supply observation; neither ID nor OS-ready')
 for i,(group,pins) in enumerate(interface_groups.items(),4):
  boundary(f'B1500{i}',list(pins.values())+['SBC_5V','CM_AUX_3V3','LOGIC_GND'],group+' exact compute interface; SD circuitrysourceimplemented; otherexternalportsNOTimplemented')
 return dict(schema_version=1,revision='motherboard-compute-r0.2-protected-SD',parent_reference_index=15,
  status='native_socket_host_and_protected_SD_source_candidate; USB_HDMI_Ethernet_NVMe_boundaries_incomplete',manufacturing_ready=False,physical_qualification=False,
  components={**parts,**bounds},sd_port=sd,aux_load_budget={'reserved_module_aux3v3_a':.410,'includes_SD_actual_branch_and_carrier':True,'USB_hub_not_implemented_or_included':True,'converted_5v_additional_screen_a':.410*3.465/(4.95*.85),'assumed_module_aux_conversion_efficiency':.85,'module_aux_conversion_efficiency_qualified':False,'SBC_3A_compute2p5_USB0p5_simultaneous_profile_closed':False},host_channels=channels,sockets=['J15001','J15002'],module_parts_separate=True,compute_som_fitted_on_carrier_bom=False,
  socket_contact_map={str(k):v for k,v in socket_nets.items()},interface_groups=interface_groups,
  compute_aux_supervisor=sup,host_enable_gate=gate,qualification_schmitt=gates,selector_ref=switch,
  module_power=dict(input='SBC_5V',ground='LOGIC_GND',power_contacts=[77,79,81,83,85,87],ground_contacts=[p['global_pin'] for p in matrix if socket_nets[p['global_pin']]=='LOGIC_GND'],aux3v3_contacts=[84,86],gpio_vref_contact=78,aux3v3_max_total_a=.6,aux3v3_max_per_contact_a=.3,module_power_planning_cap_a=2.5,SBC_branch_planning_cap_a=3,externalUSB_planning_cap_a=.5,full_capacity_qualified=False),
  socket_rating=dict(all_contacts_simultaneous_a=.3,main5v_contact_count=6,blanket_rating_total_a=1.8,planned_2p5A_selective_contact_rating_or_temperature_qualification=False),
  mechanical=dict(module_outline_mm=[40,55],hole_grid_mm=[33,48],hole_diameter_mm=2.7,mounting_screw='M2.5',socket_center_separation_mm=34,socket_A_origin_relative_module_mount_mm=[-.5,-21.5],socket_B_origin_relative_module_mount_mm=[33.5,-21.5],required_same_rotation=True,connector_mated_height_mm=1.5,module_under_clearance_mm=0,approx_mounted_top_height_mm=4.94,antenna_and_heatsink_keepout_qualified=False),
  selector=dict(bits=3,codes={'0':'AUTO_SERVICE_UNTIL_EXACT_ID_VERIFIED','1':'CM4','2':'CM5','3':'CB1_SD_v2p2_CANDIDATE','4':'CB2_CANDIDATE','5':'UNSUPPORTED','6':'UNSUPPORTED','7':'UNSUPPORTED'},DIP_controls_electrical_power_or_permission=False,automatic_hardware_ID_implemented=False,software_profile_implemented=False),
  profiles={'CM4':{'pin_sources_checked':True,'target_image_and_pinmux_qualified':False},'CM5':{'pin_sources_checked':True,'target_image_and_pinmux_qualified':False},'CB1_SD_v2p2':{'full_electrical_qualification':False,'machine_use_enabled':False},'CB1_eMMC':{'full_200_contact_mapping_available':False,'machine_use_enabled':False},'CB2':{'full_electrical_qualification':False,'pin41_conflict_resolved':False,'machine_use_enabled':False}},
  unused_contact_policy='Each unused exact connector contact has a nativeNC cross. Required rawSD/USB/HDMI/Ethernet/PCIe interfaces are exported and explicitly unfinished, never hidden asNC.',
  host_gate=dict(function='OE_N = NOT(COMPUTE_3V3_GOOD AND FPGA_CRESET_N_SCHMITT AND FPGA_CDONE_SCHMITT)',qualified_control=False,all_buffers_mpn='SN74LVC1G125DBVR',partial_power_spec_i_off_max_uA=10,buffer_input_leak_max_uA=5,signal_rate_qualified=False,no_motion_permission_bypass=True),
  unfinished=['Exact Amphenol salesdrawing visual land/assembly review: CDN download403; socket landsource is officialRaspberryPi CM5IO nativeCAD, not a fabricated generic footprint.','Selective six-power-contact2.5A socket temperature/vendor-rating qualification versus blanket0.3A simultaneous-contact specification.','ActualSD slot/currentlimit/busisolation/ESD are sourceimplemented; exactcardboot/startup/fulltemp/partialramp/discharge/timing anddiagnosticendpointsremainunqualified.','Actual USB role mux/recovery/host hub/ports and shared current limitation; no attached powered-host connector exists here.','Actual HDMI protection/power/DDC/CEC and external HDMI connector; rawsignals only.','Actual Ethernet MagJack/PHY-common-mode protection/return/shield and exact pinout; rawsignals only.','OptionalNVMe exactsocket/CORE5-fed3V3 supply sequencing/currentcap/SSDstartup profile; aggregate6ACORE capacity unclosed.','Parent native integration of fiveSPI endpoints/CDONE/reset and read-only ESP/profile path, carrier placement/loop/routing/impedance/thermal/mechanics.','Linux module-specific image/device-tree/UART/SPI GPIO-CS driver/exclusive bus and measured loaded servo timing.','No universal prepower automatic moduleID; BTT exactvariant/200pins/GPIO/reset/OS qualification required.','20ms output watchdog/inhibit, partial-power ramps/absentmodule/unconfiguredFPGA and all physical EMC tests remain unproved.'],
  primary_refs={'CM5_datasheet':'https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf','CM4_datasheet':'https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf','official_CM5IO_CAD':'https://pip-assets.raspberrypi.com/categories/1098-design-files/documents/RP-008099-DD-1-CM5%20IO%20Board%2C%20revision%202%2C%20KiCAD%20files..zip','socket_product':'https://www.amphenol-cs.com/product/101642271001a1rlf.html','socket_drawing':'https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/10164227.pdf','socket_current_spec':'https://cdn.amphenol-cs.com/media/wysiwyg/files/documentation/gs-12-1404.pdf','DIP':'https://www.ctscorp.com/Files/DataSheets/Switches/DIP-Switches/CTS-Switches-DIP-219-Series-Datasheet.pdf','buffers':'https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf','schmitt':'https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf','nand':'https://www.ti.com/lit/ds/symlink/sn74lvc1g10.pdf','supervisor':'https://www.ti.com/lit/ds/symlink/tps3808.pdf'})


def socket_footprints(out):
 """Split official200-pad native landset into two actual purchased100-pin parts.

 The pad number on socketB is1..100, with an explicit+100 module contact map.
 Socket centers and manufacturer numbering/mating orientation retain the
 official geometry exactly. Four unnumbered NPTH anchors are module mounts,
 not fictitious electrical contacts or purchased parts.
 """
 original=parse(OFFICIAL_FP.read_text(encoding='utf8'));pads=[p for p in children(original,'pad') if value(p[1])];result={}
 if len(pads)!=200:raise ValueError('OfficialCM5 land source must contain200 pads')
 for idx,name,cx in [(0,'Amphenol_10164227_1001_CM_A',-.5),(1,'Amphenol_10164227_1001_CM_B',33.5)]:
  fp=['footprint',q(name),['version','20241229'],['generator',q('pcbnew')],['layer',q('F.Cu')],['descr',q('Two-piece officialCM5IO socket land derivation; Amphenol10164227-1001A1RLF; 100contacts. Copyright/source attribution inSOURCE_NOTICE.md.')],['attr','smd']]
  for prop,content,y,layer in [('Reference','REF**',-12,'F.SilkS'),('Value',SOCKET_MPN,12,'F.Fab')]:
   fp.append(['property',q(prop),q(content),['at','0',str(y),'0'],['layer',q(layer)],['effects',['font',['size','1','1'],['thickness','.15']]]])
  for pad in pads:
   pno=int(value(pad[1]))
   if not idx*100<pno<=(idx+1)*100:continue
   p=copy.deepcopy(pad);p[1]=q(str(pno-idx*100));at=child(p,'at');at[1:3]=[str(round(float(at[1])-cx,4)),str(round(float(at[2])+21.5,4))]
   for key in ['uuid','net','pinfunction','pintype']:
    for node in list(children(p,key)):p.remove(node)
   fp.append(p)
  for y in [-26.5,21.5]:
   fp.append(['pad',q(''),'np_thru_hole','circle',['at',str(.5 if idx==0 else -.5),str(y)],['size','2.7','2.7'],['drill','2.7'],['layers',q('*.Cu'),q('*.Mask')]])
  for layer,margin in [('F.Fab',0),('F.CrtYd',.25)]:
   fp.append(['fp_rect',['start',str(-2.15-margin),str(-11.3-margin)],['end',str(2.15+margin),str(11.3+margin)],['stroke',['width','.05' if margin else '.1'],['type','default']],['fill','none'],['layer',q(layer)]])
  # Clearly identifies the antenna/end and pairing axis without claiming a
  # qualified assembled keepout. Carrier must keep the34mm center relationship.
  fp.append(['fp_text','user',q('CM_'+('A' if idx==0 else 'B')+' PIN1'),['at','-3','-10','90'],['layer',q('F.SilkS')],['effects',['font',['size','.8','.8'],['thickness','.1']]]])
  fp.append(['model',q('${KIPRJMOD}/CNC_COMPUTE.3dshapes/10164227-1001a1rlf.stp'),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','90']]])
  (out/(name+'.kicad_mod')).write_text(dump(fp)+'\n',encoding='utf8')
  result[name]=dict(numbered_pads=100,origin_original=[cx,-21.5],global_offset=idx*100,source_sha256=hashlib.sha256(OFFICIAL_FP.read_bytes()).hexdigest())
 return result


def dip_footprint(out):
 # CTS219 RevD Figure2:2.54 pitch,8.60 rowcenters,1.13x2.44 recommended lands.
 name='CTS_219-3M_GullWing';fp=['footprint',q(name),['version','20241229'],['generator',q('pcbnew')],['layer',q('F.Cu')],['descr',q('CTS219-3MSTRF Figure2 RevD primary recommended land dimensions')],['attr','smd']]
 for prop,text,y,layer in [('Reference','REF**',-6.5,'F.SilkS'),('Value','219-3MSTRF',6.5,'F.Fab')]:fp.append(['property',q(prop),q(text),['at','0',str(y),'0'],['layer',q(layer)],['effects',['font',['size','1','1'],['thickness','.15']]]])
 for n,x,y in [(1,-2.54,4.3),(2,0,4.3),(3,2.54,4.3),(4,2.54,-4.3),(5,0,-4.3),(6,-2.54,-4.3)]:fp.append(['pad',q(str(n)),'smd','rect',['at',str(x),str(y)],['size','1.13','2.44'],['layers',q('F.Cu'),q('F.Paste'),q('F.Mask')]])
 for layer,start,end in [('F.Fab',[-4.59,-3.35],[4.59,3.35]),('F.CrtYd',[-4.9,-5.77],[4.9,5.77])]:fp.append(['fp_rect',['start',*map(str,start)],['end',*map(str,end)],['stroke',['width','.05'],['type','default']],['fill','none'],['layer',q(layer)]])
 fp.append(['fp_text','user',q('1   2   3'),['at','0','3.5','0'],['layer',q('F.Fab')],['effects',['font',['size','.8','.8'],['thickness','.1']]]])
 (out/(name+'.kicad_mod')).write_text(dump(fp)+'\n',encoding='utf8')


def sd_footprints(out):
 # Molex drawing SD-503398-003 A3 page2 is independently reviewed against
 # officialCM5 native land coordinates. The imported STEP reference is broken
 # in the official archive and is removed, never replaced by a guessed solid.
 source=SOURCES/'cm5io-rev2-official/CM5IO.pretty/SDCARD_MOLEX_503398-1892.kicad_mod'
 fp=parse(source.read_text(encoding='utf8'));fp[1]=q('Molex_503398-1892_SD')
 for n in list(children(fp,'model')):fp.remove(n)
 fp.append(['descr',q('Exact Molex503398-1892 primary A3 drawing page2 lands; officialCM5IO original lands preserve pins9detectlever/10switch and four11shellpads; missingmodel notinvented')])
 # Manufacturer pattern prohibition must be reconciled in final placement.
 # This bounded internal no-copper rectangle is only a confirmed subset,
 # not an invented final complete prohibition polygon or clearance release.
 fp.append(['zone',['net','0'],['net_name',q('')],['layers',q('F.Cu')],['hatch','edge','.5'],['connect_pads',['clearance','0']],['min_thickness','.25'],['keepout',['tracks','not_allowed'],['vias','not_allowed'],['pads','not_allowed'],['copperpour','not_allowed'],['footprints','not_allowed']],['fill',['thermal_gap','.3'],['thermal_bridge_width','.3']],['polygon',['pts',['xy','-3.0','-3.5'],['xy','5.8','-3.5'],['xy','5.8','3.7'],['xy','-3.0','3.7']]]])
 (out/'Molex_503398-1892_SD.kicad_mod').write_text(dump(fp)+'\n',encoding='utf8')
 # TI DQA0010A page29 currentRevO: centers0.835 apart, 0.5pitch,
 # all10 lands0.565 wide, ground3/8 .4 high, other8 .2 high.
 fp=['footprint',q('TI_DQA0010A_TPD4E05U06'),['version','20241229'],['generator',q('pcbnew')],['layer',q('F.Cu')],['attr','smd'],['descr',q('TI TPD4E05U06 DQA0010A mfrRevO PDFpage29 exact recommendedland')]]
 for prop,text,y,layer in [('Reference','REF**',-1.75,'F.SilkS'),('Value','TPD4E05U06DQAR',1.75,'F.Fab')]:fp.append(['property',q(prop),q(text),['at','0',str(y),'0'],['layer',q(layer)],['effects',['font',['size','.8','.8'],['thickness','.1']]]])
 for n,x,y in [(1,-.4175,-1),(2,-.4175,-.5),(3,-.4175,0),(4,-.4175,.5),(5,-.4175,1),(6,.4175,1),(7,.4175,.5),(8,.4175,0),(9,.4175,-.5),(10,.4175,-1)]:
  fp.append(['pad',q(str(n)),'smd','roundrect',['at',str(x),str(y)],['size','.565','.4' if n in [3,8] else '.2'],['layers',q('F.Cu'),q('F.Paste'),q('F.Mask')],['roundrect_rratio','.25']])
 for layer,start,end in [('F.Fab',[-.5,-1.25],[.5,1.25]),('F.CrtYd',[-.95,-1.5],[.95,1.5])]:fp.append(['fp_rect',['start',*map(str,start)],['end',*map(str,end)],['stroke',['width','.05'],['type','default']],['fill','none'],['layer',q(layer)]])
 fp.append(['fp_circle',['center','-.6','-1.3'],['end','-.55','-1.3'],['stroke',['width','.08'],['type','default']],['fill','none'],['layer',q('F.SilkS')]])
 (out/'TI_DQA0010A_TPD4E05U06.kicad_mod').write_text(dump(fp)+'\n',encoding='utf8')


def build(out=OUT):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);d=description();parts=d['components'];kinds=copy.deepcopy(KINDS);matrix=json.loads((AUDIT/'pin-matrix.json').read_text(encoding='utf8'))['pins'];uid=lambda x:str(uuid.uuid5(NS,x));root=uid('root')
 for idx,k in enumerate(['SocketA','SocketB']):kinds[k]={i:(matrix[i-1+idx*100]['cm5_signal']+' ['+str(i+idx*100)+']','passive') for i in range(1,101)}
 for p in parts.values():
  if not p['physical']:kinds[p['kind']]={int(k):(k,'passive') for k in p['pins']}
 libs=[];layouts={}
 for kind,table in kinds.items():
  if kind in ['R','C']:layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
  elif kind in ['TP','PWR_FLAG']:layout=[(1,table[1][0],0,0,90,table[1][1])];body=''
  else:
   keys=list(table);half=(len(keys)+1)//2;pitch=5.08 if not kind.startswith('Socket') else 2.54
   layout=[(n,table[n][0],sign*25.4,25.4-i*pitch,0 if sign<0 else 180,table[n][1]) for sign,nums in [(-1,keys[:half]),(1,keys[half:])] for i,n in enumerate(nums)]
   body=f'(rectangle(start -22.86 30.48)(end 22.86 {min(p[3] for p in layout)-5.08})(stroke(width .254)(type default))(fill(type background)))'
  layouts[kind]=layout;libs.append(symbol(kind,layout,body,'R' if kind=='R' else 'C' if kind=='C' else 'TP' if kind=='TP' else 'J' if kind.startswith('Socket') or kind.startswith('Boundary') else '#FLG' if kind=='PWR_FLAG' else 'U'))
 items=[];ic=pas=bnd=0
 for ref,p in parts.items():
  if p['kind']=='SD_SLOT':x=114.3;y=939.8
  elif p['kind'].startswith('Socket'):x=114.3 if ref=='J15001' else 393.7;y=91.44
  elif p['physical'] and ref.startswith('U'):x=114.3+(ic%6)*172.72;y=320.04+(ic//6)*111.76;ic+=1
  elif p['physical']:x=63.5+(pas%15)*73.66;y=660.4+(pas//15)*53.34;pas+=1
  else:x=673.1+(bnd%3)*172.72;y=91.44+(bnd//3)*144.78;bnd+=1
  props=''.join(f'(property {quote(k)} {quote(v)} (at {x+4} {y-36 if k=="Reference" else y-33} 0) {effects(.9,extra="hide" if k not in ["Reference","Value"] else "")})' for k,v in [('Reference',ref),('Value',p['value']),('MPN',p['mpn']),('Footprint',p['footprint']),('Role',p['role'])])
  fitted='yes' if p['physical'] else 'no';items.append(f'(symbol(lib_id "{LIB}:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {fitted})(on_board {fitted})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_compute"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  for pin,name,px,py,ang,kind in layouts[p['kind']]:
   xy=(round(x+px,4),round(y-py,4));net=p['pins'][str(pin)]
   if net is None:items.append(f'(no_connect(at {xy[0]} {xy[1]})(uuid "{uid(ref+str(pin)+"NC")}"))');continue
   # Labels do not touch adjacentconnector contacts or symbol bodies.
   dx=0 if px==0 else (-53.34 if px<0 else 7.62);dy=-5.08 if px==0 and py>0 else 5.08 if px==0 else 0;ex=round(xy[0]+dx,4);ey=round(xy[1]+dy,4)
   items.append(f'(wire(pts(xy {xy[0]} {xy[1]})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(pin)+"wire")}"))')
   items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.85,"(justify left bottom)")}(uuid "{uid(ref+str(pin)+"label")}"))')
 for i,net in enumerate(['SBC_5V','IO_3V3','LOGIC_GND','CM_AUX_3V3'],1):
  x=50.8*i;y=1112.52;ref='#FLG1500'+str(i)
  items.append(f'(symbol(lib_id "{LIB}:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" {quote(ref)}(at {x} {y} 0){effects(extra="hide")})(property "Value" "EXTERNAL PARENT FEED"(at {x} {y} 0){effects(extra="hide")})(instances(project "motherboard_compute"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  items.append(f'(label {quote(net)}(at {x} {y} 0){effects(.9,"(justify left bottom)")}(uuid "{uid(ref+"label")}"))')
 notes=[('CM4/CM5 SOCKET + HOST-DOMAIN CARRIER r0.2 / PROTECTED SD',17.78,12.7,2),('Two actual100-contact sockets; purchasedcomputeSoM is a separate assembly. CM5 officialnative pad geometry preserves mating orientation.\nUnused exactcontacts areNC; SDslot/currentlimit/powerqualification/busisolation/ESD implemented in source; otherportsunfinished.\nNo universalBTT electrical compatibility, automaticID, targetimage, mountedkeepout or physicalcurrentqualification is claimed.',17.78,250.19,1.2),('HOSTSPI defaults: CLK/MOSI LOW, bothCS HIGH; fourforward Ioff buffers and one module-powered return.\nEnable requires actualCM3V3 supervision AND FPGA resetreleased AND CDONE. Read-onlyUARTTX is contact55/GPIO14.\nDIP is only cold-start profilemetadata, with0=AUTO/serviceuntil exactID; it cannot grantpower/motionpermission.\nAmphenol blanket0.3A/allcontacts gives1.8A acrosssix5Vcontacts: planned2.5A needs selective-contact rating/thermalproof.',17.78,483.87,1.2),('Manufacturingblocked: protectedSD sourceimplemented; USB/HDMI/Ethernet/NVMe stillrequire actualports/protection/qualifiedpower.\nOnecustommotherboard; noauxdaughterboardfamily. NoNVMeonIO3V3/moduleaux. Modulepin92conflict retainedNC.\nSPI GPIO-CS transport/pinmux/loadeddeadline, nativeparentintegration, routing/return/EMC/thermal/watchdog and physicalprototypes remain required.',430,1054.1,1.1)]
 for text,x,y,size in notes:items.append(f'(text {quote(text)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(text)}"))')
 sch=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "User" 1189 1200)(title_block(title "CM4/CM5 compute socket and host-domain carrier")(date "2026-09-30")(rev "r0.2-SD")(comment 1 "Partialnativeon-motherboard source; notmanufacturingready"))(lib_symbols '+''.join(libs).replace('(symbol "CNC:','(symbol "'+LIB+':')+')\n'+'\n'.join(items)+'\n)\n'
 (out/'motherboard_compute.kicad_sch').write_text(sch,encoding='utf8')
 (out/(LIB+'.kicad_sym')).write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')\n',encoding='utf8')
 (out/'sym-lib-table').write_text(f'(sym_lib_table (version 7) (lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.kicad_sym") (options "") (descr "ReviewedCM4/5 physicalsocket/hostdomain candidate")))\n',encoding='utf8')
 fp=out/(LIB+'.pretty');fp.mkdir(exist_ok=True);d['socket_footprint_derivation']=socket_footprints(fp);dip_footprint(fp);sd_footprints(fp)
 models=out/(LIB+'.3dshapes');models.mkdir(exist_ok=True)
 shutil.copyfile(SOURCES/'cm5io-rev2-official/CM5IO.3dshapes/10164227-1001a1rlf.stp',models/'10164227-1001a1rlf.stp')
 (out/'fp-lib-table').write_text(f'(fp_lib_table (version 7) (lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.pretty") (options "") (descr "OfficialCM5 landset split and CTSprimaryland pattern")))\n',encoding='utf8')
 (out/'motherboard_compute.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_compute.kicad_pro','version':1},'erc':{'rule_severities':{'lib_symbol_issues':'warning','similar_labels':'warning','single_global_label':'warning','four_way_junction':'warning','simulation_model_issue':'warning','footprint_filter':'warning'}}},indent=2)+'\n',encoding='utf8')
 d['physical_component_count']=sum(p['physical'] for p in parts.values());d['purchased_component_count']=sum(p['physical'] and p['kind']!='TP' for p in parts.values());d['native_NC_contact_count']=sum(n is None for n in d['socket_contact_map'].values())
 d['input_hashes']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OFFICIAL_FP,AUDIT/'pin-matrix.json',AUDIT/'transport-profiles.json',SOURCES/'cm5io-rev2-kicad-official.zip',SOURCES/'cts-219.pdf',SOURCES/'molex-5033981892-manufacturer-drawing-mirror.pdf',SOURCES/'tps2553.pdf',SOURCES/'ts3a27518e.pdf',SOURCES/'tps3808.pdf',SOURCES/'tpd6e05u06.pdf',SOURCES/'sn74lvc1g00.pdf',SOURCES/'cm5io-rev2-official/CM5IO.pretty/SDCARD_MOLEX_503398-1892.kicad_mod']}
 (out/'design.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
 with (out/'bom.csv').open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status','Scope']);w.writeheader()
  for ref,p in parts.items():
   if p['physical']:w.writerow(dict(Reference=ref,Value=p['value'],MPN=p['mpn'],Footprint=p['footprint'],Status='bare_PCB_test_pad_no_purchase' if p['kind']=='TP' else 'candidate_not_qualified',Scope='one_motherboard_compute_region'))
 (out/'SOURCE_NOTICE.md').write_text('The two connector landsets are derived solely from Raspberry Pi official CM5IO revision2 native CAD, RP-008099-DD-1, with source attributes retained in design.json. Raspberry Pi and Amphenol names identify their purchased products. Third-party design/material rights and applicable licences remain theirs; this is not an open-source promise for the commercial controller software. The complete IO-board design is archived as a primary review source, not copied as this carrier architecture. Amphenol salesdrawing visual review remains explicitly open. SD lands are also derived from the official CM5IO native CAD and checked against manufacturer Molex SD-503398-003 A3 page 2; its broken archived STEP reference was removed, not replaced by a guessed model. TPD4 ESD lands use TI DQA0010A current-datasheet page29 dimensions. The complete Molex pattern-prohibition polygon and assembled access/clearance remain final-placement work; the fitted footprint has only a reviewed bounded internal keepout subset.\n',encoding='utf8')
 print(json.dumps({'out':str(out),'physical':d['physical_component_count'],'purchased':d['purchased_component_count'],'socket_count':2,'unimplemented_port_boundaries':4,'manufacturing_ready':False},indent=2))
 return d

if __name__=='__main__':build()
