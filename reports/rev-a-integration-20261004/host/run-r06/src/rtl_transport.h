#ifndef REV_A_RTL_TRANSPORT_H
#define REV_A_RTL_TRANSPORT_H
#include <stddef.h>
#include <stdint.h>
#include "cnc3.h"
#ifdef __cplusplus
extern "C" {
#endif
void *rev_a_sim_create(void);
void rev_a_sim_destroy(void *);
void rev_a_sim_advance(void *, uint64_t);
int rev_a_sim_exchange(void *, enum cnc3_cs, const uint8_t *, uint8_t *, size_t);
uint64_t rev_a_sim_ticks(void *);
uint32_t rev_a_sim_metric(void *, unsigned);
void rev_a_sim_corrupt(void *, int);
/* Metrics: 0 transactions, 1 CAP3, 2 ARM, 3 UPDATE, 4 CONFIGURE,
 * 5 enabled mask, 6 armed mask, 7 endpoint session, 8 output authority,
 * 9 malformed transaction count, 10..21 independently observed STEP rises. */
#ifdef __cplusplus
}
#endif
#endif
