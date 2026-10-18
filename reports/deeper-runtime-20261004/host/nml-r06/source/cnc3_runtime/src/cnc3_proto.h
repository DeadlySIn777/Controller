/* SPDX-License-Identifier: LicenseRef-Proprietary */
/* CNC3 (IS-1, ABI 3) host-link and IOL1 card-link codec.
 *
 * Positions come from the generated cnc3_layout.h and acceptance rules from the generated
 * cnc3_rules.h, both produced from spec/protocol.json by gateware/v3/tools/gen_c_layout.py.
 * The Python reference codec (gateware/v3/tools/protocol_v3.py) applies the same rules in the
 * same order; cnc3/tests/test_proto.c checks both agree on every golden vector.
 *
 * Structural rules only. Stateful acceptance (current session, next sequence, armed state,
 * installed channels, configured clamps) belongs to the endpoint and the driver state machine.
 * No allocation, no blocking, no floating point: safe to call from the servo thread. */
#ifndef CNC3_PROTO_H
#define CNC3_PROTO_H
#include <stddef.h>
#include <stdint.h>
#include "cnc3_layout.h"
#ifdef __cplusplus
extern "C" {
#endif

#define CNC3_CHANNELS 12
#define CNC3_ENCODERS 12
#define CNC3_CHANNEL_MASK_LIMIT 0x0FFFu
#define CNC3_MAX_RATE 0x01000000L /* DDS rate limit carried from the record; see CAP3 page 0 */

/* Result codes. Names match protocol_v3.ProtocolError codes exactly. */
enum cnc3_result {
    CNC3_VALID = 0,
    CNC3_E_UNKNOWN_CS, CNC3_E_LENGTH, CNC3_E_CRC, CNC3_E_MAGIC, CNC3_E_ABI, CNC3_E_UNKNOWN_OPCODE,
    CNC3_E_WRONG_CS, CNC3_E_MASK_WIDTH, CNC3_E_SEQUENCE_RULE, CNC3_E_SESSION_RULE, CNC3_E_MASK_RULE,
    CNC3_E_RATE_ON_NON_UPDATE, CNC3_E_FIELD_NOT_ALLOWED, CNC3_E_PAYLOAD_NONZERO, CNC3_E_FIELD_RANGE,
    CNC3_E_EMBEDDED_FRAME, CNC3_E_RESERVED_NONZERO, CNC3_E_FIELD_BITS, CNC3_E_FIELD_RELATION,
    CNC3_E_UNMASKED_RATE, CNC3_E_SOF, CNC3_E_VERSION, CNC3_E_CLASS, CNC3_E_SLOT, CNC3_E_EPOCH,
    CNC3_E_CONTROL, CNC3_E_SEQUENCE, CNC3_E_RATE_CLAMP,
    CNC3_RESULT_COUNT
};
const char *cnc3_result_name(int result);

enum cnc3_cs { CNC3_CS_FB = 0, CNC3_CS_CMD = 1, CNC3_IOL1 = 2 };

uint16_t cnc3_crc16(const uint8_t *data, size_t length);  /* CRC-16/CCITT-FALSE */
uint32_t cnc3_crc32c(const uint8_t *data, size_t length); /* CRC-32C (Castagnoli) */

/* Big-endian field access. */
uint32_t cnc3_get(const uint8_t *p, unsigned size);
void cnc3_put(uint8_t *p, unsigned size, uint32_t value);

/* Write the frame CRC into the last two (host) or four (IOL1) bytes. */
void cnc3_seal_host(uint8_t *frame, size_t length);
void cnc3_seal_iol1(uint8_t frame[CNC3_IOL1_COMMAND_LEN]);

/* Receiver-side validation, same order and codes as protocol_v3.validate_command. */
int cnc3_validate_command(enum cnc3_cs cs, const uint8_t *frame, size_t length);
/* expected_class / expected_slot < 0: not checked. Same order as protocol_v3.validate_iol1. */
int cnc3_validate_iol1_command(const uint8_t *frame, size_t length, int expected_class, int expected_slot);
/* Validate by the golden vector's chip-select label ("CS_FB", "CS_CMD" or "IOL1"). */
int cnc3_validate_labelled(const char *label, const uint8_t *frame, size_t length);

/* CS_CMD command contents. Unused fields zero. */
struct cnc3_cmd {
    uint8_t opcode;
    uint16_t channel_mask;
    uint32_t session, sequence;
    int32_t rate[CNC3_CHANNELS];
    uint16_t dout_image;
    uint8_t output_requests;
    uint16_t index_arm_mask;
    uint8_t probe_arm;
    uint16_t pwm_duty[2];
    uint16_t aout_code[2];
    uint16_t dout_fault_clear;
    uint8_t selftest_target; /* SELFTEST byte16, 1=M or2=O; not a DDS word */
};
/* Encode, seal and validate. Returns CNC3_VALID or the first rule the contents break
 * (the frame is still written, so a test can inspect it). UPDATE rates are also checked
 * against CNC3_MAX_RATE (CNC3_E_RATE_CLAMP). */
int cnc3_build_cmd(uint8_t out[CNC3_CS_CMD_BYTES], const struct cnc3_cmd *cmd);
/* CS_FB command with a raw payload placed at byte 16 (at most CNC3_PAYLOAD_SIZE bytes). */
int cnc3_build_fb(uint8_t out[CNC3_CS_FB_BYTES], uint8_t opcode, uint16_t mask, uint32_t session,
                  uint32_t sequence, const uint8_t *payload, size_t payload_length);
int cnc3_build_fb_read(uint8_t out[CNC3_CS_FB_BYTES], uint32_t session, uint8_t event_ack,
                       uint8_t telemetry_source, uint8_t telemetry_page);

/* CNF3 feedback snapshot (section 3.6). */
struct cnc3_feedback {
    uint8_t state;
    uint16_t armed_mask;
    uint32_t session, last_sequence, snapshot_ticks, fault_word;
    uint16_t installed_mask, step_timing_latched, alarm_levels, alarm_trip_latched, enable_after_gating,
        pos_continuity;
    uint32_t step_count[CNC3_CHANNELS];    /* u24 */
    uint32_t encoder_count[CNC3_ENCODERS]; /* u24 */
    uint16_t encoder_valid_mask, encoder_illegal_mask, encoder_fault_mask, index_armed_mask;
    uint32_t mpg_count; /* u24 */
    uint8_t mpg_status, probe_status, event_status;
    uint32_t freq_count[2]; /* u24 */
    uint32_t freq_last_edge_ticks[2];
    uint32_t din; /* u24 */
    uint8_t din_age;
    uint16_t dout_applied, dout_fault_latched;
    uint8_t process_pwm_state, aout_state;
    int16_t ain[4];
    uint8_t ain_status, ain_age;
    uint8_t port_status[6]; /* L0 DIC, L1 DOA, L2 DOB, L3 ACC, S0 EIA, S1 EX8 */
    uint8_t mx4_expansion, slot_summary;
    uint32_t safety_power_word;
    uint8_t config_generation, io_config_generation;
    uint16_t pendant_inputs;
    uint8_t ex8_expansion, port_status_l4_xs;
};
/* CNS3 status (section 3.8). */
struct cnc3_status {
    uint8_t state;
    uint16_t armed_mask;
    uint32_t session, last_sequence, snapshot_ticks, fault_word;
    uint16_t dout_image_in_force, dout_applied, dout_fault_latched;
    uint32_t safety_power_word;
    uint16_t pos_continuity;
    uint8_t event_seq, event_type, event_source, event_flags;
    uint32_t event_ticks;
    uint32_t event_value[4]; /* u24 */
    uint8_t telemetry_source, telemetry_page, telemetry_counter, telemetry_validity;
    uint32_t telemetry_rx_ticks;
    uint16_t telemetry_card_age_us;
    uint8_t telemetry_data[CNC3_CMD_RESPONSE_CNS3_TELEMETRY_DATA_SIZE];
    uint16_t telemetry_rotation, last_update_interval_us, late_update_count;
    uint32_t slot_status;
};
/* Length, CRC, magic and ABI checks, then decode. Returns CNC3_VALID or a result code. */
int cnc3_decode_cnf3(const uint8_t *frame, size_t length, struct cnc3_feedback *out);
int cnc3_decode_cns3(const uint8_t *frame, size_t length, struct cnc3_status *out);
/* Encoders for endpoint models and tests (the FPGA produces these on hardware). */
void cnc3_encode_cnf3(uint8_t out[CNC3_FB_RESPONSE_CNF3_LEN], const struct cnc3_feedback *in);
void cnc3_encode_cns3(uint8_t out[CNC3_CMD_RESPONSE_CNS3_LEN], const struct cnc3_status *in);

/* CAP3 page 0 (section 3.14), returned on CS_FB by the transaction after READ_PAGE 0. */
struct cnc3_caps {
    uint8_t step_channels, installed_channels, encoders_supported, encoders_base, encoders_installed, mpg_ports;
    uint32_t feature_bitmap, core_hz, max_rate;
    uint16_t reference_timing[4], timing_min, timing_max;
    uint32_t watchdog_ticks;
    uint16_t alarm_sample_ticks;
    uint8_t filter_samples;
    uint16_t fb_frame_bytes, cmd_frame_bytes;
    uint8_t min_sclk_divider, bank_count, bank_layout[4], expansion_state, mod_id_latched,
        accepted_module_class, accepted_encoder_expansion_class;
    uint32_t qualification_ticks, gateware_build_id;
    char spec_revision[5];
    uint16_t event_ring_depth, telemetry_entries, progress_pulse_ticks;
};
/* Length, CRC, magic 'CAP3', ABI and page 0; zero fields must be zero. Returns a result code. */
int cnc3_decode_cap3_page0(const uint8_t *frame, size_t length, struct cnc3_caps *out);
void cnc3_encode_cap3_page0(uint8_t out[CNC3_CAP3_PAGE0_LEN], const struct cnc3_caps *in);

/* Extend a wrapping 24-bit counter: previous_total + signed shortest delta modulo 2^24. */
int64_t cnc3_unwrap_u24(int64_t previous_total, uint32_t raw24);

#ifdef __cplusplus
}
#endif
#endif
