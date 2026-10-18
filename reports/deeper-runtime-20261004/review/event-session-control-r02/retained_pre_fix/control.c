
#include "cnc3.h"
#include <stdio.h>
#include <string.h>
struct endpoint { unsigned post_sync; };
static int exchange(void *context, enum cnc3_cs cs, const uint8_t *tx, uint8_t *rx, size_t n) {
    (void)tx;struct endpoint *e=context;
    if(cs!=CNC3_CS_CMD || n!=CNC3_CS_CMD_BYTES)return -1;
    struct cnc3_status s;memset(&s,0,sizeof s);
    s.session=e->post_sync?18:17;s.event_seq=1;s.event_type=1;
    s.event_source=e->post_sync?1:0;s.event_ticks=e->post_sync?200:100;
    s.telemetry_source=0xff;cnc3_encode_cns3(rx,&s);return 0;
}
int main(void) {
    struct endpoint endpoint={0};struct cnc3_config config;memset(&config,0,sizeof config);
    config.axis_mask=1;config.scale[0]=640;config.maximum_velocity[0]=10;
    for(unsigned i=0;i<4;++i)config.timing[0][i]=250;
    struct cnc3_transport transport={&endpoint,exchange,CNC3_SIM_TRANSPORT_ID};
    struct cnc3_driver driver;cnc3_init(&driver,transport,&config,17);
    driver.discovered=1;driver.state=CNC3_OFF;driver.watchdog_ns=5000000;
    cnc3_write(&driver,0,1000000);
    if(driver.events_stored!=1||driver.probe_events[0]!=1||driver.event_ack!=1)return 2;
    driver.reset=1;cnc3_write(&driver,1000000,1000000);
    unsigned ack_after_sync=driver.event_ack,dedup_after_sync=driver.last_event_seq;
    endpoint.post_sync=1;driver.reset=0;cnc3_write(&driver,2000000,1000000);
    printf("{\"events_stored\":%llu,\"old_probe_events\":%llu,\"new_probe_events\":%llu,\"ack_after_sync\":%u,\"dedup_after_sync\":%u,\"event_ack\":%u,\"history_preserved\":%s,\"new_event_stored\":%s}\n",
      (unsigned long long)driver.events_stored,(unsigned long long)driver.probe_events[0],
      (unsigned long long)driver.probe_events[1],ack_after_sync,dedup_after_sync,driver.event_ack,
      driver.probe_events[0]==1?"true":"false",driver.probe_events[1]==1?"true":"false");
    return 0;
}
