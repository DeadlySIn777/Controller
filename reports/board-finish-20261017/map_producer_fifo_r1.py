"""Native events-only resource measurement after the differential passes."""
from pathlib import Path
import hashlib,importlib.util,json,re,shutil,sys
import xml.etree.ElementTree as ET
import psutil
H=Path(__file__).resolve().parent;RUN=H/'event-producer-fifo-r1';OUT=RUN/'native-events-map'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def semantic(e):return e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(map(semantic,e))
def main():
 behavior=json.loads((RUN/'behavior-receipt.json').read_bytes());assert behavior['status']=='PRODUCER_FIFO_DIFFERENTIAL_PASS'
 candidate=RUN/'cnc3_runtime_events.v';prep=json.loads((RUN/'preparation-receipt.json').read_bytes());assert sha(candidate)==prep['candidate_SHA256']
 supplement_path=H/'release-review/producer-fifo-independent-supplement-r1/receipt.json'
 supplement=json.loads(supplement_path.read_bytes())
 assert supplement['status']=='PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS'
 assert supplement['selected_candidate_SHA256']==sha(candidate)
 assert supplement['candidate_diff_normalization_equals_selected_source']
 assert (RUN/'candidate_diff.v').read_text().replace('module cnc3_runtime_events_candidate(', 'module cnc3_runtime_events(')==candidate.read_text()
 assert not OUT.exists();OUT.mkdir()
 me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 shutil.copyfile(candidate,OUT/candidate.name)
 ns='http://www.efinixinc.com/enf_proj';ET.register_namespace('efx',ns);t=lambda x:'{'+ns+'}'+x
 p=ET.Element(t('project'),name='cnc3_runtime_events',sw_version='2026.1.132');info=ET.SubElement(p,t('device_info'))
 for k,v in [('family','Trion'),('device','T20F256'),('timing_model','I4')]:ET.SubElement(info,t(k),name=v)
 info=ET.SubElement(p,t('design_info'),def_veri_version='verilog_2k',def_vhdl_version='vhdl_2008',unified_flow='false')
 ET.SubElement(info,t('top_module'),name='cnc3_runtime_events')
 ET.SubElement(info,t('design_file'),name='cnc3_runtime_events.v',version='default',library='default')
 ET.SubElement(info,t('top_vhdl_arch'),name='')
 for k in ['constraint_info','sim_info','misc_info','ip_info']:ET.SubElement(p,t(k))
 syn=ET.SubElement(p,t('synthesis'),tool_name='efx_map')
 for k,v,typ in [('max_threads','2','e_integer'),('write_efx_verilog','on','e_bool'),('mode','area2','e_option')]:ET.SubElement(syn,t('param'),name=k,value=v,value_type=typ)
 ET.indent(p);xml=OUT/'cnc3_runtime_events.xml';ET.ElementTree(p).write(xml,encoding='UTF-8',xml_declaration=True)
 before=semantic(p);shutil.copyfile(xml,OUT/'project-before.xml')
 spec=importlib.util.spec_from_file_location('guard',H/'run_efinity_ram_inference_r1.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);A.OUT=OUT
 argv=['cmd.exe','/d','/c','C:/Efinity/2026.1/bin/efx_run.bat','cnc3_runtime_events','--prj','-f','map','--timeout','600']
 result=A.run_guarded(argv,OUT,'producer-events-area2-map')
 report=OUT/'outflow/cnc3_runtime_events.map.rpt';text=report.read_text() if report.exists() else ''
 resources={k:int(v) for k,v in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)',text.split('### ### Resource Summary (begin) ### ### ###')[-1],re.M)}
 assert semantic(ET.parse(xml).getroot())==before
 assert sha(candidate)==sha(OUT/candidate.name)==prep['candidate_SHA256']
 passed=result['exit']==0 and bool(re.search(r'map\s*:\s*PASS',(OUT/'producer-events-area2-map.console.log').read_text())) and bool(resources)
 rec={'status':'NATIVE_PRODUCER_FIFO_EVENTS_ONLY_MAP_PASS' if passed else 'FAIL','execution':result,'resources':resources,'mode':'area2','source_SHA256':sha(candidate),'project_semantics_unchanged':True,'behavior_receipt_SHA256':sha(RUN/'behavior-receipt.json'),'focused_supplement_SHA256':sha(supplement_path),'full_core_fit_timing':'SEPARATE_OPEN','adopted':False,'input_output_SHA256':{str(p):sha(p) for p in [Path(__file__),xml,OUT/'project-before.xml',report,OUT/'producer-events-area2-map.console.log'] if p.exists()}}
 (OUT/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2),flush=True)
 return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
