/* SPDX-License-Identifier: LicenseRef-Proprietary */
/* Host tests: cnc3 driver core against the cnc3 endpoint reference model (simulation, not hardware). */
#include "cnc3.h"
#include "cnc3_model.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned failures, checks;
#define CHECK(cond, ...) do { checks++; if (!(cond)) { failures++; printf("FAIL %s:%d: ", __FILE__, __LINE__); \
    printf(__VA_ARGS__); printf("\n"); } } while (0)

struct rig {
    struct cnc3_model m;
    struct cnc3_driver d;
    uint64_t now, period;
    unsigned skip_write;
};

static struct cnc3_config config_for(uint16_t mask) {
    struct cnc3_config c;
    memset(&c, 0, sizeof c);
    c.axis_mask = mask;
    for (unsigned i = 0; i < CNC3_CHANNELS; i++) {
        c.scale[i] = 200.0 + 50.0 * i;
        for (unsigned k = 0; k < 4; k++) c.timing[i][k] = 250;
    }
    return c;
}

static void rig_init(struct rig *r, unsigned installed, uint16_t mask) {
    memset(r, 0, sizeof *r);
    cnc3_model_init(&r->m, installed);
    struct cnc3_transport t = {&r->m, cnc3_model_exchange};
    struct cnc3_config c = config_for(mask);
    cnc3_init(&r->d, t, &c, 0x100);
    r->now = 1000000000ull;
    r->period = 1000000ull; /* 1 kHz servo thread */
}

static void cycle(struct rig *r) {
    cnc3_read(&r->d, r->now, r->period);
    if (!r->skip_write) cnc3_write(&r->d, r->now, r->period);
    else r->skip_write--;
    cnc3_model_advance(&r->m, r->period / 20u); /* 50 MHz core ticks */
    r->now += r->period;
}

static void run(struct rig *r, unsigned n) { while (n--) cycle(r); }

static void bring_up(struct rig *r) {
    run(r, 6); /* READ_PAGE, CAP3, CONFIGURE, confirm */
    r->d.reset = 1; cycle(r); r->d.reset = 0; run(r, 2);
}

static void arm(struct rig *r) { r->d.enable = 1; run(r, 3); }

/* Move every configured joint by delta units per cycle for n cycles (continuous motion). */
static void ramp(struct rig *r, unsigned n, double delta) {
    while (n--) {
        for (unsigned i = 0; i < CNC3_CHANNELS; i++)
            if (((unsigned)r->d.config.axis_mask >> i) & 1u) r->d.position_cmd[i] += delta;
        cycle(r);
    }
}

static void test_bring_up(unsigned installed, uint16_t mask) {
    struct rig r;
    rig_init(&r, installed, mask);
    run(&r, 6);
    CHECK(r.d.state == CNC3_OFF, "%u/%03X configured: state %s fault %s", installed, mask, cnc3_state_name(r.d.state),
          cnc3_fault_name(r.d.fault));
    CHECK(r.d.caps.installed_channels == installed, "installed channels");
    CHECK(r.d.watchdog_ns == 5000000u, "watchdog from CAP3: %llu", (unsigned long long)r.d.watchdog_ns);
    CHECK(r.m.config_valid && r.m.required_mask == mask, "endpoint configured with the joint mask");
    CHECK(r.m.expected_module_class == ((mask & 0xF00) ? 1 : 0), "module class follows joints 9-12");
    r.d.enable = 1; run(&r, 3);
    CHECK(r.d.state == CNC3_OFF && !r.m.armed_mask, "enable before reset does not arm");
    r.d.enable = 0; run(&r, 1);
    r.d.reset = 1; cycle(&r); r.d.reset = 0; run(&r, 2);
    CHECK(r.d.state == CNC3_READY, "SYNC acknowledged: %s", cnc3_state_name(r.d.state));
    CHECK(!r.m.armed_mask, "SYNC never arms");
    arm(&r);
    CHECK(r.d.state == CNC3_ACTIVE && r.m.armed_mask == mask, "ARM acknowledged: %s mask %03X",
          cnc3_state_name(r.d.state), r.m.armed_mask);
}

