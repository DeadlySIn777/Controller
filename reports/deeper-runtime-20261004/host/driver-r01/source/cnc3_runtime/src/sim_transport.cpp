/* Only a disconnected Verilator backend exists. Every response byte comes
 * from actual shifted RTL SPI pins; the independent model observes STEP/DIR. */
#include "sim_transport.h"
#include "Vcnc3_runtime_sim.h"
#include "verilated.h"
#include "../providers/virtual_provider.hpp"
#include <cstring>
#include <algorithm>

static cnc3_sim::SimulationIdentity identity(const cnc3_sim_manifest&m){
    cnc3_sim::SimulationIdentity i;
    i.allow_disconnected_simulation=true;i.session=m.provider_session;
    i.config_hash=m.config.config_hash;i.source_id=m.source_id;
    std::copy(m.config_digest,m.config_digest+32,i.config_digest.begin());
    std::copy(m.source_digest,m.source_digest+32,i.source_digest.begin());return i;
}
static cnc3_sim::PlantConfig geometry(const cnc3_sim_manifest&m){
    cnc3_sim::PlantConfig p;p.reset_debounce=2500000;
    /* Explicit disconnected fixture starts two electrical steps before the
     * first authored encoder index. RTL emitted counters retain their own0
     * baseline; qualification compares deltas instead of inventing equality. */
    p.initial.fill(3198);
    std::copy(m.encoder_steps_per_revolution,m.encoder_steps_per_revolution+4,p.encoder_edges_per_rev.begin());
    std::copy(m.encoder_steps_per_revolution,m.encoder_steps_per_revolution+4,p.motor_steps_per_rev.begin());
    p.alarm_on_no_current=m.config.alarm_on_no_current;return p;
}
struct Fixture {
    VerilatedContext context;
    Vcnc3_runtime_sim rtl{&context};
    cnc3_sim::ProviderPlant plant;
    cnc3_sim_stats stats{};
    uint64_t next_cycle=0;
    uint16_t previous_step=0;
    uint32_t fault_flags=0;
    explicit Fixture(const cnc3_sim_manifest&m):plant(identity(m),geometry(m)){
        rtl.rst_n=0;rtl.spi_cs_fb_n=rtl.spi_cs_cmd_n=1;rtl.spi_sclk=rtl.spi_mosi=0;
        rtl.external_fault_word=0;rtl.physical_safety_power_word=0;
        /* Do not publish provider sequence1 into an endpoint held in reset.
         * The independent producer starts after reset release, so the actual
         * receiver observes its first immutable-lineage record exactly once. */
        for(unsigned i=0;i<8;++i){rtl.clk=0;rtl.eval();context.timeInc(10);rtl.clk=1;rtl.eval();context.timeInc(10);++stats.ticks;}
        rtl.rst_n=1;advance(2500);next_cycle=stats.ticks;
    }
    void tick(){
        auto inputs=plant.tick(stats.ticks,cnc3_sim::observe_outputs(rtl));
        cnc3_sim::drive_inputs(rtl,inputs);
        rtl.clk=0;rtl.eval();context.timeInc(10);
        rtl.clk=1;rtl.eval();context.timeInc(10);++stats.ticks;
        uint16_t rises=static_cast<uint16_t>(rtl.step_out&~previous_step);previous_step=rtl.step_out;
        for(unsigned i=0;i<12;++i)if(rises&(1u<<i)){
            ++stats.step_rises[i];stats.pin_step_count[i]+=(rtl.dir_out&(1u<<i))?-1:1;
        }
    }
    void advance(uint64_t n){while(n--)tick();}
};
extern "C" void*cnc3_sim_create(const cnc3_sim_manifest*m){
    if(!m)return nullptr;try{return new Fixture(*m);}catch(...){return nullptr;}
}
extern "C" void cnc3_sim_destroy(void*p){delete static_cast<Fixture*>(p);}
extern "C" uint64_t cnc3_sim_now_ns(void*p){return static_cast<Fixture*>(p)->stats.ticks*20u;}
extern "C" int cnc3_sim_cycle(void*p,uint64_t period){
    if(!p||period<250000u||period>2500000u)return -1;
    auto&f=*static_cast<Fixture*>(p);++f.stats.read_calls;
    f.next_cycle+=period/20u;
    if(f.stats.ticks<f.next_cycle)f.advance(f.next_cycle-f.stats.ticks);
    else f.next_cycle=f.stats.ticks;
    return 0;
}
extern "C" void cnc3_sim_reset_button(void*p,int pressed){static_cast<Fixture*>(p)->plant.set_reset_button(pressed!=0);}
extern "C" void cnc3_sim_inputs(void*p,uint32_t di,uint8_t probe){
    static_cast<Fixture*>(p)->plant.set_inputs(di,probe);
}
extern "C" void cnc3_sim_faults(void*p,uint32_t flags,uint16_t alarms,uint8_t unplug,uint16_t shorted){
    auto&f=*static_cast<Fixture*>(p);f.fault_flags=flags;
    cnc3_sim::Faults faults;faults.alarm_mask=alarms;faults.encoder_unplug=unplug;faults.do_short=shorted;
    faults.pause_heartbeat=!!(flags&4);faults.foreign_session=!!(flags&8);
    faults.inhibit=!!(flags&16);faults.watchdog_m=!!(flags&32);faults.watchdog_o=!!(flags&64);
    faults.corrupt_crc=!!(flags&128);faults.limit_low_mask=(flags&256)?1u:0u;f.plant.set_faults(faults);
}
extern "C" void cnc3_sim_observe(void*p,cnc3_sim_stats*out){
    auto&f=*static_cast<Fixture*>(p);const auto&m=f.plant.metrics();
    *out=f.stats;out->provider_records=m.accepted_provider_records;
    out->provider_sequence=m.provider_sequence;out->provider_error=static_cast<uint32_t>(f.plant.error());
    out->rtl_fault=f.rtl.fault_word;out->rtl_armed_mask=f.rtl.armed_mask;
    out->rtl_enabled_mask=static_cast<uint16_t>((~f.rtl.enable_n)&0xfff);out->dout_applied=m.applied_outputs;
    out->physical_authority=f.rtl.physical_authority;out->production_profile_complete=f.rtl.production_profile_complete;
    out->sim_ready=f.rtl.sim_ready;out->reset_ready=f.plant.inputs().reset_arm_ready;
    for(unsigned i=0;i<12;++i){out->plant_position[i]=m.position[i];out->accepted_rises[i]=m.accepted_rises[i];}
    out->model_home=f.plant.inputs().home_raw;out->model_limit_low=f.plant.inputs().limit_low_raw;
    out->model_limit_high=f.plant.inputs().limit_high_raw;
    for(unsigned i=0;i<4;++i){out->encoder_count[i]=m.encoder_count[i];out->encoder_edges[i]=m.encoder_edges[i];out->index_rises[i]=m.index_rises[i];}
}
extern "C" int cnc3_sim_exchange(void*p,enum cnc3_cs cs,const uint8_t*tx,uint8_t*rx,size_t n){
    auto&f=*static_cast<Fixture*>(p);
    if(!tx||!rx||(cs!=CNC3_CS_FB&&cs!=CNC3_CS_CMD)||n!=(cs==CNC3_CS_FB?176u:96u))return -1;
    if(f.fault_flags&1)return -1;
    ++f.stats.transactions;if(cs==CNC3_CS_CMD)++f.stats.write_calls;
    if(cs==CNC3_CS_CMD&&tx[5]==CNC3_OP_ARM)++f.stats.arm_commands;
    if(cs==CNC3_CS_CMD&&tx[5]==CNC3_OP_UPDATE)++f.stats.update_commands;
    std::memset(rx,0,n);f.advance(12);f.rtl.spi_sclk=0;
    if(cs==CNC3_CS_FB)f.rtl.spi_cs_fb_n=0;else f.rtl.spi_cs_cmd_n=0;f.advance(8);
    for(size_t bit=0;bit<n*8;++bit){
        f.rtl.spi_mosi=(tx[bit/8]>>(7-bit%8))&1;
        f.advance(4);f.rtl.spi_sclk=1;f.rtl.eval();
        rx[bit/8]=static_cast<uint8_t>((rx[bit/8]<<1)|(f.rtl.spi_miso&1));
        f.advance(4);f.rtl.spi_sclk=0;f.rtl.eval();
    }
    f.advance(8);f.rtl.spi_cs_fb_n=f.rtl.spi_cs_cmd_n=1;f.rtl.spi_mosi=0;f.advance(12);
    if(f.rtl.spi_miso_oe)return -1;
    if(n==176&&!std::memcmp(rx,"CAP3",4))++f.stats.cap3_responses;
    if(f.fault_flags&2)rx[n-1]^=1;
    return 0;
}
