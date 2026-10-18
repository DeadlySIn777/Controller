from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out,bundle):
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);manifest=json.loads((bundle/'bundle-manifest.json').read_text());before={k:sha(bundle/k) for k in manifest['files']}
 rows=[]
 for label,tamper in [('healthy-inventory',False),('changed-actual-RTL',True)]:
  copied=out/(label+'-bundle');shutil.copytree(bundle,copied,ignore=shutil.ignore_patterns('__pycache__'))
  if tamper:
   p=copied/'cnc3_rate_admission_serial.v';p.write_text(p.read_text()+'\n// intentional input-integrity negative\n',encoding='utf8',newline='\n')
  target=out/label;command=[sys.executable,'-X','utf8',str(copied/'replay_motion.py'),'--out',str(target),'--inventory']
  r=subprocess.run(command,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
  log=r.stdout+r.stderr;(out/(label+'.log')).write_text(log,encoding='utf8',newline='\n')
  report=json.loads((target/'report.json').read_text())
  if tamper:ok=r.returncode==1 and report['status']=='FAIL' and not report['input_integrity'] and report['counts']=={'PASS':0,'FAIL':11,'BLOCKED':0,'NOT_RUN':0}
  else:ok=r.returncode==0 and report['status']=='NOT_RUN' and report['input_integrity'] and report['counts']=={'PASS':0,'FAIL':0,'BLOCKED':0,'NOT_RUN':11}
  ok=ok and not report['scope_flags']['actual_simulated_SPI_edges_and_CRC'] and not any((target/name).exists() for name in ('actual_SPI_motion','actual_SPI_rate_frame_binding','stateful_motion'))
  rows.append({'name':label,'passed':ok,'actual_exit_code':r.returncode,'report_sha256':sha(target/'report.json'),'log_sha256':sha(out/(label+'.log')),'no_RTL_simulation_PASS_fabricated':True})
 unchanged=all(sha(bundle/k)==h for k,h in before.items())
 receipt={'status':'PASS' if unchanged and all(x['passed'] for x in rows) else 'FAIL','bundle_manifest_sha256':sha(bundle/'bundle-manifest.json'),'bundle_unchanged':unchanged,'controls':rows,'evidence_type':'actual CLI inventory and tampered actual RTL input rejection; no simulated functionality claim'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);a=p.parse_args();raise SystemExit(main(a.out.resolve(),a.bundle.resolve()))
