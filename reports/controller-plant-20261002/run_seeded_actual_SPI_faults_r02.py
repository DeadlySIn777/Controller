"""Fresh actual RTL simulation; seeded faults never stand in for the complete machine."""
from pathlib import Path
import argparse,json,hashlib,shutil,subprocess,time,importlib.util
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'reports/controller-plant-20261001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unix=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path);ap.add_argument('--count',type=int,default=2048);ap.add_argument('--wsl-distro',default='GarciaMechBuilder');a=ap.parse_args()
out=a.out.resolve();assert out.is_relative_to(ROOT/'reports') and not out.exists() and 8<=a.count<=4096 and a.count%8==0
out.mkdir();copied=out/'inputs';copied.mkdir()
baseline=HERE/'actual-spi-reset-fault-plant-r06';old=json.loads((baseline/'receipt.json').read_text())
assert old['status']=='PASS' and old['source_unchanged']
sources=[baseline/'inputs'/name for name in ['frames.hpp','edge_plant.hpp','spi_edge_plant.cpp','protocol_v3.py','protocol.json']]
sources+=sorted((baseline/'inputs').glob('*.v'));assert len(sources)==13
inputs={str(p):sha(p)for p in sources+[Path(__file__),baseline/'receipt.json']}
for p in sources:shutil.copyfile(p,copied/p.name)
rig=(copied/'spi_edge_plant.cpp').read_text().split('int main(int argc,char**argv){')[0]
assert 'explicit Rig(){'in rig
rig=rig.replace('std::ofstream responses{"responses.txt"};','std::ofstream responses;')
rig=rig.replace('explicit Rig(){','explicit Rig(unsigned trial): responses("responses-"+std::to_string(trial)+".txt"){')
(copied/'rig.hpp').write_text(rig,encoding='utf8',newline='\n')
(copied/'seeded.cpp').write_text(r'''#include "rig.hpp"
#include <random>
#include <algorithm>
static uint16_t crc(const std::vector<uint8_t>& bytes){
 uint16_t c=0xffff;
 for(size_t i=0;i+2<bytes.size();++i){c^=static_cast<uint16_t>(bytes[i]<<8);for(unsigned j=0;j<8;++j)c=static_cast<uint16_t>((c<<1)^((c&0x8000)?0x1021:0));}
 return c;
}
int main(int argc,char**argv){try{
 unsigned count=argc>1?static_cast<unsigned>(std::stoul(argv[1])):1024;
 std::mt19937 rng(0x434e4333u);std::ofstream cases("cases.jsonl");
 for(unsigned trial=0;trial<count;++trial){
  unsigned start_checks=checks;Rig rig(trial);rig.commissioning();
  for(unsigned j=0;j<frames::updates.size();++j){rig.exchange(frames::updates[j],"update_"+std::to_string(j));rig.advance(10000+rng()%20001);check(!rig.rtl.fault_word,"valid updates remain healthy under seeded idle intervals");}
  for(unsigned j=0;j<12;++j)check(rig.observed_rises[j]>10,"all12 real pins moved before injection");
  rig.fault_injection_cycle=rig.cycles;auto sequence=rig.rtl.last_sequence;
  unsigned kind=trial%8,location=0;Frame damaged=frames::fault_update;
  if(kind==0){location=rng()%752;damaged.bytes[location/8]^=static_cast<uint8_t>(1u<<(7-location%8));}
  else if(kind==1){location=752+rng()%16;damaged.bytes[location/8]^=static_cast<uint8_t>(1u<<(7-location%8));}
  else if(kind==2){location=rng()%752;unsigned length=1+rng()%16;for(unsigned j=0;j<length&&location+j<768;++j)damaged.bytes[(location+j)/8]^=static_cast<uint8_t>(1u<<(7-(location+j)%8));}
  else if(kind==3){location=8+rng()%4;damaged.bytes[location]^=static_cast<uint8_t>(1u<<(rng()%8));auto c=crc(damaged.bytes);damaged.bytes[94]=static_cast<uint8_t>(c>>8);damaged.bytes[95]=static_cast<uint8_t>(c);}
  else if(kind==4){location=rng()%frames::updates.size();damaged=frames::updates[location];}
  else if(kind==5){location=1+rng()%95;damaged.bytes.resize(location);}
  else if(kind==6){location=rng()%256;damaged.bytes.push_back(static_cast<uint8_t>(location));}
  if(kind==7){rig.rtl.spi_cs_cmd_n=0;rig.advance(250100+rng()%1000);check(!rig.rtl.armed_mask,"held real CS cannot feed watchdog");rig.rtl.spi_cs_cmd_n=1;rig.advance(12);}
  else rig.exchange(damaged,"injected_fault");
  rig.advance(100);
  check(rig.rtl.fault_word&&!rig.rtl.armed_mask&&rig.rtl.enable_n==all_joints&&!rig.rtl.step_out,"seeded actual serial fault inhibits all12");
  check(rig.rtl.last_sequence==sequence&&!rig.rtl.pos_continuity,"fault cannot advance sequence and loses continuity");
  check(rig.inhibit_observed_cycle>rig.fault_injection_cycle&&rig.inhibit_observed_cycle-rig.fault_injection_cycle<=250001,"simulated fault inhibition within5ms");
  auto stopped=rig.observed_rises;rig.exchange(frames::fault_update,"post_fault_correct_UPDATE");rig.advance(20000);
  check(rig.observed_rises==stopped&&!rig.rtl.armed_mask&&rig.rtl.fault_word,"correct UPDATE cannot resume after fault");
  rig.exchange(frames::read,"final_feedback");rig.advance(1000);
  check(rig.observed_rises==stopped,"read-only feedback does not restart motion");
  cases<<"{\"trial\":"<<trial<<",\"kind\":"<<kind<<",\"location\":"<<location<<",\"checks\":"<<checks-start_checks<<",\"inhibit_cycles\":"<<rig.inhibit_observed_cycle-rig.fault_injection_cycle<<",\"fault_word\":"<<rig.rtl.fault_word<<",\"passed\":true}\n";cases.flush();
  if(trial%32==31)std::cout<<"PASS "<<trial+1<<" seeded trials\n"<<std::flush;
 }
 std::cout<<"SEEDED_ACTUAL_SPI_PASS count="<<count<<" checks="<<checks<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
''',encoding='utf8',newline='\n')
compiled_inputs={str(p):sha(p)for p in copied.iterdir()if p.is_file()}
(out/'precompile-inputs.json').write_text(json.dumps(compiled_inputs,indent=2)+'\n')
commands=[]
def run(name,argv,timeout=900):
 start=time.monotonic();log=out/(name+'.log')
 with log.open('wb')as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 commands.append(dict(name=name,command=argv,exit_code=r.returncode,seconds=time.monotonic()-start,log_sha256=sha(log)))
 if r.returncode:raise RuntimeError(name+' failed; '+str(log))
