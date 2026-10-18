from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,os,sys
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True)
 import record_host
 (out/'fixtures.bin').write_bytes(b''.join(record_host.fixture_record(s,bytes(s*16+i+1 for i in range(12)),generation=g)[0] for g in [1,2] for s in range(4)))
 mutations=[
 ('sample_age_wraps_young','iol1.c','return !valid||elapsed>=65535u?0xffffu:(uint16_t)elapsed;','return !valid?0xffffu:(uint16_t)elapsed;','DIC age65536 must not wrap young'),
 ('CRC_skipped','iol1.c','if(iol1_crc32c(f,36)!=crc)','if(0 && iol1_crc32c(f,36)!=crc)','every physicalframe bitflip CRC rejected'),
 ('config_reserved_tail_skipped','iol1.c','for(unsigned i=15;i<35;i++)','for(unsigned i=35;i<35;i++)','sealed policy/header/config corruption rejected'),
 ('rejected_frame_feeds_timer','iol1.c','if(iol1_crc32c(f,36)!=crc){n->crc_errors++;return 0;}','if(iol1_crc32c(f,36)!=crc){n->accepted_us=now;n->crc_errors++;return 0;}','rejected frame no accepted progress'),
 ('factory_UID_not_bound','board_record.c','||!equal(p+32,uid,12)','||(0 && !equal(p+32,uid,12))','foreignMCU UID rejected'),
 ('commit_not_checked','board_record.c','!equal(p+508,commit,4)||','(0 && !equal(p+508,commit,4))||','every record bitflip rejected'),
 ('debounce_microseconds_as_iterations','dic_filter.c','(uint32_t)groups[i/8]*100u','(uint32_t)groups[i/8]','100us minus1'),
 ('CONFIG_grants_ACTIVE','iol1.c','n->dic_config_generation++;n->dic_config_valid=1;','n->dic_config_generation++;n->dic_config_valid=1;n->state=2;','CONFIG noACTIVE/permit/output authority')]
 rows=[]
 for name,file,old,new,label in mutations:
  d=out/name;d.mkdir();names=['iol1.c','iol1.h','dic_filter.c','dic_filter.h','board_record.c','board_record.h','test_record_config.c']
  for n in names:shutil.copyfile(H/n,d/n)
  p=d/file;s=p.read_text();assert s.count(old)==1,(name,s.count(old));p.write_text(s.replace(old,new),newline='\n')
  (d/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{unix(d)}'
gcc -O2 -std=c11 -Wall -Wextra -Werror -I. iol1.c dic_filter.c board_record.c test_record_config.c -o mutated > build.log 2>&1
set +e
./mutated '{unix(out/'fixtures.bin')}' > execute.log 2>&1
r=$?
printf '%s\\n' "$r" > exit.txt
exit 0
''',newline='\n')
  p=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh',unix(d/'run.sh')],capture_output=True,text=True,timeout=60)
  log=(d/'execute.log').read_text() if (d/'execute.log').exists() else '';code=int((d/'exit.txt').read_text()) if (d/'exit.txt').exists() else None
  rows.append({'name':name,'compiled':p.returncode==0,'runtime_exit':code,'expected_failure':label,'status':'PASS' if p.returncode==0 and code==1 and label in log else 'FAIL','input_mutation_hash':sha(d/file)})
 # Actual Python cryptographic provenance negative, separate from compiled C.
 d=out/'renamed_fixture_key_production';d.mkdir();p=d/'record_host.py';s=(H/'record_host.py').read_text();old="result['production_trusted']=False\n";assert s.count(old)==1;p.write_text(s.replace(old,"result['production_trusted']=key.get('environment')=='production'\n"),newline='\n')
 code="import record_host as r; p,k=r.fixture_record(0,bytes(range(1,13))); k={a:dict(b,environment='production') for a,b in k.items()}; assert not r.validate_record(p,0,bytes(range(1,13)),k)['production_trusted'], 'fixture key metadata cannot create manufacturer trust'"
 p=subprocess.run([sys.executable,'-X','utf8','-c',code],cwd=d,capture_output=True,text=True);(d/'execute.log').write_text(p.stdout+p.stderr)
 rows.append({'name':'renamed_fixture_key_production','evidence_type':'executed Python crypto validator mutation','status':'PASS' if p.returncode and 'fixture key metadata cannot create manufacturer trust' in p.stderr else 'FAIL'})
 r={'status':'PASS' if all(x['status']=='PASS' for x in rows) else 'FAIL','controls':rows,'actual_compiled_C_mutants':8,'executed_crypto_provenance_mutants':1,'authority_or_physical_qualification':False}
 (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return r['status']!='PASS'
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);raise SystemExit(main(ap.parse_args().out.resolve()))
