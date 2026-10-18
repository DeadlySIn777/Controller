"""Parent-authorized three-file installation with exact backup and active-read-set preservation."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent
DEST=Path('Z:/pcb-runs/claude-finish/tools/fix')
ROOT=HERE.parents[1]
COMBINED=ROOT/'recovery-composite/c06/four-fag'
NAMES=('stitch_vector_audit.py','stitch_exact_guard.py','stitch_plan3.py')
ORIGINAL='269682296227d1ebf58d1ce1cf8ad556b9f7efd9e8b380078d64fb7eae08622c'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pins_from(value,pins):
 if isinstance(value,dict):
  if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',value['sha256']):
   add_pin(pins,value['path'],value['sha256'])
  for key,item in value.items():
   if isinstance(key,str) and (':/' in key or ':\\' in key) and isinstance(item,str) and re.fullmatch('[0-9a-f]{64}',item):add_pin(pins,key,item)
   else:pins_from(item,pins)
 elif isinstance(value,list):
  for item in value:pins_from(item,pins)
def add_pin(pins,p,h):
 p=str(Path(p).resolve())
 if p in pins and pins[p]!=h:raise ValueError('Conflicting frozen source hash: '+p)
 pins[p]=h
def verify(pins):
 actual={p:digest(p) for p in pins}
 if actual!=pins:raise ValueError('Frozen source/measurement input changed')
 return actual
def active_users():
 command="$taskPlannerUsers = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(python(w)?|bash|sh|wsl|wslhost).*' -and $_.CommandLine -match 'stitch_plan3[.]py|stitch_exact_guard[.]py|stitch_vector_audit[.]py' } | Select-Object ProcessId,Name,CreationDate,CommandLine); [ordered]@{checked_utc=(Get-Date).ToUniversalTime().ToString('o'); matching_users=$taskPlannerUsers} | ConvertTo-Json -Depth 5"
 result=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,text=True)
 if result.returncode:raise ValueError('Active process inventory failed')
 snapshot=json.loads(result.stdout)
 if snapshot['matching_users']:raise ValueError('Planner/guard/helper currently in use; installation withheld')
 return snapshot
def main():
 started=time.time();ready=json.loads((HERE/'ready.json').read_bytes())
 pins=ready['files'];verify(pins)
 if ready['verdict']!='READY_TESTED_ROOT106_VECTOR_GUARD_V2' or ready['host_tests']!=16:raise ValueError('Guard readiness not complete')
 combined_ready=COMBINED/'ready-r1.json';frozen={};pins_from(json.loads(combined_ready.read_bytes()),frozen)
 for p in (combined_ready,COMBINED/'invocation-r1.json'):add_pin(frozen,p,digest(p))
 for name in ('board.kicad_pcb','LEDGER.md','LEDGER-steps.md','steps.log'):
  p=Path('Z:/pcb-runs/claude-finish/integrate')/name;add_pin(frozen,p,digest(p))
 planner_paths={str((DEST/name).resolve()) for name in NAMES}
 if planner_paths&set(frozen):raise ValueError('Active combined input closure binds a planner file')
 before=verify(frozen);users=active_users()
 destination_before={str(DEST/name):digest(DEST/name) if (DEST/name).exists() else None for name in NAMES}
 if destination_before[str(DEST/'stitch_plan3.py')]!=ORIGINAL:raise ValueError('Original planner SHA precondition failed')
 if any(destination_before[str(DEST/name)] is not None for name in NAMES[:2]):raise ValueError('Unexpected existing helper/guard; preserve and review before replacement')
 backup=DEST/'stitch_plan3.py.codex-backup-20261011-guard-v2'
 if backup.exists():
  if digest(backup)!=ORIGINAL:raise ValueError('Existing backup differs')
 else:
  with backup.open('xb') as stream:stream.write((DEST/'stitch_plan3.py').read_bytes())
 if digest(backup)!=ORIGINAL:raise ValueError('Backup identity failed')
 # Install dependencies first and final mandatory hook last, using same-directory atomic replaces.
 for name in NAMES:
  source=HERE/name;target=DEST/name;temp=DEST/(name+'.codex-guard-v2.tmp')
  if temp.exists():raise ValueError('Unexpected pending atomic temp file')
  with temp.open('xb') as stream:stream.write(source.read_bytes())
  if digest(temp)!=ready['install_files'][name]:raise ValueError('Temporary installed file identity differs')
  os.replace(temp,target)
 after=verify(frozen);verify(pins)
 installed={str(DEST/name):digest(DEST/name) for name in NAMES}
 if any(installed[str(DEST/name)]!=ready['install_files'][name] for name in NAMES):raise ValueError('Installed source differs from staged source')
 receipt={'verdict':'INSTALLED_TESTED_ROOT106_VECTOR_GUARD_V2','exit_code':0,
  'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':round(time.time()-started,3),
  'authorization':'Parent expressly authorized these three planner files after process/hash precheck; no active combined read-set binding',
  'ready_sha256':digest(HERE/'ready.json'),'install_script_sha256':digest(__file__),
  'active_use_precheck':users,'combined_ready_sha256':digest(combined_ready),
  'combined_and_live_frozen_inputs_count':len(frozen),'combined_and_live_frozen_inputs_before':before,
  'combined_and_live_frozen_inputs_after':after,'combined_read_set_excludes_planner_paths':True,
  'destination_before':destination_before,'destination_after':installed,'backup':str(backup),'backup_sha256':digest(backup),
  'targets':436,'accepted':184,'failed_after':252,'new_rejections':4,'accepted_recheck_violations':0,'host_tests':16,
  'gpu_jobs':0,'native_jobs':0,'board_modified':False,'ledger_modified':False,
  'scope':'Future ROOT106450x235 planner JSON-save guard; no stitch restart or board application',
  'limits':['Vector/stored-fill evidence only; current matching native connectivity/DRC/project/reservation and electrical gates remain required',
   'Frozen input closure preserved; active native outputs are intentionally produced by their own running measurement']}
 (HERE/'installation-receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({k:receipt[k] for k in ('verdict','backup','destination_after','combined_and_live_frozen_inputs_count','host_tests','targets','accepted','failed_after')}))
if __name__=='__main__':main()
