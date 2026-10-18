from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,re,os
from record_host import fixture_record
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True);names=['iol1.c','iol1.h','dic_filter.c','dic_filter.h','record_peer_vpi.c','tb_record_config.sv','vendor/Icarus/vpi_user.h','vendor/Icarus/_pli_types.h.in']
 before={n:sha(H/n) for n in names}
 for n in names:q=out/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/n,q)
 p,_=fixture_record(0,bytes(range(1,13)));(out/'fixtures.bin').write_bytes(p)
 (out/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{unix(out)}'
mkdir include
cp vendor/Icarus/vpi_user.h include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' vendor/Icarus/_pli_types.h.in > include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Iinclude -I. record_peer_vpi.c iol1.c dic_filter.c -o record_peer_vpi.vpi > c-build.log 2>&1
iverilog -g2012 -s tb_record_config -o record.vvp tb_record_config.sv > rtl-build.log 2>&1
vvp -M . -m record_peer_vpi record.vvp > simulation.log 2>&1
''',newline='\n')
 p=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh',unix(out/'run.sh')],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=120)
 (out/'execute.log').write_text(p.stdout+p.stderr,newline='\n');log=(out/'simulation.log').read_text() if (out/'simulation.log').exists() else '';m=re.search(r'PASS actual wire record/config checks=(\d+)',log)
 r={'status':'PASS' if p.returncode==0 and m else 'FAIL','checks':int(m.group(1)) if m else 0,'actual_simulated_SPI_with_same_staged_C':bool(m),'input_hashes':before,'inputs_unchanged':all(sha(H/n)==h for n,h in before.items()),'scope':{'proposed_IS2_RECORD_IDENT':True,'actual_GPIO_MMIO_or_DMA_ISR_execution':False,'manufacturer_authentic_record':False,'ACTIVE_outputs_or_ARM':False}}
 (out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return r['status']!='PASS'
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);raise SystemExit(main(ap.parse_args().out.resolve()))
