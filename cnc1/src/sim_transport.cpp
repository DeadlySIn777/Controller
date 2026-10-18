#include "cnc1.h"
#include "Vcnc_endpoint.h"
#include "verilated.h"
#include <array>
#include <cstring>
#include <new>

struct Simulator {
    VerilatedContext context;
    Vcnc_endpoint rtl{&context};
    uint64_t ticks=0, next_cycle=0;
    unsigned inject=0, spindle=0, edge_ticks=10000, edge_count=0, phase=0;
    std::array<uint8_t,64> previous_rx{};
    std::array<uint8_t,64> previous_update{};
    bool have_rx=false;
    bool have_update=false;
    void tick() {
        if(spindle && ticks%edge_ticks==0) {
            phase=(phase+1)%4; edge_count++;
            static const unsigned ab[4]={0,1,3,2};
            rtl.enc_a=(ab[phase]>>1) | ((ab[(4-phase)%4]>>1)<<1);
            rtl.enc_b=(ab[phase]&1) | ((ab[(4-phase)%4]&1)<<1);
            rtl.enc_z=(edge_count%32==0)?3:0;
        }
        rtl.clk=0; rtl.eval(); context.timeInc(10);
        rtl.clk=1; rtl.eval(); context.timeInc(10); ticks++;
    }
    void advance(uint64_t count) { for(uint64_t i=0;i<count;i++) tick(); }
    void reset() {
        rtl.reset_n=0; rtl.inhibit_n=1; rtl.spi_cs_n=1; rtl.spi_sclk=0; rtl.spi_mosi=0;
        rtl.enc_a=0; rtl.enc_b=0; rtl.enc_z=0; advance(8);
        rtl.reset_n=1; advance(16); next_cycle=ticks; have_rx=false; have_update=false;
    }
};
extern "C" void *cnc1_sim_create() {
    auto *s=new(std::nothrow) Simulator(); if(s) s->reset(); return s;
}
extern "C" void cnc1_sim_destroy(void *p) { delete static_cast<Simulator *>(p); }
extern "C" void cnc1_sim_advance(void *p,uint32_t ticks) { static_cast<Simulator *>(p)->advance(ticks); }
extern "C" void cnc1_sim_reset(void *p) { static_cast<Simulator *>(p)->reset(); }
extern "C" void cnc1_sim_inject(void *p,unsigned mode) { static_cast<Simulator *>(p)->inject=mode; }
extern "C" void cnc1_sim_spindle(void *p,unsigned on,unsigned interval) {
    auto *s=static_cast<Simulator *>(p); s->spindle=on; s->edge_ticks=interval>=8?interval:8;
}
extern "C" uint64_t cnc1_sim_ticks(void *p) {return static_cast<Simulator *>(p)->ticks;}
extern "C" unsigned cnc1_sim_permission(void *p) {return static_cast<Simulator *>(p)->rtl.motion_enable;}
extern "C" unsigned cnc1_sim_progress(void *p) {return static_cast<Simulator *>(p)->rtl.progress_wdi;}
extern "C" void cnc1_sim_cycle(void *p,uint64_t period) {
    if(!period || period>10000000) return; // Reject invalid periods without an unbounded loop.
    auto *s=static_cast<Simulator *>(p); s->next_cycle+=period/20;
    if(s->next_cycle>s->ticks) s->advance(s->next_cycle-s->ticks);
}
extern "C" int cnc1_sim_exchange(void *p,const uint8_t input[64],uint8_t rx[64]) {
    auto *s=static_cast<Simulator *>(p);
    if(s->inject==1) return -1; // Link removed; simulated core still advances each cycle.
    uint8_t tx[64]; std::memcpy(tx,input,64); std::memset(rx,0,64);
    if(input[5]==3) {
        if(s->inject==8 && s->have_update) std::memcpy(tx,s->previous_update.data(),64);
        else {std::memcpy(s->previous_update.data(),input,64); s->have_update=true;}
    }
    if(s->inject==2 && tx[5]==3) tx[25]^=1; // Wire CRC corruption on UPDATE.
    if(s->inject==5 && tx[5]==3) { // Correct CRC, wrong command session.
        tx[8]^=1; uint16_t crc=cnc1_crc(tx,62); tx[62]=(uint8_t)(crc>>8); tx[63]=(uint8_t)crc;
    }
    if(s->inject==6 && tx[5]==3) { // Truncated UPDATE.
        s->rtl.spi_cs_n=0; s->advance(8); s->rtl.spi_cs_n=1; s->advance(10); return -1;
    }
    s->rtl.spi_cs_n=0; s->rtl.spi_sclk=0; s->advance(8);
    for(unsigned bit=0;bit<512;bit++) {
        s->rtl.spi_mosi=(tx[bit/8]>>(7-bit%8))&1;
        s->advance(4); s->rtl.spi_sclk=1; s->rtl.eval();
        rx[bit/8]=(uint8_t)((rx[bit/8]<<1)|(s->rtl.spi_miso&1));
        s->advance(4); s->rtl.spi_sclk=0; s->rtl.eval();
    }
    s->advance(8); s->rtl.spi_cs_n=1; s->rtl.spi_mosi=0; s->advance(10);
    if(s->inject==3) rx[25]^=1; // Return-path CRC corruption.
    if(s->inject==7 && !std::memcmp(rx,"CNS1",4)) { // Valid CRC, impossible count discontinuity.
        rx[20]^=0x40; uint16_t crc=cnc1_crc(rx,62); rx[62]=(uint8_t)(crc>>8); rx[63]=(uint8_t)crc;
    }
    if(s->inject==4 && s->have_rx) std::memcpy(rx,s->previous_rx.data(),64); // Old valid snapshot.
    else {std::memcpy(s->previous_rx.data(),rx,64); s->have_rx=true;}
    return 0;
}
