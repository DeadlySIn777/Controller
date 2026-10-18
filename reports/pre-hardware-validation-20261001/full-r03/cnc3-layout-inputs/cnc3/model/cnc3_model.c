/* SPDX-License-Identifier: LicenseRef-Proprietary */
#include "cnc3_model.h"
#include <string.h>

#define FW_LINK (1u << 0)
#define FW_WATCHDOG (1u << 1)
#define FW_EXPANSION_CHANGED (1u << 5)
#define FW_EXPANSION_INVALID (1u << 6)
#define FW_CONFIG_REJECTED (1u << 7)
#define FW_MODULE_CLASS_MISMATCH (1u << 8)
#define FW_EVENT_OVERFLOW (1u << 18)
#define FW_POWER_CYCLE (FW_EXPANSION_CHANGED | FW_EXPANSION_INVALID)
#define EV_FAULT_LATCHED 0x03
#define EV_WATCHDOG_TRIP 0x07

void cnc3_model_init(struct cnc3_model *m, unsigned installed) {
    memset(m, 0, sizeof *m);
    m->installed_channels = (uint8_t)(installed == 12 ? 12 : 8);
    m->installed_mask = installed == 12 ? 0x0FFF : 0x00FF;
    m->next_event_seq = 1;
    m->page_pending = 0xFF;
    m->ticks = 1000; /* nonzero so the first snapshot differs from a reset value */
}

static void push_event(struct cnc3_model *m, uint8_t type, uint8_t source, uint32_t v0, uint32_t v1) {
    if (m->ring_count == CNC3_MODEL_RING) { m->fault_word |= FW_EVENT_OVERFLOW; return; }
    struct cnc3_model_event *e = &m->ring[(m->ring_head + m->ring_count) % CNC3_MODEL_RING];
    memset(e, 0, sizeof *e);
    e->type = type; e->source = source; e->ticks = (uint32_t)m->ticks;
    e->value[0] = v0 & 0xFFFFFFu; e->value[1] = v1 & 0xFFFFFFu;
    e->seq = m->next_event_seq;
    m->next_event_seq = (uint8_t)(m->next_event_seq == 255 ? 1 : m->next_event_seq + 1); /* skips 0 */
    m->ring_count++;
}

/* Latch fault bits; every latch in this model disarms all channels (section 3.9 responses). */
static void latch(struct cnc3_model *m, uint32_t bits) {
    uint32_t fresh = bits & ~m->fault_word;
    m->fault_word |= bits;
    for (unsigned b = 0; b < 32; b++)
        if ((fresh >> b) & 1u) {
            push_event(m, EV_FAULT_LATCHED, (uint8_t)b, m->fault_word & 0xFFFFFFu,
                       ((m->fault_word >> 24) << 16) | m->armed_mask);
            break; /* one record names the lowest newly set bit */
        }
    for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++)
        if ((((unsigned)m->armed_mask >> ch) & 1u) && m->rate[ch]) m->pos_continuity &= (uint16_t)~(1u << ch); /* not a clean stop */
    m->armed_mask = 0;
    memset(m->rate, 0, sizeof m->rate);
}

void cnc3_model_advance(struct cnc3_model *m, uint64_t ticks) {
    const int64_t one = INT64_C(1) << 32;
    for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++) {
        if (!(((unsigned)m->armed_mask >> ch) & 1u) || !m->rate[ch]) continue;
        int64_t total = m->phase[ch] + (int64_t)m->rate[ch] * (int64_t)ticks;
        int64_t whole = total >= 0 ? total / one : -((-total + one - 1) / one); /* floor division */
        m->phase[ch] = total - whole * one;
        m->steps[ch] += (uint32_t)whole;
    }
    m->ticks += ticks;
    if (m->armed_mask && m->ticks - m->progress_tick > CNC3_MODEL_WATCHDOG_TICKS) {
        push_event(m, EV_WATCHDOG_TRIP, 0, (uint32_t)(m->ticks - m->progress_tick), 0);
        latch(m, FW_WATCHDOG);
    }
    if (m->remove_expansion && m->installed_channels == 12) {
        m->installed_channels = 0;
        m->installed_mask = 0;
        latch(m, FW_EXPANSION_CHANGED); /* disarm all, installed 0, cleared only by power cycle */
    }
}

