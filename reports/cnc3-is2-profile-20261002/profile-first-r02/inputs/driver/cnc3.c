/* SPDX-License-Identifier: LicenseRef-Proprietary */
#include "cnc3.h"
#include <limits.h>
#include <math.h>
#include <string.h>

#define CAP_EXPECT_CORE_HZ 50000000u

static const char *const state_names[] = {"DISCOVER", "WAIT_CAPS", "CONFIGURE", "WAIT_CONFIG", "OFF", "WAIT_SYNC",
                                          "READY", "WAIT_ARM", "ACTIVE", "WAIT_DISARM", "FAULT"};
static const char *const fault_names[] = {"NONE", "TRANSPORT", "BAD_FRAME", "BAD_CAPS", "ACK", "TIME",
                                          "ENDPOINT", "RANGE", "SEQUENCE", "COUNT", "CONFIG", "QUALIFICATION"};

const char *cnc3_state_name(enum cnc3_state s) {
    return (unsigned)s < sizeof state_names / sizeof state_names[0] ? state_names[s] : "?";
}
const char *cnc3_fault_name(enum cnc3_fault f) {
    return (unsigned)f < sizeof fault_names / sizeof fault_names[0] ? fault_names[f] : "?";
}

static void fail(struct cnc3_driver *d, enum cnc3_fault why) {
    if (d->state != CNC3_FAULT) d->fault = why; /* the first fault is preserved */
    d->state = CNC3_FAULT;
    d->feedback_valid = 0;
}

int cnc3_rate(double pps, const struct cnc3_caps *c, int32_t *out) {
    if (!isfinite(pps) || !c->core_hz) return -1;
    double raw = pps * 4294967296.0 / (double)c->core_hz;
    if (!isfinite(raw) || fabs(raw) > (double)c->max_rate) return -1;
    *out = (int32_t)llround(raw);
    return 0;
}

void cnc3_init(struct cnc3_driver *d, struct cnc3_transport t, const struct cnc3_config *config, uint32_t seed) {
    memset(d, 0, sizeof *d);
    d->transport = t;
    d->config = *config;
    d->session = seed ? seed : 1;
    d->state = CNC3_DISCOVER;
}

static int configured_ok(const struct cnc3_driver *d) {
    const struct cnc3_config *c = &d->config;
    /* This exact IS2 derivative has four base encoders and no MPG/expansion
     * implementation. Refuse unsupported requests before any wire operation. */
    if ((c->required_encoder_mask & ~15u) || c->encoder_expansion_class || c->mpg_config) return 0;
    if (!c->axis_mask || (c->axis_mask & ~CNC3_CHANNEL_MASK_LIMIT)) return 0;
    for (unsigned i = 0; i < CNC3_CHANNELS; i++)
        if (((unsigned)c->axis_mask >> i) & 1u) {
            if (!isfinite(c->scale[i]) || c->scale[i] < 1 || c->scale[i] > 1e6) return 0;
            for (unsigned k = 0; k < 4; k++)
                if (c->timing[i][k] < 100 || c->timing[i][k] > 1023) return 0;
        }
    return 1;
}

static int transact(struct cnc3_driver *d, enum cnc3_cs cs, const uint8_t *tx, uint8_t *rx, size_t n) {
    if (d->transport.exchange(d->transport.context, cs, tx, rx, n)) {
        fail(d, CNC3_FAULT_TRANSPORT);
        return -1;
    }
    return 0;
}

