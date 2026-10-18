/* SPDX-License-Identifier: LicenseRef-Proprietary */
#include "cnc3_proto.h"
#include "cnc3_rules.h"
#include <string.h>

static const char *const result_names[CNC3_RESULT_COUNT] = {
    "valid", "UNKNOWN_CS", "LENGTH", "CRC", "MAGIC", "ABI", "UNKNOWN_OPCODE", "WRONG_CS", "MASK_WIDTH",
    "SEQUENCE_RULE", "SESSION_RULE", "MASK_RULE", "RATE_ON_NON_UPDATE", "FIELD_NOT_ALLOWED", "PAYLOAD_NONZERO",
    "FIELD_RANGE", "EMBEDDED_FRAME", "RESERVED_NONZERO", "FIELD_BITS", "FIELD_RELATION", "UNMASKED_RATE", "SOF",
    "VERSION", "CLASS", "SLOT", "EPOCH", "CONTROL", "SEQUENCE", "RATE_CLAMP"};

const char *cnc3_result_name(int result) {
    return result >= 0 && result < CNC3_RESULT_COUNT ? result_names[result] : "UNKNOWN_RESULT";
}

uint16_t cnc3_crc16(const uint8_t *p, size_t n) {
    uint16_t c = 0xFFFF;
    for (size_t i = 0; i < n; i++) {
        c ^= (uint16_t)(p[i] << 8);
        for (unsigned b = 0; b < 8; b++) c = (uint16_t)((c << 1) ^ ((c & 0x8000) ? 0x1021 : 0));
    }
    return c;
}

uint32_t cnc3_crc32c(const uint8_t *p, size_t n) {
    uint32_t c = 0xFFFFFFFFu;
    for (size_t i = 0; i < n; i++) {
        c ^= p[i];
        for (unsigned b = 0; b < 8; b++) c = (c >> 1) ^ ((c & 1u) ? 0x82F63B78u : 0u);
    }
    return c ^ 0xFFFFFFFFu;
}

uint32_t cnc3_get(const uint8_t *p, unsigned size) {
    uint32_t v = 0;
    for (unsigned i = 0; i < size; i++) v = (v << 8) | p[i];
    return v;
}

void cnc3_put(uint8_t *p, unsigned size, uint32_t v) {
    for (unsigned i = 0; i < size; i++) p[i] = (uint8_t)(v >> (8 * (size - 1 - i)));
}

void cnc3_seal_host(uint8_t *frame, size_t length) {
    cnc3_put(frame + length - 2, 2, cnc3_crc16(frame, length - 2));
}

void cnc3_seal_iol1(uint8_t frame[CNC3_IOL1_COMMAND_LEN]) {
    cnc3_put(frame + CNC3_IOL1_COMMAND_CRC32C_OFF, 4, cnc3_crc32c(frame, CNC3_IOL1_COMMAND_CRC32C_OFF));
}

static int any_nonzero(const uint8_t *p, size_t lo, size_t hi) { /* inclusive */
    for (size_t i = lo; i <= hi; i++)
        if (p[i]) return 1;
    return 0;
}

static int in_ranges(uint32_t v, const struct cnc3_range *r, unsigned count) {
    for (unsigned i = 0; i < count; i++)
        if (v >= r[i].lo && v <= r[i].hi) return 1;
    return 0;
}

static const struct cnc3_opcode_rule *opcode_rule(uint8_t code) {
    for (size_t i = 0; i < CNC3_OPCODE_RULE_COUNT; i++)
        if (cnc3_opcode_rules[i].code == code) return &cnc3_opcode_rules[i];
    return NULL;
}

/* Bytes the opcode gives its own meaning (byte 16, an embedded IOL1 frame). */
static int owned(const struct cnc3_opcode_rule *r, size_t i) {
    return (r->byte16_count && i == 16) || (r->embedded && i >= r->emb_lo && i <= r->emb_hi);
}

static int check_field(const struct cnc3_field_rule *f, const uint8_t *p) {
    if (!f->elem_size) return f->zero && any_nonzero(p, 0, f->size - 1u) ? CNC3_E_RESERVED_NONZERO : CNC3_VALID;
    for (unsigned e = 0; e < f->count; e++) {
        uint32_t v = cnc3_get(p + e * f->elem_size, f->elem_size);
        if (f->zero && v) return CNC3_E_RESERVED_NONZERO;
        if (f->range_count && !in_ranges(v, f->ranges, f->range_count)) return CNC3_E_FIELD_RANGE;
        if (f->nonzero && !v) return CNC3_E_FIELD_RANGE;
        if (v & f->zero_bits) return CNC3_E_FIELD_BITS;
    }
    return CNC3_VALID;
}

/* protocol_v3.check_layout: field rules in order, then relations in order. */
static int check_layout(int layout, const uint8_t *base, const struct cnc3_opcode_rule *op, size_t base_offset) {
    const struct cnc3_layout_rules *l = &cnc3_layouts[layout];
    for (unsigned i = 0; i < l->field_count; i++) {
        const struct cnc3_field_rule *f = &l->fields[i];
        int skip = 0;
        if (!f->size) continue;
        for (unsigned b = 0; op && b < f->size; b++)
            if (owned(op, base_offset + f->offset + b)) skip = 1;
        if (skip) continue;
        int r = check_field(f, base + f->offset);
        if (r) return r;
    }
    for (unsigned i = 0; i < l->field_count; i++) {
        const struct cnc3_field_rule *f = &l->fields[i];
        if (!f->relation || !f->elem_size) continue;
        uint32_t v = cnc3_get(base + f->offset, f->elem_size);
        uint32_t other = cnc3_get(base + f->rel_offset, f->rel_size);
        if (f->relation == 1 && (v & other)) return CNC3_E_FIELD_RELATION;
        if (f->relation == 2 && (v & ~other)) return CNC3_E_FIELD_RELATION;
        if (f->relation == 3 && (v & f->rel_bits) && !other) return CNC3_E_FIELD_RELATION;
        if (f->relation == 4 && (v & f->rel_bits) && other != f->rel_value) return CNC3_E_FIELD_RELATION;
    }
    return CNC3_VALID;
}

