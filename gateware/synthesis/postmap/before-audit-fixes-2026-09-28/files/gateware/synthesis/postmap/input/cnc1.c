#include "cnc1.h"
#include <string.h>
#include <math.h>
#include <limits.h>

static uint32_t get32(const uint8_t *p) {
    return ((uint32_t)p[0]<<24) | ((uint32_t)p[1]<<16) | ((uint32_t)p[2]<<8) | p[3];
}
static uint16_t get16(const uint8_t *p) { return (uint16_t)(((uint16_t)p[0]<<8)|p[1]); }
static void put32(uint8_t *p, uint32_t v) {
    p[0]=(uint8_t)(v>>24); p[1]=(uint8_t)(v>>16); p[2]=(uint8_t)(v>>8); p[3]=(uint8_t)v;
}
uint16_t cnc1_crc(const uint8_t *p, size_t size) {
    uint16_t c=0xffff;
    for(size_t i=0;i<size;i++) {
        c^=(uint16_t)p[i]<<8;
        for(unsigned b=0;b<8;b++) c=(uint16_t)((c<<1)^((c&0x8000)?0x1021:0));
    }
    return c;
}
void cnc1_command(uint8_t out[64], uint8_t op, uint8_t mask, uint32_t sid,
                  uint32_t seq, const int32_t rate[6]) {
    memset(out,0,64); memcpy(out,"CNC1",4); out[4]=CNC1_VERSION; out[5]=op; out[6]=mask;
    put32(out+8,sid); put32(out+12,seq);
    if(rate) for(unsigned i=0;i<6;i++) put32(out+16+4*i,(uint32_t)rate[i]);
    uint16_t crc=cnc1_crc(out,62); out[62]=(uint8_t)(crc>>8); out[63]=(uint8_t)crc;
}
static int frame_valid(const uint8_t *in, const char *magic) {
    return !memcmp(in,magic,4) && in[4]==CNC1_VERSION && cnc1_crc(in,62)==get16(in+62);
}
int cnc1_decode_caps(const uint8_t in[64], struct cnc1_caps *c) {
    if(!frame_valid(in,"CNC2")) return -1;
    for(unsigned i=32;i<62;i++) if(in[i]) return -1;
    c->version=in[4]; c->steps=in[5]; c->encoders=in[6]; c->frequencies=in[7];
    c->features=get32(in+8); c->core_hz=get32(in+12); c->max_rate=get32(in+16);
    c->pulse_ticks=get16(in+20); c->space_ticks=get16(in+22);
    c->setup_ticks=get16(in+24); c->hold_ticks=get16(in+26); c->watchdog_ticks=get32(in+28);
    /* This driver is scoped to the fitted six/two implementation, not eight/four. */
    if(c->steps!=6 || c->encoders!=2 || c->frequencies!=0 || c->features!=31 ||
       c->core_hz!=50000000 || c->max_rate!=0x01000000 || !c->watchdog_ticks ||
       !c->pulse_ticks || !c->space_ticks || !c->setup_ticks || !c->hold_ticks) return -1;
    return 0;
}
int cnc1_decode_status(const uint8_t in[64], struct cnc1_status *s) {
    if(!frame_valid(in,"CNS1") || (in[5]&0xfc) || (in[6]&0xc0) || (in[7]&0xf0) ||
       (in[60]&0xcc) || in[61]) return -1;
    s->enabled=in[5]&1; s->ready=(in[5]>>1)&1; s->mask=in[6]; s->faults=in[7];
    s->session=get32(in+8); s->sequence=get32(in+12); s->timestamp=get32(in+16);
    for(unsigned i=0;i<6;i++) s->steps[i]=get32(in+20+4*i);
    for(unsigned i=0;i<2;i++) { s->encoders[i]=get32(in+44+4*i); s->indexes[i]=get32(in+52+4*i); }
    s->encoder_flags=in[60]; return 0;
}
int64_t cnc1_counter_delta(uint32_t current,uint32_t previous) {
    uint32_t delta=current-previous;
    return delta<=INT32_MAX ? (int64_t)delta : (int64_t)delta-INT64_C(4294967296);
}
int64_t cnc1_unwrap_index(int64_t count,uint32_t raw,uint32_t index) {
    return count-cnc1_counter_delta(raw,index);
}
int cnc1_rate(double pps,const struct cnc1_caps *c,int32_t *out) {
    if(!isfinite(pps) || !c->core_hz) return -1;
    double raw=pps*4294967296.0/c->core_hz;
    if(!isfinite(raw) || fabs(raw)>c->max_rate) return -1;
    *out=(int32_t)llround(raw); return 0;
}
static void fail(struct cnc1_driver *d,enum cnc1_fault why) {
    if(d->state!=CNC1_FAULT) {d->fault=why; d->runtime_epoch++;} /* preserve first fault */
    d->state=CNC1_FAULT; d->feedback_valid=0;
}
static int configuration(struct cnc1_driver *d) {
    if(!d->axis_mask || d->axis_mask>63) {fail(d,CNC1_CONFIG);return -1;}
    for(unsigned i=0;i<6;i++) if(!isfinite(d->scale[i]) || d->scale[i]<=0 ||
        (d->config_frozen && d->scale[i]!=d->frozen_scale[i])) {fail(d,CNC1_CONFIG);return -1;}
    for(unsigned i=0;i<2;i++) if(!isfinite(d->encoder_scale[i]) || d->encoder_scale[i]<=0 ||
        (d->config_frozen && d->encoder_scale[i]!=d->frozen_encoder_scale[i])) {fail(d,CNC1_CONFIG);return -1;}
    if(d->config_frozen && d->axis_mask!=d->frozen_mask) {fail(d,CNC1_CONFIG);return -1;}
    return 0;
}
void cnc1_init(struct cnc1_driver *d,struct cnc1_transport t,uint32_t seed) {
    memset(d,0,sizeof(*d)); d->transport=t; d->session=seed?seed:1;
    d->state=CNC1_DISCOVER; d->max_age_ns=5000000; d->axis_mask=63;
    d->runtime_epoch=1;
    for(unsigned i=0;i<6;i++) d->scale[i]=200;
    for(unsigned i=0;i<2;i++) d->encoder_scale[i]=400;
}
int cnc1_configure(struct cnc1_driver *d,unsigned op,uint32_t session,
                   uint32_t revision,uint32_t epoch,const double scales[6]) {
    if(session!=d->session || revision!=d->config_revision || epoch!=d->runtime_epoch) return 2;
    if(!d->discovered || !d->feedback_valid || d->state!=CNC1_READY ||
       d->enable || d->last_enable || d->reset || d->status.enabled || d->status.mask) return 1;
    if(op==1) {if(d->config_locked) return 1; d->config_locked=1; return 0;}
    if(!d->config_locked) return 1;
    if(op==3) {d->config_locked=0; return 0;}
    if(op!=2 || !scales || d->config_revision==UINT32_MAX) return 3;
    for(unsigned i=0;i<6;i++)
        if(!isfinite(scales[i]) || scales[i]<1 || scales[i]>1000000) return 3;
    for(unsigned i=0;i<6;i++) {
        d->scale[i]=d->frozen_scale[i]=scales[i];
        d->position_fb[i]=(double)d->steps[i]/scales[i];
    }
    d->config_revision++;
    return 0;
}
void cnc1_read(struct cnc1_driver *d,uint64_t now) {
    uint8_t tx[64],rx[64];
    if(configuration(d)) return;
    if(d->have_sample && d->state!=CNC1_FAULT && d->state!=CNC1_OFF &&
       (now<d->sampled_ns || now-d->sampled_ns>d->max_age_ns)) {fail(d,CNC1_TIME);return;}
    uint8_t op=d->state==CNC1_DISCOVER?5:0;
    cnc1_command(tx,op,0,0,0,0);
    if(d->transport.exchange(d->transport.context,tx,rx)) {fail(d,CNC1_TRANSPORT);return;}
    if(d->state==CNC1_DISCOVER) {
        struct cnc1_status status;
        if(cnc1_decode_status(rx,&status)) {fail(d,CNC1_BAD_FRAME);return;}
        d->state=CNC1_WAIT_CAPS; return;
    }
    if(d->state==CNC1_WAIT_CAPS) {
        if(cnc1_decode_caps(rx,&d->caps)) {fail(d,CNC1_BAD_CAPS);return;}
        d->discovered=1; d->state=CNC1_OFF; d->have_sample=0; return;
    }
    struct cnc1_status s;
    if(cnc1_decode_status(rx,&s)) {fail(d,CNC1_BAD_FRAME);return;}
    if(!d->config_frozen) {
        for(unsigned i=0;i<6;i++) d->frozen_scale[i]=d->scale[i];
        for(unsigned i=0;i<2;i++) d->frozen_encoder_scale[i]=d->encoder_scale[i];
        d->frozen_mask=d->axis_mask; d->config_frozen=1;
    }
    if(d->have_sample) {
        uint32_t elapsed=s.timestamp-d->previous_time;
        /* Modulo wrap allowed; >10 ms or identical timestamp is stale/reset.
         * Transport/scheduling loss does not masquerade as fresh feedback. */
        if(!elapsed || elapsed>500000) {fail(d,CNC1_TIME);return;}
        uint64_t maximum=(((uint64_t)elapsed*d->caps.max_rate+UINT32_MAX)>>32)+2;
        for(unsigned i=0;i<6;i++) {
            int64_t delta=cnc1_counter_delta(s.steps[i],d->previous_steps[i]);
            if(delta>(int64_t)maximum || delta<-(int64_t)maximum) {fail(d,CNC1_COUNT);return;}
        }
        /* Logical RTL ceiling only: one decoded transition/core tick. This is
         * not a physically qualified encoder bandwidth or input filter. */
        for(unsigned i=0;i<2;i++) {
            int64_t delta=cnc1_counter_delta(s.encoders[i],d->previous_encoders[i]);
            if(delta>(int64_t)elapsed+2 || delta<-(int64_t)elapsed-2) {fail(d,CNC1_COUNT);return;}
        }
        for(unsigned i=0;i<6;i++) d->steps[i]+=cnc1_counter_delta(s.steps[i],d->previous_steps[i]);
        for(unsigned i=0;i<2;i++) d->encoders[i]+=cnc1_counter_delta(s.encoders[i],d->previous_encoders[i]);
    } else {
        for(unsigned i=0;i<6;i++) d->steps[i]=cnc1_counter_delta(s.steps[i],0);
        for(unsigned i=0;i<2;i++) d->encoders[i]=cnc1_counter_delta(s.encoders[i],0);
    }
    for(unsigned i=0;i<6;i++) {
        d->previous_steps[i]=s.steps[i];
        if(!isfinite(d->scale[i]) || d->scale[i]<=0) {fail(d,CNC1_RANGE);return;}
        d->position_fb[i]=(double)d->steps[i]/d->scale[i];
    }
    for(unsigned i=0;i<2;i++) {
        d->previous_encoders[i]=s.encoders[i];
        if(!isfinite(d->encoder_scale[i]) || d->encoder_scale[i]<=0) {fail(d,CNC1_RANGE);return;}
        /* Nearest modulo index relative to the current unwrapped count. Valid
         * only while index age is <2^31 counts; not an index-event FIFO. */
        d->indexes[i]=cnc1_unwrap_index(d->encoders[i],s.encoders[i],s.indexes[i]);
        d->encoder_position[i]=(double)d->encoders[i]/d->encoder_scale[i];
        d->index_position[i]=(double)d->indexes[i]/d->encoder_scale[i];
    }
    d->previous_time=s.timestamp; d->have_sample=1; d->sampled_ns=now; d->samples++;
    d->status=s;
    if(d->state==CNC1_FAULT || d->state==CNC1_OFF) return;
    if(s.session!=d->session || s.sequence!=d->sequence) {fail(d,CNC1_ACK);return;}
    if(s.faults || !s.ready) {fail(d,CNC1_ENDPOINT);return;}
    if(d->state==CNC1_WAIT_SYNC || d->state==CNC1_WAIT_DISARM) {
        if(s.enabled || s.mask) {fail(d,CNC1_ACK);return;}
        d->state=CNC1_READY;
    } else if(d->state==CNC1_WAIT_ARM) {
        if(!s.enabled || s.mask!=d->axis_mask) {fail(d,CNC1_ACK);return;}
        d->state=CNC1_ACTIVE;
    } else if(d->state==CNC1_ACTIVE && (!s.enabled || s.mask!=d->axis_mask)) fail(d,CNC1_ACK);
    if(d->state!=CNC1_FAULT) d->feedback_valid=1;
}
static void send_frame(struct cnc1_driver *d,uint8_t op,uint8_t mask,const int32_t *rates) {
    uint8_t tx[64],rx[64];
    cnc1_command(tx,op,mask,d->session,d->sequence,rates);
    if(d->transport.exchange(d->transport.context,tx,rx)) {fail(d,CNC1_TRANSPORT);return;}
    /* Snapshot precedes commit: never use this response to acknowledge op. */
    struct cnc1_status snapshot;
    if(cnc1_decode_status(rx,&snapshot)) {fail(d,CNC1_BAD_FRAME);return;}
    d->sent_opcode=op; d->writes++;
}
void cnc1_write(struct cnc1_driver *d,uint64_t now,uint64_t period) {
    unsigned rise=d->enable&&!d->last_enable, reset=d->reset&&!d->last_reset;
    if(d->enable!=d->last_enable || reset) d->runtime_epoch++;
    d->last_enable=d->enable; d->last_reset=d->reset;
    if(d->config_locked && d->enable) {fail(d,CNC1_CONFIG);return;}
    if(configuration(d)) return;
    if(!d->discovered) {
        if(reset && !d->enable && d->state==CNC1_FAULT) {
            d->state=CNC1_DISCOVER; d->fault=CNC1_OK; d->have_sample=0;
        }
        return;
    }
    if(reset && !d->enable && (d->state==CNC1_OFF || d->state==CNC1_FAULT || d->state==CNC1_READY)) {
        /* A stopped explicit reset creates a new epoch, never an automatic ARM. */
        d->session++; if(!d->session) d->session=1;
        d->sequence=0; d->fault=CNC1_OK; d->have_sample=0;
        d->state=CNC1_WAIT_SYNC; send_frame(d,1,0,0); return;
    }
    if(d->state==CNC1_OFF || d->state==CNC1_FAULT) return; /* no feed => RTL watchdog */
    if(!d->have_sample || now<d->sampled_ns || now-d->sampled_ns>d->max_age_ns) {fail(d,CNC1_TIME);return;}
    if(!period || period>10000000) {fail(d,CNC1_TIME);return;}
    if(d->state==CNC1_WAIT_SYNC || d->state==CNC1_WAIT_ARM || d->state==CNC1_WAIT_DISARM) return;
    if(d->sequence>=UINT32_MAX-1) {fail(d,CNC1_SEQUENCE);return;}
    if(d->state==CNC1_READY && rise) {
        d->sequence++; d->state=CNC1_WAIT_ARM; send_frame(d,2,d->axis_mask,0); return;
    }
    if(d->state!=CNC1_ACTIVE) return;
    if(!d->enable) {d->sequence++; d->state=CNC1_WAIT_DISARM; send_frame(d,4,0,0);return;}
    int32_t rates[6];
    for(unsigned i=0;i<6;i++) {
        double target=d->position_cmd[i]*d->scale[i];
        if(!isfinite(target) || fabs(target)>1e12) {fail(d,CNC1_RANGE);return;}
        /* Position-mode STEP servo: emitted counts close only the digital pulse
         * accumulator, not a physical axis. One-cycle count-error correction. */
        double pps=((double)llround(target)-(double)d->steps[i])*1e9/(double)period;
        if(!(d->axis_mask&(1u<<i))) pps=0;
        if(cnc1_rate(pps,&d->caps,&rates[i])) {fail(d,CNC1_RANGE);return;}
    }
    d->sequence++; send_frame(d,3,d->axis_mask,rates);
}