failure=None;cases=[];decoded=0;generated={};response_hashes={}
try:
 obj=out/'obj'
 run('verilate',['wsl','-d',a.wsl_distro,'--','verilator','--cc','--compiler','clang','--top-module','cnc3_motion_spi','--Mdir',unix(obj),'-Wall','-Wno-fatal',*[unix(p)for p in copied.glob('*.v')]])
 generated={str(p):sha(p)for p in obj.iterdir()if p.suffix in ['.cpp','.h']}
 run('compile',['wsl','-d',a.wsl_distro,'--','clang++','-std=c++17','-O1','-pthread','-I/usr/share/verilator/include','-I/usr/share/verilator/include/vltstd','-I'+unix(obj),'-I'+unix(copied),unix(copied/'seeded.cpp'),*[unix(p)for p in obj.glob('*.cpp')],'/usr/share/verilator/include/verilated.cpp','/usr/share/verilator/include/verilated_threads.cpp','-o',unix(out/'seeded')])
 run('seeded-actual-SPI',['wsl','-d',a.wsl_distro,'--cd',unix(out),'--',unix(out/'seeded'),str(a.count)],3600)
 cases=[json.loads(s)for s in(out/'cases.jsonl').read_text().splitlines()]
 assert len(cases)==a.count and all(c['passed']for c in cases)
 assert [c['trial']for c in cases]==list(range(a.count))
 assert all(c['kind']==c['trial']%8 and c['checks']>=57 and 0<c['inhibit_cycles']<=250001 for c in cases)
 spec=importlib.util.spec_from_file_location('seeded_codec',copied/'protocol_v3.py');codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec);codec._SPEC=codec.Spec(str(copied/'protocol.json'))
 for case in cases:
  response_file=out/('responses-'+str(case['trial'])+'.txt')
  response_hashes[response_file.name]=sha(response_file)
  lines=response_file.read_text().splitlines()
  assert sum(line.startswith('final_feedback ')for line in lines)==1
  assert sum(line.startswith('post_fault_correct_UPDATE ')for line in lines)==1
  for line in lines:
   label,n,h=line.split();frame=bytes.fromhex(h);assert len(frame)==int(n)
   if label=='injected_fault' and len(frame)!=96:continue
   cs='CS_FB'if len(frame)==176 else 'CS_CMD'
   parsed=codec.decode_response(cs,frame);decoded+=1
   if label=='final_feedback':
    assert parsed['armed_mask']==0 and parsed['pos_continuity']==0 and parsed['fault_word']!=0
except Exception as e:failure=repr(e)
unchanged=all(sha(Path(p))==h for p,h in {**inputs,**compiled_inputs,**generated}.items())
receipt=dict(status='PASS'if failure is None and unchanged else'FAIL',failure=failure,seed='0x434e4333',requested_trials=a.count,completed_trials=len(cases),cases=cases,independently_decoded_responses=decoded,input_sha256=inputs,precompile_input_sha256=compiled_inputs,response_sha256=response_hashes,generated_sha256=generated,inputs_unchanged=unchanged,executions=commands,post_fault_correct_UPDATE_restart_rejected=True,all_twelve_real_pins_exercised=True,actual_SPI_and_motion_RTL=True,ideal_power_permission_and_mechanics=True,actual_LinuxCNC_HAL=False,complete22fault_electrical_suite=False,complete_nine_machine_suite=False,physical20ms_qualified=False,manufacturing_ready=False)
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:receipt[k]for k in ['status','failure','completed_trials','independently_decoded_responses']}));raise SystemExit(0 if receipt['status']=='PASS'else 1)
