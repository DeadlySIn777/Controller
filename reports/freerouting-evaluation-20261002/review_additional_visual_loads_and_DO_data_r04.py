"""Endpoint-grounded follow-up inventory, not an extension of ordinary112."""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve();sys.path.insert(0,str(ROOT/'tools'))
import pcbnew as p
R=ROOT/'reports/freerouting-evaluation-20261002'
OUT=R/'ROOT103-additional-endpoint-review-r04'
BASE=ROOT/'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb'
MODEL=ROOT/'hardware/motherboard/design.json';XML=ROOT/'hardware/motherboard/netlist.xml'
def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
assert not OUT.exists();OUT.mkdir()
inputs={str(q):sha(q)for q in(BASE,MODEL,XML,Path(__file__).resolve(),ROOT/'hardware/motherboard_status/design.json',ROOT/'hardware/motherboard_do/design.json',ROOT/'hardware/motherboard_io_control/design.json')}
assert inputs[str(BASE)]=='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
m=json.loads(MODEL.read_text());b=p.LoadBoard(str(BASE));b.BuildConnectivity();co=b.GetConnectivity()
pads={(f.GetReference(),q.GetNumber()):q for f in b.GetFootprints()for q in f.Pads()if q.GetNumber()}
native={}
for q in b.GetPads():
 if q.GetNumber() and q.GetNetname():native.setdefault(q.GetNetname(),set()).add((q.GetParentFootprint().GetReference(),q.GetNumber()))
xmltree=ET.parse(XML);xml={n.get('name'):n for n in xmltree.findall('nets/net')};xmlcomponents={c.get('ref'):c for c in xmltree.findall('components/comp')}
def review(net,expected,scope,disposition):
 expected=set(expected);assert native[net]==expected,(net,expected,native[net])
 node=xml[net];actual={(x.get('ref'),x.get('pin'))for x in node.findall('node')};virtual=actual-expected;assert expected<=actual and all(r not in m['components'] and xmlcomponents[r].find("property[@name='exclude_from_board']")is not None and xmlcomponents[r].find("property[@name='exclude_from_bom']")is not None for r,pin in virtual),(net,expected,actual)
 nodes={(x.get('ref'),x.get('pin')):x.attrib for x in node.findall('node')};eps=[];groups=set()
 for ref,pin in sorted(expected):
  c=m['components'][ref];q=pads[ref,pin];assert q.GetNetname()==net
  eps.append(dict(reference=ref,pin=pin,mpn=c['mpn'],source_block=c['source_block'],model_pin_net=c['pins'][pin],source_role=c.get('role'),native_pad_UUID=q.m_Uuid.AsString(),native_pin_function=nodes[ref,pin].get('pinfunction'),native_pin_type=nodes[ref,pin].get('pintype')))
  connected={x.m_Uuid.AsString()for x in co.GetConnectedItems(q)if x.Type()==p.PCB_PAD_T};connected.add(q.m_Uuid.AsString());groups.add(tuple(sorted(connected)))
 return dict(net=net,classification=scope,exact_source_endpoints=eps,nonphysical_integration_ports=[dict(reference=r,pin=pin,physical=False,role=xmlcomponents[r].findtext('value'),native_source_explicitly_exclude_from_board=True,native_source_explicitly_exclude_from_bom=True)for r,pin in sorted(virtual)],actual_source_components_before=len(groups),required_joins_before=len(groups)-1,disposition=disposition)
