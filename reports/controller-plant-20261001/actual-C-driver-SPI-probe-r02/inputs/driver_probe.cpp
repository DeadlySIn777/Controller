#include "rig.hpp"
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
           <<" fault="<<cnc3_fault_name(driver.fault)<<" result="<<driver.last_result<<"\n";
 }
 check(exchanges==2,"actual driver made two discovery wire transactions");
 check(driver.state==CNC3_FAULT&&driver.fault==CNC3_FAULT_BAD_CAPS,"missing actual CAP3 is refused");
 check(!driver.discovered&&!driver.feedback_valid,"driver cannot invent discovered/valid capability");
 check(rig.rtl.armed_mask==0&&rig.rtl.enable_n==0xfff&&!rig.rtl.motion_request,"discovery failure cannot authorize motion");
 for(auto n:rig.observed_rises)check(n==0,"failed discovery produces no real step edges");
 std::ofstream f("observation.json");f<<"{\"actual_C_driver\":true,\"actual_SPI_RTL\":true,\"behavioral_endpoint\":false,"
   <<"\"state\":\""<<cnc3_state_name(driver.state)<<"\",\"fault\":\""<<cnc3_fault_name(driver.fault)
   <<"\",\"codec_result\":"<<driver.last_result<<",\"transactions\":"<<exchanges
   <<",\"motion_inhibited\":true,\"checks\":"<<checks<<",\"LinuxCNC_HAL\":false}\n";
 std::cout<<"REAL_C_DRIVER_REFUSES_MISSING_CAP3\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
