from pathlib import Path
import argparse,hashlib,json,subprocess,sys,os,time
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():return {str(p.relative_to(HERE).as_posix()):sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('bundle-manifest.json','freeze-receipt.json')}
def main(out,distro,inventory):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True);before=snapshot();declared=json.loads((HERE/'bundle-manifest.json').read_text())['files'];integrity=before==declared;rows=[];start=time.time()
 env=os.environ.copy();env['CNC3_WSL_DISTRO']=distro
 stages=[('actual_cached_target_SPI','run_acquisition_proof.py'),('compiled_safety_mutations','run_acquisition_controls.py'),('cycle_exact_optimization','run_acquisition_equivalence.py'),('composed_Efinix_family_mapping','run_acquisition_family.py')]
 for name,script in stages:
  row={'name':name,'runner':script,'status':'NOT_RUN','evidence_type':'actual compiled target protocol C / simulated SPI / compiled RTL / family mapping, no MMIO hardware'}
  if not integrity:row.update(status='FAIL',reason='exact bundle hash mismatch')
  elif inventory:row['reason']='inventory only'
  else:
   cmd=[sys.executable,'-X','utf8',str(HERE/script),'--out',str(out/name)]
   print('RUN '+name,flush=True)
   try:
    r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace',env=env,timeout=1800)
    (out/(name+'-command.log')).write_text(r.stdout+r.stderr,encoding='utf8',newline='\n');receipt=out/name/'receipt.json';data=json.loads(receipt.read_text()) if receipt.is_file() else {}
    row.update(status='PASS' if r.returncode==0 and data.get('status')=='PASS' else 'FAIL',exit_code=r.returncode,receipt=str(receipt),receipt_sha256=sha(receipt) if receipt.is_file() else None)
   except Exception as e:row.update(status='FAIL',reason=repr(e))
   print(row['status']+' '+name,flush=True)
  rows.append(row);(out/'checkpoint.json').write_text(json.dumps({'stages':rows,'bundle_integrity':integrity},indent=2)+'\n')
 after=snapshot();unchanged=before==after;counts={k:sum(r['status']==k for r in rows) for k in ('PASS','FAIL','BLOCKED','NOT_RUN')}
 passed=integrity and unchanged and counts['PASS']==4
 report={'status':'PASS' if passed else 'NOT_RUN' if inventory and integrity and unchanged else 'FAIL','counts':counts,'stages':rows,'exact_inputs':before,'bundle_integrity':integrity,'inputs_unchanged':unchanged,'bundle_manifest_sha256':sha(HERE/'bundle-manifest.json'),'duration_seconds':round(time.time()-start,3),'scope_flags':{'actual_simulated_four_lane_SPI_and_same_C_protocol':any(x['name']=='actual_cached_target_SPI' and x['status']=='PASS' for x in rows),'actual_ARM_DMA_IRQ_or_ADC':False,'commercial_ACTIVE_or_factory_identity':False,'outputs_ARM_CAP3_HAL':False,'full_machine_or_vendor_T20_fit_timing':False,'physical_qualification_or_new_ratings':False},'open_dependencies':['actual provisioned motherboard/region factory record and host trust','IDENT_READ/config/ACTIVE target implementation and real I/O qualification','actual ADC/DAC acquisition under independent safe electrical conditions','loaded SPI roundtrip/timing and vendor fit/clock closure']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'counts':counts,'report':str(out/'report.json')}),flush=True);return 0 if report['status'] in ('PASS','NOT_RUN') else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--wsl-distro',default='GarciaMechBuilder');p.add_argument('--inventory',action='store_true');a=p.parse_args();raise SystemExit(main(a.out.resolve(),a.wsl_distro,a.inventory))
