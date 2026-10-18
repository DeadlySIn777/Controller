"""Report-only exact source26 critical digital topology and native lower bounds.

This does not mutate electrical source, PCB, old ordinary eligibility or routers.
Run with KiCad Python. Numeric placement targets are engineering screens;
device switching limits retain their real primary test conditions.
"""
from pathlib import Path
import hashlib,json,math,sys,xml.etree.ElementTree as ET
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'hardware/motherboard'
ADOPT=ROOT/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/adoption.json'
BOARD=ROOT/'reports/motherboard-pcb-integration-20261001/source26-ao-display-r50/motherboard-ao-display-reconciled-candidate.kicad_pcb'
ORDINARY=ROOT/'reports/motherboard-ordinary-routing-20261001/source26-review-r08/ordinary-source-review.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
ad=json.loads(ADOPT.read_text());assert ad['adopted'] and ad['passed']
for p,h in ad['source_hashes'].items():assert sha(SRC/p)==h,p
parts=json.loads((SRC/'design.json').read_text())['components']
xml=ET.parse(SRC/'netlist.xml');native={};bypin={}
for n in xml.findall('.//nets/net'):
 rows=[]
 for p in n.findall('node'):
  r,pin=p.get('ref'),p.get('pin')
  if r not in parts:continue
  row=dict(reference=r,pin=pin,function=p.get('pinfunction',''),type=p.get('pintype',''),mpn=parts[r]['mpn'],source_block=parts[r].get('source_block',''))
  rows.append(row);bypin[r,pin]=n.get('name')
 native[n.get('name')]=rows
b=pcbnew.LoadBoard(str(BOARD));fps={f.GetReference():f for f in b.GetFootprints()}
padxy={};pads={}
for r,f in fps.items():
 for p in f.Pads():
  if p.GetNumber():
   padxy.setdefault((r,p.GetNumber()),[]).append((pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)))
   if p.GetNetCode()>0:pads.setdefault((r,p.GetNumber()),[]).append(p)
b.BuildConnectivity();conn=b.GetConnectivity()
def net(r,p):return bypin[r,str(p)]
def pos(r,p):return padxy[r,str(p)][0]
def dist(a,c):return math.dist(pos(*a),pos(*c))
def return_pins(r,g):
 return [str(p)for rr,p in bypin if rr==r and bypin[rr,p]==g and any(n['reference']==r and n['pin']==p and n['type']=='power_in'for n in native[g])]
groups=[];routes={};edges=[];source_stubs=[];tap_stubs=[]
def add(name,names,g,v,kind,notes):
 names=sorted(set(names));assert names
 for n in names:
  assert n in native and len(native[n])>=2,(name,n)
  if n.startswith('unconnected-'):raise ValueError(n)
  row=dict(type='critical_digital',signal_class=kind,maximum_voltage_v=v,return_net=g,
    source_pins=sorted([[p['reference'],p['pin']]for p in native[n]]),
    source_endpoints=[],ordinary_eligible=n in json.loads(ORDINARY.read_text())['nets'],
    proposed_layers=['F.Cu','B.Cu'],reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},
    reference_corridor_margin_mm=.4,allow_vias=True,via_diameter_mm=.6,via_drill_mm=.3,
    return_stitch_distance_mm=1.0,require_actual_reference_flash_and_connection=True,
    impedance_width_gap_mm=None,impedance_factory_stackup_qualified=False,
    source_pin_inventory_verified=True,layout_permission='EXACT_SOURCE_REVIEW_ONLY')
  for p in native[n]:
   pp=dict(p,native_pad_xy_mm=pos(p['reference'],p['pin']))
   if p['reference'].startswith('U'):
    pp['actual_return_pins']=return_pins(p['reference'],g)
    assert pp['actual_return_pins'],(name,n,p,g)
   row['source_endpoints'].append(pp)
  actual_pads=[p for ep in row['source_pins']for p in pads[tuple(ep)]]
  pending={p.m_Uuid.AsString():p for p in actual_pads};clusters=[]
  while pending:
   k,p=next(iter(pending.items()));connected={x.m_Uuid.AsString()for x in conn.GetConnectedItems(p)if x.Type()==pcbnew.PCB_PAD_T}|{k}
   groupids=connected&set(pending);assert groupids
   clusters.append(sorted(groupids));pending={u:x for u,x in pending.items()if u not in groupids}
  row['current_source_pad_clusters']=len(clusters)
  row['current_independent_missing_joins']=max(0,len(clusters)-1)
  row['current_native_clusters_are_not_signal_integrity_proof']=True
  if n in routes:assert routes[n]['return_net']==g,(name,n,g)
  else:routes[n]=row
 groups.append(dict(name=name,nets=names,return_net=g,voltage_v=v,critical_class=kind,notes=notes))
