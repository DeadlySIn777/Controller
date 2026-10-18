/* LinuxCNC HAL qualification adapter; report-local, Verilator only.
 * Uses the immutable copied C driver. No actuation/device transport exists.
 * The cycle's timestamp is simulated RTL time, not measured deadline evidence. */
#include "rtapi.h"
#include "rtapi_app.h"
#include "hal.h"
#include "cnc3.h"
#include "rtl_transport.h"
#include <stdlib.h>
#include <string.h>
MODULE_AUTHOR("Controller engineering project");
MODULE_DESCRIPTION("Disconnected twelve-channel CNC3 HAL refusal qualification");
/* The retained CNC3 codec/core carry LicenseRef-Proprietary notices. */
MODULE_LICENSE("LicenseRef-Proprietary");
static int scenario=0;
RTAPI_MP_INT(scenario,"0 normal IS2, 1 unavailable encoder, 2 unavailable MPG");
static int component_id=-1;
static void *fixture;
static struct cnc3_driver driver;
struct pins {
    hal_bit_t *enable,*reset,*corrupt,*fault,*discovered,*feedback_valid;
    hal_u32_t *state,*fault_code,*supported,*installed,*encoders,*enc_installed;
    hal_u32_t *transactions,*cap_frames,*arm_frames,*update_frames,*configure_frames;
    hal_u32_t *enabled_mask,*armed_mask,*endpoint_session,*authority,*malformed,*cycles;
    hal_float_t *command[12],*feedback[12];
    hal_u32_t *observed_step[12];
    hal_float_t *encoder[4];
};
static struct pins *p;
#ifndef CNC3_REFUSAL_MODULE_NAME
#define CNC3_REFUSAL_MODULE_NAME "cnc3_rev_a_refusal"
#endif
static void outputs(void){
    *p->state=(hal_u32_t)driver.state;*p->fault_code=(hal_u32_t)driver.fault;
    *p->fault=driver.state==CNC3_FAULT;*p->discovered=driver.discovered;
    *p->feedback_valid=driver.feedback_valid;*p->supported=driver.caps.step_channels;
    *p->installed=driver.caps.installed_channels;*p->encoders=driver.caps.encoders_supported;
    *p->enc_installed=driver.caps.encoders_installed;
    *p->transactions=rev_a_sim_metric(fixture,0);*p->cap_frames=rev_a_sim_metric(fixture,1);
    *p->arm_frames=rev_a_sim_metric(fixture,2);*p->update_frames=rev_a_sim_metric(fixture,3);
    *p->configure_frames=rev_a_sim_metric(fixture,4);*p->enabled_mask=rev_a_sim_metric(fixture,5);
    *p->armed_mask=rev_a_sim_metric(fixture,6);*p->endpoint_session=rev_a_sim_metric(fixture,7);
    *p->authority=rev_a_sim_metric(fixture,8);*p->malformed=rev_a_sim_metric(fixture,9);
    *p->cycles=(hal_u32_t)driver.cycles;
    for(unsigned i=0;i<12;++i){*p->feedback[i]=driver.position_fb[i];*p->observed_step[i]=rev_a_sim_metric(fixture,10+i);}
    for(unsigned i=0;i<4;++i)*p->encoder[i]=(double)driver.encoders[i];
}
static void read_cycle(void*arg,long period){
    (void)arg;
    /* Functional simulation only: fifty thousand actual 50MHz core ticks per
     * nominal 1ms callback. Serial exchanges add their own real core ticks. */
    if(period>0)rev_a_sim_advance(fixture,(uint64_t)period/20u);
    rev_a_sim_corrupt(fixture,*p->corrupt);
    cnc3_read(&driver,rev_a_sim_ticks(fixture)*20u,(uint64_t)period);outputs();
}
static void write_cycle(void*arg,long period){
    (void)arg;driver.enable=*p->enable;driver.reset=*p->reset;
    for(unsigned i=0;i<12;++i)driver.position_cmd[i]=*p->command[i];
    cnc3_write(&driver,rev_a_sim_ticks(fixture)*20u,(uint64_t)period);outputs();
}
int rtapi_app_main(void){
    const char*allow=getenv("CNC3_ALLOW_DISCONNECTED_RTL_SIMULATION");
    if(!allow||strcmp(allow,"1")||scenario<0||scenario>2){
        rtapi_print_msg(RTAPI_MSG_ERR,"CNC3 refusal fixture: explicit simulation opt-in missing or invalid scenario\n");return -1;
    }
    component_id=hal_init(CNC3_REFUSAL_MODULE_NAME);if(component_id<0)return component_id;
    p=hal_malloc(sizeof(*p));if(!p)goto error;memset(p,0,sizeof(*p));
#define PIN(type,dir,member,name) if(hal_pin_##type##_newf(dir,&p->member,component_id,"cnc3a." name))goto error
    PIN(bit,HAL_IN,enable,"enable");PIN(bit,HAL_IN,reset,"reset");PIN(bit,HAL_IN,corrupt,"sim-corrupt-crc");
    PIN(bit,HAL_OUT,fault,"fault");PIN(bit,HAL_OUT,discovered,"discovered");PIN(bit,HAL_OUT,feedback_valid,"feedback-valid");
    PIN(u32,HAL_OUT,state,"state");PIN(u32,HAL_OUT,fault_code,"fault-code");PIN(u32,HAL_OUT,supported,"supported-channels");
    PIN(u32,HAL_OUT,installed,"installed-channels");PIN(u32,HAL_OUT,encoders,"supported-encoders");
    PIN(u32,HAL_OUT,enc_installed,"installed-encoders");PIN(u32,HAL_OUT,transactions,"spi-transactions");
    PIN(u32,HAL_OUT,cap_frames,"cap3-frames");PIN(u32,HAL_OUT,arm_frames,"arm-frames");
    PIN(u32,HAL_OUT,update_frames,"update-frames");PIN(u32,HAL_OUT,configure_frames,"configure-frames");
    PIN(u32,HAL_OUT,enabled_mask,"rtl-enabled-mask");PIN(u32,HAL_OUT,armed_mask,"rtl-armed-mask");
    PIN(u32,HAL_OUT,endpoint_session,"rtl-session");PIN(u32,HAL_OUT,authority,"rtl-authority");
    PIN(u32,HAL_OUT,malformed,"malformed-transactions");PIN(u32,HAL_OUT,cycles,"host-cycles");
#undef PIN
    for(unsigned i=0;i<12;++i){
        if(hal_pin_float_newf(HAL_IN,&p->command[i],component_id,"cnc3a.%u.position-cmd",i)||
           hal_pin_float_newf(HAL_OUT,&p->feedback[i],component_id,"cnc3a.%u.position-fb",i)||
           hal_pin_u32_newf(HAL_OUT,&p->observed_step[i],component_id,"cnc3a.%u.observed-step-rises",i))goto error;
    }
    for(unsigned i=0;i<4;++i)if(hal_pin_float_newf(HAL_OUT,&p->encoder[i],component_id,"cnc3a.encoder.%u.count",i))goto error;
    fixture=rev_a_sim_create();if(!fixture)goto error;
    struct cnc3_config cfg;memset(&cfg,0,sizeof(cfg));cfg.axis_mask=0xfff;cfg.alarm_trip_mask=0xfff;
    cfg.config_hash=0x20261004;cfg.required_encoder_mask=scenario==1?16u:15u;
    cfg.encoder_filter_ticks=4;cfg.mpg_config=scenario==2?1u:0u;
    for(unsigned i=0;i<12;++i){cfg.scale[i]=40;for(unsigned k=0;k<4;++k)cfg.timing[i][k]=100;}
    struct cnc3_transport transport={fixture,rev_a_sim_exchange};cnc3_init(&driver,transport,&cfg,0x11223344);
    if(hal_export_funct("cnc3a.read",read_cycle,0,1,0,component_id)||
       hal_export_funct("cnc3a.write",write_cycle,0,1,0,component_id))goto error;
    outputs();hal_ready(component_id);return 0;
error:
    rtapi_print_msg(RTAPI_MSG_ERR,"CNC3 refusal fixture: HAL/RTL initialization failed\n");
    if(fixture){rev_a_sim_destroy(fixture);fixture=0;}hal_exit(component_id);return -1;
}
void rtapi_app_exit(void){if(fixture)rev_a_sim_destroy(fixture);if(component_id>=0)hal_exit(component_id);}
