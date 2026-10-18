#include "Vcnc3_runtime_sim.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static unsigned checks=0;
static void need(bool value,const char* message){++checks;if(!value)throw std::runtime_error(message);}
static void be16(std::vector<uint8_t>&v,unsigned p,uint16_t x){v[p]=x>>8;v[p+1]=x;}
static void be32(std::vector<uint8_t>&v,unsigned p,uint32_t x){for(int i=0;i<4;++i)v[p+i]=x>>(24-8*i);}
static uint16_t u16(const std::vector<uint8_t>&v,unsigned p){return(v[p]<<8)|v[p+1];}
static uint32_t u24(const std::vector<uint8_t>&v,unsigned p){return(uint32_t(v[p])<<16)|(v[p+1]<<8)|v[p+2];}
static uint32_t u32(const std::vector<uint8_t>&v,unsigned p){return(uint32_t(v[p])<<24)|(uint32_t(v[p+1])<<16)|(v[p+2]<<8)|v[p+3];}
static uint16_t crc(const std::vector<uint8_t>&v,unsigned n){uint16_t c=0xffff;for(unsigned i=0;i<n;++i){c^=uint16_t(v[i])<<8;for(int b=0;b<8;++b)c=(c&0x8000)?(c<<1)^0x1021:c<<1;}return c;}
static constexpr uint32_t hash=0x12345678,session=0x11223344;
static std::vector<uint8_t> frame(bool fb,uint8_t op,uint32_t seq=0,uint16_t mask=0,uint32_t sess=session){
 std::vector<uint8_t> f(fb?176:96);be32(f,0,0x434e4333);f[4]=3;f[5]=op;be16(f,6,mask);be32(f,8,sess);be32(f,12,seq);return f;
}
struct Rig{
 VerilatedContext context;Vcnc3_runtime_sim r{&context};uint64_t cycles=0;uint32_t sample=0,seq=0;
 bool heartbeat=true,apply_outputs=true,output_gate_present=true,output_latch_present=true;
 bool output_opi=false;uint8_t opi=0;uint16_t last_step=0;std::array<unsigned,12> rises{};
 Rig(){
  r.rst_n=0;r.spi_cs_fb_n=r.spi_cs_cmd_n=1;r.spi_sclk=r.spi_mosi=0;
  r.sim_context=1;r.sim_expected_session=session;r.sim_expected_config_hash=hash;
  r.provider_tag=0x53494d32;r.provider_abi=1;r.provider_session=session;r.provider_config_hash=hash;
  r.provider_valid_mask=31;r.provider_faults=0;r.di_raw=0xa55aa5;r.do_fault=0;
  r.probe_raw=r.home_raw=r.limit_low_raw=r.limit_high_raw=0;
  r.encoder_a=r.encoder_b=r.encoder_z=0;r.encoder_port_valid=15;r.alarm_current_raw=0;
  r.inhibit_n=r.wd_m_ok=r.wd_o_ok=r.reset_arm_ready=r.contactor_deenergized=r.sto_arm_expected=1;
  r.reset_arm_held=0;r.external_fault_word=0;r.physical_safety_power_word=0;
  advance(8);r.rst_n=1;sample=0;cycles=0;advance(2500);
  need(r.sim_ready,"provider initialized");need(!r.physical_authority&&!r.production_profile_complete,"no physical authority");
 }
 void tick(){
  r.provider_strobe=heartbeat&&cycles%5000==0;
  if(r.provider_strobe){r.provider_sequence=++sample;r.do_applied=apply_outputs?r.dout_request:0;}
  bool gate=r.inhibit_n&&r.wd_m_ok&&r.motion_request;
  r.gate_high=gate?15:0;if(!gate)opi=0;else opi|=r.opi_rearm;r.opi_ok=opi;
  r.output_gate_high=output_gate_present&&r.output_request&&r.selftest_state==0&&r.inhibit_n&&r.wd_o_ok;
  if(!r.output_gate_high)output_opi=false;else if(output_latch_present&&r.output_opi_rearm)output_opi=true;
  r.output_opi_ok=output_opi;
  r.clk=0;r.eval();context.timeInc(10);r.clk=1;r.eval();context.timeInc(10);
  uint16_t edges=r.step_out&~last_step;last_step=r.step_out;
  for(unsigned i=0;i<12;++i)if(edges&(1u<<i))++rises[i];++cycles;
 }
 void advance(uint64_t n){while(n--)tick();}
 std::vector<uint8_t> xfer(std::vector<uint8_t> f,bool corrupt=false,unsigned omit=0){
  bool fb=f.size()==176;be16(f,f.size()-2,crc(f,f.size()-2));if(corrupt)f.back()^=1;
  advance(12);r.spi_sclk=0;if(fb)r.spi_cs_fb_n=0;else r.spi_cs_cmd_n=0;advance(8);
  std::vector<uint8_t> out(f.size());
  for(unsigned bit=0;bit<(f.size()-omit)*8;++bit){r.spi_mosi=(f[bit/8]>>(7-bit%8))&1;advance(4);r.spi_sclk=1;r.eval();out[bit/8]=(out[bit/8]<<1)|(r.spi_miso&1);advance(4);r.spi_sclk=0;r.eval();}
  advance(8);r.spi_cs_fb_n=r.spi_cs_cmd_n=1;advance(12);
  need(!r.spi_miso_oe,"MISO released");if(!omit)need(u16(out,out.size()-2)==crc(out,out.size()-2),"response CRC exact");return out;
 }
 std::vector<uint8_t> read(uint8_t ack=0){auto f=frame(true,16);f[16]=ack;return xfer(f);}
 void commission(bool expect_output=true){
  auto c=frame(true,6,0,0,0);c[16]=2;c[17]=0;be16(c,18,4095);be16(c,20,4095);
  for(unsigned i=0;i<48;++i)be16(c,24+2*i,100);be32(c,120,hash);be16(c,124,1000);be16(c,128,15);
  xfer(c);need(r.config_valid,"SIM2 class0 CONFIGURE");
  xfer(frame(false,1));need(r.session==session&&!r.fault_word,"SYNC");
  auto p=frame(true,7,++seq);p[16]=1;p[17]=p[23]=1;
  p[19]=0;p[20]=1;p[21]=16;p[22]=17;p[25]=2;p[26]=3;p[27]=18;p[28]=19;
  be16(p,31,100);be16(p,35,100);be32(p,37,50);be32(p,44,50);
  p[55]=1;be16(p,56,5000);be16(p,58,50);be16(p,60,5000);be16(p,62,100);be16(p,64,100);be16(p,66,100);be16(p,68,100);
  xfer(p);need(!r.fault_word,"probe configuration accepted");
  p=frame(true,7,++seq);be16(p,23,65535);be32(p,26,hash);be16(p,30,440);be16(p,32,440);xfer(p);need(!r.fault_word,"I/O config committed");
  for(unsigned which=1;which<=2;++which){auto t=frame(false,13,++seq);t[16]=which;xfer(t);need(r.selftest_state==(which==1?1:3),"selftest actual start");advance(500000);if(which==1)r.wd_m_ok=0;else r.wd_o_ok=0;advance(10);if(which==1)r.wd_m_ok=1;else r.wd_o_ok=1;advance(10);need(!r.fault_word,"timed selftest passed");}
  need(r.selftest_passed==3,"both watchdog observations");
  xfer(frame(false,14,++seq,4095));xfer(frame(false,10,++seq));need(!r.fault_word&&r.output_request,"I/O enabled");
  if(!expect_output){advance(600);need(r.fault_word!=0,"missing output gate/OPI refuses within bound");stopped();return;}
  advance(20);need(r.output_opi_ok&&!r.physical_authority,"independent output OPI rearmed");
  xfer(frame(false,2,++seq,4095));advance(20);need(r.armed_mask==4095&&!r.fault_word,"twelve actual channels armed");
 }
 void update(uint16_t outputs=0,uint8_t indexes=0,uint8_t probes=0,bool corrupt=false){
  auto f=frame(false,3,++seq,4095);for(unsigned i=0;i<12;++i)be32(f,16+4*i,(i&1)?uint32_t(-1000000):1000000);
  be16(f,64,outputs);be16(f,68,indexes);f[70]=probes;xfer(f,corrupt);
 }
 void stopped(){need(r.enable_n==4095&&r.step_out==0&&r.dout_request==0,"all modeled actuation inhibited");}
};
int main(){try{
 {Rig q;auto p=frame(true,5,0,0,0);q.xfer(p);auto cap=q.read();need(u32(cap,0)==0x43415033&&u32(cap,68)==0x53494d32&&u32(cap,64)==0xd3494d32,"actual SIM2 CAP3");need(cap[7]==12&&cap[10]==4&&u32(cap,12)==0x17fff,"implemented capability inventory");}
 {Rig q;q.commission();q.update(0xa55a,15,3);q.advance(40000);auto f=q.read();need(u16(f,140)==0xa55a,"actual applied sixteen DO feedback");need(f[136]==0xa5&&f[137]==0x5a&&f[138]==0xa5&&f[139]<44,"actual 24DI fresh");for(auto n:q.rises)need(n>0,"all twelve emitted step lanes");
  q.r.encoder_b=15;q.advance(8);q.r.encoder_a=15;q.advance(8);q.r.encoder_b=0;q.advance(8);q.r.encoder_a=0;q.advance(8);
  q.r.encoder_z=15;q.r.probe_raw=3;q.advance(20);f=q.read();need(u16(f,114)==0,"four index one-shots fired");need((f[120]&0x30)==0,"two probe one-shots fired");need((f[121]&127)==6,"six simultaneous captures retained");
  for(unsigned i=0;i<6;++i){auto e=q.xfer(frame(false,0));need(e[36]!=0,"event present");need(e[37]==(i<2?1:2),"probe/index event type");need(e[38]==(i<2?i:i-2),"event source");
   if(i<2)need(u24(e,50)==4&&u24(e,53)==4,"probe simultaneous actual encoder values");else need(u24(e,44)==4&&u24(e,47)==0,"index actual count capture");
   q.read(uint8_t(e[36]+1));auto same=q.xfer(frame(false,0));need(same[36]==e[36],"wrong acknowledgment cannot pop");q.read(e[36]);q.update(0xa55a,15,3);}
  f=q.read();need((f[121]&127)==0,"exact delivered event acknowledgments drain");
  for(uint16_t pattern:{uint16_t(0x5aa5),uint16_t(0xffff),uint16_t(0)}){q.update(pattern,15,3);q.advance(6000);f=q.read();need(u16(f,140)==pattern,"every output can apply on and off");}
 }
 {Rig q;q.commission();q.update(65535);q.heartbeat=false;q.advance(23000);need(q.r.provider_error,"stale provider latches");q.stopped();q.heartbeat=true;q.advance(10000);q.stopped();}
 {Rig q;q.commission();q.update(3);q.r.provider_tag=0;q.advance(5001);need(q.r.provider_error,"wrong provider identity rejected");q.stopped();}
 {Rig q;q.commission();q.update(3);q.sample-=1;q.advance(5001);need(q.r.provider_error,"replayed provider sequence rejected");q.stopped();}
 {Rig q;q.commission();q.update(3);q.r.sim_expected_config_hash^=1;q.advance(2);need(q.r.provider_error,"configuration context change rejected");q.stopped();}
 {Rig q;q.commission();q.update(3);q.r.limit_high_raw=1;q.advance(5010);need(q.r.fault_word!=0,"actual modeled limit stops motion");q.stopped();}
 {Rig q;q.commission();q.update(3);q.r.do_fault=1;q.advance(5010);need(q.r.fault_word!=0,"actual output driver fault inhibits");q.stopped();}
 {Rig q;q.output_gate_present=false;q.commission(false);}
 {Rig q;q.output_latch_present=false;q.commission(false);}
 {Rig q;q.commission();q.update(3);q.output_gate_present=false;q.advance(2);need(q.r.fault_word!=0,"independent output gate loss inhibits");q.stopped();}
 {Rig q;q.commission();q.apply_outputs=false;q.update(3);q.advance(50010);need(q.r.fault_word!=0,"persistent output readback mismatch inhibits");q.stopped();}
 {Rig q;q.commission();auto f=frame(false,3,++q.seq,4095);be32(f,16,0x01000001);q.xfer(f);need(q.r.fault_word!=0,"unchanged global DDS limit enforced");q.stopped();}
 {Rig q;q.commission();auto f=frame(false,3,++q.seq,4095);be32(f,16,1000000);q.xfer(f,false,1);need(q.r.fault_word!=0,"truncated frame cannot commit");q.stopped();}
 {Rig q;q.commission();q.update(3,true,true,true);need(q.r.fault_word!=0,"CRC-corrupted whole update rejected");q.stopped();}
 {Rig q;q.commission();q.update(3);q.advance(250001);need(q.r.fault_word!=0,"watchdog has no provider-heartbeat bypass");q.stopped();}
 std::cout<<"SIM2_RUNTIME_PASS checks="<<checks<<" actual_SPI96_176=1 physical_authority=0\n";return 0;
 }catch(const std::exception&e){std::cerr<<"SIM2_RUNTIME_FAIL checks="<<checks<<" "<<e.what()<<"\n";return 1;}}