def edge(label,a,c,category):
 assert net(*a)==net(*c),(label,a,c)
 row=dict(label=label,category=category,net=net(*a),from_pin=list(a),to_pin=list(c),
  actual_minimum_straight_pad_center_distance_mm=round(dist(a,c),6),actual_routed_length_mm=None,
  flight_ps_per_mm=None,extracted_capacitance_pf=None,not_a_routed_path_proof=True)
 edges.append(row);return row
def resistor_stub(r,driver,label):
 assert parts[r]['resistance_ohm'] in (0,22,33)
 row=edge(label,driver,(r,'1'),'source_series_resistor_input_stub')
 row.update(series_resistor=r,resistance_ohm=parts[r]['resistance_ohm'],
  engineering_near_driver_target_mm=5.0,manufacturer_maximum_stub_mm=None,
  current_straight_lower_bound_meets_engineering_target=row['actual_minimum_straight_pad_center_distance_mm']<=5)
 source_stubs.append(row)
for lane,(mcu,buf,base,tap,clockpin,cs_pin,miso_pin,mosi_pin,countpin) in enumerate([
 ('U13001','U13003',13013,'R13057',16,15,17,18,44),
 ('U13004','U13006',13031,'R13058',12,11,13,14,29),
 ('U13008','U13010',13049,'R13059',12,11,13,14,29),
 ('U14501','U14503',14525,'R14533',16,15,17,18,44)]):
 ns=[];chain=[]
 for off,(tag,ip,op,mp)in enumerate([('CS_N',2,3,cs_pin),('SCLK',5,6,clockpin),('MOSI',9,8,mosi_pin)]):
  r='R'+str(base+off);assert parts[r]['resistance_ohm']==22
  assert net(buf,op)==net(r,1) and net(r,2)==net(mcu,mp)
  ns.extend([net(buf,ip),net(buf,op),net(mcu,mp)])
  fpga=next(p for p in native[net(buf,ip)]if p['reference']=='U1001')
  edge(f'IOL1 L{lane} {tag} FPGA to buffer',('U1001',fpga['pin']),(buf,str(ip)),'fpga_to_receiver_buffer')
  resistor_stub(r,(buf,str(op)),f'IOL1 L{lane} {tag} real22ohm source stub')
  edge(f'IOL1 L{lane} {tag} series output to MCU',(r,'2'),(mcu,str(mp)),'buffered_MCU_local_line')
  chain.append(dict(signal=tag,fpga_pin=fpga['pin'],buffer_input=ip,buffer_output=op,resistor=r,resistance_ohm=22,mcu_pin=mp))
 r='R'+str(base+3);assert net(mcu,miso_pin)==net(buf,12) and net(buf,11)==net(r,1)
 ns.extend([net(mcu,miso_pin),net(buf,11),net(r,2),net(tap,2)])
 fpga=next(p for p in native[net(r,2)]if p['reference']=='U1001')
 edge(f'IOL1 L{lane} MISO MCU to buffer',(mcu,str(miso_pin)),(buf,'12'),'MCU_MISO_buffer_input')
 resistor_stub(r,(buf,'11'),f'IOL1 L{lane} MISO real22ohm source stub')
 edge(f'IOL1 L{lane} MISO series output to FPGA',(r,'2'),('U1001',fpga['pin']),'buffered_FPGA_return_line')
 assert parts[tap]['resistance_ohm']==0 and net(tap,1)==net(mcu,clockpin) and net(tap,2)==net(mcu,countpin)
 t=edge(f'IOL1 L{lane} PB5 post-clock0ohm tap',(tap,'2'),(mcu,str(countpin)),'local_clock_count_stub')
 t.update(tap_resistor=tap,physical_pin=countpin,AF='AF1 TIM3_CH2',manufacturer_maximum_stub_mm=None,
  clock_MCU_to_tap_minimum_mm=round(dist((mcu,str(clockpin)),(tap,'1')),6),engineering_rule='Minimise branch; review actual round-trip flight versus minimum receiver clock rise/fall time. No arbitrary certified5mm limit.')
 tap_stubs.append(t)
 add(f'IOL1_L{lane}',ns,'/LOGIC_GND',3.3,'IOL1_point_to_point_clocked_lane',
  dict(chain=chain,MISO=dict(mcu_pin=miso_pin,buffer_input=12,buffer_output=11,resistor=r,fpga_pin=fpga['pin']),
   clock_count_tap=tap,clock_tap_is_post_source_resistor=True,common_four_node_bus=False,
   actual_series_ohm=22,actual_readonly_mode=0,actual_target_sclk_hz=50000000/6,
   output_GPIO_speed_register_currently_unset=False,current_loaded_timing_qualified=False,
   OSPEEDR11_table_conditions_still_require_actual_load_and_edge_proof=True,
   FPGA_CLK_to_output_and_input_setup_require_actual_vendor_STA=True))
 reset=net(mcu,10 if lane in (0,3)else 6)
 add(f'IOL1_L{lane}_RESET',[reset],'/LOGIC_GND',3.3,'asynchronous_supervised_reset',dict(default='actual TPS3808 supervisor open-drain reset; no software healthy tie',reset_pin=10 if lane in(0,3)else 6,reset_propagation_measurement_pending=True))
