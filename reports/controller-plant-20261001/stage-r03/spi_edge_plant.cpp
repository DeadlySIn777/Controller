// Actual Verilated CNC3 pins drive this disconnected ideal machine fixture.
// External permission/watchdog/readiness providers here are explicit ideal
// fixtures, not the completed motherboard's electrical circuits or LinuxCNC.
#include "Vcnc3_motion_spi.h"
#include "verilated.h"
#include "edge_plant.hpp"
#include "frames.hpp"
#include <array>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace controller_plant;
static unsigned checks=0;
static void check(bool value,const std::string& message){
 ++checks;if(!value)throw std::runtime_error(message);
}
static Config geometry(){
 Config c;
 for(auto&j:c.joint){j.units_per_output_rev=5;j.microsteps=1;}
 for(auto&e:c.encoder){e.edges_per_output_rev=200;e.minimum_edge_cycles=8;}
 return c;
}

struct Rig {
 VerilatedContext context;
 Vcnc3_motion_spi rtl{&context};
 EdgePlant plant{geometry(),0x9d20a452};
 Sensors sensors{};
 uint64_t cycles=0;
 bool fixture_present=true,field_power=true,sensor_power=true,external_permission=true;
 uint8_t opi_latches=0;
 std::array<uint64_t,12> observed_rises{};
 std::array<int64_t,12> observed_signed_steps{};
 uint16_t previous_step=0;
 uint64_t fault_injection_cycle=0,inhibit_observed_cycle=0;
 std::ofstream responses{"responses.txt"};
 explicit Rig(){
  rtl.rst_n=0;rtl.spi_cs_fb_n=rtl.spi_cs_cmd_n=1;rtl.spi_sclk=rtl.spi_mosi=0;
  rtl.qualification_complete=1;rtl.installed_input=all_joints;rtl.installed_module_class=1;
  rtl.inhibit_n=rtl.wd_m_ok=rtl.wd_o_ok=1;
  rtl.reset_arm_ready=1;rtl.reset_arm_held=0;rtl.contactor_deenergized=1;rtl.sto_arm_expected=1;
  rtl.motion_critical_ports_valid=1;rtl.encoder_installed=15;
  rtl.external_fault_word=0;rtl.motion_critical_io_fault=0;
  for(unsigned i=0;i<44;++i)rtl.provider_feedback[i]=0;
  for(unsigned i=0;i<24;++i)rtl.provider_status[i]=0;
  rtl.physical_safety_power_word=0;
  advance(8);rtl.rst_n=1;advance(2300);
  check(rtl.step_out==0 && rtl.enable_n==all_joints,"actual reset default inhibit");
 }
 void tick(){
  const bool gated=fixture_present&&field_power&&external_permission&&rtl.inhibit_n&&rtl.wd_m_ok&&rtl.motion_request;
  rtl.gate_high=gated?15:0;
  if(!gated)opi_latches=0;else opi_latches|=rtl.opi_rearm;
  rtl.opi_ok=opi_latches;
  rtl.encoder_a=sensors.encoder_a;rtl.encoder_b=sensors.encoder_b;rtl.encoder_z=sensors.encoder_z;
  rtl.encoder_port_valid=sensors.encoder_connected;
  rtl.alarm_current_raw=sensors.alarm;
  rtl.clk=0;rtl.eval();context.timeInc(10);
  rtl.clk=1;rtl.eval();context.timeInc(10);
  // The provider may remove physical permission independently of a command.
  PhysicalDriveState d{fixture_present,gated,static_cast<uint16_t>(rtl.enable_n),
                       static_cast<uint16_t>(field_power?all_joints:0),sensor_power};
  sensors=plant.tick(cycles++,{static_cast<uint16_t>(rtl.step_out),static_cast<uint16_t>(rtl.dir_out)},d);
  uint16_t rises=rtl.step_out&~previous_step;previous_step=rtl.step_out;
  for(unsigned i=0;i<12;++i)if(rises&(1u<<i)){
   ++observed_rises[i];observed_signed_steps[i]+=(rtl.dir_out&(1u<<i))?-1:1;
  }
  if(fault_injection_cycle && !inhibit_observed_cycle && rtl.enable_n==all_joints && rtl.step_out==0)
   inhibit_observed_cycle=cycles;
 }
 void advance(uint64_t n){while(n--)tick();}
 std::vector<uint8_t> exchange(const Frame&frame,const std::string&label){
  advance(12);rtl.spi_sclk=0;
  if(frame.feedback)rtl.spi_cs_fb_n=0;else rtl.spi_cs_cmd_n=0;
  advance(8);std::vector<uint8_t> response(frame.bytes.size(),0);
  for(unsigned bit=0;bit<frame.bytes.size()*8;++bit){
   rtl.spi_mosi=(frame.bytes[bit/8]>>(7-bit%8))&1;
   advance(4);rtl.spi_sclk=1;rtl.eval();
   response[bit/8]=static_cast<uint8_t>((response[bit/8]<<1)|(rtl.spi_miso&1));
   advance(4);rtl.spi_sclk=0;rtl.eval();
  }
  advance(8);rtl.spi_cs_fb_n=rtl.spi_cs_cmd_n=1;rtl.spi_mosi=0;advance(12);
  check(!rtl.spi_miso_oe,"MISO releases after actual serial transaction");
  responses<<label<<' '<<response.size()<<' ';
  for(auto b:response)responses<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(b);
  responses<<std::dec<<'\n';return response;
 }
 void commissioning(){
  exchange(frames::configure,"configure");check(rtl.config_valid,"configuration accepted");
  exchange(frames::sync,"sync");check(rtl.session==0x11223344 && !rtl.fault_word,"session established");
  // Explicit external fixture events: actual RTL must observe both falls and
  // recoveries at the required times. This is not a transistor/SPICE model.
  for(unsigned channel=0;channel<2;++channel){
   exchange(channel?frames::test_o:frames::test_m,channel?"test_o":"test_m");
   advance(500000);
   check(rtl.step_out==0 && rtl.enable_n==all_joints,"watchdog selftest contains real pins");
   if(channel)rtl.wd_o_ok=0;else rtl.wd_m_ok=0;
   advance(8);
   if(channel)rtl.wd_o_ok=1;else rtl.wd_m_ok=1;
   advance(8);
  }
  check(rtl.selftest_passed==3 && !rtl.fault_word,"both timed external-watchdog witnesses accepted");
  exchange(frames::clear,"continuity");exchange(frames::arm,"arm");advance(550);
  check(rtl.armed_mask==all_joints && rtl.enable_n==0 && !rtl.fault_word,"all12 actually armed");
 }
 void write_state(const std::string&path){
  std::ofstream f(path);f<<std::setprecision(17)<<"{\"joints\":[";
  for(unsigned i=0;i<12;++i){const auto&s=plant.state()[i];if(i)f<<',';
   f<<"{\"joint\":"<<i<<",\"position\":"<<s.position<<",\"electrical_steps\":"<<s.accepted_electrical_steps
    <<",\"observed_rises\":"<<observed_rises[i]<<",\"pin_signed_steps\":"<<observed_signed_steps[i]<<",\"driven_rises\":"<<s.driven_rises
    <<",\"lost_steps\":"<<s.lost_steps<<",\"inhibited_edges\":"<<s.inhibited_edges<<'}';
  }
  f<<"],\"core_cycles\":"<<cycles<<",\"fault_word\":"<<rtl.fault_word
   <<",\"armed_mask\":"<<rtl.armed_mask<<",\"pos_continuity\":"<<rtl.pos_continuity
   <<",\"encoder_backlog\":[";
  for(unsigned i=0;i<4;++i){if(i)f<<',';f<<sensors.encoder_backlog[i];}
  f<<"],\"checks\":"<<checks<<",\"fault_injection_cycle\":"<<fault_injection_cycle
   <<",\"inhibit_observed_cycle\":"<<inhibit_observed_cycle
   <<",\"actual_FPGA_integration\":true,\"actual_LinuxCNC_integration\":false,\"physical_qualified\":false}\n";
 }
};

