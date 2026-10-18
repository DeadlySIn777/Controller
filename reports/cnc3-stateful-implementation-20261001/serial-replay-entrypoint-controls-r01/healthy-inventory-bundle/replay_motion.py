"""Fresh disconnected replay of this exact bounded CNC3 motion RTL bundle."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 return {p.relative_to(HERE).as_posix():sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('bundle-manifest.json','freeze-receipt.json')}
def main(out,distro,inventory):
 if out.exists():raise RuntimeError('Output must be a fresh nonexistent directory')
 out.mkdir(parents=True)
 rows=[];tools=[];begin=time.time();before=snapshot();manifest=json.loads((HERE/'bundle-manifest.json').read_text())
 declared=manifest['files'];integrity=before==declared
 environment=os.environ.copy();environment['CNC3_WSL_DISTRO']=distro
 for name,cmd in [('Icarus',['iverilog','-V']),('Verilator',['verilator','--version']),('mapped_Yosys_rootfs',['test','-x','/root/.cache/controller-lab-linuxcnc/rootfs/usr/bin/yosys'])]:
  try:
   r=subprocess.run(['wsl','-d',distro,'--',*cmd],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=45)
   log=r.stdout+r.stderr;(out/(name+'-availability.log')).write_text(log,encoding='utf8',newline='\n')
   tools.append({'name':name,'available':r.returncode==0,'exit_code':r.returncode,'log_sha256':sha(out/(name+'-availability.log')),'detail':log[-900:]})
  except Exception as e:tools.append({'name':name,'available':False,'detail':str(e)})
 tool_ready=all(r['available'] for r in tools)
 stages=[
 ('generator_equivalence','run_component_proof.py',[],None),
 ('encoder_alarm_filters','run_filter_proof.py',[],None),
 ('stateful_motion','run_state_proof.py',[],None),
 ('rate_boundaries_mutations','run_rate_admission_proof.py',['--baseline',str(out/'stateful_motion')],'stateful_motion'),
 ('shared_admission_equivalence','run_serial_admission_equivalence.py',[],None),
 ('fault_priority','run_fault_priority_proof.py',['--baseline',str(out/'stateful_motion')],'stateful_motion'),
 ('state_safety_mutations','run_state_mutation_proof.py',['--baseline',str(out/'stateful_motion')],'stateful_motion'),
 ('actual_SPI_motion','run_spi_motion_proof.py',[],None),
 ('actual_SPI_rejection_sideband','run_rejection_header_proof.py',[],None),
 ('actual_SPI_rate_frame_binding','run_spi_admission_binding.py',['--baseline',str(out/'actual_SPI_motion')],'actual_SPI_motion'),
 ('family_synthesis_lint','run_family_proof.py',[],None)]
 for name,runner,extra,dependency in stages:
  record={'name':name,'runner':runner,'status':'NOT_RUN','evidence_type':'actual compiled RTL simulation or family synthesis, disconnected ideal-provider fixture'}
  previous=next((x['status'] for x in rows if x['name']==dependency),None)
  if not integrity:record.update(status='FAIL',reason='Exact bundle file/hash integrity failed')
  elif inventory:record['reason']='Inventory only; no validations executed'
  elif not tool_ready:record.update(status='BLOCKED',reason='Required installed simulator/family mapper unavailable in requested distro')
  elif dependency and previous!='PASS':record.update(status='BLOCKED',reason='Actual required fresh baseline failed or was unavailable: '+dependency)
  else:
   command=[sys.executable,'-X','utf8',str(HERE/runner),'--out',str(out/name),*extra]
   print('RUN '+name,flush=True);started=time.time()
   try:
    r=subprocess.run(command,capture_output=True,text=True,encoding='utf8',errors='replace',env=environment,timeout=2400)
    log=r.stdout+r.stderr;(out/(name+'-command.log')).write_text(log,encoding='utf8',newline='\n')
    receipt=out/name/'receipt.json';data=json.loads(receipt.read_text()) if receipt.is_file() else {}
    record.update(status='PASS' if r.returncode==0 and data.get('status')=='PASS' else 'FAIL',exit_code=r.returncode,receipt=str(receipt),receipt_sha256=sha(receipt) if receipt.is_file() else None,command_log_sha256=sha(out/(name+'-command.log')),duration_seconds=round(time.time()-started,3),command=command)
   except Exception as e:record.update(status='FAIL',reason=repr(e),duration_seconds=round(time.time()-started,3))
   print(record['status']+' '+name,flush=True)
  rows.append(record)
  (out/'checkpoint.json').write_text(json.dumps({'stages':rows,'input_integrity':integrity},indent=2)+'\n',encoding='utf8',newline='\n')
 after=snapshot();unchanged=before==after
 counts={k:sum(x['status']==k for x in rows) for k in ('PASS','FAIL','BLOCKED','NOT_RUN')}
 status='FAIL' if not integrity or not unchanged or counts['FAIL'] else 'BLOCKED' if counts['BLOCKED'] else 'NOT_RUN' if inventory else 'PASS'
 report={'status':status,'scope':'bounded actual frozen96/176-byte CNC3 transport +motion/session/config/watchdog/authority +twelve runtime DDS +four filtered ABZ; all other providers remain absent','evidence_type':'fresh actual Icarus/Verilator/family-Yosys execution, not a receipt aggregation','counts':counts,'stages':rows,'tool_inventory':tools,'wsl_distro':distro,'exact_inputs':before,'bundle_manifest_sha256':sha(HERE/'bundle-manifest.json'),'input_integrity':integrity,'inputs_unchanged':unchanged,'duration_seconds':round(time.time()-begin,3),'scope_flags':{'actual_physical_SPI_wire':False,'actual_simulated_SPI_edges_and_CRC':all(any(row['name']==name and row['status']=='PASS' for row in rows) for name in ('actual_SPI_motion','actual_SPI_rejection_sideband','actual_SPI_rate_frame_binding')),'real_LinuxCNC_HAL':False,'full_CNC3_CAP3_pages_IOL1_events_output_chain':False,'complete_machine_or_vendor_T20_fit_timing':False,'physical_safety_or_new_ratings':False,'standalone_experimental_2MHz_authorized_runtime':False,'request_backpressure_queue_in_motion_scope':False,'ideal_provider_inputs':True},'protocol_rate_max':16777216,'protocol_max_steps_per_second_at_assumed_50MHz':195312.5}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print(json.dumps({'status':status,'counts':counts,'inputs_unchanged':unchanged,'report':str(out/'report.json')}),flush=True)
 return 0 if status in ('PASS','NOT_RUN') else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--wsl-distro',default='GarciaMechBuilder');p.add_argument('--inventory',action='store_true');a=p.parse_args();raise SystemExit(main(a.out.resolve(),a.wsl_distro,a.inventory))
