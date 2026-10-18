"""Isolated, disconnected BRAM inference experiment; canonical RTL is read-only."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET
import psutil

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
OUT = H/'efinity-memory-inference-r1'
SOURCE = ROOT/'gateware/v3/runtime/cnc3_event_bank.v'
CANDIDATE = '''`timescale 1ns/1ps
// Keep the unconditional registered memory read visible to RAM inference.
// A separate registered bypass preserves exact write-first collision behavior.
module cnc3_event_bank(input wire clk,write_enable,
 input wire[4:0]write_address,read_address,input wire[159:0]write_data,
 output wire[159:0]read_data);
 reg[159:0]memory[0:31];
 reg[159:0]ram_read,forward_data;
 reg forward_valid;
 always@(posedge clk)begin
  if(write_enable)memory[write_address]<=write_data;
  ram_read<=memory[read_address];
  if(write_enable && write_address==read_address)forward_valid<=1'b1;
  else forward_valid<=1'b0;
  forward_data<=write_data;
 end
 assign read_data=forward_valid?forward_data:ram_read;
endmodule
'''


def sha(p):
    with Path(p).open('rb') as s:
        return hashlib.file_digest(s,'sha256').hexdigest()


def run_guarded(args, cwd, name):
    env = dict(os.environ)
    env.update({k:'2' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
    samples, paused = [], set()
    with (cwd/(name+'.console.log')).open('w') as log:
        child = subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        p = psutil.Process(child.pid)
        while child.poll() is None:
            cpu = psutil.cpu_percent(interval=1)
            try:
                family = [p,*p.children(recursive=True)]
            except psutil.NoSuchProcess:
                break
            if cpu >= 70:
                for q in reversed(family):
                    if q.pid not in paused:
                        try: q.suspend(); paused.add(q.pid)
                        except psutil.Error: pass
            elif cpu < 62:
                for q in family:
                    if q.pid in paused:
                        try: q.resume(); paused.remove(q.pid)
                        except psutil.Error: pass
            row = {'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'CPU_percent':cpu,'pid':p.pid,'paused':sorted(paused)}
            samples.append(row)
            with (OUT/'resource-samples.jsonl').open('a') as log: log.write(json.dumps(row)+'\n')
            (OUT/'status.json').write_text(json.dumps({'phase':name,'sample':row},indent=2)+'\n')
        for pid in paused:
            try: psutil.Process(pid).resume()
            except psutil.Error: pass
        rc = child.wait()
    return {'exit':rc,'samples':len(samples),'peak_total_CPU_percent':max([x['CPU_percent'] for x in samples],default=0)}


def project(where):
    ns='http://www.efinixinc.com/enf_proj';ET.register_namespace('efx',ns);t=lambda x:'{'+ns+'}'+x
    p=ET.Element(t('project'),name='cnc3_event_bank',sw_version='2026.1.132')
    d=ET.SubElement(p,t('device_info'))
    for k,v in [('family','Trion'),('device','T20F256'),('timing_model','I4')]:ET.SubElement(d,t(k),name=v)
    d=ET.SubElement(p,t('design_info'),def_veri_version='verilog_2k',def_vhdl_version='vhdl_2008',unified_flow='false')
    ET.SubElement(d,t('top_module'),name='cnc3_event_bank');ET.SubElement(d,t('design_file'),name='cnc3_event_bank.v',version='default',library='default')
    ET.SubElement(d,t('top_vhdl_arch'),name='')
    for k in ('constraint_info','sim_info','misc_info','ip_info'):ET.SubElement(p,t(k))
    s=ET.SubElement(p,t('synthesis'),tool_name='efx_map')
    for k,v in [('max_threads','2'),('write_efx_verilog','on')]:ET.SubElement(s,t('param'),name=k,value=v,value_type='e_integer' if k=='max_threads' else 'e_bool')
    ET.indent(p);ET.ElementTree(p).write(where/'cnc3_event_bank.xml',encoding='UTF-8',xml_declaration=True)


def main():
    assert not OUT.exists();OUT.mkdir()
    me=psutil.Process();me.cpu_affinity([16,17]);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    source_sha=sha(SOURCE)
    records=[]
    for name,text in [('original',SOURCE.read_text()),('registered-bypass',CANDIDATE)]:
        d=OUT/name;d.mkdir();(d/'cnc3_event_bank.v').write_text(text);project(d)
        (d/'project-before.xml').write_bytes((d/'cnc3_event_bank.xml').read_bytes())
        args=['cmd.exe','/d','/c','C:/Efinity/2026.1/bin/efx_run.bat','cnc3_event_bank','--prj','-f','map','--timeout','180']
        result=run_guarded(args,d,name+'-map')
        assert result['exit']==0
        report=(d/'outflow/cnc3_event_bank.map.rpt').read_text()
        summary=report.split('### ### Resource Summary (begin) ### ### ###')[-1]
        resources={k:int(v) for k,v in re.findall(r'^(EFX_\w+)\s*:\s*(\d+)',summary,re.M)}
        assert re.search(r'map\s*:\s*PASS',(d/(name+'-map.console.log')).read_text())
        records.append({'variant':name,**result,'resources':resources,'RTL_SHA256':sha(d/'cnc3_event_bank.v'),
            'native_report_SHA256':sha(d/'outflow/cnc3_event_bank.map.rpt')})
        print(json.dumps(records[-1]),flush=True)
    assert sha(SOURCE)==source_sha
    receipt={'status':'NATIVE_MEMORY_INFERENCE_COMPARISON_COMPLETE_BEHAVIORAL_QUALIFICATION_REQUIRED','variants':records,
        'canonical_RTL_unchanged':True,'canonical_SHA256':source_sha,'candidate_functional_regression':'UNEXECUTED',
        'physical_wrapper_fit_timing':'OPEN','adopted':False,'manufacturing_ready':False,'script_SHA256':sha(Path(__file__))}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (OUT/'status.json').write_text(json.dumps({'phase':'COMPLETE','status':receipt['status']})+'\n')


if __name__=='__main__':main()