static void test_motion(unsigned installed, uint16_t mask) {
    struct rig r;
    rig_init(&r, installed, mask);
    bring_up(&r);
    arm(&r);
    double worst = 0;
    for (unsigned k = 0; k < 3000; k++) {
        double t = k * 1e-3;
        for (unsigned i = 0; i < CNC3_CHANNELS; i++)
            r.d.position_cmd[i] = (((unsigned)mask >> i) & 1u) ? (1.0 + 0.1 * i) * sin(2 * M_PI * 0.5 * t) : 0;
        cycle(&r);
        if (k > 10)
            for (unsigned i = 0; i < CNC3_CHANNELS; i++) {
                if (!(((unsigned)mask >> i) & 1u)) continue;
                double lag = fabs(r.d.position_fb[i] - r.d.position_cmd[i]) * r.d.config.scale[i];
                if (lag > worst) worst = lag;
            }
    }
    CHECK(r.d.state == CNC3_ACTIVE, "motion run stays active: %s/%s", cnc3_state_name(r.d.state),
          cnc3_fault_name(r.d.fault));
    /* Peak travel per cycle: 2.1 units * pi rad/s * 1 ms * 750 steps/unit = 4.9 steps; allow two cycles. */
    CHECK(worst < 2 * 2.1 * M_PI * 1e-3 * 750 + 2, "tracking within two cycles of travel: %.1f steps", worst);
    for (unsigned k = 0; k < 400; k++) { /* return smoothly to 0.25 units */
        for (unsigned i = 0; i < CNC3_CHANNELS; i++)
            if (((unsigned)mask >> i) & 1u) r.d.position_cmd[i] += (0.25 - r.d.position_cmd[i]) * 0.05;
        cycle(&r);
    }
    for (unsigned i = 0; i < CNC3_CHANNELS; i++) r.d.position_cmd[i] = (((unsigned)mask >> i) & 1u) ? 0.25 : 0;
    run(&r, 20);
    for (unsigned i = 0; i < CNC3_CHANNELS; i++) {
        int64_t want = (((unsigned)mask >> i) & 1u) ? llround(0.25 * r.d.config.scale[i]) : 0;
        CHECK(r.d.steps[i] == want, "channel %u settles on %lld steps: %lld", i, (long long)want, (long long)r.d.steps[i]);
        CHECK((int64_t)(int32_t)r.m.steps[i] == r.d.steps[i], "channel %u driver count equals endpoint count", i);
    }
    r.d.enable = 0; run(&r, 3);
    CHECK(r.d.state == CNC3_READY && !r.m.armed_mask, "DISARM returns to READY");
    run(&r, 10);
    CHECK(r.d.state == CNC3_READY && !r.m.armed_mask && !r.m.fault_word, "idle NOPs keep the link healthy");
}

static void test_wrap(void) {
    struct rig r;
    rig_init(&r, 8, 0x00FF);
    r.d.config.scale[0] = 1000; /* 190 mm/s at 1000 steps/mm = 190k steps/s, near the DDS ceiling */
    bring_up(&r);
    arm(&r);
    double x = 0;
    for (unsigned k = 0; k < 100000; k++) { /* 100 s of simulated time: more than 2^24 steps */
        x += 0.19;
        r.d.position_cmd[0] = x;
        cycle(&r);
        if (r.d.state != CNC3_ACTIVE) break;
    }
    CHECK(r.d.state == CNC3_ACTIVE, "long run active: %s/%s", cnc3_state_name(r.d.state), cnc3_fault_name(r.d.fault));
    CHECK(r.d.steps[0] > (1 << 24), "count passed the 24-bit wrap: %lld", (long long)r.d.steps[0]);
    CHECK(llabs(r.d.steps[0] - llround(x * 1000)) <= 200, "unwrapped count follows the command");
}

static void test_bad_response(void) {
    struct rig r;
    rig_init(&r, 8, 0x00FF);
    bring_up(&r);
    arm(&r);
    ramp(&r, 5, 0.01);
    r.m.corrupt_responses = 1;
    ramp(&r, 1, 0.01);
    CHECK(r.d.state == CNC3_FAULT && r.d.fault == CNC3_FAULT_BAD_FRAME, "corrupted CNF3 faults the driver: %s",
          cnc3_fault_name(r.d.fault));
    run(&r, 10); /* host stopped feeding UPDATE; the endpoint watchdog must stop motion */
    CHECK(!r.m.armed_mask && (r.m.fault_word & (1u << 1)), "endpoint watchdog disarmed: fault %08X", r.m.fault_word);
    run(&r, 50);
    CHECK(r.d.state == CNC3_FAULT && !r.m.armed_mask, "no automatic restart while enable stays high");
    r.d.reset = 1; cycle(&r); r.d.reset = 0; run(&r, 3);
    CHECK(r.d.state == CNC3_FAULT, "reset with enable high is ignored");
    r.d.enable = 0; run(&r, 1);
    r.d.reset = 1; cycle(&r); r.d.reset = 0; run(&r, 3);
    CHECK(r.d.state == CNC3_READY && !r.m.armed_mask, "stopped reset: new session, still disarmed: %s",
          cnc3_state_name(r.d.state));
    CHECK(r.d.events_stored >= 1, "fault events delivered: %llu", (unsigned long long)r.d.events_stored);
    arm(&r);
    CHECK(r.d.state == CNC3_ACTIVE, "re-arm needs a new enable edge and works");
}

static void test_bad_command(void) {
    struct rig r;
    rig_init(&r, 8, 0x00FF);
    bring_up(&r);
    arm(&r);
    r.m.corrupt_commands = 1;
    run(&r, 2);
    CHECK(r.m.fault_word & 1u, "corrupted command latches LINK: %08X", r.m.fault_word);
    CHECK(!r.m.armed_mask, "LINK disarms all");
    CHECK(r.d.state == CNC3_FAULT && r.d.fault == CNC3_FAULT_ENDPOINT && (r.d.endpoint_fault_word & 1u),
          "driver reports the endpoint LINK fault: %s %08X", cnc3_fault_name(r.d.fault), r.d.endpoint_fault_word);
}