host=[]
for tag,buf,r,cm in [('SCLK','U15006','R15006',38),('MOSI','U15007','R15009',44),('CS_FB_N','U15008','R15012',54),('CS_CMD_N','U15009','R15015',47)]:
 assert parts[r]['resistance_ohm']==33
 assert net('J15001',cm)==net(buf,2) and net(buf,4)==net(r,1)
 host.extend([net(buf,2),net(buf,4),net(r,2)])
 edge(f'Host {tag} compute socket to buffer',('J15001',str(cm)),(buf,'2'),'module_to_host_buffer')
 resistor_stub(r,(buf,'4'),f'Host {tag} real33ohm source stub')
 fp=next(p for p in native[net(r,2)]if p['reference']=='U1001')
 edge(f'Host {tag} series output to FPGA',(r,'2'),('U1001',fp['pin']),'compute_FPGA_clocked_line')
host.extend([net('U15010',2),net('U15010',4),net('R15018',2),net('U15005',4)])
resistor_stub('R15018',('U15010','4'),'Host MISO real33ohm source stub')
add('HOST_SPI',host,'/LOGIC_GND',3.3,'compute_FPGA_host_SPI',dict(current_target_sclk_hz=None,
 CM5_CM4_driver_edge_and_output_strength_need_exact_profile=True,source_damping_ohm=33,
 MISO_buffer_actual_supply='CM_AUX_3V3',forward_buffer_supply='IO_3V3',
 host_OE_hardware_qualification='actual COMPUTE_3V3_GOOD and FPGA_RESET_RELEASED and CDONE NAND',
 no_automatic_supported_BTT_claim=True,current_loaded_timing_qualified=False))
cfg=[net('U1001',p)for p in ['M3','P3','L3','N1','N3','C7','D7','K13','L14','R16','B8','L12']]+[net('U1002',p)for p in [3,6,7]]
add('FPGA_FLASH_AND_CONFIG',cfg,'/LOGIC_GND',3.3,'FPGA_configuration',dict(actual_flash='W25Q32JVSSIQ',
 serial_clock_source_resistor='R1002',source_damping_ohm=33,boot_frequency_depends_on_actual_gateware_header=True,
 active_SPI_fast_read_and_standard_read_opcode_frequency_limits_are_distinct=True,configuration_pinstrap_and_power_order_qualification=False))
resistor_stub('R1002',('U1001','M3'),'FPGA flash33ohm CCK source stub')
add('FPGA_CLOCK50',[net('Y1001',3),net('U1001','H3')],'/LOGIC_GND',3.3,'reference_oscillator_clock',dict(
 actual_oscillator=parts['Y1001']['mpn'],source_damping_ohm=33,clock_load_and_stackup_extraction_pending=True,clock_frequency_hz=50000000))