int cnc3_validate_iol1_command(const uint8_t *p, size_t n, int expected_class, int expected_slot) {
    if (n != CNC3_IOL1_COMMAND_LEN) return CNC3_E_LENGTH;
    if (cnc3_get(p + CNC3_IOL1_COMMAND_CRC32C_OFF, 4) != cnc3_crc32c(p, CNC3_IOL1_COMMAND_CRC32C_OFF))
        return CNC3_E_CRC;
    if (p[CNC3_IOL1_COMMAND_SOF_OFF] != 0xA7) return CNC3_E_SOF;
    if (p[CNC3_IOL1_COMMAND_VERSION_OFF] != 0x01) return CNC3_E_VERSION;
    uint8_t slot = p[CNC3_IOL1_COMMAND_EXPECTED_SLOT_OFF], control = p[CNC3_IOL1_COMMAND_CONTROL_OFF];
    uint16_t sequence = (uint16_t)cnc3_get(p + CNC3_IOL1_COMMAND_SEQUENCE_OFF, 2);
    if (expected_class >= 0 && p[CNC3_IOL1_COMMAND_EXPECTED_CLASS_OFF] != expected_class) return CNC3_E_CLASS;
    if (expected_slot >= 0 && slot != expected_slot) return CNC3_E_SLOT;
    if (slot & 0xF0) return CNC3_E_SLOT;
    if (!cnc3_get(p + CNC3_IOL1_COMMAND_EPOCH_OFF, 2)) return CNC3_E_EPOCH;
    if (control & 0xC0) return CNC3_E_CONTROL;
    if (!!(control & 1) != (sequence == 0)) return CNC3_E_SEQUENCE;
    return CNC3_VALID;
}

static int opcode_rules(enum cnc3_cs cs, const uint8_t *p, size_t n, const struct cnc3_opcode_rule *r) {
    uint32_t session = cnc3_get(p + 8, 4), sequence = cnc3_get(p + 12, 4);
    uint16_t mask = (uint16_t)cnc3_get(p + 6, 2);
    if (r->sequence == 1 && sequence) return CNC3_E_SEQUENCE_RULE;
    if (r->sequence == 2 && !sequence) return CNC3_E_SEQUENCE_RULE;
    if (r->session_nonzero && !session) return CNC3_E_SESSION_RULE;
    if (r->paired && (session == 0) != (sequence == 0)) return CNC3_E_SEQUENCE_RULE;
    if (r->mask_zero && mask) return CNC3_E_MASK_RULE;
    if (r->mask_nonzero && !mask) return CNC3_E_MASK_RULE;
    if (cs == CNC3_CS_CMD) {
        const struct cnc3_layout_rules *l = &cnc3_layouts[CNC3_LAYOUT_CMD_COMMAND];
        for (unsigned i = 0; i < l->field_count; i++) {
            const struct cnc3_field_rule *f = &l->fields[i];
            if (!f->only_opcodes || (f->only_opcodes >> r->code) & 1u) continue;
            for (unsigned b = 0; b < f->size; b++)
                if (!owned(r, f->offset + b) && p[f->offset + b])
                    return strncmp(f->name, "rate_", 5) ? CNC3_E_FIELD_NOT_ALLOWED : CNC3_E_RATE_ON_NON_UPDATE;
        }
    }
    for (unsigned i = 0; i < r->zero_range_count; i++)
        if (any_nonzero(p, r->zero_ranges[i].lo, r->zero_ranges[i].hi)) return CNC3_E_PAYLOAD_NONZERO;
    if (r->byte16_count && !in_ranges(p[16], r->byte16, r->byte16_count)) return CNC3_E_FIELD_RANGE;
    if (r->embedded) {
        const uint8_t *inner = p + r->emb_lo;
        if (cnc3_validate_iol1_command(inner, (size_t)(r->emb_hi - r->emb_lo + 1u), -1, -1))
            return CNC3_E_EMBEDDED_FRAME;
        if (!(inner[CNC3_IOL1_COMMAND_CONTROL_OFF] & (1u << r->emb_control_bit))) return CNC3_E_EMBEDDED_FRAME;
    }
    if (r->rest_zero)
        for (size_t i = 16; i <= n - 3; i++)
            if (!owned(r, i) && p[i]) return CNC3_E_PAYLOAD_NONZERO;
    return CNC3_VALID;
}

