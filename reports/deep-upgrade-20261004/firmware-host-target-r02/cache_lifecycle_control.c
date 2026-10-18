#include "iol1.h"
#include <stdio.h>
#include <stdlib.h>
static uint16_t age(uint32_t now, uint32_t sampled, volatile uint8_t *valid) {
#ifdef CACHE_API_POINTER
    return iol1_observation_age(now,sampled,valid);
#else
    return iol1_observation_age(now,sampled,*valid);
#endif
}
int main(int argc, char **argv) {
    uint8_t valid=1; uint32_t sampled=100;
    uint16_t saturated=age(sampled+65535u,sampled,&valid);
    uint8_t valid_after_saturation=valid;
    uint16_t wrapped=age(sampled,sampled,&valid);
    printf("at_saturation=%u validity=%u at_full_wrap=%u validity=%u\n", saturated,valid_after_saturation,wrapped,valid);
    return argc != 2 || saturated != 0xffffu || wrapped != (atoi(argv[1])?0:0xffffu) || valid != atoi(argv[1]);
}