resistor_stub('R1001',('Y1001','3'),'50MHz oscillator33ohm source stub')
resets=[net('U1003',p)for p in [1,2,4]]+[net('U1004',p)for p in [2,4]]+[net('U1005',4),net('U1001','R1')]
add('FPGA_AND_COMPUTE_QUALIFICATION',resets,'/LOGIC_GND',3.3,'reset_configuration_qualification',dict(
 actual_reset_RC='R1022 10k + C1039 1u + SchmittU1004; keep cap/Schmitt local',
 reset_RC_not_ordinary_route=True,reset_assertion_and_unconfigured_state_physical_proof_pending=True))
hostanalog=[net('U14501',p)for p in [24,25,26,27,42,43]]
add('ACC_SPI2_SHARED_HOST',hostanalog,'/LOGIC_GND',3.3,'isolated_analog_host_SPI',dict(
 actual_clock_and_MOSI_fanout=3,actual_active_MISO_buffers=['U14709','U14609','U14627'],
 MISO_CS_gated_actual_hardware=True,multiple_CS_low_forbidden=True,
 profile_sclk_hz=4000000,current_target_ACC_SPI2_not_implemented=True,
 no_source_series_resistor_in_frozen_ACC_SPI2_host_bus=True,
 no_claim_shared_bus_is_three_independent_single_load_lines=True,continuous_reference_no_split=True))
for name,iso,target,pins,g in [('AI','U14707','U14734',[37,1,38,36],'/motherboard_analog_input/AI_AGND'),
 ('AO0','U14605','U14608',[6,8,7,3],'/motherboard_analog_output/AO0_COM'),
 ('AO1','U14623','U14626',[6,8,7,3],'/motherboard_analog_output/AO1_COM')]:
 names=[net(target,p)for p in pins]
 add(name+'_SPI_FIELD',names,g,5.0,'isolated_ADC_DAC_SPI',dict(iso=iso,
  side1_supply='IO_3V3',side2_supply='AI_5V'if name=='AI'else name+'_5V',
  equal_supply_ISO7761_switching_tables_do_not_guarantee_actual_mixed_rails=True,
  primary_input_output_load_conditions_must_be_preserved=True,
  no_copper_or_reference_across_actual_isolation_barrier=True,
  local_short_driver_to_receiver_routing=True,profile_sclk_hz=4000000))
 ret=net(iso,7)
 add(name+'_SDO_HOST_RETURN',[ret],'/LOGIC_GND',3.3,'isolated_SPI_MISO_gated_return',dict(
  host_return_isolation='real ISO7761 OUT7 to actual CS-selected1G125; no wired push-pull parallel return'))
 for ip,tp in zip([15,14,13,10],pins):
  edge(name+' '+str(ip)+' iso to target',(iso,str(ip)),(target,str(tp)),'local_isolated_analog_SPI')
 if name=='AI':
  localreset=[net('U14708',p)for p in [1,2,4]]
 else:
  offset=0 if name=='AO0'else 18
  localreset=[net('U'+str(14606+offset),p)for p in [1,2,4]]+[net('U'+str(14607+offset),p)for p in [1,2,4]]
 add(name+'_RESET_ENABLE',localreset,g,5.0,'isolated_power_qualified_analog_reset_enable',dict(
  power_good_qualified_actual_hardware=True,default_LOW=True,no_command_readback_when_actual_RESET_low=True,
  physical_fault_to_inhibit_timing_unqualified=True))
add('ACC_RESET_AND_PERMIT',[net('U14401',6),net('U14402',1),net('U14404',2),net('U14402',5),net('U14401',1),net('U14401',5)],
 '/LOGIC_GND',3.3,'asynchronous_permission_and_strobe',dict(
 ordinary112_eligibility_unchanged=True,real_supervisor_AND_permission_clear=True,
 strobe_is_timing_sensitive_not_ordinary=True,source_has_real_pulldowns=True,
 fault_to_inhibit_20ms_not_proven_by_route_geometry=True))
