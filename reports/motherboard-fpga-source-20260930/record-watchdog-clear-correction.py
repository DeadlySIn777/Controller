"""Preserve the prior incorrect obligation and record the reviewed correction."""
import copy
import datetime
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hardware_apply_motherboard_fpga_allocation as tool

report=tool.REPORT
for name in ('applied-source.json','receipt.json'):
    archived=report/(Path(name).stem+'-pre-watchdog-clear-audit.json')
    if not archived.exists():shutil.copyfile(report/name,archived)
metadata=tool.load(report/'applied-source.json')
old=next(r for r in metadata['parent_endpoint_obligations'] if r['signal']=='WATCHDOG_TRIP_CLEAR')
metadata['parent_endpoint_obligations']=tool.endpoint_obligations()
metadata['watchdog_clear_correction']=dict(date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    original_obligation=old,
    corrected_obligation=next(r for r in tool.endpoint_obligations() if r['signal']=='WATCHDOG_TRIP_CLEAR'),
    reason='U4019.7/.3 actively drive WD_M/O_TRIP_CLEAR_N; FPGA must instead drive the actual U4018.1/.3 WD_REARM_M/O inputs.',
    isolated_candidate_r03_pin_allocation_or_copper_changed=False,
    original_obligation_valid=False)
tool.write_json(report/'applied-source.json',metadata)
tool.write_json(tool.LIVE/'fpga-allocation-applied.json',metadata)
tool.write_json(report/'watchdog-clear-correction.json',metadata['watchdog_clear_correction'])
