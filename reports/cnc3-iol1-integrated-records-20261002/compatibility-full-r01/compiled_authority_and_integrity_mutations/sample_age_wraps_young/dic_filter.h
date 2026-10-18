#ifndef CNC_DIC_FILTER_H
#define CNC_DIC_FILTER_H
#include <stdint.h>
typedef struct { uint32_t filtered,candidate,since[24],generation;uint8_t initialized; } dic_filter;
void dic_filter_reset(dic_filter *f);
uint32_t dic_filter_sample(dic_filter *f,uint32_t raw,uint32_t now,const uint8_t groups[3],uint32_t generation);
#endif
