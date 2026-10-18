from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,os,re,sys
HERE=Path(__file__).resolve().parent
from record_host import fixture_record,validate_record,validate_four_region_set,crc32c
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def host_checks(out):
 checks=0
 def ck(x,label):
  nonlocal checks;checks+=1
  if not x:raise AssertionError(label)
 def reject(fn,label):
  try:fn()
  except ValueError:ck(True,label);return
  ck(False,label)
 records=[];registry={};uids=[]
 for s in range(4):
  uid=bytes(s*16+i+1 for i in range(12));p,r=fixture_record(s,uid);records.append(p);registry.update(r);uids.append(uid)
  absent=validate_record(p,s,uid);ck(absent['integrity_valid'] and not absent['signature_verified'] and not absent['production_trusted'],'empty trust does not authenticate')
  v=validate_record(p,s,uid,r);ck(v['signature_verified'] and not v['production_trusted'] and not v['ACTIVE_or_authority'],'actual developer signature notproduction/authority')
  renamed={key:dict(value,environment='production') for key,value in r.items()}
  ck(not validate_record(p,s,uid,renamed)['production_trusted'],'renaming fixture environment cannot create manufacturer provenance')
  reject(lambda:validate_record(p,s,uid,r,firmware_version=2),'firmware version incompatibility')
  reject(lambda:validate_record(p,s,uid,r,gateware_version=4),'gateware version incompatibility')
  for b in range(4096):
   q=bytearray(p);q[b//8]^=1<<(b%8)
   reject(lambda q=q:validate_record(q,s,uid,r),'record bitflip')
  for off in range(0,440,8):
   q=bytearray(p);q[off]^=1;q[504:508]=crc32c(q[:504]).to_bytes(4,'big')
   try:forged=validate_record(q,s,uid,r)
   except ValueError:ck(True,'CRC repair cannot forge signature')
   else:ck(not forged['signature_verified'] and not forged['production_trusted'] and not forged['ACTIVE_or_authority'],'CRC repair with unknown key remains unauthenticated')
  reject(lambda:validate_record(p,s,bytes(12),r),'foreign UID')
 ck(validate_four_region_set(records,uids,registry)['all_signatures_verified'],'same actual motherboard four uniqueMCUs')
 bad=list(records);bad[2],r=fixture_record(2,uids[2],serial=b'FOREIGN-BOARD')
 reject(lambda:validate_four_region_set(bad,uids,registry),'mixedboardlineage')
 reject(lambda:validate_four_region_set(records,[uids[0]]*4,registry),'duplicateMCU UID')
 # Disconnected one-way64-bit programming fault model; not hardware atomicity.
 for s,p in enumerate(records):
  for cut in range(64):
   q=p[:cut*8]+b'\xff'*(512-cut*8)
   reject(lambda q=q,s=s:validate_record(q,s,uids[s],registry),'every torn doublewordprefix rejected')
  for cut in range(8):
   q=p[:504]+p[504:504+cut]+b'\xff'*(8-cut)
   reject(lambda q=q,s=s:validate_record(q,s,uids[s],registry),'every torn final8B commit rejected')
 (out/'fixtures.bin').write_bytes(b''.join(records));(out/'developer-trust-fixture.json').write_text(json.dumps(registry,indent=2)+'\n')
 return checks
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True);paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts];before={str(p.relative_to(HERE)):sha(p) for p in paths}
 for p in paths:
  q=out/'inputs'/p.relative_to(HERE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 pychecks=host_checks(out);src='inputs'
 script=f'''#!/bin/sh
set -eu
cd '{unix(out)}'
gcc --version > gcc-version.txt
clang --version > clang-version.txt
ld.lld --version > linker-version.txt
flags='-O2 -std=c11 -Wall -Wextra -Werror'
gcc $flags -Iinputs inputs/iol1.c inputs/dic_filter.c inputs/board_record.c inputs/test_record_config.c -o host-record-config
./host-record-config fixtures.bin > host-checks.log
gcc -O1 -g -std=c11 -Wall -Wextra -Werror -fsanitize=undefined,address -fno-omit-frame-pointer -Iinputs inputs/iol1.c inputs/dic_filter.c inputs/board_record.c inputs/test_record_config.c -o sanitized-record-config
./sanitized-record-config fixtures.bin > sanitizer-checks.log
aflags='--target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -O2 -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections'
for source in iol1 dic_filter board_record
do clang $aflags -Iinputs -c inputs/$source.c -o $source.o;done
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -c inputs/startup.S -o startup.o
for slot in 0 1 2 3
do
 clang $aflags -Iinputs -Iinputs/vendor/ST -Iinputs/vendor/ARM -DNODE_SLOT=$slot -c inputs/target.c -o target$slot.o
 ld.lld -T inputs/stm32g031.ld --gc-sections -Map=node$slot.map startup.o iol1.o dic_filter.o board_record.o target$slot.o -o node$slot.elf
 readelf -h -l -S -s node$slot.elf > node$slot-elf-review.txt
 size node$slot.elf >> sizes.txt
 objcopy -I elf32-little -O binary node$slot.elf node$slot.bin
done
'''
 (out/'run.sh').write_text(script,newline='\n');p=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh',unix(out/'run.sh')],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=600)
 (out/'execute.log').write_text(p.stdout+p.stderr,newline='\n')
 text=(out/'host-checks.log').read_text() if (out/'host-checks.log').exists() else '';m=re.search(r'PASS record/config checks=(\d+)',text)
 status='PASS' if p.returncode==0 and m else 'FAIL'
 receipt={'status':status,'host_Python_signature_record_checks':pychecks,'actual_C_record_config_filter_checks':int(m.group(1)) if m else 0,'sanitizers':p.returncode==0,'four_actual_ARM_ELF_bin_compilation':p.returncode==0,'target_sizes':(out/'sizes.txt').read_text() if (out/'sizes.txt').exists() else None,'inputs':before,'inputs_unchanged':all(sha(HERE/n)==h for n,h in before.items()),'scope':{'proposed_IS2_record_and_IDENT_supplement':True,'actual_developer_signature_verification':True,'real_manufacturer_trust_key':False,'production_or_ACTIVE':False,'actual_flash_program_or_MMIO_execution':False,'outputs_ARM_HAL':False},'exit_code':p.returncode}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='inputs'}));return status!='PASS'
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();raise SystemExit(main(a.out.resolve()))