int cnc3_validate_command(enum cnc3_cs cs, const uint8_t *p, size_t n) {
    if (cs != CNC3_CS_FB && cs != CNC3_CS_CMD) return CNC3_E_UNKNOWN_CS;
    size_t length = cs == CNC3_CS_FB ? CNC3_CS_FB_BYTES : CNC3_CS_CMD_BYTES;
    if (n != length) return CNC3_E_LENGTH;
    if (cnc3_get(p + n - 2, 2) != cnc3_crc16(p, n - 2)) return CNC3_E_CRC;
    if (memcmp(p, "CNC3", 4)) return CNC3_E_MAGIC;
    if (p[4] != 3) return CNC3_E_ABI;
    const struct cnc3_opcode_rule *r = opcode_rule(p[5]);
    if (!r) return CNC3_E_UNKNOWN_OPCODE;
    if (!(((cs == CNC3_CS_FB ? CNC3_CS_FB_OPCODES : CNC3_CS_CMD_OPCODES) >> p[5]) & 1u)) return CNC3_E_WRONG_CS;
    uint16_t mask = (uint16_t)cnc3_get(p + 6, 2);
    if (mask & ~CNC3_CHANNEL_MASK_LIMIT) return CNC3_E_MASK_WIDTH;
    int result = opcode_rules(cs, p, n, r);
    if (result) return result;
    result = check_layout(cs == CNC3_CS_FB ? CNC3_LAYOUT_FB_COMMAND : CNC3_LAYOUT_CMD_COMMAND, p, r, 0);
    if (result) return result;
    if (cs == CNC3_CS_CMD) {
        for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++)
            if (!(mask & (1u << ch)) && cnc3_get(p + CNC3_CMD_COMMAND_RATE_0_OFF + 4 * ch, 4) &&
                !(ch == 0 && owned(r, 16)))
                return CNC3_E_UNMASKED_RATE;
        return CNC3_VALID;
    }
    int payload = r->payload_layout;
    if (r->page_layout_count) {
        payload = -1;
        for (unsigned i = 0; i < r->page_layout_count && payload < 0; i++) {
            const struct cnc3_layout_rules *l = &cnc3_layouts[(int)r->page_layouts[i]];
            for (unsigned f = 0; f < l->field_count; f++)
                if (!strcmp(l->fields[f].name, "page") &&
                    check_field(&l->fields[f], p + CNC3_PAYLOAD_OFF + l->fields[f].offset) == CNC3_VALID)
                    payload = r->page_layouts[i];
        }
        if (payload < 0) return CNC3_E_FIELD_RANGE;
    }
    return payload >= 0 ? check_layout(payload, p + CNC3_PAYLOAD_OFF, NULL, CNC3_PAYLOAD_OFF) : CNC3_VALID;
}

int cnc3_validate_labelled(const char *label, const uint8_t *frame, size_t length) {
    if (!strcmp(label, "IOL1")) return cnc3_validate_iol1_command(frame, length, -1, -1);
    if (!strcmp(label, "CS_FB")) return cnc3_validate_command(CNC3_CS_FB, frame, length);
    if (!strcmp(label, "CS_CMD")) return cnc3_validate_command(CNC3_CS_CMD, frame, length);
    return CNC3_E_UNKNOWN_CS;
}

static void header(uint8_t *out, uint8_t opcode, uint16_t mask, uint32_t session, uint32_t sequence) {
    memcpy(out, "CNC3", 4);
    out[4] = 3;
    out[5] = opcode;
    cnc3_put(out + 6, 2, mask);
    cnc3_put(out + 8, 4, session);
    cnc3_put(out + 12, 4, sequence);
}

int cnc3_build_cmd(uint8_t out[CNC3_CS_CMD_BYTES], const struct cnc3_cmd *c) {
    memset(out, 0, CNC3_CS_CMD_BYTES);
    header(out, c->opcode, c->channel_mask, c->session, c->sequence);
    for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++)
        cnc3_put(out + CNC3_CMD_COMMAND_RATE_0_OFF + 4 * ch, 4, (uint32_t)c->rate[ch]);
    cnc3_put(out + CNC3_CMD_COMMAND_DOUT_IMAGE_OFF, 2, c->dout_image);
    out[CNC3_CMD_COMMAND_OUTPUT_REQUESTS_OFF] = c->output_requests;
    cnc3_put(out + CNC3_CMD_COMMAND_INDEX_ARM_MASK_OFF, 2, c->index_arm_mask);
    out[CNC3_CMD_COMMAND_PROBE_ARM_OFF] = c->probe_arm;
    cnc3_put(out + CNC3_CMD_COMMAND_PWM0_DUTY_OFF, 2, c->pwm_duty[0]);
    cnc3_put(out + CNC3_CMD_COMMAND_PWM1_DUTY_OFF, 2, c->pwm_duty[1]);
    cnc3_put(out + CNC3_CMD_COMMAND_AOUT0_CODE_OFF, 2, c->aout_code[0]);
    cnc3_put(out + CNC3_CMD_COMMAND_AOUT1_CODE_OFF, 2, c->aout_code[1]);
    cnc3_put(out + CNC3_CMD_COMMAND_DOUT_FAULT_CLEAR_OFF, 2, c->dout_fault_clear);
    if(c->selftest_target){
        if(c->opcode!=CNC3_OP_SELFTEST)return CNC3_E_FIELD_NOT_ALLOWED;
        out[16]=c->selftest_target;
    }
    cnc3_seal_host(out, CNC3_CS_CMD_BYTES);
    if (c->opcode == CNC3_OP_UPDATE)
        for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++)
            if (c->rate[ch] > CNC3_MAX_RATE || c->rate[ch] < -CNC3_MAX_RATE) return CNC3_E_RATE_CLAMP;
    return cnc3_validate_command(CNC3_CS_CMD, out, CNC3_CS_CMD_BYTES);
}

int cnc3_build_fb(uint8_t out[CNC3_CS_FB_BYTES], uint8_t opcode, uint16_t mask, uint32_t session,
                  uint32_t sequence, const uint8_t *payload, size_t payload_length) {
    memset(out, 0, CNC3_CS_FB_BYTES);
    header(out, opcode, mask, session, sequence);
    if (payload_length > CNC3_PAYLOAD_SIZE) return CNC3_E_LENGTH;
    if (payload_length) memcpy(out + CNC3_PAYLOAD_OFF, payload, payload_length);
    cnc3_seal_host(out, CNC3_CS_FB_BYTES);
    return cnc3_validate_command(CNC3_CS_FB, out, CNC3_CS_FB_BYTES);
}

