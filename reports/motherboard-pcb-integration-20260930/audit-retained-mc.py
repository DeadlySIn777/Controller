"""Inventory actual retained physical parts; labels do not create rack hardware."""
from collections import Counter,defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
model_path=ROOT/'hardware/motherboard/design.json'
net_path=ROOT/'hardware/motherboard/netlist.xml'
model=json.loads(model_path.read_text(encoding='utf8'))
retained_blocks={'fpga_core','mc_local_power','watchdog_conditioning','mc_permission','mc_motor_buffers'}
parts={r:c for r,c in model['components'].items() if c.get('source_block') in retained_blocks}
assert len(parts)==327
nodes={};groups=defaultdict(list)
for net in ET.parse(net_path).findall('.//nets/net'):
    for node in net.findall('node'):
        key=node.attrib['ref'],node.attrib['pin'];nodes[key]=net.attrib['name'];groups[net.attrib['name']].append('.'.join(key))
by_block={k:dict(physical_parts=sum(c['source_block']==k for c in parts.values()),
                 packages_by_MPN=dict(Counter(c['mpn'] for c in parts.values() if c['source_block']==k))) for k in sorted(retained_blocks)}
legacy=sorted({n for (r,p),n in nodes.items() if r in parts and re.search(r'MIA|MX4|DIC|BANK_B_BUFFER',n)})
connectors=[r for r,c in model['components'].items() if 'Connector' in c['footprint'] or r.startswith(('J','P','X'))]
summary=dict(scope='Actual current-source retained 327-part physical audit; no removal authorized or made',
    source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (model_path,net_path)},
    entire_parent_parts=len(model['components']),retained_parts=327,by_block=by_block,
    actual_physical_connector_parts=connectors,actual_CM_compute_socket_parts=0,
    actual_compute_SoM_parts=0,actual_ESP_module_socket_or_module_parts=0,
    actual_rack_backplane_connector_parts=0,actual_card_cage_or_card_ID_EEPROM_parts=0,
    legacy_marker_native_nets={n:groups[n] for n in legacy},
    buffer_use=dict(bank_A_packages=['U5001','U5002','U5003','U5004'],bank_A_capacity=32,bank_A_used=25,
                    bank_B_packages=['U5005','U5006','U5007','U5008','U5009','U5010','U5011'],bank_B_capacity=14,bank_B_used=13,
                    required_signals=38,unused_channels=8,
                    possible_package_consolidation='U5004 uses only one octal-buffer channel; seven unused outputs are true native NC. A separately reviewed single-channel Ioff buffer could replace that package. No deletion or cost saving qualified.'),
    core_power=dict(regulators={'U2001':'CORE_5V -> CORE_1V2','U2002':'CORE_5V -> IO_3V3'},
                    supervisors={'U2003':'CORE_5V UV/OV qualification -> MC_SEQ_5V_OK',
                                 'U2004':'CORE_1V2 UV/OV qualification enabled by MC_SEQ_5V_OK -> IO_3V3_EN',
                                 'U2005':'IO_3V3 UV/OV qualification enabled by IO_3V3_EN -> MC_RAILS_OK_5V'},
                    duplicate_regulator_rails_found=False,
                    qualification='Three cascaded supervisor packages are a consolidation study candidate, not three redundant regulators. Preserve sequencing, windows, reset and brownout behavior before replacing.'),
    preserve_required={'U3001/U3002':'Separate actual useful-progress motion and output watchdog timers',
                       'U4005/U4006':'Deliberate rising-request motion/output arm latches with asynchronous permission clear',
                       'U4011/U4012/U4013':'Actual TX/output/buffer interruption latches; labels do not turn these into card identity',
                       'U4014/U4015/U4016/U4017/U4018/U4019':'Actual sticky watchdog falling-edge records and reset/rearm qualification',
                       'U5001-U5011':'Source-backed Ioff/default-state buffers; bank-B physical OE differs from bank A. Same board alone does not prove partial-power protection unnecessary.'},
    obsolete_requirements_requiring_real_replacement={'DIC_OK_QUALIFIED':'U4001.6 BASE qualification input still needs authentic onboard DI/field health; never tie permanently healthy',
        'BANK_B_BUFFER_ENABLE_QUALIFIED':'Actual U5005-U5011 OE + U4013 interruption observation still require reviewed bank health/permission qualification; not a removable-card-present substitute'},
    changed_components=[],removed_components=[],physical_qualification=False)
(OUT/'retained-mc-audit.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
with (OUT/'retained-mc-inventory.csv').open('w',encoding='utf8',newline='') as stream:
    fields=['reference','source_block','MPN','footprint','role','exact_native_pin_nets'];w=csv.DictWriter(stream,fieldnames=fields);w.writeheader()
    for ref,c in sorted(parts.items()):
        w.writerow(dict(reference=ref,source_block=c['source_block'],MPN=c['mpn'],footprint=c['footprint'],role=c.get('role',''),
                        exact_native_pin_nets=json.dumps({p:n for (r,p),n in nodes.items() if r==ref},sort_keys=True)))
print(json.dumps({k:summary[k] for k in ('entire_parent_parts','retained_parts','actual_physical_connector_parts','actual_CM_compute_socket_parts','actual_compute_SoM_parts','actual_ESP_module_socket_or_module_parts','actual_rack_backplane_connector_parts')},indent=2))
