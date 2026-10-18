"""Independent read-only full native map source/settings/resource check."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/board-finish-20261017'
MAP=BASE/'event-producer-fifo-r1/native-full-map'
OUT=BASE/'release-review/producer-full-native-map-independent-r1';OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(e):return e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(map(semantic,e))
r=json.loads((MAP/'receipt.json').read_text());plan=json.loads((MAP/'plan.json').read_text())
assert r['status']=='NATIVE_PRODUCER_FIFO_FULL_SIM2_MAP_PASS_FIT_AND_TIMING_SEPARATE'
assert r['execution']['exit']==0 and r['canonical_sources_unchanged'] and r['project_semantics_unchanged']
assert not r['adopted'] and not r['manufacturing_ready']
assert r['source_inventory']==plan['source_inventory'] and r['mode']==plan['mode']=='area2'
for p,h in r['input_output_SHA256'].items():assert sha(p)==h,p
expected_overlays={'cnc3_runtime_events.v':'4d21b8af4ca2decc10d872361fb033fcaecb939b14ff4d62d959609cdc2f30d6',
 'cnc3_event_bank.v':'6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841',
 'cnc3_spi_transport_stateful.v':'c909378cb28cf87c7113b1b92c6cdd82f71e166c64eb87548a8880ba85c9d4cc'}
changed=[]
for item in r['source_inventory']:
 assert sha(item['copy'])==sha(item['selected_source'])==item['copy_SHA256']
 name=Path(item['canonical']).name
 if item['canonical_SHA256']!=item['copy_SHA256']:
  assert expected_overlays[name]==item['copy_SHA256'];changed.append(name)
assert sorted(changed)==sorted(expected_overlays)
before=ET.parse(MAP/'project-before.xml').getroot();after=ET.parse(MAP/'cnc3_runtime_sim.xml').getroot()
assert semantic(before)==semantic(after)
ns={'e':'http://www.efinixinc.com/enf_proj'}
assert after.find('e:device_info/e:device',ns).get('name')=='T20F256'
assert after.find('e:device_info/e:timing_model',ns).get('name')=='I4'
assert after.find('e:design_info/e:top_module',ns).get('name')=='cnc3_runtime_sim'
xml_sources=[(MAP/e.get('name')).resolve() for e in after.findall('e:design_info/e:design_file',ns)]
assert sorted(map(str,xml_sources))==sorted(str(Path(x['copy']).resolve()) for x in r['source_inventory'])
params={x.get('name'):x.get('value') for x in after.findall('e:synthesis/e:param',ns)}
assert params['mode']=='area2' and params['max_threads']=='2' and params['blackbox-error']=='1'
assert len(after.find('e:constraint_info',ns))==0
report=(MAP/'outflow/cnc3_runtime_sim.map.rpt').read_text()
resources={k:int(v) for k,v in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)',report.split('### ### Resource Summary (begin) ### ### ###')[-1],re.M)}
assert resources==r['resources']
assert 'insert-ios : 0' in report and 'mode : area2' in report
assert re.search(r'map\s*:\s*PASS',(MAP/'producer-full-area2-map.console.log').read_text())
netlist=MAP/'outflow/cnc3_runtime_sim.map.v'
primitive_counts=dict(Counter(re.findall(r'^\s*(EFX_\w+)\s+',netlist.read_text(),re.M)))
assert primitive_counts==resources,(primitive_counts,resources)
csv=(MAP/'outflow/cnc3_runtime_sim.res.csv').read_text()
root_line=next(x for x in csv.splitlines() if x.startswith('cnc3_runtime_sim:cnc3_runtime_sim'))
csv_totals=[int(x) for x in re.findall(r'(\d+)\(\d+\)',root_line)]
assert csv_totals==[resources[k] for k in ['EFX_FF','EFX_ADD','EFX_LUT4','EFX_RAM_5K','EFX_MULT']]
bank_lines=[x for x in csv.splitlines() if re.search(r'\+producers\[\d+\]\.memory:',x)]
assert len(bank_lines)==7
assert all([int(x) for x in re.findall(r'(\d+)\(\d+\)',line)][3]==9 for line in bank_lines)
assert len(re.findall(r'\+motors\[\d+\]\.generator:',csv))==12
assert len(re.findall(r'\+encoders\[\d+\]\.encoder:',csv))==4
cells=resources['EFX_LUT4']+resources['EFX_ADD'];assert cells==17912 and 19728-cells==1816
receipt={'status':'INDEPENDENT_EXACT_NATIVE_FULL_SIM2_MAP_RESOURCE_SCOPE_PASS',
 'created_utc':datetime.now(timezone.utc).isoformat(),'source_inventory_files':len(xml_sources),
 'exact_three_overlays':expected_overlays,'XML_semantics_preserved':True,'mode':'area2','max_threads':2,
 'device':'T20F256','timing_model':'I4','top':'cnc3_runtime_sim',
 'resources':resources,'primitive_instances_equal_report_equal_root_CSV':True,
 'twelve_generators_four_encoders_present':True,'seven_producer_memories_nine_RAM5K_each':True,
 'coarse_LE_screen':{'LUT4_plus_ADD':cells,'published_T20_LE':19728,'remaining':1816,'remaining_percent':round(1816/19728*100,3),
  'interpretation':'Mapped core resource screen only. LE contains LUT OR full-adder; summed usage remains a coarse bound, not proof of actual packing, package IO fit, clocking, placement/routing or timing. Missing physical wrapper/provider/output functions need a new complete budget;1816 is not guaranteed implementable spare capacity.'},
 'scope':{'disconnected_SIM2':True,'physical_wrapper':False,'insert_ios':0,'constraints_present':False,
  'place_route_timing_bitstream_or_physical_measurement':False,'source_functional_suite':'separate bound receipt',
  'mapped_event_behavior':'root postmap-r3 running separately at review; adoption pending that result',
  'production_adopted':False,'manufacturing_ready':False},
 'evidence_SHA256':{str(p):sha(p) for p in [MAP/'receipt.json',MAP/'plan.json',MAP/'project-before.xml',MAP/'cnc3_runtime_sim.xml',MAP/'outflow/cnc3_runtime_sim.map.rpt',MAP/'outflow/cnc3_runtime_sim.res.csv',netlist]},
 'no_sources_settings_native_outputs_or_archives_modified':True}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'resources':resources,'coarse_LE':cells,'headroom':1816,'receipt_SHA256':sha(OUT/'receipt.json')}))