/* Capability checks: this derivative explicitly implements the staged IS-2 inventory profile only. */
static int caps_ok(const struct cnc3_caps *c) {
    return c->step_channels == CNC3_CHANNELS && c->fb_frame_bytes == CNC3_CS_FB_BYTES &&
           c->cmd_frame_bytes == CNC3_CS_CMD_BYTES && c->core_hz == CAP_EXPECT_CORE_HZ &&
           c->max_rate == (uint32_t)CNC3_MAX_RATE && c->watchdog_ticks && !memcmp(c->spec_revision, "IS-2", 4) &&
           c->encoders_supported == 4 && c->encoders_base == 4 &&
           (c->encoders_installed == 0 || c->encoders_installed == 4) &&
           c->mpg_ports == 0 && c->accepted_module_class == 0 && c->accepted_encoder_expansion_class == 0 &&
           c->expansion_state == 0 && c->mod_id_latched == 0 &&
           c->event_ring_depth == 0 && c->telemetry_entries == 0 &&
           c->feature_bitmap == UINT32_C(0x00013ffb) &&
           (c->installed_channels == 0 || c->installed_channels == 8 || c->installed_channels == 12) &&
           c->timing_min >= 100 && c->timing_max <= 1023 && c->timing_min <= c->timing_max;
}

static void build_configure(const struct cnc3_driver *d, uint8_t payload[CNC3_PAYLOAD_SIZE]) {
    const struct cnc3_config *c = &d->config;
    uint8_t *p = payload;
    memset(p, 0, CNC3_PAYLOAD_SIZE);
    p[CNC3_CONFIGURE_PAYLOAD_AT_16_FORMAT_OFF] = 0x02;
    p[CNC3_CONFIGURE_PAYLOAD_AT_16_EXPECTED_MODULE_CLASS_OFF] =
        (c->axis_mask & 0x0F00u) ? d->caps.accepted_module_class : 0;
    cnc3_put(p + CNC3_CONFIGURE_PAYLOAD_AT_16_REQUIRED_MASK_OFF, 2, c->axis_mask);
    cnc3_put(p + CNC3_CONFIGURE_PAYLOAD_AT_16_ALARM_TRIP_MASK_OFF, 2, c->alarm_trip_mask & c->axis_mask);
    cnc3_put(p + CNC3_CONFIGURE_PAYLOAD_AT_16_ALARM_ON_NO_CURRENT_OFF, 2, c->alarm_on_no_current & 0x0FFFu);
    for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++)
        for (unsigned k = 0; k < 4; k++) {
            uint16_t v = (((unsigned)c->axis_mask >> ch) & 1u) ? c->timing[ch][k] : d->caps.reference_timing[k];
            cnc3_put(p + CNC3_CONFIGURE_PAYLOAD_AT_16_TIMING_0_OFF + 8 * ch + 2 * k, 2, v);
        }
    cnc3_put(p + CNC3_CONFIGURE_PAYLOAD_AT_16_CONFIG_HASH_OFF, 4, c->config_hash);
    cnc3_put(p + CNC3_CONFIGURE_PAYLOAD_AT_16_SERVO_PERIOD_US_OFF, 2, (uint32_t)(d->servo_period_ns / 1000u));
    p[CNC3_CONFIGURE_PAYLOAD_AT_16_EXPECTED_ENCODER_EXPANSION_CLASS_OFF] = c->encoder_expansion_class;
    p[CNC3_CONFIGURE_PAYLOAD_AT_16_ENCODER_FILTER_TICKS_OFF] = c->encoder_filter_ticks;
    cnc3_put(p + CNC3_CONFIGURE_PAYLOAD_AT_16_REQUIRED_ENCODER_MASK_OFF, 2, c->required_encoder_mask);
    p[CNC3_CONFIGURE_PAYLOAD_AT_16_MPG_CONFIG_OFF] = c->mpg_config;
}

/* Host sample-age acceptance is never looser than the discovered endpoint watchdog. */
static int sample_fresh(const struct cnc3_driver *d, uint64_t now) {
    return d->have_sample && now >= d->sampled_ns && now - d->sampled_ns <= d->watchdog_ns;
}

