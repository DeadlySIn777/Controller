"""Map an isolated one-file BRAM inference correction against the full SIM2 top."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import psutil
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
ROOT=H.parent.parent
OUT=H/'efinity-functional-SIM2-bram-map-r2'


def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()


def semantic(e):return (e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(map(semantic,e)))


def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'inputs').mkdir()
    me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    old=json.loads((H/'efinity-functional-SIM2-map-r1/plan.json').read_bytes())
    inventory=[]
    candidate=H/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v'
    assert sha(candidate)=='6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841'
    for row in old['source_inventory']:
        source=Path(row['source']);assert sha(source)==row['SHA256']
        copy=OUT/'inputs'/source.name;shutil.copyfile(candidate if source.name=='cnc3_event_bank.v' else source,copy)
        inventory.append({'canonical':str(source),'canonical_SHA256':sha(source),'copy':str(copy),'copy_SHA256':sha(copy)})
    xml=OUT/'cnc3_runtime_sim.xml'
    shutil.copyfile(H/'efinity-functional-SIM2-map-review-r1/reconstructed-original-project.xml',xml)
    initial=semantic(ET.parse(xml).getroot());shutil.copyfile(xml,OUT/'project-before.xml')
    spec=importlib.util.spec_from_file_location('bounded_efinity_helpers',H/'run_efinity_ram_inference_r1.py')
    A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);A.OUT=OUT
    args=['cmd.exe','/d','/c','C:/Efinity/2026.1/bin/efx_run.bat','cnc3_runtime_sim','--prj','-f','map','--timeout','900']
    (OUT/'plan.json').write_text(json.dumps({'profile':'DISCONNECTED_SIM2_ONE_FILE_BRAM_INFERENCE_DIAGNOSTIC','source_inventory':inventory,'args':args,'affinity':[16,17],'adopted':False},indent=2)+'\n')
    print('Mapping isolated full SIM2 BRAM candidate on two logical CPUs.',flush=True)
    result=A.run_guarded(args,OUT,'full-SIM2-BRAM-map')
    assert semantic(ET.parse(xml).getroot())==initial
    assert all(sha(row['canonical'])==row['canonical_SHA256'] and sha(row['copy'])==row['copy_SHA256'] for row in inventory)
    resources={}
    report=OUT/'outflow/cnc3_runtime_sim.map.rpt'
    if report.exists():
        summary=report.read_text().split('### ### Resource Summary (begin) ### ### ###')[-1]
        resources={k:int(v) for k,v in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)',summary,re.M)}
    record={'status':'ISOLATED_NATIVE_SIM2_BRAM_MAP_COMPLETE_RESULT_REVIEW_REQUIRED','execution':result,'resources':resources,
        'source_inventory':inventory,'canonical_sources_unchanged':True,'project_semantics_unchanged':True,
        'full_physical_wrapper_place_route_static_timing':'OPEN_UNEXECUTED','candidate_behavioral_regression':'SEPARATE_RECEIPT_REQUIRED',
        'PNR_bitstream_or_programming':False,'adopted':False,'manufacturing_ready':False,
        'output_SHA256':{str(p):sha(p) for p in [Path(__file__),OUT/'plan.json',OUT/'project-before.xml',xml,report,OUT/'full-SIM2-BRAM-map.console.log'] if p.exists()}}
    (OUT/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    (OUT/'status.json').write_text(json.dumps({'phase':'COMPLETE','exit':result['exit'],'resources':resources})+'\n')
    print(json.dumps({'status':record['status'],'execution':result,'resources':resources}),flush=True)
    return result['exit']


if __name__=='__main__':raise SystemExit(main())
