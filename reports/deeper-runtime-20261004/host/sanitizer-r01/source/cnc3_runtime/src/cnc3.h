/* SPDX-License-Identifier: LicenseRef-Proprietary */
/* CNC3 SIM2 disconnected runtime driver. ABI 3 frozen frame sizes.
 * Separate from retained physical IS-1 / incomplete IS-2 drivers; this source
 * never accepts production capabilities and is not physical qualification.
 *
 * Owns the per-cycle protocol of section 3.2: cnc3_read() performs the CS_FB transaction
 * (FB_READ -> CNF3 feedback, or discovery/CONFIGURE while not yet configured) and
 * cnc3_write() performs the CS_CMD transaction (SYNC/ARM/UPDATE/DISARM/NOP -> CNS3 status,
 * event ring head and telemetry mirror entry). All frames go through cnc3_proto.
 *
 * Safety rules carried from cnc1 and IS-1: the first fault is latched and preserved; nothing
 * re-arms automatically (a stopped reset starts a new session with SYNC, and only a later
 * enable rising edge sends ARM); an endpoint fault word, a rejected or implausible frame, a
 * stale sample or an unacknowledged command all disarm on the host side, and the endpoint's own
 * 5 ms watchdog stops pulses when UPDATEs stop. No allocation, blocking or libc I/O. */
#ifndef CNC3_H
#define CNC3_H
#include <stdint.h>
#include "cnc3_proto.h"
#ifdef __cplusplus
extern "C" {
#endif

enum cnc3_state { CNC3_DISCOVER, CNC3_WAIT_CAPS, CNC3_CONFIGURE, CNC3_WAIT_CONFIG, CNC3_OFF, CNC3_WAIT_SYNC,
                  CNC3_READY, CNC3_WAIT_ARM, CNC3_ACTIVE, CNC3_WAIT_DISARM, CNC3_FAULT };
enum cnc3_fault { CNC3_FAULT_NONE, CNC3_FAULT_TRANSPORT, CNC3_FAULT_BAD_FRAME, CNC3_FAULT_BAD_CAPS, CNC3_FAULT_ACK,
                  CNC3_FAULT_TIME, CNC3_FAULT_ENDPOINT, CNC3_FAULT_RANGE, CNC3_FAULT_SEQUENCE, CNC3_FAULT_COUNT,
                  CNC3_FAULT_CONFIG, CNC3_FAULT_QUALIFICATION };

/* Fault-word bits of section 3.9 used by the driver. */
#define CNC3_FW_LINK (1u << 0)
#define CNC3_FW_WATCHDOG (1u << 1)
#define CNC3_FW_CONFIG_REJECTED (1u << 7)
#define CNC3_FW_POWER_CYCLE ((1u << 5) | (1u << 6)) /* EXPANSION_CHANGED, EXPANSION_INVALID */
/* CNF3/CNS3 state byte (section 3.6). */
#define CNC3_ST_PERMISSION 0x01u
#define CNC3_ST_READY 0x02u
#define CNC3_ST_QUALIFIED 0x04u
#define CNC3_ST_CONFIG_VALID 0x08u

/* One transaction on one chip select; length is exact (176 on CS_FB, 96 on CS_CMD).
 * Returns 0 on a completed transfer. Must be deterministic and must not block unboundedly. */
struct cnc3_transport {
    void *context;
    int (*exchange)(void *context, enum cnc3_cs cs, const uint8_t *tx, uint8_t *rx, size_t length);
    uint32_t simulation_identity; /* factory-only disconnected context marker */
};
#define CNC3_SIM_TRANSPORT_ID UINT32_C(0x53494D32)
#define CNC3_SIM_GATEWARE_BUILD UINT32_C(0xD3494D32)

#define CNC3_EVENT_LOG 64
struct cnc3_event {
    uint8_t seq, type, source, flags;
    uint32_t ticks;
    uint32_t value[4];
    uint64_t cycle; /* host cycle that stored it (fault-history ordering) */
};
struct cnc3_telemetry {
    uint8_t valid, source, page, counter, validity;
    uint32_t rx_ticks;
    uint16_t card_age_us;
    uint8_t data[CNC3_CMD_RESPONSE_CNS3_TELEMETRY_DATA_SIZE];
};
#define CNC3_TELEMETRY_SLOTS 64

struct cnc3_config {
    uint16_t axis_mask;          /* joints driven by this machine: 0x00FF (8) or up to 0x0FFF (12) */
    double scale[CNC3_CHANNELS]; /* steps per machine unit */
    double maximum_velocity[CNC3_CHANNELS]; /* saved mm/s limits for commands */
    uint16_t timing[CNC3_CHANNELS][4]; /* STEP high, STEP low min, DIR setup, DIR hold (core ticks) */
    uint16_t alarm_trip_mask, alarm_on_no_current;
    uint32_t config_hash;
    uint8_t encoder_expansion_class, encoder_filter_ticks, mpg_config;
    uint16_t required_encoder_mask;
    uint16_t dout_enable_mask; /* simulated supported DO mask, never a rating */
};

struct cnc3_driver {
    struct cnc3_transport transport;
    struct cnc3_config config;
    struct cnc3_caps caps;
    struct cnc3_feedback fb;  /* last accepted CNF3 */
    struct cnc3_status status; /* last accepted CNS3 */
    enum cnc3_state state;
    enum cnc3_fault fault;
    uint32_t endpoint_fault_word; /* fault word that caused CNC3_FAULT_ENDPOINT */
    int last_result;              /* cnc3_result of the last rejected frame */
    uint32_t session, sequence;
    uint64_t servo_period_ns, watchdog_ns, sampled_ns, cycles, writes;
    uint32_t previous_ticks;
    uint8_t have_sample, feedback_valid, discovered, caps_attempts;
    uint8_t enable, reset, last_enable, last_reset;
    uint8_t commissioned,commission_phase,commission_wait;
    uint64_t commission_started_ns;
    uint16_t dout_image,index_arm_mask;
    uint8_t probe_arm;
    int64_t steps[CNC3_CHANNELS], encoders[CNC3_ENCODERS];
    double position_cmd[CNC3_CHANNELS], position_fb[CNC3_CHANNELS];
    double previous_command[CNC3_CHANNELS];
    uint8_t have_command;
    uint16_t position_valid_mask; /* configured joints with pos_continuity set */
    uint8_t event_ack, last_event_seq;
    struct cnc3_event events[CNC3_EVENT_LOG];
    unsigned event_head, event_count;
    uint64_t events_stored;
    uint64_t probe_events[2],index_events[4];
    struct cnc3_telemetry telemetry[CNC3_TELEMETRY_SLOTS];
};

/* Maximum CAP3 polls while the endpoint reports installed_channels 0 (qualification running). */
#define CNC3_CAPS_ATTEMPTS 64

void cnc3_init(struct cnc3_driver *, struct cnc3_transport, const struct cnc3_config *, uint32_t session_seed);
void cnc3_read(struct cnc3_driver *, uint64_t now_ns, uint64_t period_ns);
void cnc3_write(struct cnc3_driver *, uint64_t now_ns, uint64_t period_ns);
/* steps/s -> DDS rate word; -1 when non-finite or beyond caps.max_rate. */
int cnc3_rate(double steps_per_second, const struct cnc3_caps *, int32_t *out);
const char *cnc3_state_name(enum cnc3_state);
const char *cnc3_fault_name(enum cnc3_fault);

#ifdef __cplusplus
}
#endif
#endif