static void accept_feedback(struct cnc3_driver *d, const struct cnc3_feedback *f, uint64_t now) {
    if (d->have_sample) {
        uint32_t elapsed = f->snapshot_ticks - d->previous_ticks;
        /* Modulo wrap allowed; an identical timestamp or more than 10 ms is stale or a reset. */
        if (!elapsed || elapsed > 500000u) { fail(d, CNC3_FAULT_TIME); return; }
        uint64_t maximum = (((uint64_t)elapsed * d->caps.max_rate + UINT32_MAX) >> 32) + 2;
        int64_t next[CNC3_CHANNELS];
        for (unsigned i = 0; i < CNC3_CHANNELS; i++) {
            next[i] = cnc3_unwrap_u24(d->steps[i], f->step_count[i]);
            int64_t delta = next[i] - d->steps[i];
            if (delta > (int64_t)maximum || delta < -(int64_t)maximum) { fail(d, CNC3_FAULT_COUNT); return; }
        }
        memcpy(d->steps, next, sizeof next);
        for (unsigned i = 0; i < CNC3_ENCODERS; i++) d->encoders[i] = cnc3_unwrap_u24(d->encoders[i], f->encoder_count[i]);
    } else {
        /* First sample (or after a reset): baseline from the raw 24-bit counters. */
        for (unsigned i = 0; i < CNC3_CHANNELS; i++) d->steps[i] = cnc3_unwrap_u24(0, f->step_count[i]);
        for (unsigned i = 0; i < CNC3_ENCODERS; i++) d->encoders[i] = cnc3_unwrap_u24(0, f->encoder_count[i]);
    }
    for (unsigned i = 0; i < CNC3_CHANNELS; i++)
        d->position_fb[i] = (((unsigned)d->config.axis_mask >> i) & 1u) ? (double)d->steps[i] / d->config.scale[i] : 0.0;
    d->position_valid_mask = (uint16_t)(f->pos_continuity & d->config.axis_mask);
    d->previous_ticks = f->snapshot_ticks;
    d->have_sample = 1;
    d->sampled_ns = now;
    d->fb = *f;
}

/* FB_READ and NOP accept session 0 or the endpoint's current session (section 3.4). Inside a
 * session this driver started, that is d->session; anywhere else (before SYNC, after a fault)
 * the endpoint's session is not known to be ours, so 0 is used. */
static uint32_t link_session(const struct cnc3_driver *d) {
    return d->state >= CNC3_WAIT_SYNC && d->state <= CNC3_WAIT_DISARM ? d->session : 0;
}

static void check_ack(struct cnc3_driver *d, const struct cnc3_feedback *f) {
    if (d->state == CNC3_OFF || d->state == CNC3_FAULT) return;
    if (f->fault_word) { d->endpoint_fault_word = f->fault_word; fail(d, CNC3_FAULT_ENDPOINT); return; }
    if (f->session != d->session || f->last_sequence != d->sequence) { fail(d, CNC3_FAULT_ACK); return; }
    if ((f->state & (CNC3_ST_QUALIFIED | CNC3_ST_CONFIG_VALID)) != (CNC3_ST_QUALIFIED | CNC3_ST_CONFIG_VALID)) {
        fail(d, CNC3_FAULT_ENDPOINT);
        return;
    }
    if (d->state == CNC3_WAIT_SYNC || d->state == CNC3_WAIT_DISARM) {
        if (f->armed_mask) { fail(d, CNC3_FAULT_ACK); return; }
        d->state = CNC3_READY;
    } else if (d->state == CNC3_WAIT_ARM) {
        if (f->armed_mask != d->config.axis_mask) { fail(d, CNC3_FAULT_ACK); return; }
        d->state = CNC3_ACTIVE;
    } else if (d->state == CNC3_ACTIVE && f->armed_mask != d->config.axis_mask) {
        fail(d, CNC3_FAULT_ACK);
        return;
    }
    d->feedback_valid = 1;
}

