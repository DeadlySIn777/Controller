#include "rig.hpp"
#include "cnc3.h"
#include <cstring>
static unsigned exchanges=0;
static int transport(void*context,cnc3_cs cs,const uint8_t*tx,uint8_t*rx,size_t length){
 auto&rig=*static_cast<Rig*>(context);
 if((cs!=CNC3_CS_FB&&cs!=CNC3_CS_CMD)||length!=(cs==CNC3_CS_FB?176u:96u))return -1;
 Frame f{cs==CNC3_CS_FB,std::vector<uint8_t>(tx,tx+length)};
 auto r=rig.exchange(f,"C_driver_"+std::to_string(exchanges++));std::memcpy(rx,r.data(),length);return 0;
}
static Frame fb(uint8_t op,uint32_t session=0,uint8_t page=0){
 std::vector<uint8_t>b(176);check(cnc3_build_fb(b.data(),op,0,session,0,op==5?&page:nullptr,op==5?1:0)==0,"actual C builds FB wire frame");return{true,b};
}
static Frame nop(){cnc3_cmd c{};c.opcode=CNC3_OP_NOP;std::vector<uint8_t>b(96);check(cnc3_build_cmd(b.data(),&c)==0,"actual C builds CMD NOP");return{false,b};}
static void cnf(const std::vector<uint8_t>&b,const std::string&label){cnc3_feedback f{};check(cnc3_decode_cnf3(b.data(),b.size(),&f)==0,label);}
static void cap(const std::vector<uint8_t>&b){
 cnc3_caps c{};check(cnc3_decode_cap3_page0(b.data(),b.size(),&c)==0,"actual RTL snapshot is real CRC-valid CAP3 page0");
 check(std::memcmp(c.spec_revision,"IS-2",4)==0,"literal versioned IS2 profile");
 check(c.step_channels==12&&c.installed_channels==0,"12 integrated support is distinct from unqualified installed0");
 check(c.encoders_supported==4&&c.encoders_base==4&&c.encoders_installed==0,"four base encoders only; no invented expansion");
 check(c.mpg_ports==0&&c.expansion_state==0&&c.mod_id_latched==0&&c.accepted_module_class==0&&c.accepted_encoder_expansion_class==0,"no fake card/presence/MPG");
 check(c.feature_bitmap==0x13ffb&&c.event_ring_depth==0&&c.telemetry_entries==0,"unsupported index/event/telemetry bits remain clear");
 check(c.core_hz==50000000&&c.max_rate==0x1000000&&c.timing_min==100&&c.timing_max==1023&&c.min_sclk_divider==8,"actual frozen rate/timing limits unchanged");
 check(c.watchdog_ticks==250000&&c.progress_pulse_ticks==50&&c.qualification_ticks==0,"no fabricated completed qualifier");
 for(auto n:c.reference_timing)check(n==100,"actual reference timing remains100");
 for(size_t i=78;i<174;++i)check(b[i]==0,"CAP3 reserved bytes remain zero");
}
static void off(Rig&r){check(r.rtl.armed_mask==0&&r.rtl.enable_n==0xfff&&r.rtl.step_out==0&&!r.rtl.motion_request&&!r.rtl.output_request&&!r.rtl.permit_out_req&&!r.rtl.progress_m&&!r.rtl.progress_o,"incomplete profile keeps actual full authority inhibited");}
int main(){try{
 {Rig r;cnf(r.exchange(fb(0x10),"cold"),"cold reply is CNF3, no prequeued capability");
  cnf(r.exchange(fb(5),"readpage"),"accepted request returns previous CNF snapshot");
  auto cmd=r.exchange(nop(),"CMD_cannot_consume");check(!std::memcmp(cmd.data(),"CNS3",4),"CMD keeps actual CNS3 snapshot");
  cap(r.exchange(fb(0x10),"pending_page"));cnf(r.exchange(fb(0x10),"consumed"),"complete valid FB consumes exactly once");off(r);}
 {Rig r;auto bad=fb(5);bad.bytes.back()^=1;r.exchange(bad,"bad_request_crc");cnf(r.exchange(fb(0x10),"not_queued"),"bad CRC READ_PAGE cannot queue capability");off(r);}
 {Rig r;r.exchange(fb(5),"queue");auto bad=fb(0x10);bad.bytes.back()^=1;cap(r.exchange(bad,"bad_reply_command_crc"));cap(r.exchange(fb(0x10),"retained_after_CRC"));cnf(r.exchange(fb(0x10),"once"),"bad CRC command never consumes pending page");off(r);}
 {Rig r;r.exchange(fb(5),"queue");cap(r.exchange(fb(0x10,0xabcdef),"foreign_session"));cap(r.exchange(fb(0x10),"retained_after_foreign_session"));cnf(r.exchange(fb(0x10),"once"),"foreign session cannot consume pending page");off(r);}
 {Rig r;r.exchange(fb(5),"queue");auto shortf=fb(0x10);shortf.bytes.resize(8);r.exchange(shortf,"truncated");cap(r.exchange(fb(0x10),"retained_after_short"));cnf(r.exchange(fb(0x10),"once"),"truncated frame cannot consume pending page");off(r);}
 {Rig r;r.exchange(fb(5),"queue");auto wrong=fb(5);wrong.feedback=false;wrong.bytes.resize(96);cnc3_seal_host(wrong.bytes.data(),wrong.bytes.size());r.exchange(wrong,"wrong_CS");cap(r.exchange(fb(0x10),"retained_after_CMD_readpage"));off(r);}
 {Rig r;r.exchange(fb(5,0,1),"unsupported_page1");cnf(r.exchange(fb(0x10),"not_fake_page1"),"unsupported I/O page explicitly fails without invented capabilities");off(r);}
 {Rig r;r.exchange(fb(5),"queue");r.rtl.rst_n=0;r.advance(8);r.rtl.rst_n=1;r.advance(100);cnf(r.exchange(fb(0x10),"reset"),"reset clears pending page/in-flight ownership");off(r);}
 {Rig r;cnc3_driver d;cnc3_config cfg{};cfg.axis_mask=0xfff;cfg.alarm_trip_mask=0xfff;cfg.required_encoder_mask=15;cfg.encoder_filter_ticks=4;cfg.config_hash=0x1234;
  for(unsigned i=0;i<12;++i){cfg.scale[i]=40;for(auto&t:cfg.timing[i])t=100;}
  cnc3_init(&d,{&r,transport},&cfg,0x11223344);
  for(unsigned i=0;i<130&&d.state!=CNC3_FAULT;++i){r.advance(50000);cnc3_read(&d,r.cycles*20,1000000);cnc3_write(&d,r.cycles*20,1000000);off(r);}
#ifdef ORIGINAL_DRIVER
  check(exchanges==2&&d.state==CNC3_FAULT&&d.fault==CNC3_FAULT_BAD_CAPS,"unchanged IS1 driver correctly refuses real IS2 profile");
#else
  check(exchanges==128&&d.state==CNC3_FAULT&&d.fault==CNC3_FAULT_QUALIFICATION,"versioned driver parses real CAP3 but refuses incomplete qualification after64tries");
  check(d.last_result==0&&d.caps.step_channels==12&&d.caps.encoders_supported==4&&d.caps.accepted_module_class==0,"actual driver learned real integrated12/four/class0 metadata");
#endif
  check(!d.discovered&&!d.feedback_valid&&!r.rtl.config_valid&&r.rtl.session==0,"no false discovery/config/session/ARM");off(r);
  for(auto n:r.observed_rises)check(n==0,"driver refusal never emits any physical step edge");
 }
#ifndef ORIGINAL_DRIVER
 // Unsupported requested functions fail before the copied driver sends a byte.
 for(unsigned mode=0;mode<3;++mode){Rig r;cnc3_driver d;cnc3_config cfg{};cfg.axis_mask=0xfff;
  for(unsigned i=0;i<12;++i){cfg.scale[i]=40;for(auto&t:cfg.timing[i])t=100;}
  if(mode==0)cfg.required_encoder_mask=16;else if(mode==1)cfg.encoder_expansion_class=1;else cfg.mpg_config=1;
  unsigned before=exchanges;cnc3_init(&d,{&r,transport},&cfg,1);cnc3_read(&d,r.cycles*20,1000000);
  check(d.state==CNC3_FAULT&&d.fault==CNC3_FAULT_CONFIG&&exchanges==before,"unsupported encoder/MPG configuration cannot enter discovery or send authority");off(r);
 }
#endif
 std::ofstream out("observation.json");out<<"{\"checks\":"<<checks<<",\"transactions\":"<<exchanges<<",\"actual_C_driver_and_RTL_SPI\":true,\"profile_complete\":false,\"motion_inhibited\":true,\"HAL\":false}\n";
 std::cout<<"PASS real IS2 page lifecycle and compiled driver checks="<<checks<<"\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