static void cnf3(const struct cnc3_model *m, uint8_t *rx) {
    struct cnc3_feedback f;
    memset(&f, 0, sizeof f);
    f.state = (uint8_t)((m->armed_mask ? 1u : 0u) | (m->fault_word ? 0u : 2u) | 4u | (m->config_valid ? 8u : 0u));
    f.armed_mask = m->armed_mask;
    f.session = m->session;
    f.last_sequence = m->last_sequence;
    f.snapshot_ticks = (uint32_t)m->ticks;
    f.fault_word = m->fault_word;
    f.installed_mask = m->installed_mask;
    f.pos_continuity = m->pos_continuity;
    for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++) f.step_count[ch] = m->steps[ch] & 0xFFFFFFu;
    f.event_status = (uint8_t)(m->ring_count > 127 ? 127 : m->ring_count);
    f.din_age = 255; /* no DIC card in this model: stale, never a plausible value */
    f.ain_age = 255;
    f.safety_power_word = m->selftest_ok ? (3u << 21) : 0;
    f.config_generation = (uint8_t)m->config_valid;
    cnc3_encode_cnf3(rx, &f);
}

static void cns3(struct cnc3_model *m, uint8_t *rx) {
    struct cnc3_status s;
    memset(&s, 0, sizeof s);
    s.state = (uint8_t)((m->armed_mask ? 1u : 0u) | (m->fault_word ? 0u : 2u) | 4u | (m->config_valid ? 8u : 0u));
    s.armed_mask = m->armed_mask;
    s.session = m->session;
    s.last_sequence = m->last_sequence;
    s.snapshot_ticks = (uint32_t)m->ticks;
    s.fault_word = m->fault_word;
    s.pos_continuity = m->pos_continuity;
    s.safety_power_word = m->selftest_ok ? (3u << 21) : 0;
    if (m->ring_count) {
        const struct cnc3_model_event *e = &m->ring[m->ring_head];
        s.event_seq = e->seq; s.event_type = e->type; s.event_source = e->source; s.event_flags = e->flags;
        s.event_ticks = e->ticks;
        memcpy(s.event_value, e->value, sizeof s.event_value);
        m->shown_event_seq = e->seq;
    }
    s.telemetry_source = 0xFF; /* no mirror entries in this model */
    s.last_update_interval_us = m->last_update_interval_us;
    s.late_update_count = m->late_update_count;
    cnc3_encode_cns3(rx, &s);
}

static void cap3_page0(const struct cnc3_model *m, uint8_t *rx) {
    struct cnc3_caps c;
    memset(&c, 0, sizeof c);
    c.step_channels = 12; c.installed_channels = m->installed_channels; c.encoders_supported = 12;
    c.encoders_base = 4; c.encoders_installed = 4; c.mpg_ports = 1; c.feature_bitmap = 0x7FF;
    c.core_hz = 50000000u; c.max_rate = (uint32_t)CNC3_MAX_RATE;
    for (unsigned k = 0; k < 4; k++) c.reference_timing[k] = 100;
    c.timing_min = 100; c.timing_max = 1023; c.watchdog_ticks = CNC3_MODEL_WATCHDOG_TICKS; c.alarm_sample_ticks = 500;
    c.filter_samples = 4; c.fb_frame_bytes = CNC3_CS_FB_BYTES; c.cmd_frame_bytes = CNC3_CS_CMD_BYTES;
    c.min_sclk_divider = 8; c.bank_count = 2; c.bank_layout[1] = 8; c.bank_layout[2] = 8; c.bank_layout[3] = 4;
    c.accepted_module_class = 1; c.accepted_encoder_expansion_class = 1; c.qualification_ticks = 1048576u;
    memcpy(c.spec_revision, "IS-1", 4);
    c.event_ring_depth = CNC3_MODEL_RING; c.telemetry_entries = 45; c.progress_pulse_ticks = 50;
    cnc3_encode_cap3_page0(rx, &c);
}