void cnc3_read(struct cnc3_driver *d, uint64_t now, uint64_t period) {
    uint8_t tx[CNC3_CS_FB_BYTES], rx[CNC3_CS_FB_BYTES];
    d->servo_period_ns = period;
    d->cycles++;
    if (!configured_ok(d)) { fail(d, CNC3_FAULT_CONFIG); return; }
    if (d->state == CNC3_DISCOVER) {
        uint8_t page = 0;
        if (cnc3_build_fb(tx, CNC3_OP_READ_PAGE, 0, 0, 0, &page, 1) || transact(d, CNC3_CS_FB, tx, rx, sizeof rx)) return;
        struct cnc3_feedback f;
        if ((d->last_result = cnc3_decode_cnf3(rx, sizeof rx, &f))) { fail(d, CNC3_FAULT_BAD_FRAME); return; }
        d->fb = f; /* the endpoint's session and sequence decide how CONFIGURE is numbered */
        d->state = CNC3_WAIT_CAPS;
        return;
    }
    if (d->state == CNC3_WAIT_CAPS) {
        if (cnc3_build_fb_read(tx, 0, 0, 0xFF, 0) || transact(d, CNC3_CS_FB, tx, rx, sizeof rx)) return;
        if ((d->last_result = cnc3_decode_cap3_page0(rx, sizeof rx, &d->caps)) || !caps_ok(&d->caps)) {
            fail(d, CNC3_FAULT_BAD_CAPS);
            return;
        }
        if (!d->caps.installed_channels) { /* qualification still running: ask again, bounded */
            if (++d->caps_attempts >= CNC3_CAPS_ATTEMPTS) fail(d, CNC3_FAULT_QUALIFICATION);
            else d->state = CNC3_DISCOVER;
            return;
        }
        uint16_t installed = d->caps.installed_channels == 12 ? 0x0FFFu : 0x00FFu;
        if (d->config.axis_mask & ~installed) { fail(d, CNC3_FAULT_CONFIG); return; }
        d->watchdog_ns = (uint64_t)d->caps.watchdog_ticks * UINT64_C(1000000000) / d->caps.core_hz;
        d->state = CNC3_CONFIGURE;
        return;
    }
    if (d->state == CNC3_CONFIGURE) {
        uint8_t payload[CNC3_PAYLOAD_SIZE];
        uint64_t period_us = period / 1000u;
        if (period_us < 250 || period_us > 2500 || period > d->watchdog_ns / 2) { fail(d, CNC3_FAULT_CONFIG); return; }
        build_configure(d, payload);
        /* Section 3.4 (record 5.3 rule): session 0 / sequence 0 before a session, otherwise the
         * endpoint's current session and its next sequence. The endpoint is disarmed here. */
        uint32_t session = d->fb.session, sequence = session ? d->fb.last_sequence + 1u : 0u;
        if (session && !sequence) { fail(d, CNC3_FAULT_SEQUENCE); return; }
        if ((d->last_result = cnc3_build_fb(tx, CNC3_OP_CONFIGURE, 0, session, sequence, payload, sizeof payload))) {
            fail(d, CNC3_FAULT_CONFIG);
            return;
        }
        if (transact(d, CNC3_CS_FB, tx, rx, sizeof rx)) return;
        struct cnc3_feedback f;
        if ((d->last_result = cnc3_decode_cnf3(rx, sizeof rx, &f))) { fail(d, CNC3_FAULT_BAD_FRAME); return; }
        d->state = CNC3_WAIT_CONFIG;
        return;
    }
    if (d->state == CNC3_FAULT && !d->discovered) return; /* nothing proven to talk to: wait for a stopped reset */
    if (cnc3_build_fb_read(tx, link_session(d), d->event_ack, 0xFF, 0) || transact(d, CNC3_CS_FB, tx, rx, sizeof rx))
        return;
    struct cnc3_feedback f;
    if ((d->last_result = cnc3_decode_cnf3(rx, sizeof rx, &f))) { fail(d, CNC3_FAULT_BAD_FRAME); return; }
    if (d->state == CNC3_WAIT_CONFIG) {
        if (!(f.state & CNC3_ST_CONFIG_VALID) || (f.fault_word & CNC3_FW_CONFIG_REJECTED) ||
            f.installed_mask != (d->caps.installed_channels == 12 ? 0x0FFFu : 0x00FFu)) {
            d->endpoint_fault_word = f.fault_word;
            fail(d, CNC3_FAULT_CONFIG);
            return;
        }
        d->discovered = 1;
        d->have_sample = 0;
        d->state = CNC3_OFF;
    }
    accept_feedback(d, &f, now);
    if (d->state != CNC3_FAULT) check_ack(d, &f);
}

