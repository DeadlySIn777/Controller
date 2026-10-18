/* Startup verifies a reviewed immutable configuration; cyclic work is compiled
 * C + actual RTL SPI + disconnected virtual providers. No device backend exists. */
#include "rtapi.h"
#include "rtapi_app.h"
#include "hal.h"
#include "sim_transport.h"
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
MODULE_AUTHOR("Controller engineering project");
MODULE_DESCRIPTION("Explicit disconnected SIM2 twelve-channel LinuxCNC runtime");
MODULE_LICENSE("LicenseRef-Proprietary");
#ifndef CNC3_SIM_MODULE_NAME
#define CNC3_SIM_MODULE_NAME "cnc3_runtime_sim"
#endif
static int component_id=-1;
static void*fixture;
static struct cnc3_driver driver;
static struct cnc3_sim_manifest manifest;
struct pins {
    hal_bit_t *enable,*reset,*fault,*ready,*armed,*discovered,*feedback_valid,*permission;
    hal_bit_t *reset_button,*reset_ready,*reset_held,*physical,*production;
    hal_u32_t *state,*fault_code,*phase,*sequence,*session,*endpoint_faults,*snapseq;
    hal_u32_t *fitted,*active_mask,*installed,*encoders,*config_hash,*provider_session,*source_id;
    hal_u32_t *sim_faults,*sim_alarms,*sim_unplug,*sim_short,*sim_di,*sim_probe;
    hal_u32_t *di,*di_age,*do_cmd,*do_applied,*do_fault,*probe_arm,*probe_status,*index_arm;
    hal_u32_t *provider_sequence,*provider_error,*config_digest[8],*source_digest[8];
    hal_u32_t *event_seq,*event_type,*event_source,*event_values[4],*encoder_valid,*index_armed,*rtl_armed,*rtl_enabled;
    hal_float_t *events_stored;
    hal_u32_t *event_status,*model_home,*model_limit_low,*model_limit_high;
    hal_float_t *probe_events[2],*index_events[4],*index_rises[4];
    hal_float_t *command[12],*feedback[12],*scale[12],*max_velocity[12];
    hal_float_t *steps[12],*rises[12],*model_position[12],*accepted_rises[12];
    hal_float_t *encoder[4],*model_encoder[4],*encoder_edges[4];
    hal_float_t *sim_seconds,*transactions,*updates,*samples;
};
static struct pins*p;
static void latch_fault(enum cnc3_fault fault){
    if(driver.state!=CNC3_FAULT)driver.fault=fault;
    driver.state=CNC3_FAULT;driver.feedback_valid=0;
}
static int preflight(const char*path){
    const char*verify=getenv("CNC3_SIM_VERIFIER"),*store=getenv("CNC3_SIM_STORE");
    if(!verify||!store||verify[0]!='/'||store[0]!='/')return -1;
    pid_t child=fork();if(child<0)return -1;
    if(!child){execl("/usr/bin/python3","python3",verify,"--store",store,"--verify",path,(char*)0);_exit(127);}
    int status;if(waitpid(child,&status,0)!=child)return -1;
    return WIFEXITED(status)&&WEXITSTATUS(status)==0?0:-1;
}
static void outputs(void){
    struct cnc3_sim_stats s;cnc3_sim_observe(fixture,&s);
    __atomic_add_fetch(p->snapseq,1,__ATOMIC_SEQ_CST);
    *p->state=(hal_u32_t)driver.state;*p->fault_code=(hal_u32_t)driver.fault;
    *p->fault=driver.state==CNC3_FAULT;*p->phase=driver.commission_phase;
    *p->ready=driver.commissioned&&(driver.state==CNC3_READY||driver.state==CNC3_ACTIVE);
    *p->armed=driver.state==CNC3_ACTIVE;*p->discovered=driver.discovered;
    *p->feedback_valid=driver.commissioned&&driver.feedback_valid;
    *p->permission=s.rtl_enabled_mask!=0;*p->physical=s.physical_authority;*p->production=s.production_profile_complete;
    *p->reset_ready=s.reset_ready;*p->reset_held=s.reset_held;*p->sequence=driver.sequence;*p->session=driver.session;
    *p->endpoint_faults=s.rtl_fault;*p->fitted=driver.caps.step_channels;
    *p->installed=driver.caps.installed_channels;*p->encoders=driver.caps.encoders_supported;
    *p->provider_sequence=s.provider_sequence;*p->provider_error=s.provider_error;
    *p->rtl_armed=s.rtl_armed_mask;*p->rtl_enabled=s.rtl_enabled_mask;
    *p->encoder_valid=driver.fb.encoder_valid_mask;*p->index_armed=driver.fb.index_armed_mask;
    *p->events_stored=(double)driver.events_stored;*p->event_seq=driver.last_event_seq;
    *p->event_status=driver.fb.event_status;
    *p->model_home=s.model_home;*p->model_limit_low=s.model_limit_low;*p->model_limit_high=s.model_limit_high;
    for(unsigned i=0;i<2;++i)*p->probe_events[i]=(double)driver.probe_events[i];
    for(unsigned i=0;i<4;++i){*p->index_events[i]=(double)driver.index_events[i];*p->index_rises[i]=(double)s.index_rises[i];}
    if(driver.event_count){
        const struct cnc3_event*e=&driver.events[(driver.event_head+driver.event_count-1u)%CNC3_EVENT_LOG];
        *p->event_type=e->type;*p->event_source=e->source;
        for(unsigned i=0;i<4;++i)*p->event_values[i]=e->value[i];
    }
    *p->di=driver.fb.din;*p->di_age=driver.fb.din_age;*p->do_applied=driver.fb.dout_applied;
    *p->do_fault=driver.fb.dout_fault_latched;*p->probe_status=driver.fb.probe_status;
    *p->transactions=(double)s.transactions;*p->updates=(double)s.update_commands;
    *p->samples=(double)driver.cycles;*p->sim_seconds=(double)s.ticks/50000000.0;
    for(unsigned i=0;i<12;++i){
        *p->feedback[i]=driver.position_fb[i];*p->steps[i]=(double)driver.steps[i];
        *p->rises[i]=(double)s.step_rises[i];*p->model_position[i]=(double)s.plant_position[i];
        *p->accepted_rises[i]=(double)s.accepted_rises[i];
    }
    for(unsigned i=0;i<4;++i){*p->encoder[i]=(double)driver.encoders[i];*p->model_encoder[i]=(double)s.encoder_count[i];*p->encoder_edges[i]=(double)s.encoder_edges[i];}
    __atomic_add_fetch(p->snapseq,1,__ATOMIC_SEQ_CST);
}
static void read_cycle(void*arg,long period){
    (void)arg;
    if(period<250000||period>2500000){
        latch_fault(CNC3_FAULT_CONFIG);
        cnc3_sim_faults(fixture,16,0,0,0);(void)cnc3_sim_cycle(fixture,1000000);outputs();return;
    }
    uint32_t invalid=(*p->sim_alarms&~0xfffu)||(*p->sim_unplug&~15u)||(*p->sim_short&~0xffffu)||
        (*p->sim_di&~0xffffffu)||(*p->sim_probe&~3u)||(*p->sim_faults&~511u);
    cnc3_sim_reset_button(fixture,*p->reset_button);
    cnc3_sim_inputs(fixture,*p->sim_di&0xffffffu,(uint8_t)(*p->sim_probe&3u));
    cnc3_sim_faults(fixture,(*p->sim_faults&511u)|(invalid?16u:0u),
        (uint16_t)(*p->sim_alarms&0xfffu),(uint8_t)(*p->sim_unplug&15u),(uint16_t)(*p->sim_short&0xffffu));
    (void)cnc3_sim_cycle(fixture,(uint64_t)period);
    if(invalid)latch_fault(CNC3_FAULT_CONFIG);
    cnc3_read(&driver,cnc3_sim_now_ns(fixture),(uint64_t)period);outputs();
}
static void write_cycle(void*arg,long period){
    (void)arg;driver.enable=*p->enable;driver.reset=*p->reset;
    if(period<250000||period>2500000){latch_fault(CNC3_FAULT_CONFIG);outputs();return;}
    if((*p->do_cmd&~0xffffu)||(*p->index_arm&~15u)||(*p->probe_arm&~3u)){
        latch_fault(CNC3_FAULT_RANGE);outputs();return;
    }
    for(unsigned i=0;i<12;++i)driver.position_cmd[i]=*p->command[i];
    driver.dout_image=(uint16_t)(*p->do_cmd&0xffffu);
    driver.index_arm_mask=(uint16_t)(*p->index_arm&15u);driver.probe_arm=(uint8_t)(*p->probe_arm&3u);
    cnc3_write(&driver,cnc3_sim_now_ns(fixture),(uint64_t)period);outputs();
}
int rtapi_app_main(void){
    const char*allow=getenv("CNC3_ALLOW_DISCONNECTED_RTL_SIMULATION"),*path=getenv("CNC3_SIM_MANIFEST");
    if(!allow||strcmp(allow,"1")||!path||path[0]!='/'||preflight(path)||cnc3_sim_manifest_read(path,&manifest)){
        rtapi_print_msg(RTAPI_MSG_ERR,"SIM2: explicit reviewed disconnected configuration refused\n");return -1;
    }
    component_id=hal_init(CNC3_SIM_MODULE_NAME);if(component_id<0)return component_id;
    p=hal_malloc(sizeof(*p));if(!p)goto error;memset(p,0,sizeof(*p));
#define PIN(type,dir,member,name) if(hal_pin_##type##_newf(dir,&p->member,component_id,"cnc3r." name))goto error
    PIN(bit,HAL_IN,enable,"enable");PIN(bit,HAL_IN,reset,"reset");PIN(bit,HAL_OUT,fault,"fault");
    PIN(bit,HAL_OUT,ready,"ready");PIN(bit,HAL_OUT,armed,"armed");PIN(bit,HAL_OUT,discovered,"discovered");
    PIN(bit,HAL_OUT,feedback_valid,"feedback-valid");PIN(bit,HAL_OUT,permission,"sim-permission");
    PIN(bit,HAL_IN,reset_button,"sim-reset-button");PIN(bit,HAL_OUT,reset_ready,"sim-reset-ready");
    PIN(bit,HAL_OUT,reset_held,"sim-reset-held");
    PIN(bit,HAL_OUT,physical,"physical-authority");PIN(bit,HAL_OUT,production,"production-profile-complete");
    PIN(u32,HAL_OUT,state,"state");PIN(u32,HAL_OUT,fault_code,"fault-code");PIN(u32,HAL_OUT,phase,"commission-phase");
    PIN(u32,HAL_OUT,sequence,"sequence");PIN(u32,HAL_OUT,session,"session");PIN(u32,HAL_OUT,endpoint_faults,"endpoint-faults");
    PIN(u32,HAL_OUT,snapseq,"snapshot-sequence");PIN(u32,HAL_OUT,fitted,"fitted-channels");
    PIN(u32,HAL_OUT,active_mask,"active-mask");PIN(u32,HAL_OUT,installed,"installed-channels");
    PIN(u32,HAL_OUT,encoders,"encoder-channels");PIN(u32,HAL_OUT,config_hash,"config-hash");
    PIN(u32,HAL_OUT,provider_session,"provider-session");PIN(u32,HAL_OUT,source_id,"source-id");
    PIN(u32,HAL_IN,sim_faults,"sim-faults");PIN(u32,HAL_IN,sim_alarms,"sim-alarms");
    PIN(u32,HAL_IN,sim_unplug,"sim-encoder-unplug");PIN(u32,HAL_IN,sim_short,"sim-do-short");
    PIN(u32,HAL_IN,sim_di,"sim-di");PIN(u32,HAL_IN,sim_probe,"sim-probes");
    PIN(u32,HAL_OUT,di,"di");PIN(u32,HAL_OUT,di_age,"di-age");PIN(u32,HAL_IN,do_cmd,"do-command");
    PIN(u32,HAL_OUT,do_applied,"do-applied");PIN(u32,HAL_OUT,do_fault,"do-fault");
    PIN(u32,HAL_IN,probe_arm,"probe-arm");PIN(u32,HAL_OUT,probe_status,"probe-status");PIN(u32,HAL_IN,index_arm,"index-arm");
    PIN(u32,HAL_OUT,provider_sequence,"provider-sequence");PIN(u32,HAL_OUT,provider_error,"provider-error");
    PIN(u32,HAL_OUT,event_seq,"event-sequence");PIN(u32,HAL_OUT,event_type,"event-type");
    PIN(u32,HAL_OUT,event_source,"event-source");PIN(u32,HAL_OUT,encoder_valid,"encoder-valid-mask");
    PIN(u32,HAL_OUT,index_armed,"index-armed-mask");PIN(u32,HAL_OUT,rtl_armed,"rtl-armed-mask");
    PIN(u32,HAL_OUT,rtl_enabled,"rtl-enabled-mask");PIN(float,HAL_OUT,events_stored,"events-stored");
    PIN(u32,HAL_OUT,event_status,"event-status");PIN(u32,HAL_OUT,model_home,"sim-home-mask");
    PIN(u32,HAL_OUT,model_limit_low,"sim-limit-low-mask");PIN(u32,HAL_OUT,model_limit_high,"sim-limit-high-mask");
    PIN(float,HAL_OUT,sim_seconds,"sim-seconds");PIN(float,HAL_OUT,transactions,"transactions");
    PIN(float,HAL_OUT,updates,"updates");PIN(float,HAL_OUT,samples,"samples");
#undef PIN
    for(unsigned i=0;i<12;++i){
#define JOINT(member,dir,label) if(hal_pin_float_newf(dir,&p->member[i],component_id,"cnc3r.%u." label,i))goto error
        JOINT(command,HAL_IN,"position-cmd");JOINT(feedback,HAL_OUT,"position-fb");
        JOINT(scale,HAL_OUT,"scale");JOINT(max_velocity,HAL_OUT,"maximum-velocity");
        JOINT(steps,HAL_OUT,"reported-steps");JOINT(rises,HAL_OUT,"observed-step-rises");
        JOINT(model_position,HAL_OUT,"model-position-steps");JOINT(accepted_rises,HAL_OUT,"model-accepted-rises");
#undef JOINT
        *p->scale[i]=manifest.config.scale[i];*p->max_velocity[i]=manifest.max_velocity[i];
    }
    for(unsigned i=0;i<4;++i){
        if(hal_pin_float_newf(HAL_OUT,&p->encoder[i],component_id,"cnc3r.encoder.%u.count",i)||
           hal_pin_float_newf(HAL_OUT,&p->model_encoder[i],component_id,"cnc3r.encoder.%u.model-count",i)||
           hal_pin_float_newf(HAL_OUT,&p->encoder_edges[i],component_id,"cnc3r.encoder.%u.observed-edges",i))goto error;
        if(hal_pin_float_newf(HAL_OUT,&p->index_events[i],component_id,"cnc3r.index.%u.events",i)||
           hal_pin_float_newf(HAL_OUT,&p->index_rises[i],component_id,"cnc3r.encoder.%u.model-index-rises",i))goto error;
        if(hal_pin_u32_newf(HAL_OUT,&p->event_values[i],component_id,"cnc3r.event-value-%u",i))goto error;
    }
    for(unsigned i=0;i<2;++i)if(hal_pin_float_newf(HAL_OUT,&p->probe_events[i],component_id,"cnc3r.probe.%u.events",i))goto error;
    for(unsigned i=0;i<8;++i){
        if(hal_pin_u32_newf(HAL_OUT,&p->config_digest[i],component_id,"cnc3r.config-digest-%u",i)||
           hal_pin_u32_newf(HAL_OUT,&p->source_digest[i],component_id,"cnc3r.source-digest-%u",i))goto error;
        *p->config_digest[i]=cnc3_get(manifest.config_digest+4*i,4);*p->source_digest[i]=cnc3_get(manifest.source_digest+4*i,4);
    }
    *p->active_mask=manifest.config.axis_mask;*p->config_hash=manifest.config.config_hash;
    *p->provider_session=manifest.provider_session;*p->source_id=manifest.source_id;
    fixture=cnc3_sim_create(&manifest);if(!fixture)goto error;
    struct cnc3_transport transport={fixture,cnc3_sim_exchange,CNC3_SIM_TRANSPORT_ID};
    cnc3_init(&driver,transport,&manifest.config,0x11223344);
    if(hal_export_funct("cnc3r.read",read_cycle,0,1,0,component_id)||
       hal_export_funct("cnc3r.write",write_cycle,0,1,0,component_id))goto error;
    outputs();hal_ready(component_id);return 0;
error:
    if(fixture){cnc3_sim_destroy(fixture);fixture=0;}hal_exit(component_id);return -1;
}
void rtapi_app_exit(void){if(fixture)cnc3_sim_destroy(fixture);if(component_id>=0)hal_exit(component_id);}