int cnc3_build_fb_read(uint8_t out[CNC3_CS_FB_BYTES], uint32_t session, uint8_t event_ack,
                       uint8_t telemetry_source, uint8_t telemetry_page) {
    uint8_t payload[3];
    payload[CNC3_FB_READ_PAYLOAD_AT_16_EVENT_ACK_OFF] = event_ack;
    payload[CNC3_FB_READ_PAYLOAD_AT_16_TELEMETRY_PRIORITY_SOURCE_OFF] = telemetry_source;
    payload[CNC3_FB_READ_PAYLOAD_AT_16_TELEMETRY_PRIORITY_PAGE_OFF] = telemetry_page;
    return cnc3_build_fb(out, CNC3_OP_FB_READ, 0, session, 0, payload, sizeof payload);
}

static int response_checks(const uint8_t *p, size_t n, size_t length, const char *magic) {
    if (n != length) return CNC3_E_LENGTH;
    if (cnc3_get(p + n - 2, 2) != cnc3_crc16(p, n - 2)) return CNC3_E_CRC;
    if (memcmp(p, magic, 4)) return CNC3_E_MAGIC;
    if (p[4] != 3) return CNC3_E_ABI;
    return CNC3_VALID;
}

#define F(frame, field) (p + CNC3_##frame##_##field##_OFF)
#define G(frame, field) cnc3_get(F(frame, field), CNC3_##frame##_##field##_SIZE)

int cnc3_decode_cnf3(const uint8_t *p, size_t n, struct cnc3_feedback *o) {
    int r = response_checks(p, n, CNC3_FB_RESPONSE_CNF3_LEN, "CNF3");
    if (r) return r;
    memset(o, 0, sizeof *o);
    o->state = (uint8_t)G(FB_RESPONSE_CNF3, STATE);
    o->armed_mask = (uint16_t)G(FB_RESPONSE_CNF3, ARMED_MASK);
    o->session = G(FB_RESPONSE_CNF3, SESSION);
    o->last_sequence = G(FB_RESPONSE_CNF3, LAST_SEQUENCE);
    o->snapshot_ticks = G(FB_RESPONSE_CNF3, SNAPSHOT_TICKS);
    o->fault_word = G(FB_RESPONSE_CNF3, FAULT_WORD);
    o->installed_mask = (uint16_t)G(FB_RESPONSE_CNF3, INSTALLED_MASK);
    o->step_timing_latched = (uint16_t)G(FB_RESPONSE_CNF3, STEP_TIMING_LATCHED);
    o->alarm_levels = (uint16_t)G(FB_RESPONSE_CNF3, ALARM_LEVELS);
    o->alarm_trip_latched = (uint16_t)G(FB_RESPONSE_CNF3, ALARM_TRIP_LATCHED);
    o->enable_after_gating = (uint16_t)G(FB_RESPONSE_CNF3, ENABLE_AFTER_GATING);
    o->pos_continuity = (uint16_t)G(FB_RESPONSE_CNF3, POS_CONTINUITY);
    for (unsigned i = 0; i < CNC3_CHANNELS; i++) o->step_count[i] = cnc3_get(F(FB_RESPONSE_CNF3, STEP_COUNT_0) + 3 * i, 3);
    for (unsigned i = 0; i < CNC3_ENCODERS; i++)
        o->encoder_count[i] = cnc3_get(F(FB_RESPONSE_CNF3, ENCODER_COUNT_0) + 3 * i, 3);
    o->encoder_valid_mask = (uint16_t)G(FB_RESPONSE_CNF3, ENCODER_VALID_MASK);
    o->encoder_illegal_mask = (uint16_t)G(FB_RESPONSE_CNF3, ENCODER_ILLEGAL_MASK);
    o->encoder_fault_mask = (uint16_t)G(FB_RESPONSE_CNF3, ENCODER_FAULT_MASK);
    o->index_armed_mask = (uint16_t)G(FB_RESPONSE_CNF3, INDEX_ARMED_MASK);
    o->mpg_count = G(FB_RESPONSE_CNF3, MPG_COUNT);
    o->mpg_status = (uint8_t)G(FB_RESPONSE_CNF3, MPG_STATUS);
    o->probe_status = (uint8_t)G(FB_RESPONSE_CNF3, PROBE_STATUS);
    o->event_status = (uint8_t)G(FB_RESPONSE_CNF3, EVENT_STATUS);
    o->freq_count[0] = G(FB_RESPONSE_CNF3, FREQ0_COUNT);
    o->freq_last_edge_ticks[0] = G(FB_RESPONSE_CNF3, FREQ0_LAST_EDGE_TICKS);
    o->freq_count[1] = G(FB_RESPONSE_CNF3, FREQ1_COUNT);
    o->freq_last_edge_ticks[1] = G(FB_RESPONSE_CNF3, FREQ1_LAST_EDGE_TICKS);
    o->din = G(FB_RESPONSE_CNF3, DIN);
    o->din_age = (uint8_t)G(FB_RESPONSE_CNF3, DIN_AGE);
    o->dout_applied = (uint16_t)G(FB_RESPONSE_CNF3, DOUT_APPLIED);
    o->dout_fault_latched = (uint16_t)G(FB_RESPONSE_CNF3, DOUT_FAULT_LATCHED);
    o->process_pwm_state = (uint8_t)G(FB_RESPONSE_CNF3, PROCESS_PWM_STATE);
    o->aout_state = (uint8_t)G(FB_RESPONSE_CNF3, AOUT_STATE);
    for (unsigned i = 0; i < 4; i++) o->ain[i] = (int16_t)cnc3_get(F(FB_RESPONSE_CNF3, AIN0) + 2 * i, 2);
    o->ain_status = (uint8_t)G(FB_RESPONSE_CNF3, AIN_STATUS);
    o->ain_age = (uint8_t)G(FB_RESPONSE_CNF3, AIN_AGE);
    for (unsigned i = 0; i < 6; i++) o->port_status[i] = F(FB_RESPONSE_CNF3, PORT_STATUS_L0_DIC)[i];
    o->mx4_expansion = (uint8_t)G(FB_RESPONSE_CNF3, MX4_EXPANSION);
    o->slot_summary = (uint8_t)G(FB_RESPONSE_CNF3, SLOT_SUMMARY);
    o->safety_power_word = G(FB_RESPONSE_CNF3, SAFETY_POWER_WORD);
    o->config_generation = (uint8_t)G(FB_RESPONSE_CNF3, CONFIG_GENERATION);
    o->io_config_generation = (uint8_t)G(FB_RESPONSE_CNF3, IO_CONFIG_GENERATION);
    o->pendant_inputs = (uint16_t)G(FB_RESPONSE_CNF3, PENDANT_INPUTS);
    o->ex8_expansion = (uint8_t)G(FB_RESPONSE_CNF3, EX8_EXPANSION);
    o->port_status_l4_xs = (uint8_t)G(FB_RESPONSE_CNF3, PORT_STATUS_L4_XS);
    return CNC3_VALID;
}