static void store_event(struct cnc3_driver *d, const struct cnc3_status *s) {
    if (!s->event_seq || s->event_seq == d->last_event_seq) return; /* none, or the same record shown again */
    struct cnc3_event *e = &d->events[(d->event_head + d->event_count) % CNC3_EVENT_LOG];
    if (d->event_count == CNC3_EVENT_LOG) d->event_head = (d->event_head + 1) % CNC3_EVENT_LOG;
    else d->event_count++;
    e->seq = s->event_seq; e->type = s->event_type; e->source = s->event_source; e->flags = s->event_flags;
    e->ticks = s->event_ticks;
    memcpy(e->value, s->event_value, sizeof e->value);
    e->cycle = d->cycles;
    d->events_stored++;
    d->last_event_seq = s->event_seq;
    d->event_ack = s->event_seq; /* acknowledged in the next FB_READ: stored before acknowledged */
}

static void store_telemetry(struct cnc3_driver *d, const struct cnc3_status *s) {
    if (s->telemetry_source == 0xFF || !(s->telemetry_validity & 1u)) return;
    unsigned slot = ((unsigned)s->telemetry_source * 7u + s->telemetry_page) % CNC3_TELEMETRY_SLOTS;
    struct cnc3_telemetry *t = &d->telemetry[slot];
    t->valid = 1; t->source = s->telemetry_source; t->page = s->telemetry_page; t->counter = s->telemetry_counter;
    t->validity = s->telemetry_validity; t->rx_ticks = s->telemetry_rx_ticks; t->card_age_us = s->telemetry_card_age_us;
    memcpy(t->data, s->telemetry_data, sizeof t->data);
}

static void send_cmd(struct cnc3_driver *d, const struct cnc3_cmd *c) {
    uint8_t tx[CNC3_CS_CMD_BYTES], rx[CNC3_CS_CMD_BYTES];
    if ((d->last_result = cnc3_build_cmd(tx, c))) { fail(d, CNC3_FAULT_RANGE); return; }
    if (transact(d, CNC3_CS_CMD, tx, rx, sizeof rx)) return;
    struct cnc3_status s;
    /* The CNS3 snapshot precedes this command's commit: never use it to acknowledge the command. */
    if ((d->last_result = cnc3_decode_cns3(rx, sizeof rx, &s))) { fail(d, CNC3_FAULT_BAD_FRAME); return; }
    d->status = s;
    store_event(d, &s);
    store_telemetry(d, &s);
    d->writes++;
}

static void send_nop(struct cnc3_driver *d) {
    struct cnc3_cmd c;
    memset(&c, 0, sizeof c);
    c.opcode = CNC3_OP_NOP;
    c.session = link_session(d);
    send_cmd(d, &c);
}

