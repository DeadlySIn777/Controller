#include "dic_filter.h"
/* Actual sampled time, not polling-loop iteration count. No unsampled pulse
 * or physical propagation/timer-jitter claim. Configuration resets debounce. */
void dic_filter_reset(dic_filter *f){
    f->filtered=0;f->candidate=0;f->generation=0;f->initialized=0;
    for(unsigned i=0;i<24;i++)f->since[i]=0;
}
uint32_t dic_filter_sample(dic_filter *f,uint32_t raw,uint32_t now,const uint8_t groups[3],uint32_t generation){
    raw&=0xffffffu;
    if(!f->initialized||f->generation!=generation){
        f->candidate=raw;for(unsigned i=0;i<24;i++)f->since[i]=now;
        f->generation=generation;f->initialized=1;
    }
    for(unsigned i=0;i<24;i++){
        uint32_t bit=1u<<i;
        if((raw^f->candidate)&bit){f->candidate^=bit;f->since[i]=now;}
        if(((raw^f->filtered)&bit)&&((uint32_t)(now-f->since[i])>=(uint32_t)groups[i/8]))f->filtered^=bit;
    }
    return f->filtered;
}