int cnc3_decode_cns3(const uint8_t *p, size_t n, struct cnc3_status *o) {
    int r = response_checks(p, n, CNC3_CMD_RESPONSE_CNS3_LEN, "CNS3");
    if (r) return r;
    memset(o, 0, sizeof *o);
    o->state = (uint8_t)G(CMD_RESPONSE_CNS3, STATE);
    o->armed_mask = (uint16_t)G(CMD_RESPONSE_CNS3, ARMED_MASK);
    o->session = G(CMD_RESPONSE_CNS3, SESSION);
    o->last_sequence = G(CMD_RESPONSE_CNS3, LAST_SEQUENCE);
    o->snapshot_ticks = G(CMD_RESPONSE_CNS3, SNAPSHOT_TICKS);
    o->fault_word = G(CMD_RESPONSE_CNS3, FAULT_WORD);
    o->dout_image_in_force = (uint16_t)G(CMD_RESPONSE_CNS3, DOUT_IMAGE_IN_FORCE);
    o->dout_applied = (uint16_t)G(CMD_RESPONSE_CNS3, DOUT_APPLIED);
    o->dout_fault_latched = (uint16_t)G(CMD_RESPONSE_CNS3, DOUT_FAULT_LATCHED);
    o->safety_power_word = G(CMD_RESPONSE_CNS3, SAFETY_POWER_WORD);
    o->pos_continuity = (uint16_t)G(CMD_RESPONSE_CNS3, POS_CONTINUITY);
    o->event_seq = (uint8_t)G(CMD_RESPONSE_CNS3, EVENT_SEQ);
    o->event_type = (uint8_t)G(CMD_RESPONSE_CNS3, EVENT_TYPE);
    o->event_source = (uint8_t)G(CMD_RESPONSE_CNS3, EVENT_SOURCE);
    o->event_flags = (uint8_t)G(CMD_RESPONSE_CNS3, EVENT_FLAGS);
    o->event_ticks = G(CMD_RESPONSE_CNS3, EVENT_TICKS);
    for (unsigned i = 0; i < 4; i++) o->event_value[i] = cnc3_get(F(CMD_RESPONSE_CNS3, EVENT_VALUE0) + 3 * i, 3);
    o->telemetry_source = (uint8_t)G(CMD_RESPONSE_CNS3, TELEMETRY_SOURCE);
    o->telemetry_page = (uint8_t)G(CMD_RESPONSE_CNS3, TELEMETRY_PAGE);
    o->telemetry_counter = (uint8_t)G(CMD_RESPONSE_CNS3, TELEMETRY_COUNTER);
    o->telemetry_validity = (uint8_t)G(CMD_RESPONSE_CNS3, TELEMETRY_VALIDITY);
    o->telemetry_rx_ticks = G(CMD_RESPONSE_CNS3, TELEMETRY_RX_TICKS);
    o->telemetry_card_age_us = (uint16_t)G(CMD_RESPONSE_CNS3, TELEMETRY_CARD_AGE_US);
    memcpy(o->telemetry_data, F(CMD_RESPONSE_CNS3, TELEMETRY_DATA), sizeof o->telemetry_data);
    o->telemetry_rotation = (uint16_t)G(CMD_RESPONSE_CNS3, TELEMETRY_ROTATION);
    o->last_update_interval_us = (uint16_t)G(CMD_RESPONSE_CNS3, LAST_UPDATE_INTERVAL_US);
    o->late_update_count = (uint16_t)G(CMD_RESPONSE_CNS3, LATE_UPDATE_COUNT);
    o->slot_status = G(CMD_RESPONSE_CNS3, SLOT_STATUS);
    return CNC3_VALID;
}

#define P(frame, field, v) cnc3_put(F(frame, field), CNC3_##frame##_##field##_SIZE, (uint32_t)(v))

