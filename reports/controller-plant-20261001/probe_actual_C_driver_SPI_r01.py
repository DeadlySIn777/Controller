"""Connect preserved real C driver to actual Verilated SPI; never fabricate discovery."""
from pathlib import Path
import hashlib,json,shutil,subprocess,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=HERE/'actual-C-driver-SPI-probe-r01';OUT.mkdir(exist_ok=False)
ACTUAL=HERE/'actual-spi-transport-fault-plant-r04'
EXTERNAL=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec/cnc3/src')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unix=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
sources=list(EXTERNAL.glob('*.[ch]'))+[HERE/'stage-r02/spi_edge_plant.cpp',HERE/'stage-r02/edge_plant.hpp',Path(__file__)]
sources += [p for p in (ACTUAL/'inputs').iterdir()if p.suffix in ['.v']or p.name=='frames.hpp']
before={str(p):sha(p)for p in sources};copied=OUT/'inputs';copied.mkdir()
for p in sources:shutil.copyfile(p,copied/p.name)
rig=(copied/'spi_edge_plant.cpp').read_text().split('int main(int argc,char**argv){')[0]
assert 'struct Rig {' in rig and 'int main' not in rig
(copied/'rig.hpp').write_text(rig,encoding='utf8',newline='\n')
(copied/'driver_probe.cpp').write_text('''#include "rig.hpp"
#include "cnc3.h"
#include <cstring>
static unsigned exchanges=0;
static int transport(void*context,cnc3_cs cs,const uint8_t*tx,uint8_t*rx,size_t length){
 auto&rig=*static_cast<Rig*>(context);
 if((cs!=CNC3_CS_FB&&cs!=CNC3_CS_CMD)||length!=(cs==CNC3_CS_FB?176u:96u))return -1;
 Frame frame{cs==CNC3_CS_FB,std::vector<uint8_t>(tx,tx+length)};
 auto reply=rig.exchange(frame,"C_driver_transaction_"+std::to_string(exchanges++));
 std::memcpy(rx,reply.data(),length);return 0;
}
int main(){try{
 Rig rig;cnc3_driver driver;cnc3_config config{};
 config.axis_mask=0xfff;config.alarm_trip_mask=0xfff;config.required_encoder_mask=15;
 config.encoder_filter_ticks=4;config.config_hash=0xabcdef12;
 for(unsigned i=0;i<12;++i){config.scale[i]=40;for(auto&t:config.timing[i])t=100;}
 cnc3_transport link{&rig,transport};cnc3_init(&driver,link,&config,0x11223344);
 for(unsigned i=0;i<3&&driver.state!=CNC3_FAULT;++i){
  rig.advance(50000);uint64_t ns=rig.cycles*20;
  cnc3_read(&driver,ns,1000000);cnc3_write(&driver,rig.cycles*20,1000000);
  std::cout<<"C_DRIVER_CYCLE "<<i<<" state="<<cnc3_state_name(driver.state)
           <<" fault="<<cnc3_fault_name(driver.fault)<<" result="<<driver.last_result<<"\\n";
 }
 check(exchanges==2,"actual driver made two discovery wire transactions");
 check(driver.state==CNC3_FAULT&&driver.fault==CNC3_FAULT_BAD_CAPS,"missing actual CAP3 is refused");
 check(!driver.discovered&&!driver.feedback_valid,"driver cannot invent discovered/valid capability");
 check(rig.rtl.armed_mask==0&&rig.rtl.enable_n==0xfff&&!rig.rtl.motion_request,"discovery failure cannot authorize motion");
 for(auto n:rig.observed_rises)check(n==0,"failed discovery produces no real step edges");
 std::ofstream f("observation.json");f<<"{\\"actual_C_driver\\":true,\\"actual_SPI_RTL\\":true,\\"behavioral_endpoint\\":false,"
   <<"\\"state\\":\\""<<cnc3_state_name(driver.state)<<"\\",\\"fault\\":\\""<<cnc3_fault_name(driver.fault)
   <<"\\",\\"codec_result\\":"<<driver.last_result<<",\\"transactions\\":"<<exchanges
   <<",\\"motion_inhibited\\":true,\\"checks\\":"<<checks<<",\\"LinuxCNC_HAL\\":false}\\n";
 std::cout<<"REAL_C_DRIVER_REFUSES_MISSING_CAP3\\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\\n';return 1;}}
''',encoding='utf8',newline='\n')
executions=[]
def run(name,argv,timeout=900):
    start=time.monotonic();p=subprocess.run(argv,capture_output=True,timeout=timeout)
    log=OUT/(name+'.log');log.write_bytes(p.stdout+p.stderr)
    executions.append(dict(name=name,command=argv,exit_code=p.returncode,seconds=time.monotonic()-start,log_sha256=sha(log)))
    if p.returncode:raise RuntimeError(name+' failed; see '+str(log))
try:
    # Reuse exact already compiled model sources, not its executable or responses.
    generated=sorted((ACTUAL/'obj').glob('*.cpp'))
    assert generated
    for name in ['cnc3_proto.c','cnc3.c']:
        run('compile-'+name,['wsl','-d','GarciaMechBuilder','--','clang','-std=c11','-O1','-Wall','-Wextra','-Werror','-pedantic','-Wconversion','-Wshadow',
                            '-I'+unix(copied),'-c',unix(copied/name),'-o',unix(OUT/(name+'.o'))])
    run('compile-real-driver-RTL',['wsl','-d','GarciaMechBuilder','--','clang++','-std=c++17','-O1','-pthread',
        '-I/usr/share/verilator/include','-I/usr/share/verilator/include/vltstd','-I'+unix(ACTUAL/'obj'),'-I'+unix(copied),
        unix(copied/'driver_probe.cpp'),*[unix(p)for p in generated],unix(OUT/'cnc3.c.o'),unix(OUT/'cnc3_proto.c.o'),
        '/usr/share/verilator/include/verilated.cpp','/usr/share/verilator/include/verilated_threads.cpp','-o',unix(OUT/'driver_probe')])
    run('actual-probe',['wsl','-d','GarciaMechBuilder','--cd',unix(OUT),'--',unix(OUT/'driver_probe')])
    observation=json.loads((OUT/'observation.json').read_text());error=None
except Exception as exc:
    observation=None;error=str(exc)
unchanged=all(sha(Path(p))==h for p,h in before.items())
receipt=dict(status='BLOCKED'if observation and unchanged else 'FAIL',probe_passed=bool(observation and unchanged),
    error=error,input_sha256=before,input_unchanged=unchanged,executions=executions,observation=observation,
    missing_implementation=['Actual RTL CAP3 READ_PAGE response','C-driver commissioning of both measured watchdog self-tests and continuity acknowledgement','CNC3 LinuxCNC HAL integration'],
    scope='First bounded actual preserved C driver to real compiled RTL serial discovery; a missing feature is exposed, never substituted',
    physical_qualified=False,manufacturing_ready=False)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:receipt[k]for k in ['status','probe_passed','error','observation']}))
raise SystemExit(2 if receipt['probe_passed'] else 1)