visual=[]
status=json.loads((ROOT/'hardware/motherboard_status/design.json').read_text())
for ch,entry in enumerate(status['receive_indicators'][:24]):
 assert entry['index']==ch and entry['observed_net']=='DI'+str(ch)+'_LOGIC'
 led=entry['led_ref'];res=entry['current_ref'];bleed=entry['bleed_ref'];sink=entry['sink_ref'];pin=str(entry['output_pin'])
 assert m['components'][bleed]['role']=='off-leak shunt prevents an LED path becoming a leakage display' and m['components'][bleed]['resistance_ohm']==10000
 lc,rc,sc=(m['components'][v]for v in(led,res,sink))
 assert lc['mpn']=='APT1608SGC'and lc['label']=='IN'+str(ch+1)
 assert rc['resistance_ohm']==1000 and rc['tolerance']==.01 and rc['role']=='bounded receive LED current, even a shorted LED'
 assert sc['mpn']=='74LVC07APW,118' and sc['pins'][pin]==lc['pins']['1']
 for term,ep in [('A',[(res,'2'),(led,'2'),(bleed,'1')]),('K',[(led,'1'),(sink,pin),(bleed,'2')])]:
  net=pads[ep[0]].GetNetname()
  row=review(net,ep,'ordinary_general_DI_visual_LED_load_power','All three exact endpoints are only the IN1–IN24 visible LED load,1k series resistor,10k off-leak shunt or independent07 sink. No controller permission, enable, watchdog, fault qualifier, motion, clock or process-PWM endpoint. Candidate for a NEW separately reviewed low-current LED-power route scope; not admitted by the frozen ordinary112 executor and not a digital reference/authority grant.')
  row.update(proposed_scope_eligible=True,allowlist_or_executor_changed=False,actual_return_net=pads[sink,'7'].GetNetname(),source_voltage_ceiling_v=5.5,conservative_zero_VF_LED_current_a=5.5/(1000*(1-.01)),required_separate_acceptance=['complete actual Source current-loop/return continuity','allocated LED current and trace/drop screen','native foreign copper/drill/board geometry','actual receiving/sink/default behavior; no visual hardware-health claim'])
  visual.append(row)
assert len(visual)==48 and all(q['actual_return_net']=='/LOGIC_GND'for q in visual)
do=[]
for bank,mc,iso in [('DOA','U13004','U10003'),('DOB','U13008','U10016')]:
 for func,mpin,ipin in [('SCLK','32','2'),('SDI','31','3'),('SDO','30','6'),('CS_N','1','4')]:
  assert m['components'][mc]['pins'][mpin]==m['components'][iso]['pins'][ipin]
  net=pads[mc,mpin].GetNetname()
  ep=native[net]
  row=review(net,ep,'actual_smart_DO_serial_data_bus','These actual MCU-to-ISO7762 endpoints are SPI data/clock/chip-select, with TPS addressed CRC/watchdog/commissioning semantics downstream. They are independently hardware-gated, but this does not convert their actual timing/CRC/SPI role into a generic GPIO. Retain under controlled source/electrical/timing routing unless a NEW separately reviewed bus scope is explicitly accepted; no ordinary112 admission or safety/enable routing exception.')
  row.update(proposed_scope_eligible=False,general_individual_DO_command_GPIO_found=False,reason='Actual Source uses addressed SPI, not individual low-speed digital channel-command pins.',user_exclusion_preserved='SPI/clock and all power/permission/enable/inhibit paths remain protected',actual_hardware_gate_equation=m.get('source_integrations',{}))
  row.pop('actual_hardware_gate_equation')
  do.append(row)
assert len(do)==8
data=dict(passed=True,scope='Additional exact endpoint inventory only, frozen ordinary112 review/DSN unchanged. Visual LED load power is proposed separately; actual smart-DO data SPI stays excluded.',input_sha256=inputs,board_sha256=sha(BASE),additional_proposed_visual_load_nets=48,visual_loads=visual,additional_actual_unjoined_visual_nets=sum(q['required_joins_before']>0 for q in visual),additional_actual_visual_joins=sum(q['required_joins_before']for q in visual),reviewed_actual_smart_DO_bus_nets=do,new_gpio_DO_command_nets=0,ordinary_allowlist_or_executor_modified=False,any_actual_route_run=False,manufacturing_ready=False)
(OUT/'source-endpoint-inventory.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8');assert all(sha(q)==h for q,h in inputs.items())
print(json.dumps(dict(passed=True,visual_proposed=48,visual_unjoined=data['additional_actual_unjoined_visual_nets'],visual_joins=data['additional_actual_visual_joins'],actual_DO_SPI_excluded=8)),flush=True)