void cnc3_encode_cnf3(uint8_t out[CNC3_FB_RESPONSE_CNF3_LEN], const struct cnc3_feedback *o) {
    uint8_t *p = out;
    memset(out, 0, CNC3_FB_RESPONSE_CNF3_LEN);
    memcpy(out, "CNF3", 4);
    out[4] = 3;
    P(FB_RESPONSE_CNF3, STATE, o->state);
    P(FB_RESPONSE_CNF3, ARMED_MASK, o->armed_mask);
    P(FB_RESPONSE_CNF3, SESSION, o->session);
    P(FB_RESPONSE_CNF3, LAST_SEQUENCE, o->last_sequence);
    P(FB_RESPONSE_CNF3, SNAPSHOT_TICKS, o->snapshot_ticks);
    P(FB_RESPONSE_CNF3, FAULT_WORD, o->fault_word);
    P(FB_RESPONSE_CNF3, INSTALLED_MASK, o->installed_mask);
    P(FB_RESPONSE_CNF3, STEP_TIMING_LATCHED, o->step_timing_latched);
    P(FB_RESPONSE_CNF3, ALARM_LEVELS, o->alarm_levels);
    P(FB_RESPONSE_CNF3, ALARM_TRIP_LATCHED, o->alarm_trip_latched);
    P(FB_RESPONSE_CNF3, ENABLE_AFTER_GATING, o->enable_after_gating);
    P(FB_RESPONSE_CNF3, POS_CONTINUITY, o->pos_continuity);
    for (unsigned i = 0; i < CNC3_CHANNELS; i++)
        cnc3_put(F(FB_RESPONSE_CNF3, STEP_COUNT_0) + 3 * i, 3, o->step_count[i] & 0xFFFFFFu);
    for (unsigned i = 0; i < CNC3_ENCODERS; i++)
        cnc3_put(F(FB_RESPONSE_CNF3, ENCODER_COUNT_0) + 3 * i, 3, o->encoder_count[i] & 0xFFFFFFu);
    P(FB_RESPONSE_CNF3, ENCODER_VALID_MASK, o->encoder_valid_mask);
    P(FB_RESPONSE_CNF3, ENCODER_ILLEGAL_MASK, o->encoder_illegal_mask);
    P(FB_RESPONSE_CNF3, ENCODER_FAULT_MASK, o->encoder_fault_mask);
    P(FB_RESPONSE_CNF3, INDEX_ARMED_MASK, o->index_armed_mask);
    P(FB_RESPONSE_CNF3, MPG_COUNT, o->mpg_count & 0xFFFFFFu);
    P(FB_RESPONSE_CNF3, MPG_STATUS, o->mpg_status);
    P(FB_RESPONSE_CNF3, PROBE_STATUS, o->probe_status);
    P(FB_RESPONSE_CNF3, EVENT_STATUS, o->event_status);
    P(FB_RESPONSE_CNF3, FREQ0_COUNT, o->freq_count[0] & 0xFFFFFFu);
    P(FB_RESPONSE_CNF3, FREQ0_LAST_EDGE_TICKS, o->freq_last_edge_ticks[0]);
    P(FB_RESPONSE_CNF3, FREQ1_COUNT, o->freq_count[1] & 0xFFFFFFu);
    P(FB_RESPONSE_CNF3, FREQ1_LAST_EDGE_TICKS, o->freq_last_edge_ticks[1]);
    P(FB_RESPONSE_CNF3, DIN, o->din & 0xFFFFFFu);
    P(FB_RESPONSE_CNF3, DIN_AGE, o->din_age);
    P(FB_RESPONSE_CNF3, DOUT_APPLIED, o->dout_applied);
    P(FB_RESPONSE_CNF3, DOUT_FAULT_LATCHED, o->dout_fault_latched);
    P(FB_RESPONSE_CNF3, PROCESS_PWM_STATE, o->process_pwm_state);
    P(FB_RESPONSE_CNF3, AOUT_STATE, o->aout_state);
    for (unsigned i = 0; i < 4; i++) cnc3_put(F(FB_RESPONSE_CNF3, AIN0) + 2 * i, 2, (uint16_t)o->ain[i]);
    P(FB_RESPONSE_CNF3, AIN_STATUS, o->ain_status);
    P(FB_RESPONSE_CNF3, AIN_AGE, o->ain_age);
    for (unsigned i = 0; i < 6; i++) F(FB_RESPONSE_CNF3, PORT_STATUS_L0_DIC)[i] = o->port_status[i];
    P(FB_RESPONSE_CNF3, MX4_EXPANSION, o->mx4_expansion);
    P(FB_RESPONSE_CNF3, SLOT_SUMMARY, o->slot_summary);
    P(FB_RESPONSE_CNF3, SAFETY_POWER_WORD, o->safety_power_word);
    P(FB_RESPONSE_CNF3, CONFIG_GENERATION, o->config_generation);
    P(FB_RESPONSE_CNF3, IO_CONFIG_GENERATION, o->io_config_generation);
    P(FB_RESPONSE_CNF3, PENDANT_INPUTS, o->pendant_inputs);
    P(FB_RESPONSE_CNF3, EX8_EXPANSION, o->ex8_expansion);
    P(FB_RESPONSE_CNF3, PORT_STATUS_L4_XS, o->port_status_l4_xs);
    cnc3_seal_host(out, CNC3_FB_RESPONSE_CNF3_LEN);
}