static int next_sequence(const struct cnc3_model *m, const uint8_t *tx) {
    return cnc3_get(tx + 8, 4) == m->session && m->session && cnc3_get(tx + 12, 4) == m->last_sequence + 1;
}

/* Semantic CONFIGURE checks that need endpoint state (installed channels, accepted class). */
static int configure_ok(const struct cnc3_model *m, const uint8_t *p) {
    uint8_t cls = p[CNC3_CONFIGURE_PAYLOAD_AT_16_EXPECTED_MODULE_CLASS_OFF];
    uint16_t required = (uint16_t)cnc3_get(p + CNC3_CONFIGURE_PAYLOAD_AT_16_REQUIRED_MASK_OFF, 2);
    if (cls && cls != 1) return 0;
    if (required & ~m->installed_mask) return 0;
    return 1;
}

static void commit(struct cnc3_model *m, enum cnc3_cs cs, const uint8_t *tx) {
    uint8_t op = tx[5];
    uint16_t mask = (uint16_t)cnc3_get(tx + 6, 2);
    uint32_t session = cnc3_get(tx + 8, 4), sequence = cnc3_get(tx + 12, 4);
    int ok = 0;
    (void)cs;
    switch (op) {
    case CNC3_OP_NOP:
        ok = session == 0 || session == m->session;
        break;
    case CNC3_OP_FB_READ:
        ok = session == 0 || session == m->session;
        if (ok && m->ring_count && tx[CNC3_PAYLOAD_OFF] == m->shown_event_seq && m->shown_event_seq) {
            m->ring_head = (m->ring_head + 1) % CNC3_MODEL_RING;
            m->ring_count--;
            m->shown_event_seq = 0;
        }
        break;
    case CNC3_OP_READ_PAGE:
        ok = !m->armed_mask && (session == 0 || session == m->session);
        if (ok) m->page_pending = tx[16];
        break;
    case CNC3_OP_CONFIGURE: {
        ok = !m->armed_mask && ((session == 0 && sequence == 0 && m->session == 0) || next_sequence(m, tx));
        if (!ok) break;
        if (sequence) m->last_sequence = sequence;
        const uint8_t *p = tx + CNC3_PAYLOAD_OFF;
        if (!configure_ok(m, p)) { /* rejection clears config_valid, required_mask and alarm masks */
            m->config_valid = 0; m->required_mask = 0; m->alarm_trip_mask = 0;
            latch(m, FW_CONFIG_REJECTED);
            return;
        }
        m->config_valid = 1;
        m->expected_module_class = p[CNC3_CONFIGURE_PAYLOAD_AT_16_EXPECTED_MODULE_CLASS_OFF];
        m->required_mask = (uint16_t)cnc3_get(p + CNC3_CONFIGURE_PAYLOAD_AT_16_REQUIRED_MASK_OFF, 2);
        m->alarm_trip_mask = (uint16_t)cnc3_get(p + CNC3_CONFIGURE_PAYLOAD_AT_16_ALARM_TRIP_MASK_OFF, 2);
        m->servo_period_us = cnc3_get(p + CNC3_CONFIGURE_PAYLOAD_AT_16_SERVO_PERIOD_US_OFF, 2);
        m->config_hash = cnc3_get(p + CNC3_CONFIGURE_PAYLOAD_AT_16_CONFIG_HASH_OFF, 4);
        break;
    }
    case CNC3_OP_SYNC:
        ok = session && session != m->session && !m->armed_mask && !(m->fault_word & FW_POWER_CYCLE);
        if (!ok) break;
        m->session = session;
        m->last_sequence = 0;
        m->fault_word &= FW_POWER_CYCLE | (m->config_valid ? 0u : FW_CONFIG_REJECTED);
        m->late_update_count = 0;
        break;
    case CNC3_OP_ARM:
        ok = next_sequence(m, tx) && !m->armed_mask && !m->fault_word;
        if (!ok) break;
        if (!m->config_valid || mask != m->required_mask || (mask & ~m->installed_mask)) {
            m->last_sequence = sequence;
            latch(m, FW_CONFIG_REJECTED); /* ARM mask != required_mask */
            return;
        }
        if ((mask & 0x0F00u) && m->expected_module_class != 1) {
            m->last_sequence = sequence;
            latch(m, FW_MODULE_CLASS_MISMATCH);
            return;
        }
        m->last_sequence = sequence;
        m->armed_mask = mask;
        memset(m->rate, 0, sizeof m->rate);
        m->progress_tick = m->ticks;
        m->last_update_tick = m->ticks;
        break;
    case CNC3_OP_UPDATE:
        ok = next_sequence(m, tx) && m->armed_mask && !m->fault_word && mask == m->armed_mask;
        if (!ok) break;
        m->last_sequence = sequence;
        for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++) m->rate[ch] = (int32_t)cnc3_get(tx + 16 + 4 * ch, 4);
        {
            uint64_t interval_us = (m->ticks - m->last_update_tick) / 50u;
            m->last_update_interval_us = (uint16_t)(interval_us > 65535u ? 65535u : interval_us);
            if (m->servo_period_us && interval_us * 2u > 3u * m->servo_period_us && m->late_update_count < 65535u)
                m->late_update_count++;
        }
        m->last_update_tick = m->ticks;
        m->progress_tick = m->ticks;
        break;
    case CNC3_OP_DISARM:
        ok = next_sequence(m, tx);
        if (!ok) break;
        m->last_sequence = sequence;
        m->armed_mask = 0; /* clean commanded stop: continuity is kept */
        memset(m->rate, 0, sizeof m->rate);
        break;
    case CNC3_OP_CLEAR_CONTINUITY:
        ok = next_sequence(m, tx) && !m->armed_mask && !(mask & ~m->installed_mask);
        if (!ok) break;
        m->last_sequence = sequence;
        m->pos_continuity |= mask;
        break;
    case CNC3_OP_SELFTEST:
        ok = next_sequence(m, tx) && !m->armed_mask;
        if (!ok) break;
        m->last_sequence = sequence;
        m->selftest_ok = 1;
        break;
    case CNC3_OP_IO_DISABLE:
        ok = next_sequence(m, tx);
        if (ok) m->last_sequence = sequence;
        break;
    default:
        ok = 0; /* I/O opcodes and MAINT are not modelled: the model refuses them as a LINK fault */
        break;
    }
    if (!ok) {
        m->rejected++;
        latch(m, FW_LINK);
    } else {
        m->accepted++;
    }
}