for name,mcu,iso,drivers,g in [('DOA','U13004','U10003',['U10004','U10009'],'/motherboard_motors/FIELD_GND'),
 ('DOB','U13008','U10016',['U10017','U10022'],'/motherboard_do/FIELD_B_0V')]:
 add(name+'_SPI_HOST',[net(mcu,p)for p in [1,30,31,32]],'/LOGIC_GND',3.3,'isolated_smart_output_host_SPI',dict(
  actual_target_SPI2_hz=4000000,mode=1,shared_addressed_driver_count=2,
  current_OSPEEDR11_source_setting_exists=True,hardware_enable_kept_LOW_by_readonly_target=True))
 add(name+'_SPI_FIELD',[net(drivers[0],p)for p in [7,8,9,10]],g,3.3,'isolated_smart_output_field_SPI',dict(
  actual_iso=iso,actual_driver_refs=drivers,actual_field_supply=name+'_FIELD_3V3',
  ISO7762_equal3V3_timing_table_applies_only_if_actual_supplies_and_load_meet_table=True,
  addressable_shared_CS=True,driver_clock_max_hz=10000000,driver_CSDO_test_load_pf=30,
  minimum_CS_high_between_transfers_ns=500,each_driver_output_CS_address_HiZ_protocol_must_be_verified=True,
  source_series_damping_resistors_in_field_bus=False,no_reference_across_ISO_barrier=True))
 add(name+'_ENABLE_FIELD',[net(drivers[0],3)],g,3.3,'isolated_hard_permission',dict(
  default_LOW=True,real_OUT_PERMIT_reset_latch_before_iso=True,readonly_never_asserts=True))
primary_files=[
 'reports/motherboard-io-control-20260930/sources/74lvc125a-nexperia.pdf',
 'reports/motherboard-compute-20260930/sources/sn74lvc1g125.pdf',
 'reports/motherboard-analog-20260930/sources/iso7761.pdf',
 'reports/motherboard-analog-input-20260930/sources/ads8684a.pdf',
 'research/fpga-core/trion20-ds-v6.0.pdf','research/fpga-core/w25q32jv.pdf',
 'research/fpga-core/ase.pdf','research/mc-motor-buffers/sn74lvc244a.pdf',
 'reports/motherboard-do-20260930/sources/tps274c65.pdf']
report=dict(passed=True,meaning='Exact electrical source/pin/domain/series-resource inventory; not permission to autoroute or timing signoff',
 source_revision=26,source_adoption_sha256=sha(ADOPT),source_design_sha256=sha(SRC/'design.json'),source_netlist_sha256=sha(SRC/'netlist.xml'),
 inspection_board=str(BOARD),inspection_board_sha256=sha(BOARD),ordinary112_sha256=sha(ORDINARY),ordinary112_unchanged=True,
 groups=groups,nets=routes,critical_group_count=len(groups),exact_critical_native_nets=len(routes),
 current_critical_missing_joins=sum(r['current_independent_missing_joins']for r in routes.values()),
 actual_point_to_point_lower_bounds=edges,source_resistor_stub_screens=source_stubs,PB5_clock_tap_stubs=tap_stubs,
 primary_input_sha256={p:sha(ROOT/p)for p in primary_files},primary_online_sources=[
  {'url':'https://www.st.com/resource/en/datasheet/stm32g031g6.pdf','revision':'DS12992 Rev4 June2025','pages':[41,74,75,87,88,89,90],'retained_PDF':False,'retrieval':'official web PDF text checked; direct download timed out'},
  {'url':'https://www.analog.com/media/en/technical-documentation/data-sheets/AD5683R_5682R_5681R_5683.pdf','revision':'RevD','pages':[6,7],'retained_PDF':False,'retrieval':'official web PDF text checked; direct download timed out'}],
 target_source_sha256={p:sha(ROOT/p)for p in ['firmware/motherboard_iol1_readonly/target.c','gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v']},
 physical_timing_qualification=False,vendor_STA_pass=False,route_execution_permission=False,manufacturing_ready=False)
write(OUT/'critical-digital-source-review.json',report)
print(json.dumps(dict(passed=True,groups=len(groups),exact_nets=len(routes),actual_edges=len(edges),source_stubs=len(source_stubs),source_stub_target_misses=sum(not x['current_straight_lower_bound_meets_engineering_target']for x in source_stubs))))
