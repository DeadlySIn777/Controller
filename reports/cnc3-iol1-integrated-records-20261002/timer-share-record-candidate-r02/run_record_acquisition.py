from pathlib import Path
import argparse,hashlib,json,subprocess,os,re,importlib.util,shutil
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True)
 names=['cnc_iol1_record_master.v','cnc_iol1_record_acquisition.v','cnc_mbr2_stream_checker.v','tb_record_acquisition.sv','peer.sv','peer_cached_vpi.c','target/iol1.c','target/iol1.h','target/board_record.c','target/board_record.h','originals/vpi_user.h','originals/_pli_types.h.in','record_bundle/record_host.py']
 before={n:sha(H/n) for n in names}
 for n in names:q=out/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/n,q)
 spec=importlib.util.spec_from_file_location('actual_record_host',H/'record_bundle/record_host.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 source=bytes.fromhex('6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8')
 records=[];uids=[];keys={}
 for s in range(4):
  uid=bytes(s*16+k for k in range(12));record,registry=m.fixture_record(s,uid,source_sha=source);records.append(record);uids.append(uid);keys.update(registry)
 observed=m.validate_four_region_set(records,uids,keys,source)
 assert observed['all_signatures_verified'] and not observed['production_trusted'] and not observed['ACTIVE_or_authority']
 (out/'records.bin').write_bytes(b''.join(records));(out/'fixture-provenance.json').write_text(json.dumps(observed,indent=2)+'\n')
 (out/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{unix(out)}'
mkdir vpi-include
cp originals/vpi_user.h vpi-include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' originals/_pli_types.h.in > vpi-include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include peer_cached_vpi.c target/iol1.c target/board_record.c -o peer_cached_vpi.vpi > vpi-build.log 2>&1
iverilog -g2012 -Wall -s tb_record_acquisition -o acquisition.vvp cnc_iol1_record_master.v cnc_iol1_record_acquisition.v cnc_mbr2_stream_checker.v peer.sv tb_record_acquisition.sv > rtl-build.log 2>&1
vvp -M . -m peer_cached_vpi acquisition.vvp > simulation.log 2>&1
''',newline='\n')
 done=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh',unix(out/'run.sh')],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=900)
 (out/'execute.log').write_text(done.stdout+done.stderr,newline='\n')
 log=(out/'simulation.log').read_text() if(out/'simulation.log').exists() else '';match=re.search(r'PASS record acquisition checks=(\d+) actual_bytes=(\d+)',log)
 unchanged=all(sha(H/n)==h for n,h in before.items())
 receipt={'status':'PASS' if done.returncode==0 and match and unchanged else 'FAIL','checks':int(match.group(1)) if match else 0,'actual_received_record_bytes':int(match.group(2)) if match else 0,'input_hashes':before,'inputs_unchanged':unchanged,'scope_flags':{'actual_simulated_four_lane_IDENT_CONFIG_SPI_into_exact_r03_C':bool(match),'record_CRC_structure_and_selected_Source_observed':bool(match),'FPGA_signature_authentication_or_hardware_UID_authentication':False,'production_identity_ACTIVE_ARM_output_authority':False,'actual_MMIO_DMA_ISR_flash_execution':False,'physical_timing_Efinity_fit_or_product_rating':False},'output_hashes':{q.relative_to(out).as_posix():sha(q) for q in out.rglob('*') if q.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'checks':receipt['checks'],'out':str(out)}));return receipt['status']!='PASS'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);raise SystemExit(main(p.parse_args().out.resolve()))