int cnc3_model_exchange(void *context, enum cnc3_cs cs, const uint8_t *tx, uint8_t *rx, size_t n) {
    struct cnc3_model *m = context;
    uint8_t frame[CNC3_CS_FB_BYTES];
    size_t expected = cs == CNC3_CS_FB ? CNC3_CS_FB_BYTES : CNC3_CS_CMD_BYTES;
    if (n != expected || n > sizeof frame) { /* wrong length on a chip select: rejected, LINK */
        memset(rx, 0, n);
        latch(m, FW_LINK);
        return 0;
    }
    memcpy(frame, tx, n);
    if (m->corrupt_commands) { m->corrupt_commands--; frame[n / 2] ^= 0x10; }
    /* Snapshot at CS assertion, before this frame commits. */
    if (cs == CNC3_CS_FB) {
        if (m->page_pending == 0) cap3_page0(m, rx);
        else cnf3(m, rx);
        if (m->page_pending != 0xFF) m->page_pending = 0xFF; /* the page is consumed */
    } else {
        cns3(m, rx);
    }
    if (m->corrupt_responses) { m->corrupt_responses--; rx[n / 3] ^= 0x04; }
    if (cnc3_validate_command(cs, frame, n) != CNC3_VALID) {
        m->rejected++;
        latch(m, FW_LINK);
        return 0;
    }
    commit(m, cs, frame);
    return 0;
}
