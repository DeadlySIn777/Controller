#include "rig.hpp"
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
