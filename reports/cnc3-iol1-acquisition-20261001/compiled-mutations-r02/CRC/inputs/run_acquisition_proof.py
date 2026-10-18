from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,re,os
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True)
 sources=[HERE/'cnc_iol1_acquisition_master.v',HERE/'cnc_iol1_diagnostic_acquisition.v',HERE/'peer_cached_vpi.c',HERE/'tb_iol1_acquisition.sv',HERE/'originals/iol1.c',HERE/'originals/iol1.h',HERE/'originals/tb_iol1_target_c.sv',HERE/'originals/vpi_user.h',HERE/'originals/_pli_types.h.in']
 before={str(p):sha(p) for p in sources}
 for p in sources:
  q=out/p.relative_to(HERE);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
 peer=(HERE/'originals/tb_iol1_target_c.sv').read_text().split('module tb_iol1_target_c;')[0]
 (out/'peer.sv').write_text(peer,encoding='utf8',newline='\n')
 (out/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{unix(out)}'
mkdir vpi-include
cp originals/vpi_user.h vpi-include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' originals/_pli_types.h.in > vpi-include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include peer_cached_vpi.c originals/iol1.c -o peer_cached_vpi.vpi > vpi-build.log 2>&1
iverilog -g2012 -s tb_iol1_acquisition -o acquisition.vvp cnc_iol1_acquisition_master.v cnc_iol1_diagnostic_acquisition.v peer.sv tb_iol1_acquisition.sv > rtl-build.log 2>&1
vvp -M . -m peer_cached_vpi acquisition.vvp > simulation.log 2>&1
''',encoding='utf8',newline='\n')
 r=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh',unix(out/'run.sh')],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=600)
 (out/'command.log').write_text(r.stdout+r.stderr,encoding='utf8',newline='\n')
 log=(out/'simulation.log').read_text() if(out/'simulation.log').is_file() else ''
 count=re.search(r'PASS acquisition checks=(\d+)',log)
 receipt={'status':'PASS' if r.returncode==0 and count else 'FAIL','actual_compiled_C_and_physical_SPI_edges_simulated':bool(count),'checks':int(count.group(1)) if count else 0,'input_hashes':before,'source_unchanged':all(sha(Path(p))==h for p,h in before.items()),'scope_flags':{'four_integrated_motherboard_regions':True,'read_only_diagnostic_observations':True,'factory_identity_VERIFIED':False,'commercial_ACTIVE':False,'real_ADC_or_GPIO_hardware':False,'actual_ARM_DMA_IRQ_execution':False,'outputs_motion_ARM_CAP3_HAL':False},'output_hashes':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'checks':receipt['checks'],'out':str(out)}));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);raise SystemExit(main(p.parse_args().out.resolve()))
