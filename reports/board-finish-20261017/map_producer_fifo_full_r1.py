"""Full disconnected SIM2 native map, with behavior-bound report-only overlays."""
from pathlib import Path
import hashlib,importlib.util,json,re,shutil,sys
import xml.etree.ElementTree as ET
import psutil
H=Path(__file__).resolve().parent;RUN=H/'event-producer-fifo-r1';OUT=RUN/'native-full-map'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def semantic(e):return e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(map(semantic,e))
def main():
 behavior=json.loads((RUN/'behavior-receipt.json').read_bytes());assert behavior['status']=='PRODUCER_FIFO_DIFFERENTIAL_PASS'
 eventmap=json.loads((RUN/'native-events-map/receipt.json').read_bytes());assert eventmap['status']=='NATIVE_PRODUCER_FIFO_EVENTS_ONLY_MAP_PASS'
 assert eventmap['source_SHA256']==sha(RUN/'cnc3_runtime_events.v')
 assert not OUT.exists();OUT.mkdir();(OUT/'inputs').mkdir()
 me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 baseline=json.loads((H/'efinity-functional-SIM2-bram-map-r2/receipt.json').read_bytes())
 overlay={'cnc3_runtime_events.v':RUN/'cnc3_runtime_events.v',
          'cnc3_event_bank.v':H/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v',
          'cnc3_spi_transport_stateful.v':H/'release-review/transport-cmd-alignment-r1/cnc3_spi_transport_stateful.v'}
 # The transport correction has its own independent actual-wire differential
 # and complete-suite packet; the composite full suite remains separate.
 transport_packet=H/'release-review/transport-cmd-alignment-r1/reviewable-transport-overlay-packet.json'
 assert transport_packet.exists()
 inventory=[]
 for row in baseline['source_inventory']:
  canonical=Path(row['canonical']);assert sha(canonical)==row['canonical_SHA256']
  source=overlay.get(canonical.name,canonical);copy=OUT/'inputs'/canonical.name;shutil.copyfile(source,copy)
  inventory.append({'canonical':str(canonical),'canonical_SHA256':sha(canonical),'selected_source':str(source),'copy':str(copy),'copy_SHA256':sha(copy)})
 xml=OUT/'cnc3_runtime_sim.xml';shutil.copyfile(H/'efinity-functional-SIM2-bram-map-r2/project-before.xml',xml)
 tree=ET.parse(xml);ns={'e':'http://www.efinixinc.com/enf_proj'};syn=tree.getroot().find('e:synthesis',ns);assert syn is not None
 modes=[x for x in syn if x.attrib.get('name')=='mode'];assert len(modes)<=1
 mode=modes[0] if modes else ET.SubElement(syn,'{'+ns['e']+'}param');mode.attrib.update(name='mode',value='area2',value_type='e_option')
 ET.indent(tree);tree.write(xml,encoding='UTF-8',xml_declaration=True)
 before=semantic(tree.getroot());shutil.copyfile(xml,OUT/'project-before.xml')
 spec=importlib.util.spec_from_file_location('guard',H/'run_efinity_ram_inference_r1.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);A.OUT=OUT
 argv=['cmd.exe','/d','/c','C:/Efinity/2026.1/bin/efx_run.bat','cnc3_runtime_sim','--prj','-f','map','--timeout','900']
 (OUT/'plan.json').write_text(json.dumps({'profile':'DISCONNECTED_SIM2_PRODUCER_FIFO_AND_TRANSPORT_EXPERIMENT','source_inventory':inventory,'argv':argv,'mode':'area2','physical_wrapper':False,'adopted':False},indent=2)+'\n')
 result=A.run_guarded(argv,OUT,'producer-full-area2-map')
 report=OUT/'outflow/cnc3_runtime_sim.map.rpt';text=report.read_text() if report.exists() else ''
 resources={k:int(v) for k,v in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)',text.split('### ### Resource Summary (begin) ### ### ###')[-1],re.M)}
 assert semantic(ET.parse(xml).getroot())==before
 assert all(sha(r['canonical'])==r['canonical_SHA256'] and sha(r['copy'])==r['copy_SHA256'] for r in inventory)
 passed=result['exit']==0 and bool(re.search(r'map\s*:\s*PASS',(OUT/'producer-full-area2-map.console.log').read_text())) and bool(resources)
 rec={'status':'NATIVE_PRODUCER_FIFO_FULL_SIM2_MAP_PASS_FIT_AND_TIMING_SEPARATE' if passed else 'FAIL','execution':result,'resources':resources,'mode':'area2','source_inventory':inventory,'canonical_sources_unchanged':True,'project_semantics_unchanged':True,'physical_wrapper_place_route_timing':'OPEN_UNEXECUTED','composite_runtime_suite':'SEPARATE_RECEIPT_REQUIRED','adopted':False,'manufacturing_ready':False,'input_output_SHA256':{str(p):sha(p) for p in [Path(__file__),RUN/'behavior-receipt.json',RUN/'native-events-map/receipt.json',transport_packet,xml,OUT/'project-before.xml',report,OUT/'producer-full-area2-map.console.log'] if p.exists()}}
 (OUT/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'status':rec['status'],'resources':resources,'execution':result}),flush=True)
 return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
