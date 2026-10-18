from pathlib import Path
import argparse,hashlib,json,subprocess,os,re,importlib.util,shutil
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True)
 names=['cnc_mbr2_stream_checker.v','tb_stream_checker.sv','record_bundle/record_host.py']
 before={n:sha(H/n) for n in names}
 for n in names:q=out/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/n,q)
 spec=importlib.util.spec_from_file_location('host',H/'record_bundle/record_host.py');host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
 records=[host.fixture_record(s,bytes(s*16+k for k in range(12)),source_sha=bytes.fromhex('6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'))[0] for s in range(4)]
 alterations={1:(504,1),2:(0,1),3:(4,1),4:(6,1),5:(7,3),6:(9,1),7:(10,1),8:(15,1),9:(16,0),10:(45,2),11:(46,4),12:(49,2),13:(53,4),14:(56,1),15:(66,1),16:(68,1),17:(212,1),18:(508,1),19:(440,1)}
 vectors=[]
 for scenario in range(20):
  bank=list(records)
  if scenario:
   b=bytearray(bank[0]);offset,mask=alterations[scenario];b[offset]=0 if scenario in (8,10) else mask if scenario==9 else b[offset]^mask
   if scenario!=1:b[504:508]=host.crc32c(b[:504]).to_bytes(4,'big')
   bank[0]=bytes(b)
  vectors.extend(record[c:c+8].hex() for record in bank for c in range(0,512,8))
 (out/'vectors.hex').write_text('\n'.join(vectors)+'\n')
 distro=os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder')
 def run(directory,tag):
  command=f"cd '{unix(directory)}' && iverilog -g2012 -s tb_stream_checker -o checker.vvp cnc_mbr2_stream_checker.v tb_stream_checker.sv && vvp checker.vvp"
  p=subprocess.run(['wsl','-d',distro,'--','sh','-c',command],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=300)
  (directory/(tag+'.log')).write_text(p.stdout+p.stderr,newline='\n');return p
 baseline=run(out,'baseline');match=re.search(r'PASS stream checker checks=(\d+)',baseline.stdout)
 mutations=[('bypass_record_crc',"queued_data[selection][63:32]==(crc[selection]^32'hffffffff)","1'b1"),('bypass_source',"d[31:0]==SOURCE_SHA[255:224]","1'b1"),('bypass_chunk_order',"{1'b0,queued_index[selection]}!=next_chunk[selection]","1'b0"),('trust_from_crc','assign signature_authenticated=0','assign signature_authenticated=|record_integrity_observed'),('ignore_busy_fault','if(enable&&!lane_fault[owner]&&!record_failed[owner]&&!current_queue_fault[owner])','if(enable)'),('skip_commit',"queued_data[selection][31:0]==32'h434d5432","1'b1"),('remove_current_collision_priority','||current_queue_fault[i]','')]
 rows=[]
 source=(H/'cnc_mbr2_stream_checker.v').read_text()
 for name,a,b in mutations:
  directory=out/name;directory.mkdir();assert a in source
  (directory/'cnc_mbr2_stream_checker.v').write_text(source.replace(a,b),newline='\n');shutil.copyfile(out/'tb_stream_checker.sv',directory/'tb_stream_checker.sv');shutil.copyfile(out/'vectors.hex',directory/'vectors.hex')
  if name=='ignore_busy_fault':(directory/'cnc_mbr2_stream_checker.v').write_text(source.replace('lane_fault[i]',"1'b0").replace('lane_fault[owner]',"1'b0").replace('lane_fault[selection]',"1'b0"),newline='\n')
  if name=='remove_current_collision_priority':(directory/'cnc_mbr2_stream_checker.v').write_text(source.replace('&&!current_queue_fault[owner]','').replace('||current_queue_fault[selection]','').replace('||current_queue_fault[i]',''),newline='\n')
  result=run(directory,'mutant');rejected=result.returncode!=0 and 'FATAL' in result.stdout
  rows.append({'name':name,'compiled':(directory/'checker.vvp').is_file(),'runtime_rejected':rejected,'exit':result.returncode})
 unchanged=all(sha(H/n)==h for n,h in before.items());passed=baseline.returncode==0 and match and all(x['compiled'] and x['runtime_rejected'] for x in rows) and unchanged
 receipt={'status':'PASS' if passed else 'FAIL','baseline_checks':int(match.group(1)) if match else 0,'independent_record_cases':20,'compiled_mutations':rows,'input_hashes':before,'inputs_unchanged':unchanged,'scope':'actual compiled shared record CRC/structure/queue reset/fault logic; independent Python vectors; not SPI/target/MMIO/identity authentication','output_hashes':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'checks':receipt['baseline_checks'],'mutations':rows}));return receipt['status']!='PASS'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);raise SystemExit(main(p.parse_args().out.resolve()))
