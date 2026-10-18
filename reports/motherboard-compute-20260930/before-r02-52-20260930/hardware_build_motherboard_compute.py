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
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},
 'TP':{1:('TP','passive')},'PWR_FLAG':{1:('pwr','power_out')}}
MPNS={'BUF':('SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'SCHMITT':('SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'NAND3':('SN74LVC1G10DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'SUP':('TPS3808G33DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'DIP3':('219-3MSTRF','CNC_COMPUTE:CTS_219-3M_GullWing')}
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
  r+=1;ref=f'R{r}';mpn={33:'CRCW060333R0FKEA',1000:'CRCW06031K00FKEA',10000:'CRCW060310K0FKEA',47000:'CRCW060347K0FKEA'}[ohm]
  parts[ref]=dict(kind='R',mpn=mpn,value=f'{ohm}R 1%',footprint='Resistor_SMD:R_0603_1608Metric',physical=True,dnp=False,pins={'1':a,'2':b},role=role,resistance_ohm=ohm,tolerance=.01)
  return ref
 def cap(net,nf,role):
  nonlocal c
  c+=1;ref=f'C{c}';mpn,fp,v={100:('GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric',100),1000:('GRM188R71H105KA12D','Capacitor_SMD:C_0603_1608Metric',50),10000:('GRM21BR61E106KA73L','Capacitor_SMD:C_0805_2012Metric',25)}[nf]
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
 bounds={}
 def boundary(ref,nets,role):bounds[ref]=dict(kind='Boundary'+str(len(nets)),mpn='',value=role,footprint='',physical=False,dnp=False,pins={str(i+1):n for i,n in enumerate(nets)},role=role)
 boundary('B15001',['SBC_5V','IO_3V3','LOGIC_GND','FPGA_CRESET_N','FPGA_CDONE'],'actual protected parent supplies and native FPGA qualification observations')
 boundary('B15002',['HOST_SPI_SCLK','HOST_SPI_MOSI','HOST_SPI_CS_FB_N','HOST_SPI_CS_CMD_N','HOST_SPI_MISO'],'dedicated frozen dual-CS FPGA host interface; no Ethernet in hard timing path')
 boundary('B15003',['COMPUTE_SERVICE_TX','COMPUTE_PROFILE0','COMPUTE_PROFILE1','COMPUTE_PROFILE2','COMPUTE_3V3_GOOD'],'read-only ESP service/profile/actual supply observation; neither ID nor OS-ready')
 for i,(group,pins) in enumerate(interface_groups.items(),4):
  boundary(f'B1500{i}',list(pins.values())+['SBC_5V','CM_AUX_3V3','LOGIC_GND'],group+' exact raw compute signals; external port circuitry NOT implemented inr01')
 return dict(schema_version=1,revision='motherboard-compute-r0.1',parent_reference_index=15,
  status='native_socket_and_host_domain_source_candidate; raw_port_boundaries_incomplete',manufacturing_ready=False,physical_qualification=False,
  components={**parts,**bounds},host_channels=channels,sockets=['J15001','J15002'],module_parts_separate=True,compute_som_fitted_on_carrier_bom=False,
  socket_contact_map={str(k):v for k,v in socket_nets.items()},interface_groups=interface_groups,
  compute_aux_supervisor=sup,host_enable_gate=gate,qualification_schmitt=gates,selector_ref=switch,
  module_power=dict(input='SBC_5V',ground='LOGIC_GND',power_contacts=[77,79,81,83,85,87],ground_contacts=[p['global_pin'] for p in matrix if socket_nets[p['global_pin']]=='LOGIC_GND'],aux3v3_contacts=[84,86],gpio_vref_contact=78,aux3v3_max_total_a=.6,aux3v3_max_per_contact_a=.3,module_power_planning_cap_a=2.5,SBC_branch_planning_cap_a=3,externalUSB_planning_cap_a=.5,full_capacity_qualified=False),
  socket_rating=dict(all_contacts_simultaneous_a=.3,main5v_contact_count=6,blanket_rating_total_a=1.8,planned_2p5A_selective_contact_rating_or_temperature_qualification=False),
  mechanical=dict(module_outline_mm=[40,55],hole_grid_mm=[33,48],hole_diameter_mm=2.7,mounting_screw='M2.5',socket_center_separation_mm=34,socket_A_origin_relative_module_mount_mm=[-.5,-21.5],socket_B_origin_relative_module_mount_mm=[33.5,-21.5],required_same_rotation=True,connector_mated_height_mm=1.5,module_under_clearance_mm=0,approx_mounted_top_height_mm=4.94,antenna_and_heatsink_keepout_qualified=False),
  selector=dict(bits=3,codes={'0':'AUTO_SERVICE_UNTIL_EXACT_ID_VERIFIED','1':'CM4','2':'CM5','3':'CB1_SD_v2p2_CANDIDATE','4':'CB2_CANDIDATE','5':'UNSUPPORTED','6':'UNSUPPORTED','7':'UNSUPPORTED'},DIP_controls_electrical_power_or_permission=False,automatic_hardware_ID_implemented=False,software_profile_implemented=False),
  profiles={'CM4':{'pin_sources_checked':True,'target_image_and_pinmux_qualified':False},'CM5':{'pin_sources_checked':True,'target_image_and_pinmux_qualified':False},'CB1_SD_v2p2':{'full_electrical_qualification':False,'machine_use_enabled':False},'CB1_eMMC':{'full_200_contact_mapping_available':False,'machine_use_enabled':False},'CB2':{'full_electrical_qualification':False,'pin41_conflict_resolved':False,'machine_use_enabled':False}},
  unused_contact_policy='Each unused exact connector contact has a nativeNC cross. Required rawSD/USB/HDMI/Ethernet/PCIe interfaces are exported and explicitly unfinished, never hidden asNC.',
  host_gate=dict(function='OE_N = NOT(COMPUTE_3V3_GOOD AND FPGA_CRESET_N_SCHMITT AND FPGA_CDONE_SCHMITT)',qualified_control=False,all_buffers_mpn='SN74LVC1G125DBVR',partial_power_spec_i_off_max_uA=10,buffer_input_leak_max_uA=5,signal_rate_qualified=False,no_motion_permission_bypass=True),
  unfinished=['Exact Amphenol salesdrawing visual land/assembly review: CDN download403; socket landsource is officialRaspberryPi CM5IO nativeCAD, not a fabricated generic footprint.','Selective six-power-contact2.5A socket temperature/vendor-rating qualification versus blanket0.3A simultaneous-contact specification.','Actual SD power-switch/protection and qualifiedcard current/boot profiles; only raw pinboundaries exist.','Actual USB role mux/recovery/host hub/ports and shared current limitation; no attached powered-host connector exists here.','Actual HDMI protection/power/DDC/CEC and external HDMI connector; rawsignals only.','Actual Ethernet MagJack/PHY-common-mode protection/return/shield and exact pinout; rawsignals only.','OptionalNVMe exactsocket/CORE5-fed3V3 supply sequencing/currentcap/SSDstartup profile; aggregate6ACORE capacity unclosed.','Parent native integration of fiveSPI endpoints/CDONE/reset and read-only ESP/profile path, carrier placement/loop/routing/impedance/thermal/mechanics.','Linux module-specific image/device-tree/UART/SPI GPIO-CS driver/exclusive bus and measured loaded servo timing.','No universal prepower automatic moduleID; BTT exactvariant/200pins/GPIO/reset/OS qualification required.','20ms output watchdog/inhibit, partial-power ramps/absentmodule/unconfiguredFPGA and all physical EMC tests remain unproved.'],
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
  fp.append(['fp_text','user',q('CM_'+('A' if idx==0 else 'B')+' PIN1'),['at','-3','-10','90'],['layer',q('F.SilkS')],['effects',['font',['size','.7','.7'],['thickness','.1']]]])
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
 fp.append(['fp_text','user',q('1   2   3'),['at','0','3.5','0'],['layer',q('F.SilkS')],['effects',['font',['size','.6','.6'],['thickness','.1']]]])
 (out/(name+'.kicad_mod')).write_text(dump(fp)+'\n',encoding='utf8')


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
  if p['kind'].startswith('Socket'):x=114.3 if ref=='J15001' else 393.7;y=91.44
  elif p['physical'] and ref.startswith('U'):x=114.3+(ic%6)*172.72;y=320.04+(ic//6)*111.76;ic+=1
  elif p['physical']:x=63.5+(pas%15)*73.66;y=584.2+(pas//15)*53.34;pas+=1
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
  x=50.8*i;y=797.56;ref='#FLG1500'+str(i)
  items.append(f'(symbol(lib_id "{LIB}:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" {quote(ref)}(at {x} {y} 0){effects(extra="hide")})(property "Value" "EXTERNAL PARENT FEED"(at {x} {y} 0){effects(extra="hide")})(instances(project "motherboard_compute"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
  items.append(f'(label {quote(net)}(at {x} {y} 0){effects(.9,"(justify left bottom)")}(uuid "{uid(ref+"label")}"))')
 notes=[('CM4/CM5 SOCKET + HOST-DOMAIN CARRIER r0.1',17.78,12.7,2),('Two actual100-contact sockets; purchasedcomputeSoM is a separate assembly. CM5 officialnative pad geometry preserves mating orientation.\nUnused exactcontacts areNC; requiredexternalSD/USB/HDMI/Ethernet/PCIe endpoints remain visible as unfinishedboundaries.\nNo universalBTT electrical compatibility, automaticID, targetimage, mountedkeepout or physicalcurrentqualification is claimed.',17.78,250.19,1.2),('HOSTSPI defaults: CLK/MOSI LOW, bothCS HIGH; fourforward Ioff buffers and one module-powered return.\nEnable requires actualCM3V3 supervision AND FPGA resetreleased AND CDONE. Read-onlyUARTTX is contact55/GPIO14.\nDIP is only cold-start profilemetadata, with0=AUTO/serviceuntil exactID; it cannot grantpower/motionpermission.\nAmphenol blanket0.3A/allcontacts gives1.8A acrosssix5Vcontacts: planned2.5A needs selective-contact rating/thermalproof.',17.78,483.87,1.2),('Manufacturingblocked: noexternalportconnectors here; rawhighspeedboundaries stillrequire actualprotection/portcircuits.\nOnecustommotherboard; noauxdaughterboardfamily. NoNVMeonIO3V3/moduleaux. Modulepin92conflict retainedNC.\nSPI GPIO-CS transport/pinmux/loadeddeadline, nativeparentintegration, routing/return/EMC/thermal/watchdog and physicalprototypes remain required.',430,780,1.1)]
 for text,x,y,size in notes:items.append(f'(text {quote(text)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(text)}"))')
 sch=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "A0")(title_block(title "CM4/CM5 compute socket and host-domain carrier")(date "2026-09-30")(rev "r0.1")(comment 1 "Partialnativeon-motherboard source; notmanufacturingready"))(lib_symbols '+''.join(libs).replace('(symbol "CNC:','(symbol "'+LIB+':')+')\n'+'\n'.join(items)+'\n)\n'
 (out/'motherboard_compute.kicad_sch').write_text(sch,encoding='utf8')
 (out/(LIB+'.kicad_sym')).write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')\n',encoding='utf8')
 (out/'sym-lib-table').write_text(f'(sym_lib_table (version 7) (lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.kicad_sym") (options "") (descr "ReviewedCM4/5 physicalsocket/hostdomain candidate")))\n',encoding='utf8')
 fp=out/(LIB+'.pretty');fp.mkdir(exist_ok=True);d['socket_footprint_derivation']=socket_footprints(fp);dip_footprint(fp)
 models=out/(LIB+'.3dshapes');models.mkdir(exist_ok=True)
 shutil.copyfile(SOURCES/'cm5io-rev2-official/CM5IO.3dshapes/10164227-1001a1rlf.stp',models/'10164227-1001a1rlf.stp')
 (out/'fp-lib-table').write_text(f'(fp_lib_table (version 7) (lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.pretty") (options "") (descr "OfficialCM5 landset split and CTSprimaryland pattern")))\n',encoding='utf8')
 (out/'motherboard_compute.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_compute.kicad_pro','version':1},'erc':{'rule_severities':{'lib_symbol_issues':'warning','similar_labels':'warning','single_global_label':'warning','four_way_junction':'warning','simulation_model_issue':'warning','footprint_filter':'warning'}}},indent=2)+'\n',encoding='utf8')
 d['physical_component_count']=sum(p['physical'] for p in parts.values());d['purchased_component_count']=sum(p['physical'] and p['kind']!='TP' for p in parts.values());d['native_NC_contact_count']=sum(n is None for n in d['socket_contact_map'].values())
 d['input_hashes']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OFFICIAL_FP,AUDIT/'pin-matrix.json',AUDIT/'transport-profiles.json',SOURCES/'cm5io-rev2-kicad-official.zip',SOURCES/'cts-219.pdf']}
 (out/'design.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
 with (out/'bom.csv').open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status','Scope']);w.writeheader()
  for ref,p in parts.items():
   if p['physical']:w.writerow(dict(Reference=ref,Value=p['value'],MPN=p['mpn'],Footprint=p['footprint'],Status='bare_PCB_test_pad_no_purchase' if p['kind']=='TP' else 'candidate_not_qualified',Scope='one_motherboard_compute_region'))
 (out/'SOURCE_NOTICE.md').write_text('The two connector landsets are derived solely from Raspberry Pi official CM5IO revision2 native CAD, RP-008099-DD-1, with source attributes retained in design.json. Raspberry Pi and Amphenol names identify their purchased products. Third-party design/material rights and applicable licences remain theirs; this is not an open-source promise for the commercial controller software. The complete IO-board design is archived as a primary review source, not copied as this carrier architecture. Amphenol salesdrawing visual review remains explicitly open.\n',encoding='utf8')
 print(json.dumps({'out':str(out),'physical':d['physical_component_count'],'purchased':d['purchased_component_count'],'socket_count':2,'unimplemented_port_boundaries':5,'manufacturing_ready':False},indent=2))
 return d

if __name__=='__main__':build()
