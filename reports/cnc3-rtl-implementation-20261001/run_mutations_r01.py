from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
BASE=Path(__file__).resolve().parent;OUT=BASE/'mutation-controls-r01';STAGE=BASE/'stage-r01';PROOF=BASE/'proof-r06'
a=argparse.ArgumentParser();a.add_argument('--out',type=Path);args=a.parse_args()
if args.out:OUT=args.out.resolve()
OUT.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
mutations=[
 ('missing_crc16','cnc3_spi_transport.v',' && rx_crc==rx_shift[15:0]','', 'spi','bad CRC accepted'),
 ('missing_post_guard','cnc3_spi_transport.v',' && !sck_fall','', 'spi','CS postguard accepted'),
 ('missing_handoff_guard','cnc3_spi_transport.v',' && !fb_start && !cmd_start','', 'spi','zero-gap CMD to FB handoff accepted'),
 ('wrong_embedded_crc','cnc3_spi_transport.v','selected_fb && (~inner_crc==rx_shift[983:952])',"1'b1", 'spi','bad embedded CRC accepted'),
 ('missing_mask_width','cnc3_command_validate.v',"(mask & 16'hf000) != 0","1'b0",'validate','mask_bit12'),
 ('drive_both_cs','cnc3_spi_transport.v','(spi_cs_fb_n ^ spi_cs_cmd_n)','(~spi_cs_fb_n | ~spi_cs_cmd_n)','spi','both CS drove MISO')]
rows=[];before={str(f):sha(f) for f in (STAGE/'rtl').glob('*.v')}
for name,file,old,new,bench,token in mutations:
 path=OUT/name;path.mkdir();src=(STAGE/'rtl'/file).read_text();assert src.count(old)==1,(name,src.count(old))
 for f in (STAGE/'rtl').glob('*.v'):shutil.copyfile(f,path/f.name)
 (path/file).write_text(src.replace(old,new))
 script=path/'run.sh';script.write_text(f'''#!/bin/sh
set -eu
cd '{unix(path)}'
iverilog -g2012 -s tb -o simulation *.v '{unix(PROOF)}/{bench}_tb.sv'
vvp simulation
''',newline='\n')
 r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',unix(script)],capture_output=True,text=True,timeout=120)
 log=r.stdout+r.stderr;(path/'command.log').write_text(log)
 # Actual compiled RTL must fail a functional assertion, not parsing/elaboration.
 rejected=r.returncode!=0 and 'FATAL:' in log and token in log
 rows.append({'name':name,'actual_compiled_copy_rejected':rejected,'exit_code':r.returncode,'reason_token':token,'log_sha256':sha(path/'command.log'),'mutated_source_sha256':sha(path/file)})
receipt={'status':'PASS' if all(x['actual_compiled_copy_rejected'] for x in rows) else 'FAIL','mutations':rows,'original_stage_sources_unchanged':all(sha(Path(f))==h for f,h in before.items()),'source_hashes':before,'actual_full_machine':False}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));raise SystemExit(receipt['status']!='PASS')
