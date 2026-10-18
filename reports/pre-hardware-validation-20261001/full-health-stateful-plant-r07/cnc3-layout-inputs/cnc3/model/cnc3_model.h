/* SPDX-License-Identifier: LicenseRef-Proprietary */
/* Behavioural reference model of the IS-1 motion-card endpoint's host-link semantics.
 *
 * Scope (what it models): exact frame validation through cnc3_proto; the stateful acceptance
 * rules of section 3.4 for NOP, SYNC, ARM, UPDATE, DISARM, READ_PAGE (CAP3 page 0), CONFIGURE,
 * FB_READ, CLEAR_CONTINUITY and SELFTEST; snapshot-before-commit responses; the shared
 * sequence counter; LINK, WATCHDOG, CONFIG_REJECTED and expansion faults of section 3.9 with
 * disarm-all responses; the 5 ms motion watchdog; DDS step generation on twelve channels in
 * closed form; position continuity; and the event ring of section 3.11 (FAULT_LATCHED records,
 * acknowledgement pop).
 *
 * Not modelled (named, not hidden): pulse-level STEP/DIR timing, encoders, probes, frequency
 * inputs, PWM, the IOL1 card links and every I/O opcode except IO_DISABLE, telemetry mirror
 * contents, and pages 1-3. Those belong to the gateware (gateware/v3) and its RTL testbench.
 * This model is a host test double and a differential reference, not the FPGA implementation. */
#ifndef CNC3_MODEL_H
#define CNC3_MODEL_H
#include <stdint.h>
#include "cnc3_proto.h"
#ifdef __cplusplus
extern "C" {
#endif

#define CNC3_MODEL_WATCHDOG_TICKS 250000u /* 5 ms at 50 MHz (CAP3 page 0) */
#define CNC3_MODEL_RING 256

struct cnc3_model_event { uint8_t type, source, flags, seq; uint32_t ticks; uint32_t value[4]; };

struct cnc3_model {
    uint64_t ticks;
    uint8_t installed_channels; /* 8 (base) or 12 (MX4 fitted and qualified) */
    uint16_t installed_mask;
    uint32_t session, last_sequence, fault_word;
    uint8_t config_valid, expected_module_class, page_pending, selftest_ok;
    uint16_t required_mask, alarm_trip_mask, armed_mask, pos_continuity;
    uint32_t servo_period_us, config_hash;
    int32_t rate[CNC3_CHANNELS];
    int64_t phase[CNC3_CHANNELS];  /* DDS accumulator, 0 .. 2^32-1 */
    uint32_t steps[CNC3_CHANNELS]; /* 32-bit emitted-step counters; CNF3 carries the low 24 bits */
    uint64_t progress_tick, last_update_tick;
    uint16_t last_update_interval_us, late_update_count;
    struct cnc3_model_event ring[CNC3_MODEL_RING];
    unsigned ring_head, ring_count;
    uint8_t next_event_seq, shown_event_seq;
    /* Fault injection. */
    unsigned corrupt_responses; /* flip one bit in the next N responses */
    unsigned corrupt_commands;  /* flip one bit in the next N commands before validation */
    uint8_t remove_expansion;   /* MX4 presence lost after qualification */
    uint64_t accepted, rejected;
};

void cnc3_model_init(struct cnc3_model *, unsigned installed_channels);
/* Transport entry point with the cnc3_transport exchange signature. */
int cnc3_model_exchange(void *model, enum cnc3_cs cs, const uint8_t *tx, uint8_t *rx, size_t length);
/* Advance core time; steps accrue on armed channels; the watchdog trips when overdue. */
void cnc3_model_advance(struct cnc3_model *, uint64_t ticks);

#ifdef __cplusplus
}
#endif
#endif