void cnc3_encode_cns3(uint8_t out[CNC3_CMD_RESPONSE_CNS3_LEN], const struct cnc3_status *o) {
    uint8_t *p = out;
    memset(out, 0, CNC3_CMD_RESPONSE_CNS3_LEN);
    memcpy(out, "CNS3", 4);
    out[4] = 3;
    P(CMD_RESPONSE_CNS3, STATE, o->state);
    P(CMD_RESPONSE_CNS3, ARMED_MASK, o->armed_mask);
    P(CMD_RESPONSE_CNS3, SESSION, o->session);
    P(CMD_RESPONSE_CNS3, LAST_SEQUENCE, o->last_sequence);
    P(CMD_RESPONSE_CNS3, SNAPSHOT_TICKS, o->snapshot_ticks);
    P(CMD_RESPONSE_CNS3, FAULT_WORD, o->fault_word);
    P(CMD_RESPONSE_CNS3, DOUT_IMAGE_IN_FORCE, o->dout_image_in_force);
    P(CMD_RESPONSE_CNS3, DOUT_APPLIED, o->dout_applied);
    P(CMD_RESPONSE_CNS3, DOUT_FAULT_LATCHED, o->dout_fault_latched);
    P(CMD_RESPONSE_CNS3, SAFETY_POWER_WORD, o->safety_power_word);
    P(CMD_RESPONSE_CNS3, POS_CONTINUITY, o->pos_continuity);
    P(CMD_RESPONSE_CNS3, EVENT_SEQ, o->event_seq);
    P(CMD_RESPONSE_CNS3, EVENT_TYPE, o->event_type);
    P(CMD_RESPONSE_CNS3, EVENT_SOURCE, o->event_source);
    P(CMD_RESPONSE_CNS3, EVENT_FLAGS, o->event_flags);
    P(CMD_RESPONSE_CNS3, EVENT_TICKS, o->event_ticks);
    for (unsigned i = 0; i < 4; i++) cnc3_put(F(CMD_RESPONSE_CNS3, EVENT_VALUE0) + 3 * i, 3, o->event_value[i] & 0xFFFFFFu);
    P(CMD_RESPONSE_CNS3, TELEMETRY_SOURCE, o->telemetry_source);
    P(CMD_RESPONSE_CNS3, TELEMETRY_PAGE, o->telemetry_page);
    P(CMD_RESPONSE_CNS3, TELEMETRY_COUNTER, o->telemetry_counter);
    P(CMD_RESPONSE_CNS3, TELEMETRY_VALIDITY, o->telemetry_validity);
    P(CMD_RESPONSE_CNS3, TELEMETRY_RX_TICKS, o->telemetry_rx_ticks);
    P(CMD_RESPONSE_CNS3, TELEMETRY_CARD_AGE_US, o->telemetry_card_age_us);
    memcpy(F(CMD_RESPONSE_CNS3, TELEMETRY_DATA), o->telemetry_data, sizeof o->telemetry_data);
    P(CMD_RESPONSE_CNS3, TELEMETRY_ROTATION, o->telemetry_rotation);
    P(CMD_RESPONSE_CNS3, LAST_UPDATE_INTERVAL_US, o->last_update_interval_us);
    P(CMD_RESPONSE_CNS3, LATE_UPDATE_COUNT, o->late_update_count);
    P(CMD_RESPONSE_CNS3, SLOT_STATUS, o->slot_status);
    cnc3_seal_host(out, CNC3_CMD_RESPONSE_CNS3_LEN);
}

int cnc3_decode_cap3_page0(const uint8_t *p, size_t n, struct cnc3_caps *o) {
    int r = response_checks(p, n, CNC3_CAP3_PAGE0_LEN, "CAP3");
    if (r) return r;
    if (G(CAP3_PAGE0, PAGE) != 0) return CNC3_E_FIELD_RANGE;
    if (G(CAP3_PAGE0, ZERO_A) || G(CAP3_PAGE0, ZERO_B) || G(CAP3_PAGE0, ZERO_C) ||
        any_nonzero(p, CNC3_CAP3_PAGE0_ZERO_OFF, CNC3_CAP3_PAGE0_ZERO_OFF + CNC3_CAP3_PAGE0_ZERO_SIZE - 1))
        return CNC3_E_RESERVED_NONZERO;
    memset(o, 0, sizeof *o);
    o->step_channels = (uint8_t)G(CAP3_PAGE0, STEP_CHANNELS);
    o->installed_channels = (uint8_t)G(CAP3_PAGE0, INSTALLED_CHANNELS);
    o->encoders_supported = (uint8_t)G(CAP3_PAGE0, ENCODERS_SUPPORTED);
    o->encoders_base = (uint8_t)G(CAP3_PAGE0, ENCODERS_BASE);
    o->encoders_installed = (uint8_t)G(CAP3_PAGE0, ENCODERS_INSTALLED);
    o->mpg_ports = (uint8_t)G(CAP3_PAGE0, MPG_PORTS);
    o->feature_bitmap = G(CAP3_PAGE0, FEATURE_BITMAP);
    o->core_hz = G(CAP3_PAGE0, CORE_HZ);
    o->max_rate = G(CAP3_PAGE0, MAX_RATE);
    for (unsigned i = 0; i < 4; i++) o->reference_timing[i] = (uint16_t)cnc3_get(F(CAP3_PAGE0, REFERENCE_TIMING) + 2 * i, 2);
    o->timing_min = (uint16_t)G(CAP3_PAGE0, TIMING_MIN);
    o->timing_max = (uint16_t)G(CAP3_PAGE0, TIMING_MAX);
    o->watchdog_ticks = G(CAP3_PAGE0, WATCHDOG_TICKS);
    o->alarm_sample_ticks = (uint16_t)G(CAP3_PAGE0, ALARM_SAMPLE_TICKS);
    o->filter_samples = (uint8_t)G(CAP3_PAGE0, FILTER_SAMPLES);
    o->fb_frame_bytes = (uint16_t)G(CAP3_PAGE0, FB_FRAME_BYTES);
    o->cmd_frame_bytes = (uint16_t)G(CAP3_PAGE0, CMD_FRAME_BYTES);
    o->min_sclk_divider = (uint8_t)G(CAP3_PAGE0, MIN_SCLK_DIVIDER);
    o->bank_count = (uint8_t)G(CAP3_PAGE0, BANK_COUNT);
    for (unsigned i = 0; i < 4; i++) o->bank_layout[i] = F(CAP3_PAGE0, BANK_LAYOUT)[i];
    o->expansion_state = (uint8_t)G(CAP3_PAGE0, EXPANSION_STATE);
    o->mod_id_latched = (uint8_t)G(CAP3_PAGE0, MOD_ID_LATCHED);
    o->accepted_module_class = (uint8_t)G(CAP3_PAGE0, ACCEPTED_MODULE_CLASS);
    o->accepted_encoder_expansion_class = (uint8_t)G(CAP3_PAGE0, ACCEPTED_ENCODER_EXPANSION_CLASS);
    o->qualification_ticks = G(CAP3_PAGE0, QUALIFICATION_TICKS);
    o->gateware_build_id = G(CAP3_PAGE0, GATEWARE_BUILD_ID);
    memcpy(o->spec_revision, F(CAP3_PAGE0, SPEC_REVISION), 4);
    o->event_ring_depth = (uint16_t)G(CAP3_PAGE0, EVENT_RING_DEPTH);
    o->telemetry_entries = (uint16_t)G(CAP3_PAGE0, TELEMETRY_ENTRIES);
    o->progress_pulse_ticks = (uint16_t)G(CAP3_PAGE0, PROGRESS_PULSE_TICKS);
    return CNC3_VALID;
}

