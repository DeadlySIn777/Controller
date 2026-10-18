from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,sys,re
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
 if out.exists():raise RuntimeError('fresh controls directory required')
 out.mkdir(parents=True)
 base={str(p):sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 rows=[]
 mutations=[
 ('CRC', 'cnc_iol1_acquisition_master.v',"rx_shift[31:0] == (rx_crc ^ 32'hffffffff)","1'b1",'up to two rejected replies'),
 ('slot_upper_bits','cnc_iol1_acquisition_master.v',"rx_shift[295:288] == {4'b0,SLOT_ID}","rx_shift[291:288] == SLOT_ID",'upper reserved slot'),
 ('transmitted_sequence','cnc_iol1_acquisition_master.v','if(synced)begin expected_sequence<=tx_sequence;tx_sequence<=next_sequence(tx_sequence);end','', 'deadline'),
 ('prepared_reply_residency','cnc_iol1_diagnostic_acquisition.v',"{1'b0,reported_age[a]}+{1'b0,reply_elapsed_us[a]}","{1'b0,reported_age[a]}",'DI age includes'),
 ('third_failure','cnc_iol1_acquisition_master.v','if(failures == 2)','if(failures == 3)','third failed poll'),
 ('invented_factory','cnc_iol1_diagnostic_acquisition.v','assign factory_identity_verified=0;','assign factory_identity_verified=15;','SYNCED/transport'),
 ('invented_ADC','cnc_iol1_diagnostic_acquisition.v','assign analog_valid=0;','assign analog_valid=15;','SYNCED/transport')]
 for name,file,old,new,expected in mutations:
  candidate=out/name/'inputs';shutil.copytree(HERE,candidate,ignore=shutil.ignore_patterns('__pycache__'))
  p=candidate/file;s=p.read_text()
  if s.count(old)!=1:raise RuntimeError('not exact single mutant '+name)
  p.write_text(s.replace(old,new),encoding='utf8',newline='\n')
  q=out/name/'actual-proof'
  r=subprocess.run([sys.executable,'-X','utf8',str(candidate/'run_acquisition_proof.py'),'--out',str(q)],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
  (out/name/'command.log').write_text(r.stdout+r.stderr,encoding='utf8',newline='\n')
  compilelog=(q/'rtl-build.log').read_text() if(q/'rtl-build.log').is_file() else 'MISSING'
  log=(q/'simulation.log').read_text() if(q/'simulation.log').is_file() else ''
  correct=r.returncode!=0 and 'FATAL:' in log and expected in log and 'syntax error' not in compilelog and 'MISSING' not in compilelog
  rows.append({'name':name,'status':'PASS' if correct else 'FAIL','compiled_actual_RTL':not ('syntax error' in compilelog or compilelog=='MISSING'),'expected_failed_assertion':expected,'actual_tail':log[-1200:],'mutated_file_sha256':sha(p),'proof_receipt_sha256':sha(q/'receipt.json') if(q/'receipt.json').is_file() else None})
  print(name,rows[-1]['status'],flush=True)
 receipt={'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL','actual_compiled_rejected_mutations':rows,'baseline_hashes':base,'baseline_unchanged':all(sha(Path(p))==h for p,h in base.items()),'physical_execution':False}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);raise SystemExit(main(p.parse_args().out.resolve()))
