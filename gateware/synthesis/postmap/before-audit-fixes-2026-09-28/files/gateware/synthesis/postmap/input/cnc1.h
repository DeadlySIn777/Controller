#ifndef CNC1_H
#define CNC1_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CNC1_FRAME 64
#define CNC1_AXES 6
#define CNC1_ENCODERS 2
#define CNC1_VERSION 2
enum cnc1_state { CNC1_DISCOVER, CNC1_WAIT_CAPS, CNC1_OFF, CNC1_WAIT_SYNC,
                  CNC1_READY, CNC1_WAIT_ARM, CNC1_ACTIVE, CNC1_WAIT_DISARM, CNC1_FAULT };
enum cnc1_fault { CNC1_OK, CNC1_TRANSPORT, CNC1_BAD_FRAME, CNC1_BAD_CAPS,
                  CNC1_ACK, CNC1_TIME, CNC1_ENDPOINT, CNC1_RANGE, CNC1_SEQUENCE, CNC1_COUNT, CNC1_CONFIG };
struct cnc1_caps {
    uint8_t version, steps, encoders, frequencies;
    uint32_t features, core_hz, max_rate, watchdog_ticks;
    uint16_t pulse_ticks, space_ticks, setup_ticks, hold_ticks;
};
struct cnc1_status {
    uint8_t enabled, ready, mask, faults, encoder_flags;
    uint32_t session, sequence, timestamp;
    uint32_t steps[6], encoders[2], indexes[2];
};
/* Replacement transports exchange one fixed frame and own no motion policy.
 * No hardware implementation is shipped. A production implementation must meet
 * measured deterministic deadlines and must not allocate or block unboundedly. */
struct cnc1_transport {
    void *context;
    int (*exchange)(void *, const uint8_t tx[64], uint8_t rx[64]);
};
struct cnc1_driver {
    struct cnc1_transport transport;
    struct cnc1_caps caps;
    struct cnc1_status status;
    enum cnc1_state state;
    enum cnc1_fault fault;
    uint32_t session, sequence, previous_time;
    uint32_t previous_steps[6], previous_encoders[2];
    int64_t steps[6], encoders[2], indexes[2];
    uint64_t sampled_ns, max_age_ns, samples, writes;
    uint8_t have_sample, discovered, last_enable, last_reset, enable, reset;
    uint8_t axis_mask, sent_opcode;
    uint8_t config_frozen, frozen_mask, feedback_valid;
    uint8_t config_locked;
    uint32_t config_revision, runtime_epoch;
    double position_cmd[6], scale[6], position_fb[6];
    double encoder_scale[2], encoder_position[2], index_position[2];
    double frozen_scale[6], frozen_encoder_scale[2];
};
uint16_t cnc1_crc(const uint8_t *, size_t);
void cnc1_command(uint8_t out[64], uint8_t opcode, uint8_t mask, uint32_t session,
                  uint32_t sequence, const int32_t rates[6]);
int cnc1_decode_status(const uint8_t in[64], struct cnc1_status *);
int cnc1_decode_caps(const uint8_t in[64], struct cnc1_caps *);
int64_t cnc1_counter_delta(uint32_t current, uint32_t previous);
int64_t cnc1_unwrap_index(int64_t continuous_count, uint32_t raw_count, uint32_t raw_index);
int cnc1_rate(double steps_per_second, const struct cnc1_caps *, int32_t *out);
void cnc1_init(struct cnc1_driver *, struct cnc1_transport, uint32_t session_seed);
void cnc1_read(struct cnc1_driver *, uint64_t now_ns);
void cnc1_write(struct cnc1_driver *, uint64_t now_ns, uint64_t period_ns);
/* Stopped calibration transaction. 1=acquire inhibit, 2=commit, 3=release.
 * Caller also verifies authoritative interpreter-idle and unhomes LinuxCNC.
 * Returns 0 success; 1 unsafe state; 2 stale binding; 3 invalid scales/op. */
int cnc1_configure(struct cnc1_driver *, unsigned operation, uint32_t session,
                   uint32_t revision, uint32_t epoch, const double scales[6]);

/* Compiled, actual-Verilator-RTL simulation transport. No device paths. */
void *cnc1_sim_create(void);
void cnc1_sim_destroy(void *);
int cnc1_sim_exchange(void *, const uint8_t tx[64], uint8_t rx[64]);
void cnc1_sim_cycle(void *, uint64_t period_ns);
void cnc1_sim_advance(void *, uint32_t ticks);
void cnc1_sim_reset(void *);
void cnc1_sim_inject(void *, unsigned mode);
void cnc1_sim_spindle(void *, unsigned enabled, unsigned edge_ticks);
uint64_t cnc1_sim_ticks(void *);
unsigned cnc1_sim_permission(void *);
#ifdef __cplusplus
}
#endif
#endif