static void test_watchdog(void) {
    struct rig r;
    rig_init(&r, 8, 0x00FF);
    bring_up(&r);
    arm(&r);
    r.skip_write = 6; /* host thread stalls on the command side for 6 ms */
    run(&r, 8);
    CHECK((r.m.fault_word & 2u) && !r.m.armed_mask, "5 ms endpoint watchdog trips: %08X", r.m.fault_word);
    CHECK(r.d.state == CNC3_FAULT, "driver faults: %s/%s", cnc3_state_name(r.d.state), cnc3_fault_name(r.d.fault));
}

static void test_stale_sample(void) {
    struct rig r;
    rig_init(&r, 8, 0x00FF);
    bring_up(&r);
    arm(&r);
    cnc3_write(&r.d, r.now + 6000000u, r.period); /* write with a 6 ms old sample */
    CHECK(r.d.state == CNC3_FAULT && r.d.fault == CNC3_FAULT_TIME, "stale sample refused: %s", cnc3_fault_name(r.d.fault));
}

static void test_period_bound(void) {
    struct rig r;
    rig_init(&r, 8, 0x00FF);
    r.period = 3000000u; /* above half the 5 ms watchdog */
    run(&r, 6);
    CHECK(r.d.state == CNC3_FAULT && r.d.fault == CNC3_FAULT_CONFIG && !r.m.config_valid,
          "servo period above watchdog/2 refused before CONFIGURE: %s", cnc3_fault_name(r.d.fault));
}

static void test_twelve_needs_module(void) {
    struct rig r;
    rig_init(&r, 8, 0x0FFF);
    run(&r, 6);
    CHECK(r.d.state == CNC3_FAULT && r.d.fault == CNC3_FAULT_CONFIG && !r.m.config_valid,
          "twelve joints without the MX4 module refused: %s", cnc3_fault_name(r.d.fault));
}

static void test_expansion_removed(void) {
    struct rig r;
    rig_init(&r, 12, 0x0FFF);
    bring_up(&r);
    arm(&r);
    ramp(&r, 3, 0.01);
    r.m.remove_expansion = 1;
    ramp(&r, 3, 0.01);
    CHECK(!r.m.armed_mask && (r.m.fault_word & (1u << 5)), "module removal latches EXPANSION_CHANGED");
    CHECK(r.d.state == CNC3_FAULT && (r.d.endpoint_fault_word & (1u << 5)), "driver faults on removal");
    CHECK(!(r.d.position_valid_mask & 0x0F00), "positions of moving channels are not valid after removal");
    r.d.enable = 0; run(&r, 1);
    r.d.reset = 1; cycle(&r); r.d.reset = 0; run(&r, 8);
    CHECK(r.d.state != CNC3_READY && r.d.state != CNC3_ACTIVE && !r.m.armed_mask,
          "power-cycle fault is not cleared by a reset: %s/%s", cnc3_state_name(r.d.state), cnc3_fault_name(r.d.fault));
}

static void test_continuity(void) {
    struct rig r;
    rig_init(&r, 8, 0x00FF);
    bring_up(&r);
    CHECK(r.d.position_valid_mask == 0, "positions start unreferenced");
    /* A re-reference is a host procedure; the endpoint records it with CLEAR_CONTINUITY. */
    uint8_t tx[CNC3_CS_CMD_BYTES], rx[CNC3_CS_CMD_BYTES];
    struct cnc3_cmd c;
    memset(&c, 0, sizeof c);
    c.opcode = CNC3_OP_CLEAR_CONTINUITY; c.channel_mask = 0x00FF; c.session = r.d.session; c.sequence = ++r.d.sequence;
    CHECK(cnc3_build_cmd(tx, &c) == CNC3_VALID, "CLEAR_CONTINUITY builds");
    cnc3_model_exchange(&r.m, CNC3_CS_CMD, tx, rx, sizeof tx);
    run(&r, 2);
    CHECK(r.d.position_valid_mask == 0x00FF, "continuity published: %03X", r.d.position_valid_mask);
    arm(&r);
    ramp(&r, 3, 0.01);
    r.m.corrupt_commands = 1; /* fault while moving: an unclean stop */
    ramp(&r, 3, 0.01);
    CHECK((r.d.position_valid_mask & 0x00FF) != 0x00FF, "an unclean stop clears continuity: %03X", r.d.position_valid_mask);
}

int main(void) {
    test_bring_up(8, 0x00FF);
    test_bring_up(12, 0x0FFF);
    test_bring_up(12, 0x00FF); /* module fitted, eight joints used */
    test_motion(8, 0x00FF);
    test_motion(12, 0x0FFF);
    test_motion(8, 0x001F); /* five-joint subset */
    test_wrap();
    test_bad_response();
    test_bad_command();
    test_watchdog();
    test_stale_sample();
    test_period_bound();
    test_twelve_needs_module();
    test_expansion_removed();
    test_continuity();
    printf("cnc3 driver vs endpoint model: %u/%u checks passed\n", checks - failures, checks);
    return failures != 0;
}
