/* Disconnected functional RTL fixture only. No target devices or real-time
 * performance claim. Frames and the incomplete-profile guard are unchanged.
 * SPI bytes are shifted across actual pins; responses are never synthesized. */
#include "rtl_transport.h"
#include "Vcnc3_motion_spi.h"
#include "verilated.h"
#include <array>
#include <cstring>
#include <new>

struct Fixture {
    VerilatedContext context;
    Vcnc3_motion_spi rtl{&context};
    uint64_t ticks=0;
    std::array<uint32_t,22> metrics{};
    uint16_t previous_step=0;
    bool corrupt=false;
    Fixture() {
        rtl.rst_n=0; rtl.spi_cs_fb_n=rtl.spi_cs_cmd_n=1;
        rtl.spi_sclk=rtl.spi_mosi=0;
        /* Even requesting ideal external qualification cannot override the
         * source's constant-false full-profile completion guard. */
        rtl.qualification_complete=1; rtl.installed_input=0xfff;
        rtl.installed_module_class=0; rtl.inhibit_n=rtl.wd_m_ok=rtl.wd_o_ok=1;
        rtl.reset_arm_ready=1; rtl.reset_arm_held=0;
        rtl.contactor_deenergized=rtl.sto_arm_expected=1;
        rtl.motion_critical_ports_valid=1; rtl.gate_high=rtl.opi_ok=0;
        rtl.alarm_current_raw=rtl.encoder_a=rtl.encoder_b=rtl.encoder_z=0;
        rtl.encoder_installed=rtl.encoder_port_valid=15;
        rtl.external_fault_word=0; rtl.motion_critical_io_fault=0;
        for(unsigned i=0;i<44;++i)rtl.provider_feedback[i]=0;
        for(unsigned i=0;i<24;++i)rtl.provider_status[i]=0;
        rtl.physical_safety_power_word=0;
        advance(8); rtl.rst_n=1; advance(2300);
    }
    void tick() {
        rtl.clk=0;rtl.eval();context.timeInc(10);
        rtl.clk=1;rtl.eval();context.timeInc(10);++ticks;
        uint16_t rises=static_cast<uint16_t>(rtl.step_out & ~previous_step);
        previous_step=rtl.step_out;
        for(unsigned i=0;i<12;++i)if(rises&(1u<<i))++metrics[10+i];
    }
    void advance(uint64_t n) {while(n--)tick();}
};
extern "C" void *rev_a_sim_create(void) {try{return new Fixture;}catch(...){return nullptr;}}
extern "C" void rev_a_sim_destroy(void *p){delete static_cast<Fixture*>(p);}
extern "C" void rev_a_sim_advance(void*p,uint64_t n){static_cast<Fixture*>(p)->advance(n);}
extern "C" uint64_t rev_a_sim_ticks(void*p){return static_cast<Fixture*>(p)->ticks;}
extern "C" void rev_a_sim_corrupt(void*p,int value){static_cast<Fixture*>(p)->corrupt=value!=0;}
extern "C" uint32_t rev_a_sim_metric(void*p,unsigned metric){
    auto&f=*static_cast<Fixture*>(p);
    if(metric==5)return static_cast<uint32_t>((~f.rtl.enable_n)&0xfff);
    if(metric==6)return f.rtl.armed_mask;
    if(metric==7)return f.rtl.session;
    if(metric==8)return static_cast<uint32_t>(f.rtl.motion_request|f.rtl.output_request|f.rtl.permit_out_req);
    return metric<f.metrics.size()?f.metrics[metric]:0;
}
extern "C" int rev_a_sim_exchange(void*p,enum cnc3_cs cs,const uint8_t*tx,uint8_t*rx,size_t n){
    auto&f=*static_cast<Fixture*>(p);
    if(!tx||!rx||(cs!=CNC3_CS_FB&&cs!=CNC3_CS_CMD)||n!=(cs==CNC3_CS_FB?176u:96u)){
        ++f.metrics[9];return -1;
    }
    ++f.metrics[0];
    if(cs==CNC3_CS_CMD&&tx[5]==CNC3_OP_ARM)++f.metrics[2];
    if(cs==CNC3_CS_CMD&&tx[5]==CNC3_OP_UPDATE)++f.metrics[3];
    if(cs==CNC3_CS_FB&&tx[5]==CNC3_OP_CONFIGURE)++f.metrics[4];
    std::memset(rx,0,n);
    f.advance(12);f.rtl.spi_sclk=0;
    if(cs==CNC3_CS_FB)f.rtl.spi_cs_fb_n=0;else f.rtl.spi_cs_cmd_n=0;
    f.advance(8);
    for(size_t bit=0;bit<n*8;++bit){
        f.rtl.spi_mosi=(tx[bit/8]>>(7-bit%8))&1;
        f.advance(4);f.rtl.spi_sclk=1;f.rtl.eval();
        rx[bit/8]=static_cast<uint8_t>((rx[bit/8]<<1)|(f.rtl.spi_miso&1));
        f.advance(4);f.rtl.spi_sclk=0;f.rtl.eval();
    }
    f.advance(8);f.rtl.spi_cs_fb_n=f.rtl.spi_cs_cmd_n=1;
    f.rtl.spi_mosi=0;f.advance(12);
    if(f.rtl.spi_miso_oe){++f.metrics[9];return -1;}
    if(n==176&&!std::memcmp(rx,"CAP3",4)){
        cnc3_caps caps{};
        if(cnc3_decode_cap3_page0(rx,n,&caps)!=CNC3_VALID){++f.metrics[9];return -1;}
        ++f.metrics[1];
    }
    if(f.corrupt)rx[n-1]^=1; /* Actual returned frame; explicit host-side CRC fault. */
    return 0;
}
