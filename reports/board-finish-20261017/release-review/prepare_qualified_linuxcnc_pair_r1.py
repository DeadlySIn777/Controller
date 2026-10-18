"""Freeze a report-only source closure for fresh actual LinuxCNC SIM2 runs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/board-finish-20261017'
OUT=BASE/'release-review/qualified-linuxcnc-pair-r1'
assert not OUT.exists();OUT.mkdir()
STAGE=OUT/'source-root';STAGE.mkdir()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sys.path.insert(0,str(ROOT))
from tools.create_cnc3_qualification_fixture import runtime_sources
inventory=runtime_sources()
original={p:sha(ROOT/p) for p in inventory}
native=json.loads((BASE/'event-producer-fifo-r1/native-full-map/receipt.json').read_text())
native_sources={Path(r['copy']).name:r for r in native['source_inventory']}
for relative in inventory:
 destination=STAGE/relative;destination.parent.mkdir(parents=True,exist_ok=True)
 if relative.startswith('gateware/v3/runtime/') and Path(relative).suffix=='.v':
  row=native_sources[Path(relative).name];assert sha(row['copy'])==row['copy_SHA256']
  shutil.copyfile(row['copy'],destination)
 else:shutil.copyfile(ROOT/relative,destination)

# This is a report-local runner change, not a protocol or test relaxation.
runfile=STAGE/'cnc3_runtime/run.py';s=runfile.read_text()
old='wsl=["wsl","-d","GarciaMechBuilder","-u","root","--"]'
new='wsl=["wsl","-d","GarciaMechBuilder","-u","root","--","taskset","-c","16,17"]'
assert s.count(old)==1;runfile.write_text(s.replace(old,new),encoding='utf-8')
provenance=STAGE/'gateware/v3/runtime/source-provenance.json'
p=json.loads(provenance.read_text());assert p['production_adopted'] is False
p['report_local_qualification_overlay']={
 'scope':'Disconnected source-bound actual LinuxCNC8/12joint qualification; all12fitted; no physical authority',
 'native_map_receipt':str(BASE/'event-producer-fifo-r1/native-full-map/receipt.json'),
 'native_map_receipt_SHA256':sha(BASE/'event-producer-fifo-r1/native-full-map/receipt.json'),
 'selected_RTL':{name:{'source':r['selected_source'],'SHA256':r['copy_SHA256']} for name,r in native_sources.items()},
 'independent_functional_packet_SHA256':sha(BASE/'release-review/producer-fifo-independent-supplement-r1/independent-reviewed-overlay-packet.json'),
 'production_adopted':False,
}
provenance.write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
fixtures={}
for motors in (8,12):
 folder=f'reports/deeper-runtime-20261004/host/fixtures-{motors}'
 fixtures[motors]={}
 for name in ['setup.json','binding.json','encoder-mapping.json','preparation.json']:
  source=ROOT/folder/name;destination=STAGE/folder/name;destination.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(source,destination);fixtures[motors][name]={'original':str(source),'SHA256':sha(source)}

launcher=OUT/'run_qualified_pair.py'
launcher.write_text(r'''"""Run two fresh disconnected LinuxCNC integrations from a frozen report closure."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
STAGE=BASE/'source-root'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--out',required=True,type=Path,help='New exclusive output folder under reports')
 parser.add_argument('--motors',nargs='+',type=int,choices=[8,12],default=[12,8])
 args=parser.parse_args()
 assert len(args.motors)==len(set(args.motors))
 output=args.out.resolve();assert output.is_relative_to(ROOT/'reports') and output!=ROOT/'reports'
 assert not output.exists()
 preparation=json.loads((BASE/'preparation-receipt.json').read_text())
 assert all(sha(STAGE/p)==h for p,h in preparation['staged_runtime_source_SHA256'].items())
 gate=ROOT/'reports/board-finish-20261017/event-producer-fifo-r1/postmap-behavior-r3/receipt.json'
 assert gate.exists(),'Mapped event-engine qualification is pending; do not run or adopt on startup-failed evidence.'
 postmap=json.loads(gate.read_text())
 assert postmap['status']=='MAPPED_FULL_EVENT_ENGINE_VENDOR_PRIMITIVE_FUNCTIONAL_PASS'
 assert '-g2005' in postmap['executions'][0]['argv']
 output.mkdir()
 commands=[];error=None
 try:
  for motors in args.motors:
   run_out=output/f'linuxcnc-{motors}'
   cmd=[sys.executable,str(STAGE/'cnc3_runtime/run.py'),'--motors',str(motors),'--linuxcnc','--out',str(run_out)]
   with (output/f'launcher-{motors}.log').open('wb') as log:
    result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1500)
   commands.append({'motors':motors,'argv':cmd,'exit':result.returncode})
   print(json.dumps(commands[-1]),flush=True)
   assert result.returncode==0
   r=json.loads((run_out/'receipt.json').read_text())
   assert r['status']=='PASS' and r['source_inputs_unchanged'] and r['settings_preserved'] and r['installed_existing_rootfs_modules_preserved']
   assert r['scope']['actual_CNC3_C_driver'] and r['scope']['actual_serial_SPI'] and r['scope']['compiled_RTL'] and r['scope']['actual_LinuxCNC_task_trajectory']
   assert r['scope']['hardware_connections']==0 and r['scope']['physical_qualification'] is False
 except Exception as e:error=repr(e)
 unchanged=all(sha(STAGE/p)==h for p,h in preparation['staged_runtime_source_SHA256'].items())
 fixtures_preserved=all(sha(item['original'])==item['SHA256'] for files in preparation['fixture_inputs'].values() for item in files.values())
 receipt={'status':'PASS' if not error and unchanged and fixtures_preserved else 'FAIL','error':error,
  'preparation_receipt_SHA256':sha(BASE/'preparation-receipt.json'),'mapped_event_qualification_receipt_SHA256':sha(gate),
  'commands':commands,'frozen_source_closure_unchanged':unchanged,'original_fixture_settings_preserved':fixtures_preserved,
  'scope':'Actual LinuxCNC task/FREE joint planners/HAL→C driver→serial SPI→selected compiled RTL→independent virtual STEP/DIR plant;8or12active,all12fitted,disconnectedSIM2. No physical timing/commissioning or Cartesian machining qualification.',
  'production_adopted':False,'physical_authority':False,'hardware_connections':0}
 (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'status':receipt['status'],'error':error}),flush=True)
 return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