int main(int argc,char**argv){
 try{
  const std::string scenario=argc>1?argv[1]:"clean";
  Rig rig;rig.commissioning();
  if(scenario=="missed_steps"){
   Faults f;f.lose_every_nth[0]=2;rig.plant.faults(f);
  }
  for(unsigned i=0;i<frames::updates.size();++i){
   rig.exchange(frames::updates[i],"update_"+std::to_string(i));rig.advance(30000);
   check(rig.rtl.fault_word==0,"legitimate twelve-axis update remains healthy");
  }
  for(unsigned i=0;i<12;++i)check(rig.observed_rises[i]>20,"each actual motor output moved");
  if(scenario!="clean"&&scenario!="missed_steps")rig.fault_injection_cycle=rig.cycles;
  if(scenario=="watchdog"){
   rig.advance(250100);
   check((rig.rtl.fault_word&2)&&rig.rtl.armed_mask==0,"actual link watchdog inhibits all12");
  }else if(scenario=="FPGA_reset"||scenario=="FPGA_reset_during_CS"){
   const auto before=rig.plant.state();
   if(scenario=="FPGA_reset_during_CS"){
    rig.rtl.spi_cs_cmd_n=0;rig.advance(12);
    // Real clocks shift part of a command; reset occurs before CS release.
    for(unsigned bit=0;bit<37;++bit){
     rig.rtl.spi_mosi=(frames::fault_update.bytes[bit/8]>>(7-bit%8))&1;
     rig.advance(4);rig.rtl.spi_sclk=1;rig.advance(4);rig.rtl.spi_sclk=0;
    }
   }
   rig.rtl.rst_n=0;rig.rtl.eval();rig.advance(20);
   check(rig.rtl.enable_n==all_joints&&rig.rtl.step_out==0&&rig.rtl.pos_continuity==0,
         "actual asynchronous reset removes enable and invalidates continuity");
   check(!rig.rtl.spi_miso_oe&&!rig.rtl.config_valid&&!rig.rtl.session,
         "reset releases serial driver and discards configuration/session authority");
   rig.rtl.spi_sclk=rig.rtl.spi_mosi=0;rig.rtl.spi_cs_fb_n=rig.rtl.spi_cs_cmd_n=1;
   rig.rtl.rst_n=1;rig.advance(3000);
   check(rig.rtl.enable_n==all_joints&&!rig.rtl.armed_mask&&!rig.rtl.config_valid,
         "reset release does not automatically configure or arm");
   for(unsigned i=0;i<12;++i)check(rig.plant.state()[i].accepted_electrical_steps>=before[i].accepted_electrical_steps-2&&
      rig.plant.state()[i].accepted_electrical_steps<=before[i].accepted_electrical_steps+2,
      "interrupted frame and reset do not create uncontrolled mechanical displacement");
  }else if(scenario=="CS_stuck_low"){
   const auto sequence=rig.rtl.last_sequence;
   rig.rtl.spi_cs_cmd_n=0;rig.advance(250100);
   check((rig.rtl.fault_word&2)&&rig.rtl.armed_mask==0,"unreleased physical CS cannot feed watchdog");
   check(rig.rtl.last_sequence==sequence,"incomplete transaction cannot consume sequence");
   rig.rtl.spi_cs_cmd_n=1;rig.advance(12);
  }else if(scenario=="bad_CRC"||scenario=="replayed_update"||scenario=="wrong_session"||
           scenario=="MOSI_stuck_high"||scenario=="MOSI_stuck_low"||scenario=="short_frame"){
   const auto sequence=rig.rtl.last_sequence;
   Frame damaged=frames::fault_update;
   if(scenario=="bad_CRC")damaged.bytes.back()^=1;
   if(scenario=="replayed_update")damaged=frames::updates.back();
   if(scenario=="wrong_session")damaged=frames::foreign_update;
   if(scenario=="MOSI_stuck_high")for(auto&b:damaged.bytes)b=255;
   if(scenario=="MOSI_stuck_low")for(auto&b:damaged.bytes)b=0;
   if(scenario=="short_frame")damaged.bytes.pop_back();
   rig.exchange(damaged,"injected_transport_fault");rig.advance(100);
   check(rig.rtl.fault_word&&rig.rtl.armed_mask==0,"actual malformed or stale SPI transaction inhibits motion");
   check(rig.rtl.last_sequence==sequence,"rejected wire transaction cannot advance command sequence");
  }else if(scenario=="encoder_unplug"){
   Faults f;f.encoder_unplugged=1;rig.plant.faults(f);rig.advance(600);
   check((rig.rtl.fault_word&0x80000)&&rig.rtl.armed_mask==0,"real encoder-valid loss inhibits actual motion");
  }else if(scenario=="permission_drop"){
   rig.external_permission=false;rig.advance(600);
   check(rig.rtl.fault_word&&rig.rtl.armed_mask==0,"independent physical permission loss inhibits actual motion");
  }else if(scenario=="field_power_loss"||scenario=="provider_missing"){
   const auto before=rig.plant.state();
   if(scenario=="field_power_loss")rig.field_power=false;else rig.fixture_present=false;
   rig.advance(600);
   check(rig.rtl.fault_word&&rig.rtl.armed_mask==0,"lost ideal physical power/provider inhibits actual motion");
   for(unsigned i=0;i<12;++i)check(rig.plant.state()[i].position==before[i].position,
                                 "ideal unpowered or absent drive cannot advance the mechanics");
  }else if(scenario=="sensor_power_loss"){
   rig.sensor_power=false;rig.advance(600);
   check((rig.rtl.fault_word&0x80000)&&rig.rtl.armed_mask==0,
         "required encoder validity loss from ideal sensor supply inhibits actual motion");
   check(!rig.sensors.sensors_valid&&!rig.sensors.encoder_connected,
         "missing ideal sensor supply cannot invent valid encoder observations");
  }else if(scenario=="drive_alarm"){
   Faults f;f.forced_alarm=1;rig.plant.faults(f);rig.advance(3000);
   check((rig.rtl.fault_word&0x10)&&rig.rtl.armed_mask==0,"actual filtered drive alarm inhibits all12");
  }else if(scenario!="clean"&&scenario!="missed_steps")throw std::invalid_argument("unknown scenario");
  if(scenario=="clean"||scenario=="missed_steps"){
   rig.exchange(frames::disarm,"disarm");rig.advance(1200);
   check(!rig.rtl.fault_word&&rig.rtl.armed_mask==0&&rig.rtl.pos_continuity==all_joints,"clean actual pulse drain preserves continuity");
  }else{
   check(rig.rtl.enable_n==all_joints&&rig.rtl.pos_continuity==0,"fault loses continuity and disables actual outputs");
   check(rig.inhibit_observed_cycle>rig.fault_injection_cycle &&
         rig.inhibit_observed_cycle-rig.fault_injection_cycle<=250001,"modeled motion inhibition within5ms; not a physical20ms guarantee");
   const auto before=rig.observed_rises;rig.external_permission=true;
   rig.fixture_present=rig.field_power=rig.sensor_power=true;
   Faults f;rig.plant.faults(f);rig.advance(20000);
   check(rig.observed_rises==before&&rig.rtl.armed_mask==0,"restoring a fault cannot automatically restart motion");
   rig.exchange(frames::fault_update,"post_fault_valid_update");rig.advance(20000);
   check(rig.observed_rises==before&&rig.rtl.armed_mask==0&&rig.rtl.fault_word,
         "a correctly encoded fresh UPDATE cannot restart faulted real motion");
  }
  rig.advance(2000);rig.exchange(frames::read,"stopped_feedback");
  for(unsigned i=0;i<12;++i){const auto&s=rig.plant.state()[i];
   check(s.observed_rises==rig.observed_rises[i],"separate output observer and plant count every actual rising edge");
   if(scenario!="missed_steps")check(s.lost_steps==0,"no fictitious lost mechanical steps in nominal ideal load");
  }
  if(scenario=="missed_steps")check(rig.plant.state()[0].lost_steps>10,"mechanical loss injection active independently of RTL step count");
  rig.write_state("state.json");
  std::cout<<"ACTUAL_SPI_EDGE_PLANT_PASS scenario="<<scenario<<" checks="<<checks
           <<" actual_FPGA_integration=1 actual_LinuxCNC_integration=0 physical_qualification=0\n";
 }catch(const std::exception&e){std::cerr<<"ACTUAL_SPI_EDGE_PLANT_FAIL "<<e.what()<<'\n';return 1;}
}
