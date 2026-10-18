"""Bounded native events-only original/case-selector resource comparison."""
from pathlib import Path
import hashlib,importlib.util,json,re,shutil,sys
import xml.etree.ElementTree as ET
import psutil
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;RUN=H/'event-capture-area-r6';OUT=RUN/'native-events-map'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    spec=importlib.util.spec_from_file_location('bounded_helpers',H.parent/'run_efinity_ram_inference_r1.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);A.OUT=OUT
    records=[]
    bank=H.parent/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v'
    for name,source in [('area',RUN/'cnc3_runtime_events.v')]:
        d=OUT/name;d.mkdir();shutil.copyfile(source,d/'cnc3_runtime_events.v');shutil.copyfile(bank,d/'cnc3_event_bank.v')
        ns='http://www.efinixinc.com/enf_proj';ET.register_namespace('efx',ns);t=lambda x:'{'+ns+'}'+x
        p=ET.Element(t('project'),name='cnc3_runtime_events',sw_version='2026.1.132');info=ET.SubElement(p,t('device_info'))
        for k,v in [('family','Trion'),('device','T20F256'),('timing_model','I4')]:ET.SubElement(info,t(k),name=v)
        info=ET.SubElement(p,t('design_info'),def_veri_version='verilog_2k',def_vhdl_version='vhdl_2008',unified_flow='false')
        ET.SubElement(info,t('top_module'),name='cnc3_runtime_events')
        for f in ['cnc3_runtime_events.v','cnc3_event_bank.v']:ET.SubElement(info,t('design_file'),name=f,version='default',library='default')
        ET.SubElement(info,t('top_vhdl_arch'),name='')
        for k in ['constraint_info','sim_info','misc_info','ip_info']:ET.SubElement(p,t(k))
        syn=ET.SubElement(p,t('synthesis'),tool_name='efx_map')
        for k,v in [('max_threads','2'),('write_efx_verilog','on')]:ET.SubElement(syn,t('param'),name=k,value=v,value_type='e_integer' if k=='max_threads' else 'e_bool')
        ET.SubElement(syn,t('param'),name='mode',value='area',value_type='e_option')
        ET.indent(p);xml=d/'cnc3_runtime_events.xml';ET.ElementTree(p).write(xml,encoding='UTF-8',xml_declaration=True)
        shutil.copyfile(xml,d/'project-before.xml')
        result=A.run_guarded(['cmd.exe','/d','/c','C:/Efinity/2026.1/bin/efx_run.bat','cnc3_runtime_events','--prj','-f','map','--timeout','600'],d,name+'-map')
        report=d/'outflow/cnc3_runtime_events.map.rpt';text=report.read_text() if report.exists() else ''
        resources={k:int(v) for k,v in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)',text.split('### ### Resource Summary (begin) ### ### ###')[-1],re.M)}
        row={'variant':name,'execution':result,'resources':resources,'events_SHA256':sha(d/'cnc3_runtime_events.v'),'bank_SHA256':sha(d/'cnc3_event_bank.v'),'map_report_SHA256':sha(report) if report.exists() else None}
        records.append(row);print(json.dumps(row),flush=True)
        (OUT/'progress-receipt.json').write_text(json.dumps(records,indent=2)+'\n')
        if result['exit']:break
    record={'status':'NATIVE_EVENTS_ONLY_AREA_SETTING_MAP_COMPLETE','variants':records,'full_physical_wrapper_fit_timing':'OPEN','adopted':False,'script_SHA256':sha(Path(__file__))}
    (OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    return 0 if len(records)==1 and all(r['execution']['exit']==0 for r in records) else 1
if __name__=='__main__':raise SystemExit(main())
