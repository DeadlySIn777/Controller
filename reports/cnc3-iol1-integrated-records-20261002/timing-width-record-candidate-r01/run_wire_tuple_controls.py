from pathlib import Path
import argparse,hashlib,json,subprocess,os,shutil,sys
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True)
 names=['cnc_iol1_record_master.v','cnc_iol1_record_acquisition.v','cnc_mbr2_stream_checker.v','tb_record_acquisition.sv','peer.sv','peer_cached_vpi.c','target/iol1.c','target/iol1.h','target/board_record.c','target/board_record.h','originals/vpi_user.h','originals/_pli_types.h.in','record_bundle/record_host.py','run_record_acquisition.py']
 before={n:sha(H/n) for n in names};rows=[]
 changes=[('use_current_control_for_previous_reply','accepted_control<=expected_control','accepted_control<=tx_frame[255:248]'),('use_current_chunk_for_previous_reply','accepted_chunk<=expected_chunk','accepted_chunk<=tx_frame[237:232]')]
 for label,a,b in changes:
  stage=out/label/'inputs';stage.mkdir(parents=True)
  for n in names:q=stage/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/n,q)
  master=stage/'cnc_iol1_record_master.v';text=master.read_text();assert text.count(a)==1;master.write_text(text.replace(a,b),newline='\n')
  result=subprocess.run([sys.executable,'-X','utf8',str(stage/'run_record_acquisition.py'),'--out',str(stage.parent/'run')],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=900)
  (stage.parent/'command.log').write_text(result.stdout+result.stderr,newline='\n')
  log=(stage.parent/'run/simulation.log').read_text() if(stage.parent/'run/simulation.log').exists() else ''
  rejected=result.returncode!=0 and ('FAIL wire IDENT chunks arrive in exact order' in log or 'FAIL all eight received bytes equal actual C-selected record' in log)
  rows.append({'name':label,'source_sha256':sha(master),'compiled':(stage.parent/'run/acquisition.vvp').exists(),'runtime_rejected_by_actual_received_wire_tuple':rejected,'exit':result.returncode})
 unchanged=all(sha(H/n)==h for n,h in before.items());passed=all(r['compiled'] and r['runtime_rejected_by_actual_received_wire_tuple'] for r in rows) and unchanged
 receipt={'status':'PASS' if passed else 'FAIL','actual_SPI_C_tuple_mutations':rows,'input_hashes':before,'inputs_unchanged':unchanged,'scope':'actual SPI bit streams into exact C; previous-response metadata binding negative controls; no production trust or authority','output_hashes':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'rows':rows}));return receipt['status']!='PASS'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);raise SystemExit(main(p.parse_args().out.resolve()))
