/* Compiled HAL cyclic interface. This build links ONLY actual-RTL simulation.
 * No sockets, file/device I/O, allocation, printing or Python in read/write. */
#include "rtapi.h"
#include "rtapi_app.h"
#include "hal.h"
#include "cnc1.h"
#include <string.h>
#include <stdlib.h>
#include <time.h>
MODULE_AUTHOR("Controller engineering project");
MODULE_DESCRIPTION("CNC1 compiled cyclic driver with Verilator-only transport");
MODULE_LICENSE("GPL");
static int component_id=-1;
struct pins {
    hal_bit_t *enable,*reset,*fault,*ready,*armed,*permission,*discovered,*spindle,*feedback_valid;
    hal_u32_t *state,*fault_code,*step_channels,*encoder_channels,*frequency_channels;
    hal_u32_t *features,*core_hz,*timestamp,*sequence,*endpoint_faults,*inject,*edge_ticks,*index_flags;
    hal_u32_t *session,*revision,*epoch,*snapshot_sequence,*max_rate;
    hal_u32_t *instance_hi,*instance_lo;
    hal_bit_t *config_locked;
    hal_u32_t *config_request,*config_ack,*config_result,*config_op,*config_session,*config_revision,*config_epoch;
    hal_float_t *config_scale[6];
    hal_float_t *position_cmd[6],*position_fb[6],*scale[6],*emitted[6];
    hal_float_t *encoder[2],*index[2],*encoder_scale[2],*encoder_position[2],*index_position[2],*sample_count,*sim_seconds;
};
static struct pins *p;
static struct cnc1_driver driver;
static void *simulator;
static uint32_t last_config_request;
static uint64_t now_ns(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return (uint64_t)t.tv_sec*UINT64_C(1000000000)+(uint64_t)t.tv_nsec;
}
static void outputs(void) {
    __atomic_add_fetch(p->snapshot_sequence,1,__ATOMIC_SEQ_CST);
    *p->state=(hal_u32_t)driver.state; *p->fault_code=(hal_u32_t)driver.fault;
    *p->fault=driver.state==CNC1_FAULT; *p->discovered=driver.discovered;
    *p->feedback_valid=driver.feedback_valid;
    *p->ready=driver.state==CNC1_READY || driver.state==CNC1_ACTIVE;
    *p->armed=driver.state==CNC1_ACTIVE; *p->permission=cnc1_sim_permission(simulator);
    *p->step_channels=driver.caps.steps; *p->encoder_channels=driver.caps.encoders;
    *p->frequency_channels=driver.caps.frequencies; *p->features=driver.caps.features;
    *p->core_hz=driver.caps.core_hz; *p->timestamp=driver.status.timestamp;
    *p->max_rate=driver.caps.max_rate; *p->session=driver.session;
    *p->revision=driver.config_revision; *p->epoch=driver.runtime_epoch;
    *p->config_locked=driver.config_locked;
    *p->sequence=driver.status.sequence; *p->endpoint_faults=driver.status.faults;
    *p->sample_count=(double)driver.samples; *p->sim_seconds=(double)cnc1_sim_ticks(simulator)/50000000;
    *p->index_flags=driver.status.encoder_flags;
    for(unsigned i=0;i<6;i++) {*p->scale[i]=driver.scale[i]; *p->position_fb[i]=driver.position_fb[i]; *p->emitted[i]=(double)driver.steps[i];}
    for(unsigned i=0;i<2;i++) {
        *p->encoder[i]=(double)driver.encoders[i]; *p->index[i]=(double)driver.indexes[i];
        *p->encoder_position[i]=driver.encoder_position[i]; *p->index_position[i]=driver.index_position[i];
    }
    __atomic_add_fetch(p->snapshot_sequence,1,__ATOMIC_SEQ_CST);
}
static void read_cycle(void *arg,long period) {
    (void)arg;
    /* Simulation clocks forward even while communications are missing. */
    cnc1_sim_inject(simulator,*p->inject);
    cnc1_sim_spindle(simulator,*p->spindle,*p->edge_ticks);
    cnc1_sim_cycle(simulator,(uint64_t)period);
    for(unsigned i=0;i<2;i++) driver.encoder_scale[i]=*p->encoder_scale[i];
    cnc1_read(&driver,now_ns()); outputs();
}
static void write_cycle(void *arg,long period) {
    (void)arg;
    driver.enable=*p->enable; driver.reset=*p->reset;
    uint32_t request=*p->config_request;
    if(request!=*p->config_ack) {
        double scales[6]; for(unsigned i=0;i<6;i++) scales[i]=*p->config_scale[i];
        if(!request || request<=last_config_request) *p->config_result=4;
        else {
            last_config_request=request;
            *p->config_result=(hal_u32_t)cnc1_configure(&driver,*p->config_op,*p->config_session,
                                                     *p->config_revision,*p->config_epoch,scales);
        }
        *p->config_ack=request;
    }
    for(unsigned i=0;i<6;i++) driver.position_cmd[i]=*p->position_cmd[i];
    cnc1_write(&driver,now_ns(),(uint64_t)period); outputs();
}
int rtapi_app_main(void) {
    if(!getenv("CNC1_ALLOW_RTL_SIMULATION") || strcmp(getenv("CNC1_ALLOW_RTL_SIMULATION"),"1")) return -1;
    component_id=hal_init("cnc1_sim"); if(component_id<0) return component_id;
    p=hal_malloc(sizeof(*p)); if(!p) goto error;
    memset(p,0,sizeof(*p));
#define PIN(type,dir,member,name) if(hal_pin_##type##_newf(dir,&p->member,component_id,"cnc1." name)) goto error
    PIN(bit,HAL_IN,enable,"enable"); PIN(bit,HAL_IN,reset,"reset");
    PIN(bit,HAL_OUT,fault,"fault"); PIN(bit,HAL_OUT,ready,"ready"); PIN(bit,HAL_OUT,armed,"armed");
    PIN(bit,HAL_OUT,permission,"sim-permission"); PIN(bit,HAL_OUT,discovered,"discovered");
    PIN(bit,HAL_IN,spindle,"sim-spindle");
    PIN(bit,HAL_OUT,feedback_valid,"feedback-valid");
    PIN(u32,HAL_OUT,state,"state"); PIN(u32,HAL_OUT,fault_code,"fault-code");
    PIN(u32,HAL_OUT,step_channels,"step-channels"); PIN(u32,HAL_OUT,encoder_channels,"encoder-channels");
    PIN(u32,HAL_OUT,frequency_channels,"frequency-channels"); PIN(u32,HAL_OUT,features,"features");
    PIN(u32,HAL_OUT,core_hz,"core-hz"); PIN(u32,HAL_OUT,timestamp,"timestamp");
    PIN(u32,HAL_OUT,sequence,"sequence"); PIN(u32,HAL_OUT,endpoint_faults,"endpoint-faults");
    PIN(u32,HAL_IN,inject,"sim-inject"); PIN(u32,HAL_IN,edge_ticks,"sim-spindle-edge-ticks");
    PIN(u32,HAL_OUT,index_flags,"encoder-flags");
    PIN(u32,HAL_OUT,session,"session"); PIN(u32,HAL_OUT,revision,"config-revision");
    PIN(u32,HAL_OUT,epoch,"runtime-epoch"); PIN(u32,HAL_OUT,snapshot_sequence,"snapshot-sequence");
    PIN(u32,HAL_OUT,max_rate,"max-rate"); PIN(bit,HAL_OUT,config_locked,"config-locked");
    PIN(u32,HAL_OUT,instance_hi,"instance-hi"); PIN(u32,HAL_OUT,instance_lo,"instance-lo");
    PIN(u32,HAL_IN,config_request,"config-request"); PIN(u32,HAL_OUT,config_ack,"config-ack");
    PIN(u32,HAL_OUT,config_result,"config-result"); PIN(u32,HAL_IN,config_op,"config-op");
    PIN(u32,HAL_IN,config_session,"config-session"); PIN(u32,HAL_IN,config_revision,"config-expected-revision");
    PIN(u32,HAL_IN,config_epoch,"config-expected-epoch");
    PIN(float,HAL_OUT,sample_count,"samples"); PIN(float,HAL_OUT,sim_seconds,"sim-seconds");
#undef PIN
    for(unsigned i=0;i<6;i++) {
        if(hal_pin_float_newf(HAL_IN,&p->position_cmd[i],component_id,"cnc1.%u.position-cmd",i) ||
           hal_pin_float_newf(HAL_OUT,&p->position_fb[i],component_id,"cnc1.%u.position-fb",i) ||
           hal_pin_float_newf(HAL_OUT,&p->scale[i],component_id,"cnc1.%u.scale",i) ||
           hal_pin_float_newf(HAL_IN,&p->config_scale[i],component_id,"cnc1.%u.config-scale",i) ||
           hal_pin_float_newf(HAL_OUT,&p->emitted[i],component_id,"cnc1.%u.emitted-count",i)) goto error;
        *p->scale[i]=200; *p->config_scale[i]=200;
    }
    for(unsigned i=0;i<2;i++) {
        if(
        hal_pin_float_newf(HAL_OUT,&p->encoder[i],component_id,"cnc1.encoder.%u.count",i) ||
        hal_pin_float_newf(HAL_OUT,&p->index[i],component_id,"cnc1.encoder.%u.index-count",i) ||
        hal_pin_float_newf(HAL_IN,&p->encoder_scale[i],component_id,"cnc1.encoder.%u.scale",i) ||
        hal_pin_float_newf(HAL_OUT,&p->encoder_position[i],component_id,"cnc1.encoder.%u.position",i) ||
        hal_pin_float_newf(HAL_OUT,&p->index_position[i],component_id,"cnc1.encoder.%u.index-position",i)) goto error;
        *p->encoder_scale[i]=400;
    }
    *p->edge_ticks=10000;
    simulator=cnc1_sim_create(); if(!simulator) goto error;
    struct cnc1_transport t={simulator,cnc1_sim_exchange};
    uint64_t instance=now_ns(); *p->instance_hi=(uint32_t)(instance>>32); *p->instance_lo=(uint32_t)instance;
    cnc1_init(&driver,t,(uint32_t)instance);
    driver.axis_mask=7; /* This LinuxCNC acceptance profile has exactly XYZ. */
    /* Functional simulation can run slower than real time. Not a target limit. */
    driver.max_age_ns=500000000;
    if(hal_export_funct("cnc1.read",read_cycle,0,1,0,component_id) ||
       hal_export_funct("cnc1.write",write_cycle,0,1,0,component_id)) goto error;
    hal_ready(component_id); return 0;
error:
    if(simulator) cnc1_sim_destroy(simulator);
    hal_exit(component_id); return -1;
}
void rtapi_app_exit(void) {
    if(simulator) cnc1_sim_destroy(simulator);
    if(component_id>=0) hal_exit(component_id);
}
