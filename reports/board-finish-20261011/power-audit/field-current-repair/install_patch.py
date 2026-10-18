"""Authorized atomic helper/source install after unchanged active read-set and process prechecks."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent
DEST=Path('Z:/pcb-runs/claude-finish/tools')
NAMES=('field_current_guard.py','field_pdn_design.py')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(pins,p,h):
 p=str(Path(p).resolve())
 if p in pins and pins[p]!=h:raise ValueError('Contradictory frozen input identity')
 pins[p]=h
def collect(v,pins):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and re.fullmatch('[0-9a-f]{64}',str(v.get('sha256',''))):add(pins,v['path'],v['sha256'])
  for key,value in v.items():
   if isinstance(key,str) and (':/' in key or ':\\' in key) and isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value):add(pins,key,value)
   else:collect(value,pins)
 elif isinstance(v,list):
  for value in v:collect(value,pins)
def verify(pins):
 actual={p:digest(p) for p in pins}
 if actual!=pins:raise ValueError('Frozen measurement/evidence input changed')
 return actual
def main():
 started=time.time();ready_path=HERE/'ready.json';ready=json.loads(ready_path.read_bytes());verify(ready['files'])
 if ready['verdict']!='READY_TESTED_FIELD_CURRENT_PATCH' or ready['host_tests']!=21:raise ValueError('Current patch not ready')
 combined=BASE/'recovery-composite/c06/four-fag';pins={}
 for name in ('ready-r1.json','invocation-r1.json'):
  p=combined/name;add(pins,p,digest(p))
 collect(json.loads((combined/'ready-r1.json').read_bytes()),pins)
 for name in ('board.kicad_pcb','LEDGER.md','LEDGER-steps.md','steps.log'):
  p=Path('Z:/pcb-runs/claude-finish/integrate')/name;add(pins,p,digest(p))
 if {str((DEST/name).resolve()) for name in NAMES}&set(pins):raise ValueError('Active frozen measurement binds field source/helper; stage only')
 before=verify(pins)
 query="$taskCurrentUsers = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(python(w)?|bash|sh|wsl|wslhost).*' -and $_.CommandLine -match 'field_pdn_design[.]py|field_current_guard[.]py' } | Select-Object ProcessId,Name,CreationDate,CommandLine); [ordered]@{checked_utc=(Get-Date).ToUniversalTime().ToString('o'); matching_users=$taskCurrentUsers} | ConvertTo-Json -Depth 5"
 result=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,text=True)
 if result.returncode:raise ValueError('Active current planner inventory failed')
 processes=json.loads(result.stdout)
 if processes['matching_users']:raise ValueError('Current planner in use; stage only')
 original=ready['original_source_sha256'];dest_before={str(DEST/name):digest(DEST/name) if (DEST/name).exists() else None for name in NAMES}
 if dest_before[str(DEST/'field_pdn_design.py')]!=original:raise ValueError('Original shared field source changed')
 if dest_before[str(DEST/'field_current_guard.py')] is not None:raise ValueError('Unexpected existing helper: preserve and review before replacing')
 backup=DEST/'field_pdn_design.py.codex-backup-20261011-current-guard'
 if backup.exists():
  if digest(backup)!=original:raise ValueError('Existing backup differs')
 else:
  with backup.open('xb') as stream:stream.write((DEST/'field_pdn_design.py').read_bytes())
 if digest(backup)!=original:raise ValueError('Exact backup failed')
 for name in NAMES:
  source=HERE/name;target=DEST/name;temp=DEST/(name+'.codex-current-guard.tmp')
  if temp.exists():raise ValueError('Unexpected pending install temp')
  with temp.open('xb') as stream:stream.write(source.read_bytes())
  if digest(temp)!=ready['install_files'][name]:raise ValueError('Install temp identity differs')
  os.replace(temp,target)
 after=verify(pins);verify(ready['files'])
 installed={str(DEST/name):digest(DEST/name) for name in NAMES}
 if any(installed[str(DEST/name)]!=ready['install_files'][name] for name in NAMES):raise ValueError('Installed field source differs')
 # Historical current/spec/planner output files are read-only; original shared source is the sole replaced historical hash.
 history=json.loads((HERE/'construction.json').read_bytes())['input_sha256']
 history={p:h for p,h in history.items() if Path(p).resolve()!=(DEST/'field_pdn_design.py').resolve()}
 verify(history)
 receipt={'verdict':'INSTALLED_TESTED_FIELD_CURRENT_PATCH','exit_code':0,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'elapsed_seconds':round(time.time()-started,3),'authorization':'Parent explicit after focused review and fresh process/frozen350precheck',
  'ready_sha256':digest(ready_path),'install_script_sha256':digest(__file__),'backup':str(backup),'backup_sha256':digest(backup),
  'destination_before':dest_before,'destination_after':installed,'active_process_precheck':processes,
  'active_combined_and_live_input_count':len(pins),'active_combined_and_live_inputs_before':before,'active_combined_and_live_inputs_after':after,
  'historical_model_and_plans_unchanged':history,'host_tests':21,
  'real_documented_cluster_sums_a':{'FA':5.036,'FAG':5.268,'FB':6.55,'FBG':6.61},
  'real_3_05A_arrays':{'arrays':2,'actual_vias_each':5,'required_vias_each':7,'policy_amps_per_via':.5,'qualified':False},
  'partial_0_096A_scope':'Explicit partial JD01 documented cluster only; full_rail_qualified alwaysfalse',
  'gpu_jobs':0,'native_jobs':0,'heavy_planner_execution':False,'board_modified':False,'ledger_modified':False,
  'capacity_geometry_mask_constants_modified':False,'load_reductions_or_concurrency_added':False,
  'limits':['Model assumptions/current policy only; source-rating/current-sharing/native/thermal/fault/transient/return qualification remains open',
   'No planner restart, candidate application or historical route/current ledger rewrite']}
 (HERE/'installation-receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({k:receipt[k] for k in ('verdict','backup','destination_after','active_combined_and_live_input_count','host_tests')}))
if __name__=='__main__':main()
