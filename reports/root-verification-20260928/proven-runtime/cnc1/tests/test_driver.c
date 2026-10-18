#include "cnc1.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define CHECK(expr,msg) do {checks++; if(!(expr)) {fprintf(stderr,"FAIL %s line %d state=%d fault=%d\n",msg,__LINE__,d.state,d.fault);exit(1);} printf("PASS %s\n",msg);} while(0)
static unsigned checks;
static uint64_t now;
static struct cnc1_driver d;
static void cycle(void) {
    now+=1000000; cnc1_sim_cycle(d.transport.context,1000000);
    cnc1_read(&d,now); cnc1_write(&d,now+1000,1000000);
}
static void fresh(void) {
    if(d.transport.context) cnc1_sim_destroy(d.transport.context);
    void *s=cnc1_sim_create(); struct cnc1_transport t={s,cnc1_sim_exchange};
    cnc1_init(&d,t,0x10001000); now=0; cycle(); cycle(); cycle();
    CHECK(d.discovered && d.state==CNC1_OFF,"actual RTL discovery");
    CHECK(d.caps.steps==6 && d.caps.encoders==2 && d.caps.frequencies==0 && d.caps.features==31,"fitted capabilities are six/two/no frequency");
    CHECK(!cnc1_sim_permission(s),"discovery never arms");
    d.reset=1; cycle(); d.reset=0; cycle();
    CHECK(d.state==CNC1_READY && !cnc1_sim_permission(s),"explicit stopped SYNC acknowledged");
}
static void arm(void) {
    d.enable=1; cycle();
    CHECK(d.state==CNC1_WAIT_ARM && d.sent_opcode==2,"ARM dispatch waits for later acknowledgment");
    cycle(); CHECK(d.state==CNC1_ACTIVE && cnc1_sim_permission(d.transport.context),"zero-speed ARM acknowledgment");
}
static void fix_crc(uint8_t frame[64]) {
    uint16_t crc=cnc1_crc(frame,62); frame[62]=(uint8_t)(crc>>8); frame[63]=(uint8_t)crc;
}
static void put32(uint8_t *p,uint32_t value) {
    p[0]=(uint8_t)(value>>24);p[1]=(uint8_t)(value>>16);p[2]=(uint8_t)(value>>8);p[3]=(uint8_t)value;
}
static int fixture_exchange(void *context,const uint8_t tx[64],uint8_t rx[64]) {
    (void)tx; memcpy(rx,context,64); return 0;
}
static void fault_case(unsigned mode,const char *name) {
    fresh(); arm(); d.position_cmd[0]=0.05; cycle();
    cnc1_sim_inject(d.transport.context,mode); cycle(); cycle();
    CHECK(d.state==CNC1_FAULT,name);
    for(unsigned i=0;i<7;i++) cycle();
    CHECK(!cnc1_sim_permission(d.transport.context),"RTL permission gone after fault/watchdog");
    cnc1_sim_inject(d.transport.context,0); for(unsigned i=0;i<3;i++) cycle();
    CHECK(d.state==CNC1_FAULT && !cnc1_sim_permission(d.transport.context),"link return with enable held high cannot rearm");
    d.enable=0; d.reset=1; cycle(); d.reset=0; cycle();
    CHECK(d.state==CNC1_READY && !cnc1_sim_permission(d.transport.context),"fault recovery requires explicit stopped fresh-session SYNC");
}
int main(void) {
    fresh();
    uint8_t tx[64],rx[64],caps_frame[64]; struct cnc1_caps parsed;
    cnc1_command(tx,5,0,0,0,0); cnc1_sim_exchange(d.transport.context,tx,rx);
    cnc1_command(tx,0,0,0,0,0); cnc1_sim_exchange(d.transport.context,tx,caps_frame);
    CHECK(!cnc1_decode_caps(caps_frame,&parsed),"capability page decoded from actual RTL");
    const unsigned changed[]={4,5,6,7,11,32,62};
    for(unsigned i=0;i<sizeof(changed)/sizeof(changed[0]);i++) {
        memcpy(rx,caps_frame,64); rx[changed[i]]^=1;
        if(changed[i]!=62) fix_crc(rx);
        CHECK(cnc1_decode_caps(rx,&parsed)!=0,"capability version/count/function/reserved/CRC mismatch rejected");
    }
    CHECK(cnc1_crc((const uint8_t *)"123456789",9)==0x29b1,"CRC independent known-answer");
    CHECK(cnc1_counter_delta(2,0xfffffffeu)==4 && cnc1_counter_delta(0xfffffffeu,2)==-4,"signed counter wrap both directions");
    CHECK(cnc1_unwrap_index(INT64_C(4294967298),2,0xfffffffeu)==INT64_C(4294967294) &&
          cnc1_unwrap_index(INT64_C(-2147483650),0x7ffffffeu,0x80000002u)==INT64_C(-2147483646),
          "index and continuous count share epoch across unsigned and signed boundaries");
    int32_t rate;
    CHECK(!cnc1_rate(1000,&d.caps,&rate) && rate==85899,"rate scaling rounds bounded DDS units");
    CHECK(cnc1_rate(NAN,&d.caps,&rate) && cnc1_rate(200000,&d.caps,&rate),"nonfinite and excessive rates rejected");
    arm();
    for(unsigned i=0;i<6;i++) d.position_cmd[i]=(i+1)*0.01*(i%2?-1:1);
    for(unsigned i=0;i<8;i++) cycle();
    for(unsigned i=0;i<6;i++) CHECK(fabs(d.position_fb[i]-d.position_cmd[i])<=0.0051,"all six signed commands return scaled emitted-count feedback");
    CHECK(d.status.sequence==d.sequence-1,"read snapshot acknowledges preceding write");
    cnc1_sim_spindle(d.transport.context,1,10000);
    int64_t before=d.encoders[0]; for(unsigned i=0;i<10;i++) cycle(); int64_t slow=d.encoders[0]-before;
    cnc1_sim_spindle(d.transport.context,1,2500); before=d.encoders[0];
    for(unsigned i=0;i<10;i++) cycle();
    int64_t fast=d.encoders[0]-before;
    CHECK(fast>slow*3 && slow>30,"varying simulated AB transitions traverse actual RTL counters");
    CHECK(d.encoders[1]<0 && (d.status.encoder_flags&3)==3 && d.status.indexes[0]!=0,"reverse ABZ and index latches return through protocol");
    CHECK(d.encoder_position[0]==(double)d.encoders[0]/400 && d.encoder_position[1]<0,
          "encoder counts scaled to signed revolutions");
    d.enable=0; cycle(); cycle(); CHECK(d.state==CNC1_READY && !d.status.enabled,"DISARM acknowledgment");
    fault_case(1,"missing transport response faults driver");
    fault_case(2,"wire-corrupted UPDATE faults actual endpoint");
    fault_case(3,"corrupt response rejected by common decoder");
    fault_case(4,"stale valid response rejected");
    fault_case(5,"wrong-session UPDATE rejected by actual endpoint");
    fault_case(6,"truncated UPDATE cannot become motion");
    fault_case(7,"impossible emitted counter discontinuity rejected");
    fault_case(8,"duplicate old UPDATE rejected by actual RTL sequence validation");
    fresh(); arm(); cnc1_read(&d,now); cnc1_write(&d,now+6000000,1000000);
    CHECK(d.state==CNC1_FAULT && d.fault==CNC1_TIME,"stale host sample prevents write");
    fresh(); arm(); cnc1_read(&d,now+6000000);
    CHECK(d.state==CNC1_FAULT && d.fault==CNC1_TIME,"host scheduling gap checked before refreshing sample timestamp");
    fresh(); arm(); d.sequence=0xfffffffeu; cnc1_write(&d,now,1000000);
    CHECK(d.state==CNC1_FAULT && d.fault==CNC1_SEQUENCE,"sequence exhaustion never wraps or silently changes session");
    fresh(); arm(); cnc1_sim_reset(d.transport.context); cycle();
    CHECK(d.state==CNC1_FAULT,"FPGA reset cannot be mistaken for continued session");
    cnc1_init(&d,d.transport,0x31415926); cnc1_sim_inject(d.transport.context,3); cycle();
    CHECK(d.state==CNC1_FAULT && !d.discovered,"discovery failure remains disarmed");
    cnc1_sim_inject(d.transport.context,0); d.reset=1; cycle(); d.reset=0;
    cycle(); cycle(); cycle();
    CHECK(d.state==CNC1_OFF && d.discovered && !cnc1_sim_permission(d.transport.context),"explicit stopped retry rediscovers after discovery failure without arm");
    fresh(); arm(); d.position_cmd[0]=0.1; cycle(); cycle(); cycle();
    uint64_t writes=d.writes; double feedback=d.position_fb[0]; d.scale[0]=300;
    cycle();
    CHECK(d.state==CNC1_FAULT && d.fault==CNC1_CONFIG && d.writes==writes && d.position_fb[0]==feedback,
          "changing scale with fixed position cannot issue new motion or rescale feedback");
    fresh(); arm(); writes=d.writes; d.axis_mask=7; cycle();
    CHECK(d.state==CNC1_FAULT && d.fault==CNC1_CONFIG && d.writes==writes,"armed mask mutation rejected before any command");
    fresh();
    double scales[6]={250,200,200,200,200,200};
    uint32_t epoch=d.runtime_epoch, session=d.session;
    CHECK(cnc1_configure(&d,1,session,0,epoch+1,scales)==2 && !d.config_locked,"stale runtime epoch cannot acquire configuration inhibit");
    CHECK(cnc1_configure(&d,1,session+1,0,epoch,scales)==2,"wrong session cannot configure");
    CHECK(cnc1_configure(&d,2,session,0,epoch,scales)==1,"commit cannot bypass acquired inhibit");
    CHECK(!cnc1_configure(&d,1,session,0,epoch,scales) && d.config_locked,"stopped guard acquires inhibit");
    scales[0]=NAN;
    CHECK(cnc1_configure(&d,2,session,0,epoch,scales)==3 && d.scale[0]==200,"invalid staged scale cannot partially apply");
    scales[0]=250;
    CHECK(!cnc1_configure(&d,2,session,0,epoch,scales) && d.scale[0]==250 && d.config_revision==1,"stopped scales commit under inhibit");
    CHECK(cnc1_configure(&d,2,session,0,epoch,scales)==2,"same preview revision cannot replay");
    CHECK(!cnc1_sim_permission(d.transport.context) && d.config_locked,"commit cannot authorize motion");
    CHECK(!cnc1_configure(&d,3,session,1,epoch,scales) && !d.config_locked,"explicit release preserves stopped state");
    arm();
    CHECK(cnc1_configure(&d,1,d.session,1,d.runtime_epoch,scales)==1,"enabled driver rejects configuration at compiled boundary");
    fresh(); epoch=d.runtime_epoch;
    CHECK(!cnc1_configure(&d,1,d.session,0,epoch,scales),"acquire inhibit for attempted-enable race");
    d.enable=1; cycle();
    CHECK(d.state==CNC1_FAULT && d.fault==CNC1_CONFIG && !cnc1_sim_permission(d.transport.context),"enable racing acquired configuration faults without ARM");
    fresh(); d.persistence_required=1;d.persistence_pending=1;d.config_locked=1;
    uint32_t hash[8]={1,2,3,4,5,6,7,8};
    CHECK(cnc1_configure(&d,3,d.session,0,d.runtime_epoch,scales)==5 && d.config_locked,"ordinary release cannot bypass persistent startup gate");
    d.reset=1;cycle();d.reset=0;cycle();
    CHECK(d.persistence_pending && d.config_locked && d.state==CNC1_READY,"driver reset preserves persistent gate");
    CHECK(!cnc1_persistence_commit(&d,d.session,0,d.runtime_epoch,1,hash) && !d.persistence_pending && d.config_locked,"durable acknowledgment records identity but does not release inhibit");
    CHECK(!cnc1_configure(&d,3,d.session,0,d.runtime_epoch,scales),"persistent committed gate can release while still stopped");
    CHECK(cnc1_configure(&d,2,d.session,0,d.runtime_epoch,scales)==1,"unlocked durable runtime cannot mutate scales");
    CHECK(!cnc1_configure(&d,4,d.session,0,d.runtime_epoch,scales) && d.persistence_pending && d.config_locked,"new persistent transaction reacquires pending inhibit");
    hash[0]=9;
    CHECK(cnc1_persistence_commit(&d,d.session,0,d.runtime_epoch,1,hash)==3,"same durable generation with different hash cannot acknowledge");
    CHECK(cnc1_persistence_commit(&d,d.session,0,d.runtime_epoch,0,hash)==3,"zero or older durable generation cannot acknowledge");
    CHECK(!cnc1_persistence_commit(&d,d.session,0,d.runtime_epoch,2,hash),"new durable generation can acknowledge while stopped");
    /* A CRC-correct synthetic frame drives boundary values impossible to reach
     * economically in a short 50 MHz RTL run. This is common-code unit evidence. */
    struct cnc1_driver wrap;
    memset(rx,0,64); memcpy(rx,"CNS1",4); rx[4]=2;rx[5]=3;rx[6]=63;
    put32(rx+8,123);put32(rx+12,1);put32(rx+16,0x200);
    put32(rx+20,0xfffffff4u);put32(rx+44,2);put32(rx+52,0xfffffffeu);fix_crc(rx);
    struct cnc1_transport fixture={rx,fixture_exchange}; cnc1_init(&wrap,fixture,123);
    wrap.caps=d.caps;wrap.discovered=1;wrap.state=CNC1_ACTIVE;wrap.sequence=1;
    wrap.have_sample=1;wrap.previous_time=0xfffffe00u;wrap.previous_steps[0]=0xfffffff0u;
    wrap.steps[0]=INT64_C(4294967280);wrap.previous_encoders[0]=0xfffffffeu;wrap.encoders[0]=INT64_C(4294967294);
    cnc1_read(&wrap,1000000);
    CHECK(wrap.state==CNC1_ACTIVE && wrap.feedback_valid && wrap.steps[0]==INT64_C(4294967284) &&
          wrap.encoders[0]==INT64_C(4294967298) && wrap.indexes[0]==INT64_C(4294967294),
          "CRC-valid frame fixture proves timestamp/counter/index epoch wrap handling");
    cnc1_read(&wrap,2000000);
    CHECK(wrap.state==CNC1_FAULT && wrap.fault==CNC1_TIME && !wrap.feedback_valid,
          "identical timestamp invalidates feedback and preserves first cause");
    uint64_t ticks=cnc1_sim_ticks(d.transport.context);cnc1_sim_cycle(d.transport.context,UINT64_MAX);
    CHECK(cnc1_sim_ticks(d.transport.context)==ticks,"invalid simulation period cannot create unbounded clock work");
    cnc1_sim_destroy(d.transport.context);
    printf("CNC1_COMPILED_RTL_CHECKS=%u\n",checks); return 0;
}