void cnc3_write(struct cnc3_driver *d, uint64_t now, uint64_t period) {
    unsigned rise = d->enable && !d->last_enable, reset = d->reset && !d->last_reset;
    d->last_enable = d->enable;
    d->last_reset = d->reset;
    if (!d->discovered) {
        if (reset && !d->enable && d->state == CNC3_FAULT) { /* stopped reset: rediscover, never arm */
            uint32_t seed = d->session;
            struct cnc3_config config = d->config;
            struct cnc3_transport t = d->transport;
            cnc3_init(d, t, &config, seed);
        }
        return;
    }
    if (period > d->watchdog_ns / 2 || !period) { fail(d, CNC3_FAULT_CONFIG); send_nop(d); return; }
    if (reset && !d->enable && (d->state == CNC3_OFF || d->state == CNC3_READY || d->state == CNC3_FAULT)) {
        if (d->state == CNC3_FAULT && (d->fault == CNC3_FAULT_CONFIG || d->fault == CNC3_FAULT_BAD_CAPS ||
                                       (d->endpoint_fault_word & (CNC3_FW_CONFIG_REJECTED | CNC3_FW_POWER_CYCLE)))) {
            uint32_t seed = d->session; /* configuration must be proven again before any session */
            struct cnc3_config config = d->config;
            struct cnc3_transport t = d->transport;
            cnc3_init(d, t, &config, seed);
            return;
        }
        /* New session (nonzero, different from the endpoint's), sequence 0. SYNC never arms. */
        do { d->session++; } while (!d->session || d->session == d->fb.session);
        d->sequence = 0;
        d->fault = CNC3_FAULT_NONE;
        d->endpoint_fault_word = 0;
        d->have_sample = 0; /* re-baseline counters; retained positions must be re-referenced */
        d->state = CNC3_WAIT_SYNC;
        struct cnc3_cmd c;
        memset(&c, 0, sizeof c);
        c.opcode = CNC3_OP_SYNC;
        c.session = d->session;
        send_cmd(d, &c);
        return;
    }
    if (d->state == CNC3_OFF || d->state == CNC3_FAULT) { send_nop(d); return; } /* no feed => endpoint watchdog */
    if (!sample_fresh(d, now)) { fail(d, CNC3_FAULT_TIME); send_nop(d); return; }
    if (d->state == CNC3_WAIT_SYNC || d->state == CNC3_WAIT_ARM || d->state == CNC3_WAIT_DISARM) { send_nop(d); return; }
    if (d->sequence >= UINT32_MAX - 1) { fail(d, CNC3_FAULT_SEQUENCE); send_nop(d); return; }
    struct cnc3_cmd c;
    memset(&c, 0, sizeof c);
    c.session = d->session;
    if (d->state == CNC3_READY) {
        if (!rise) { send_nop(d); return; }
        c.opcode = CNC3_OP_ARM;
        c.channel_mask = d->config.axis_mask;
        c.sequence = ++d->sequence;
        d->state = CNC3_WAIT_ARM;
        send_cmd(d, &c);
        return;
    }
    if (d->state != CNC3_ACTIVE) { send_nop(d); return; }
    if (!d->enable) {
        c.opcode = CNC3_OP_DISARM;
        c.sequence = ++d->sequence;
        d->state = CNC3_WAIT_DISARM;
        send_cmd(d, &c);
        return;
    }
    c.opcode = CNC3_OP_UPDATE;
    c.channel_mask = d->config.axis_mask;
    for (unsigned i = 0; i < CNC3_CHANNELS; i++) {
        if (!(((unsigned)d->config.axis_mask >> i) & 1u)) continue;
        double target = d->position_cmd[i] * d->config.scale[i];
        if (!isfinite(target) || fabs(target) > 1e12) { fail(d, CNC3_FAULT_RANGE); send_nop(d); return; }
        /* Position-mode STEP servo on the emitted-count accumulator (one-cycle correction). */
        double pps = ((double)llround(target) - (double)d->steps[i]) * 1e9 / (double)period;
        if (cnc3_rate(pps, &d->caps, &c.rate[i])) { fail(d, CNC3_FAULT_RANGE); send_nop(d); return; }
    }
    c.sequence = ++d->sequence;
    send_cmd(d, &c);
}