''',encoding='utf-8')

staged={r:sha(STAGE/r) for r in inventory}
assert all(sha(ROOT/p)==h for p,h in original.items()),'Concurrent canonical changes during preparation'
receipt={'status':'PREPARED_NOT_EXECUTED_FRESH_LINUXCNC8_12_WITH_EXACT_QUALIFIED_RTL',
 'created_utc':datetime.now(timezone.utc).isoformat(),'source_closure_files':len(inventory),
 'canonical_source_SHA256_at_preparation':original,'staged_runtime_source_SHA256':staged,
 'fixture_inputs':fixtures,'runner_delta':{'before':old,'after':new,'purpose':'Every WSL build/test/LinuxCNC descendant inherits logical CPUs16,17; test/protocol code unchanged.'},
 'staged_provenance_only_modified':True,'canonical_sources_and_existing_settings_modified':False,
 'three_RTL_overlays':{name:native_sources[name]['copy_SHA256'] for name in ['cnc3_event_bank.v','cnc3_runtime_events.v','cnc3_spi_transport_stateful.v']},
 'qualification_gate':'Exact mapped event-engine Verilog2005 PASS required before launch; failedr1/r2 receipts remain retained',
 'launcher_SHA256':sha(launcher),'production_adopted':False,'physical_authority':False,
 'native_mapping_or_postmap_job_duplicated':False,'execution_performed':False,
 'expected_execution':'Run run_qualified_pair.py --out <newreportsfolder>; runs12then8 sequentially using exact copied pre-existing tests/fixtures/module-guard.'}
(OUT/'preparation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':receipt['status'],'source_closure_files':len(inventory),'launcher':str(launcher),'launcher_SHA256':sha(launcher),'preparation_SHA256':sha(OUT/'preparation-receipt.json')}))
