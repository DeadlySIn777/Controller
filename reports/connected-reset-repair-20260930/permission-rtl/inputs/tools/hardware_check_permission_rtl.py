"""Run actual endpoint RTL against the independent permission connection model.

Uses existing WSL Icarus only, with a fresh copied input set and an immutable run
directory. No machine interface, firmware flashing or vendor tools are invoked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCES=('gateware/rtl/cnc_endpoint.v','gateware/rtl/cnc_spi_frame.v',
         'gateware/rtl/cnc_stepgen.v','gateware/rtl/cnc_encoder.v',
         'gateware/board_review/tb_permission_connection.sv',
         'tools/hardware_check_permission_rtl.py')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    out=Path(args.output_dir).resolve()
    if out.exists():raise SystemExit('Refusing to replace existing RTL evidence: '+str(out))
    names=list(SOURCES)
    for name in ('netlist.xml','pin-map.json','design-envelope.json','machine_permission.kicad_sch'):
        rel='hardware/machine_permission/'+name
        if (ROOT/rel).is_file():names.append(rel)
    raw={name:(ROOT/name).read_bytes() for name in names}
    before={name:sha(data) for name,data in raw.items()}
    out.mkdir(parents=True)
    for name,data in raw.items():
        path=out/'inputs'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    script='''#!/bin/sh
set -eu
cd "$(dirname "$0")"
iverilog -V > tool-version.txt 2>&1
iverilog -g2012 -Wall -s tb_permission_connection -o simulation \\
  inputs/gateware/rtl/cnc_endpoint.v inputs/gateware/rtl/cnc_spi_frame.v \\
  inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v \\
  inputs/gateware/board_review/tb_permission_connection.sv > build.log 2>&1
vvp simulation > run.log 2>&1
'''
    (out/'run.sh').write_text(script,encoding='utf-8',newline='\n')
    if not re.match(r'^[A-Za-z]:',str(out)):
        command=['sh',str(out/'run.sh')]
    else:
        unix='/mnt/'+str(out)[0].lower()+str(out)[2:].replace('\\','/')+'/run.sh'
        command=['wsl','-d','GarciaMechBuilder','--','sh',unix]
    run=subprocess.run(command,capture_output=True,text=True,timeout=150)
    (out/'launcher.log').write_text(run.stdout+run.stderr,encoding='utf-8')
    log=(out/'run.log').read_text() if (out/'run.log').exists() else ''
    matches=re.findall(r'^PASS permission connection checks=(\d+);',log,re.M)
    count=int(matches[0]) if len(matches)==1 else 0
    changed=[name for name,data in raw.items()
             if (ROOT/name).read_bytes()!=data or (out/'inputs'/name).read_bytes()!=data]
    ok=run.returncode==0 and count==49 and not changed and 'FAIL ' not in log
    result={'schema_version':1,'checks_pass':ok,'checks':count,'exit_code':run.returncode,
            'scope':'Actual six-channel cnc_endpoint RTL plus ideal digital external-permission gates/latch and separate post-CDONE user-reset hold',
            'manufacturing_ready':False,'watchdog_timing_model':False,
            'watchdog_output':'Explicit independent fault/release injection; timer tolerance analyzed separately',
            'source_sha256':before,'changed_during_run':changed,
            'not_proved':['expanded motion protocol','analog gate timing or metastability','watchdog physical response',
                          'package fit','routed timing','physical fault interruption','machine stopping distance']}
    result['artifact_sha256']={p.name:sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','artifact_sha256')},indent=2))
    return not ok


if __name__=='__main__':raise SystemExit(main())
