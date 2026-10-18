from pathlib import Path
import argparse,hashlib,json,subprocess,sys,os,re,importlib.util
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def run(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True)
 sources=[HERE/n for n in ['cnc_iol1_acquisition_master.v','cnc_iol1_diagnostic_acquisition.v','peer_cached_vpi.c','tb_iol1_acquisition.sv','target/iol1.c','target/iol1.h','target/board_record.c','target/board_record.h','originals/tb_iol1_target_c.sv','originals/vpi_user.h','originals/_pli_types.h.in','record_bundle/record_host.py']]
 before={str(q):sha(q) for q in sources}
 for q in sources:
  dest=out/q.relative_to(HERE);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(q.read_bytes())
 spec=importlib.util.spec_from_file_location('fixture_host',HERE/'record_bundle/record_host.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 records=[];uids=[];registry={}
 for s in range(4):
  uid=bytes(s*16+k for k in range(12));record,keys=m.fixture_record(s,uid);records.append(record);uids.append(uid);registry.update(keys)
 trust=m.validate_four_region_set(records,uids,registry)
 assert trust['all_signatures_verified'] and not trust['production_trusted'] and not trust['ACTIVE_or_authority']
 (out/'records.bin').write_bytes(b''.join(records))
 (out/'fixture-provenance.json').write_text(json.dumps(trust,indent=2)+'\n')
 peer=(HERE/'originals/tb_iol1_target_c.sv').read_text().split('module tb_iol1_target_c;')[0]
 (out/'peer.sv').write_text(peer,newline='\n')
 (out/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{unix(out)}'
mkdir vpi-include
cp originals/vpi_user.h vpi-include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' originals/_pli_types.h.in > vpi-include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include peer_cached_vpi.c target/iol1.c target/board_record.c -o peer_cached_vpi.vpi > vpi-build.log 2>&1
iverilog -g2012 -s tb_iol1_acquisition -o acquisition.vvp cnc_iol1_acquisition_master.v cnc_iol1_diagnostic_acquisition.v peer.sv tb_iol1_acquisition.sv > rtl-build.log 2>&1
vvp -M . -m peer_cached_vpi acquisition.vvp > simulation.log 2>&1
''',newline='\n')
 env=os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder')
 cmd=['wsl','-d',env,'--','sh',unix(out/'run.sh')]
 done=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=600)
 (out/'command.log').write_text(done.stdout+done.stderr,newline='\n')
 log=(out/'simulation.log').read_text() if(out/'simulation.log').is_file() else ''
 count=re.search(r'PASS acquisition checks=(\d+)',log)
 healthy=done.returncode==0 and bool(count)
 # A genuine record-major suppression mutant must lose the actual-major check.
 mutation=out/'mutation';mutation.mkdir()
 for q in out.iterdir():
  if q.is_file() and q.name.endswith(('.v','.sv','.bin')):(mutation/q.name).write_bytes(q.read_bytes())
 # Mutate only the real fixture's final header assignment, leaving earlier
 # legacy injected-major tests unchanged so this control reaches the new case.
 import shutil
 shutil.copytree(out/'target',mutation/'target')
 shutil.copytree(out/'vpi-include',mutation/'vpi-include')
 mutant=(out/'peer_cached_vpi.c').read_text().replace('node[s].hw_major=records[s][7]','node[s].hw_major=0')
 assert mutant!=(out/'peer_cached_vpi.c').read_text()
 (mutation/'peer_cached_vpi.c').write_text(mutant,newline='\n')
 shell=f"cd '{unix(mutation)}' && gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include peer_cached_vpi.c target/iol1.c target/board_record.c -o peer_cached_vpi.vpi && iverilog -g2012 -s tb_iol1_acquisition -o mutant.vvp *.v *.sv && vvp -M . -m peer_cached_vpi mutant.vvp"
 attacked=subprocess.run(['wsl','-d',env,'--','sh','-c',shell],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=600)
 (mutation/'execution.log').write_text(attacked.stdout+attacked.stderr,newline='\n')
 rejected=attacked.returncode!=0 and 'real major1 record response rejected' in attacked.stdout
 unchanged=all(sha(Path(q))==h for q,h in before.items())
 receipt={'status':'PASS' if healthy and rejected and unchanged else 'FAIL','checks':int(count.group(1)) if count else 0,'actual_supported_blank_record_diagnostic_wire_compatibility':healthy,'actual_valid_record_major_rejection':healthy,'compiled_major_suppression_mutation_rejected':rejected,'input_hashes':before,'inputs_unchanged':unchanged,'scope_flags':{'actual_simulated_four_lane_SPI_into_r03_C':healthy,'real_signed_developer_fixture_integrity_and_UID_selection':healthy,'real_production_signature_trust':False,'frozen_FPGA_sends_CONFIG_IDENT':False,'commercial_ACTIVE':False,'real_ARM_DMA_IRQ_GPIO_or_flash_execution':False},'output_hashes':{q.relative_to(out).as_posix():sha(q) for q in out.rglob('*') if q.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'checks':receipt['checks'],'out':str(out)}));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);raise SystemExit(run(p.parse_args().out.resolve()))
