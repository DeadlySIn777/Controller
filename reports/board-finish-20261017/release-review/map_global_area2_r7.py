"""Native full-SIM2 map of two isolated RAM/dispatch overlays, no adoption."""
from pathlib import Path
import hashlib, importlib.util, json, re, shutil, sys
import xml.etree.ElementTree as ET
import psutil
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
H=HERE.parent
OUT=HERE/'event-capture-global-area2-r7/native-full-map'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def semantic(e):return (e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(map(semantic,e)))
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'inputs').mkdir()
    me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    baseline=json.loads((H/'efinity-functional-SIM2-bram-map-r2/receipt.json').read_bytes())
    overlay={'cnc3_runtime_events.v':HERE/'event-capture-select-r2/cnc3_runtime_events.v',
             'cnc3_event_bank.v':H/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v'}
    inventory=[]
    for old in baseline['source_inventory']:
        canonical=Path(old['canonical']);assert sha(canonical)==old['canonical_SHA256']
        source=overlay.get(canonical.name,canonical)
        copy=OUT/'inputs'/canonical.name;shutil.copyfile(source,copy)
        inventory.append({'canonical':str(canonical),'canonical_SHA256':sha(canonical),'selected_source':str(source),'copy':str(copy),'copy_SHA256':sha(copy)})
    xml=OUT/'cnc3_runtime_sim.xml';shutil.copyfile(H/'efinity-functional-SIM2-bram-map-r2/project-before.xml',xml)
    tree=ET.parse(xml);ns={'e':'http://www.efinixinc.com/enf_proj'}
    syn=tree.getroot().find('e:synthesis',ns);assert syn is not None
    modes=[x for x in syn if x.attrib.get('name')=='mode'];assert len(modes)<=1
    mode=modes[0] if modes else ET.SubElement(syn,'{'+ns['e']+'}param')
    mode.attrib.update(name='mode',value='area2',value_type='e_option')
    ET.indent(tree);tree.write(xml,encoding='UTF-8',xml_declaration=True)
    initial=semantic(ET.parse(xml).getroot());shutil.copyfile(xml,OUT/'project-before.xml')
    spec=importlib.util.spec_from_file_location('bounded_native_helper',H/'run_efinity_ram_inference_r1.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);helper.OUT=OUT
    argv=['cmd.exe','/d','/c','C:/Efinity/2026.1/bin/efx_run.bat','cnc3_runtime_sim','--prj','-f','map','--timeout','900']
    (OUT/'plan.json').write_text(json.dumps({'profile':'DISCONNECTED_SIM2_BRAM_AND_CAPTURE_EXPERIMENT','source_inventory':inventory,'argv':argv,'affinity':[16,17],'max_vendor_threads':2,'adopted':False},indent=2)+'\n')
    print('Mapping isolated capture selector plus registered RAM bypass full SIM2.',flush=True)
    result=helper.run_guarded(argv,OUT,'full-SIM2-global-area2-map')
    report=OUT/'outflow/cnc3_runtime_sim.map.rpt'
    text=report.read_text() if report.exists() else ''
    resources={k:int(v) for k,v in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)',text.split('### ### Resource Summary (begin) ### ### ###')[-1],re.M)}
    assert re.search(r'^mode\s*:\s*area2\s*$',text,re.M)
    assert all(sha(x['canonical'])==x['canonical_SHA256'] and sha(x['copy'])==x['copy_SHA256'] for x in inventory)
    assert semantic(ET.parse(xml).getroot())==initial
    record={'status':'EXPLORATORY_NATIVE_SIM2_GLOBAL_AREA2_MAP_COMPLETE_BEHAVIOR_AND_FIT_SEPARATE','execution':result,'resources':resources,'baseline_BRAM_only_resources':baseline['resources'],'source_inventory':inventory,'canonical_sources_unchanged':True,'project_semantics_unchanged':True,'physical_wrapper_place_route_timing':'OPEN_UNEXECUTED','candidate_differential':'SEPARATE_RECEIPT_REQUIRED','adopted':False,'manufacturing_ready':False,'input_output_SHA256':{str(p):sha(p) for p in [Path(__file__),OUT/'plan.json',OUT/'project-before.xml',xml,report,OUT/'full-SIM2-global-area2-map.console.log'] if p.exists()}}
    (OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    (OUT/'status.json').write_text(json.dumps({'phase':'COMPLETE','exit':result['exit'],'resources':resources})+'\n')
    print(json.dumps({'status':record['status'],'execution':result,'resources':resources}),flush=True)
    return result['exit']
if __name__=='__main__':raise SystemExit(main())
