#ifndef CNC3_RUNTIME_SIM_TRANSPORT_H
#define CNC3_RUNTIME_SIM_TRANSPORT_H
#include "manifest.h"
#ifdef __cplusplus
extern "C" {
#endif
struct cnc3_sim_stats {
    uint64_t ticks,transactions,cap3_responses,arm_commands,update_commands;
    uint64_t read_calls,write_calls;
    uint64_t step_rises[12],accepted_rises[12],encoder_edges[4],index_rises[4],provider_records;
    int64_t pin_step_count[12],plant_position[12],encoder_count[4];
    uint32_t provider_sequence,provider_error,rtl_fault;
    uint16_t rtl_armed_mask,rtl_enabled_mask,dout_applied,model_home,model_limit_low,model_limit_high;
    uint8_t physical_authority,production_profile_complete,sim_ready,reset_ready;
};
void *cnc3_sim_create(const struct cnc3_sim_manifest *);
void cnc3_sim_destroy(void *);
int cnc3_sim_cycle(void *,uint64_t period_ns);
int cnc3_sim_exchange(void *,enum cnc3_cs,const uint8_t *,uint8_t *,size_t);
uint64_t cnc3_sim_now_ns(void *);
void cnc3_sim_reset_button(void *,int);
void cnc3_sim_inputs(void *,uint32_t,uint8_t);
/* faults: bit0 drop link,1 corrupt returnedCRC,2 providerheartbeatpause,
 * 3 foreignprovideridentity,4 emergencyinhibit,5 wdM,6 wdO,7 providerCRC;
 * masks independently select12alarms,4encoderunplug,16DOshort. */
void cnc3_sim_faults(void *,uint32_t,uint16_t,uint8_t,uint16_t);
void cnc3_sim_observe(void *,struct cnc3_sim_stats *);
#ifdef __cplusplus
}
#endif
#endif
