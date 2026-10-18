from pathlib import Path
import hashlib,json,shutil,py_compile
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=HERE/'serial-replay-candidate-r01';out=HERE/'serial-replay-candidate-r02'
 if out.exists():raise RuntimeError('Fresh candidate required')
 shutil.copytree(old,out,ignore=shutil.ignore_patterns('__pycache__','bundle-manifest.json','prepare-receipt.json'))
 src=HERE/'stage-r02/run_spi_admission_binding.py';q=out/src.name
 text='import os\n'+src.read_text();anchor="'wsl','-d','GarciaMechBuilder'"
 assert text.count(anchor)==1;text=text.replace(anchor,"'wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder')")
 q.write_text(text,encoding='utf8',newline='\n')
 replay=out/'replay_motion.py';s=replay.read_text()
 oldflag="'actual_simulated_SPI_edges_and_CRC':not inventory and counts['PASS']>0"
 newflag="'actual_simulated_SPI_edges_and_CRC':all(any(row['name']==name and row['status']=='PASS' for row in rows) for name in ('actual_SPI_motion','actual_SPI_rejection_sideband','actual_SPI_rate_frame_binding'))"
 assert s.count(oldflag)==1;s=s.replace(oldflag,newflag,1);replay.write_text(s,encoding='utf8',newline='\n')
 for p in out.glob('*.py'):py_compile.compile(str(p),doraise=True)
 receipt={'status':'PREPARED_NOT_EXECUTED','parent_bundle_manifest_sha256':sha(old/'bundle-manifest.json'),'exact_RTL_unchanged':all(sha(p)==sha(old/p.name) for p in out.glob('cnc3_*.v')),'bounded_changes':[{'path':src.name,'before_sha256':sha(old/src.name),'after_sha256':sha(q),'change':'Inherited progress-width assertion remains50ticks when rst_n is high; asynchronous reset is separately required to force immediate inactive progress/state/masks.'},{'path':replay.name,'before_sha256':sha(old/replay.name),'after_sha256':sha(replay),'change':'SimulatedSPI evidence flag requires all three actualSPI fresh stage statuses PASS, never unrelated component PASS.'}],'shared_source_mutated':False}
 (out/'prepare-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
 files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('bundle-manifest.json','freeze-receipt.json')}
 (out/'bundle-manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n',encoding='utf8',newline='\n')
 print(json.dumps(receipt))
if __name__=='__main__':main()
