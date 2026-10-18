#include "sim_transport.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

static unsigned checks=0;
static void check(bool ok,const char*why){++checks;if(!ok)throw std::runtime_error(why);}
int main(int argc,char**argv){
    void*fixture=nullptr;
    try{
        check(argc==2,"manifest argument");cnc3_sim_manifest manifest{};
        check(!cnc3_sim_manifest_read(argv[1],&manifest),"numeric manifest validation");
        fixture=cnc3_sim_create(&manifest);check(fixture,"explicit virtual factory");
        cnc3_transport transport{fixture,cnc3_sim_exchange,CNC3_SIM_TRANSPORT_ID};cnc3_driver driver{};
        cnc3_init(&driver,transport,&manifest.config,0x33445566);
        auto cycle=[&](){check(!cnc3_sim_cycle(fixture,1000000),"bounded clock cycle");
            cnc3_read(&driver,cnc3_sim_now_ns(fixture),1000000);
            cnc3_write(&driver,cnc3_sim_now_ns(fixture),1000000);};
        auto healthy=[&](){if(driver.state==CNC3_FAULT){std::fprintf(stderr,"FAULT %s result%d endpoint%08x phase%u seq%u fbseq%u safety%08x\n",cnc3_fault_name(driver.fault),driver.last_result,driver.endpoint_fault_word,driver.commission_phase,driver.sequence,driver.fb.last_sequence,driver.fb.safety_power_word);throw std::runtime_error("driver fault");}};
        for(unsigned i=0;i<20&&driver.state!=CNC3_OFF;++i){cycle();healthy();}
        check(driver.state==CNC3_OFF&&driver.discovered,"real CAP3/configuration discovery");
        driver.reset=1;cycle();driver.reset=0;
        for(unsigned i=0;i<100&&!driver.commissioned;++i){cycle();healthy();}
        check(driver.commissioned&&driver.state==CNC3_READY,"both timed selftests and IO commissioning");
        cnc3_sim_stats initial{};cnc3_sim_observe(fixture,&initial);
        check(initial.arm_commands==0&&initial.rtl_armed_mask==0,"commissioning did not arm");
        check(!initial.reset_ready,"reset authority starts inhibited");
        cnc3_sim_reset_button(fixture,1);for(unsigned i=0;i<52;++i){cycle();healthy();}
        cnc3_sim_reset_button(fixture,0);cycle();healthy();
        cnc3_sim_observe(fixture,&initial);check(initial.reset_ready,"deliberate timed reset release");
        driver.enable=1;cycle();for(unsigned i=0;i<5&&driver.state!=CNC3_ACTIVE;++i){cycle();healthy();}
        check(driver.state==CNC3_ACTIVE,"actual ARM admitted");
        cnc3_sim_observe(fixture,&initial);check(initial.rtl_armed_mask==manifest.config.axis_mask,"all requested lanes armed");
        driver.index_arm_mask=15;driver.probe_arm=3;
        // Concurrent twelve (or eight) commands, bounded below reviewed 10mm/s.
        for(unsigned tick=0;tick<800;++tick){
            for(unsigned i=0;i<12;++i)if(manifest.config.axis_mask&(1u<<i))driver.position_cmd[i]+=.006;
            if(tick==20)cnc3_sim_inputs(fixture,0xabcdef,3);
            if(tick==25)cnc3_sim_inputs(fixture,0xabcdef,0);
            driver.dout_image=tick<400?0xffff:0;
            cycle();healthy();
        }
        // Settle command while clocks, watchdog feeds and actual feedback continue.
        for(unsigned i=0;i<20;++i){cycle();healthy();}
        cnc3_sim_stats final{};cnc3_sim_observe(fixture,&final);
        for(unsigned i=0;i<12;++i){
            const bool active=manifest.config.axis_mask&(1u<<i);
            check(active?final.step_rises[i]>3000:final.step_rises[i]==0,"each fitted lane active/inactive pulse invariant");
            check(final.plant_position[i]-initial.plant_position[i]==final.pin_step_count[i]-initial.pin_step_count[i],"actual pin/ideal plant delta equal");
            check(std::llabs(driver.steps[i]-final.pin_step_count[i])<=8,"serial counter agrees independent STEP monitor");
        }
        for(unsigned i=0;i<4;++i){
            check(final.encoder_edges[i]>3000,"all four actual AB paths moved");
            check(final.index_rises[i]>initial.index_rises[i],"all four model index sources crossed");
            check(std::llabs((driver.encoders[i])-(final.encoder_count[i]-initial.encoder_count[i]))<=8,"serial encoder agrees delta baseline");
            check(driver.index_events[i]>0,"actual serial index capture received");
        }
        check(driver.probe_events[0]&&driver.probe_events[1],"both actual serial probe captures received");
        check(driver.fb.din==0xabcdef,"all 24 DI serial image");
        check(final.dout_applied==0,"16DO returned neutral through independent OUT domain");
        check(!final.physical_authority&&!final.production_profile_complete,"no physical promotion");
        cnc3_sim_faults(fixture,0,1,0,0);for(unsigned i=0;i<3;++i)cycle();
        check(driver.state==CNC3_FAULT,"actual alarm propagates to host");
        cnc3_sim_observe(fixture,&final);const auto stopped=final.step_rises[0];
        for(unsigned i=0;i<8;++i){cycle();}cnc3_sim_observe(fixture,&final);
        check(final.step_rises[0]==stopped&&final.rtl_enabled_mask==0,"fault cuts emitted STEP and enables");
        driver.enable=0;cnc3_sim_faults(fixture,0,0,0,0);driver.reset=1;cycle();driver.reset=0;
        for(unsigned i=0;i<100&&!driver.commissioned;++i){cycle();healthy();}
        check(driver.commissioned&&driver.state==CNC3_READY,"new session requalified");
        cnc3_sim_observe(fixture,&final);check(!final.reset_ready&&final.rtl_armed_mask==0,"restart requires fresh deliberate button and enable");
        std::printf("{\"status\":\"PASS\",\"checks\":%u,\"active_mask\":%u,\"cap3\":%llu,\"transactions\":%llu,\"simulated_physical_authority\":false}\n",checks,manifest.config.axis_mask,(unsigned long long)final.cap3_responses,(unsigned long long)final.transactions);
        cnc3_sim_destroy(fixture);return 0;
    }catch(const std::exception&e){std::fprintf(stderr,"FAIL checks%u: %s\n",checks,e.what());if(fixture)cnc3_sim_destroy(fixture);return 1;}
}