void cnc3_encode_cap3_page0(uint8_t out[CNC3_CAP3_PAGE0_LEN], const struct cnc3_caps *o) {
    uint8_t *p = out;
    memset(out, 0, CNC3_CAP3_PAGE0_LEN);
    memcpy(out, "CAP3", 4);
    out[4] = 3;
    P(CAP3_PAGE0, STEP_CHANNELS, o->step_channels);
    P(CAP3_PAGE0, INSTALLED_CHANNELS, o->installed_channels);
    P(CAP3_PAGE0, ENCODERS_SUPPORTED, o->encoders_supported);
    P(CAP3_PAGE0, ENCODERS_BASE, o->encoders_base);
    P(CAP3_PAGE0, ENCODERS_INSTALLED, o->encoders_installed);
    P(CAP3_PAGE0, MPG_PORTS, o->mpg_ports);
    P(CAP3_PAGE0, FEATURE_BITMAP, o->feature_bitmap);
    P(CAP3_PAGE0, CORE_HZ, o->core_hz);
    P(CAP3_PAGE0, MAX_RATE, o->max_rate);
    for (unsigned i = 0; i < 4; i++) cnc3_put(F(CAP3_PAGE0, REFERENCE_TIMING) + 2 * i, 2, o->reference_timing[i]);
    P(CAP3_PAGE0, TIMING_MIN, o->timing_min);
    P(CAP3_PAGE0, TIMING_MAX, o->timing_max);
    P(CAP3_PAGE0, WATCHDOG_TICKS, o->watchdog_ticks);
    P(CAP3_PAGE0, ALARM_SAMPLE_TICKS, o->alarm_sample_ticks);
    P(CAP3_PAGE0, FILTER_SAMPLES, o->filter_samples);
    P(CAP3_PAGE0, FB_FRAME_BYTES, o->fb_frame_bytes);
    P(CAP3_PAGE0, CMD_FRAME_BYTES, o->cmd_frame_bytes);
    P(CAP3_PAGE0, MIN_SCLK_DIVIDER, o->min_sclk_divider);
    P(CAP3_PAGE0, BANK_COUNT, o->bank_count);
    for (unsigned i = 0; i < 4; i++) F(CAP3_PAGE0, BANK_LAYOUT)[i] = o->bank_layout[i];
    P(CAP3_PAGE0, EXPANSION_STATE, o->expansion_state);
    P(CAP3_PAGE0, MOD_ID_LATCHED, o->mod_id_latched);
    P(CAP3_PAGE0, ACCEPTED_MODULE_CLASS, o->accepted_module_class);
    P(CAP3_PAGE0, ACCEPTED_ENCODER_EXPANSION_CLASS, o->accepted_encoder_expansion_class);
    P(CAP3_PAGE0, QUALIFICATION_TICKS, o->qualification_ticks);
    P(CAP3_PAGE0, GATEWARE_BUILD_ID, o->gateware_build_id);
    memcpy(F(CAP3_PAGE0, SPEC_REVISION), o->spec_revision, 4);
    P(CAP3_PAGE0, EVENT_RING_DEPTH, o->event_ring_depth);
    P(CAP3_PAGE0, TELEMETRY_ENTRIES, o->telemetry_entries);
    P(CAP3_PAGE0, PROGRESS_PULSE_TICKS, o->progress_pulse_ticks);
    cnc3_seal_host(out, CNC3_CAP3_PAGE0_LEN);
}

int64_t cnc3_unwrap_u24(int64_t previous_total, uint32_t raw24) {
    uint32_t delta = (raw24 - (uint32_t)((uint64_t)previous_total & 0xFFFFFFu)) & 0xFFFFFFu;
    int64_t signed_delta = delta >= 0x800000u ? (int64_t)delta - 0x1000000 : (int64_t)delta;
    return previous_total + signed_delta;
}
