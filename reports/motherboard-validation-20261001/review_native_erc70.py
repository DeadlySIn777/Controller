"""Review every exact current ERC warning without suppressing native checks."""
import json,re,hashlib,sys,collections,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_map_motherboard_domains import SEEDS,RAW_RETURNS
out=Path(__file__).parent/'source24-native-rerun-r01'
erc=out/'erc.json';model=ROOT/'hardware/motherboard/design.json';xml=ROOT/'hardware/motherboard/netlist.xml';sub=ROOT/'reports/motherboard-return-zoning-20261001/floating-substrates-r03/receipt.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen={str(p):sha(p)for p in(erc,model,xml,sub,ROOT/'research/digital-inputs/iso1212.pdf')}
d=json.loads(erc.read_text());parts=json.loads(model.read_text())['components'];tree=ET.parse(xml)
by_net={q.attrib['name']:[(p.attrib['ref'],p.attrib['pin'])for p in q.findall('node')]for q in tree.findall('.//nets/net')};native={pair:name for name,pairs in by_net.items()for pair in pairs}
warnings=[v for s in d['sheets']for v in s['violations']]
assert not d['ignored_checks']and len(warnings)==70 and all(v['severity']=='warning'for v in warnings)
assert collections.Counter(v['type']for v in warnings)=={'isolated_pin_label':44,'ground_pin_not_ground':24,'pin_to_pin':2}
ground_pins={('U10003','9'),('U10016','9'),('U14615','1'),('U14615','7'),('U14623','9'),('U14617','5'),('U14633','1'),('U14633','7'),('U14605','9'),('U14635','5'),('U19001','9'),('U19001','14'),('U19002','9'),('U19002','14'),('U19003','9'),('U19003','14'),('U19017','9'),('U19017','16'),('U19025','5'),('U19019','8'),('U14812','11'),('U14813','11'),('U22003','1'),('U22003','8')}
review=[];seen_ground=set();seen_clock=set();seen_sub=set()
for v in warnings:
 row=dict(native_type=v['type'],native_description=v['description'],native_item_UUIDs=[i['uuid']for i in v['items']],suppressed=False)
 if v['type']=='isolated_pin_label':
  label=re.fullmatch("Label '([^']+)'",v['items'][0]['description']).group(1)
  matches=[(name,pairs)for name,pairs in by_net.items()if name.split('/')[-1]==label]
  assert len(matches)==1 and len(matches[0][1])==1 and 'SUB' in label
  net,pairs=matches[0];ref,pin=pairs[0];assert parts[ref]['mpn']=='ISO1212DBQR'and pin in('12','13')
  seen_sub.add((ref,pin));row.update(native_net=net,source_pin=[ref,pin],exact_MPN=parts[ref]['mpn'],disposition='Required single-device floating substrate thermal net; never connect to ground or the other substrate.',primary_source='https://www.ti.com/lit/ds/symlink/iso1212.pdf',primary_pin_table='ISO1212 Table6-2, SUB1/SUB2 pins13/12',native_substrate_donor_receipt=str(sub.relative_to(ROOT)),substrate_physical_loop_verified_on_donor=True)
 elif v['type']=='ground_pin_not_ground':
  ref,pin=re.search(r'Symbol (U[0-9]+) Pin ([0-9]+)',v['items'][0]['description']).groups();assert (ref,pin)in ground_pins
  net=native[ref,pin];assert net in set(SEEDS.values())|set(RAW_RETURNS)
  seen_ground.add((ref,pin));row.update(native_net=net,source_pin=[ref,pin],exact_MPN=parts[ref]['mpn'],disposition='Actual ground pin is assigned to its own isolated functional/raw-converter return. KiCad does not recognize this hierarchical alias as a global ground symbol. Preserve the source reference and domain isolation; do not join unrelated grounds to silence the warning.',actual_PCB_ground_joining_is_separate_routing_gate=True)
 else:
  nodes=[re.search(r'Symbol ([^ ]+) Pin ([0-9]+)',i['description']).groups()for i in v['items']]
  assert len(nodes)==2 and nodes[0]in(('U21001','2'),('U21001','7'))and nodes[1]==('#FLG2002','1')
  # KiCad excludes power-flag pseudo-symbols from the physical export. Native
  # ERC itself proves its connection; validate the real repeater pin against
  # the full fitted-pin netlist rather than inventing a physical flag pin.
  assert parts['U21001']['mpn']=='TCA9517ADGKR'and native[nodes[0]]=='/LOGIC_GND'and '#FLG2002'not in parts
  seen_clock.add(nodes[0]);row.update(native_net='/LOGIC_GND',source_pin=list(nodes[0]),exact_MPN='TCA9517ADGKR',disposition='Unused open-drain SCLA/SCLB are directly grounded as TI Table4-1 specifies. The schematic power flag denotes the ground reference; it is not a physical push-pull source.',primary_source='https://www.ti.com/lit/ds/symlink/tca9517a.pdf',primary_revision='SCPS245E, October2025, Table4-1 page4; freshly verified1October2026')
 review.append(row)
assert seen_ground==ground_pins and len(seen_sub)==44 and seen_clock=={('U21001','2'),('U21001','7')}
assert json.loads(sub.read_text())['passed']and all(sha(Path(p))==h for p,h in frozen.items())
result=dict(passed=True,native_ERC_errors=0,native_ERC_warnings=70,all70_exact_warnings_reviewed=True,native_ignored_checks=[],source_or_project_check_settings_modified=False,source_hashes=frozen,warning_dispositions=review,manufacturing_ready=False,scope='Technical review of unsuppressed source warnings only; separate final native PCB connectivity/planes and physical qualification remain required.')
(out/'erc70-technical-dispositions.json').write_text(json.dumps(result,indent=2)+'\n')
print(dict(passed=True,exact_native_warnings_reviewed=70,ignored_or_suppressed=0))
