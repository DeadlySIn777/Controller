/* SPDX-License-Identifier: LicenseRef-Proprietary */
/* Host tests of the C CNC3 codec against the Python reference's golden vectors. */
#include "cnc3_proto.h"
#include "cnc3_vectors.h"
#include <stdio.h>
#include <string.h>

static unsigned failures, checks;
#define CHECK(cond, ...) do { checks++; if (!(cond)) { failures++; printf("FAIL %s:%d: ", __FILE__, __LINE__); \
    printf(__VA_ARGS__); printf("\n"); } } while (0)

static void test_crc(void) {
    CHECK(cnc3_crc16((const uint8_t *)"123456789", 9) == 0x29B1, "crc16 check value");
    CHECK(cnc3_crc32c((const uint8_t *)"123456789", 9) == 0xE3069283u, "crc32c check value");
}

static void test_golden_vectors(void) {
    for (size_t i = 0; i < CNC3_VECTOR_COUNT; i++) {
        const struct cnc3_vector *v = &cnc3_vectors[i];
        int r = cnc3_validate_labelled(v->chip_select, v->data, v->length);
        CHECK(!strcmp(cnc3_result_name(r), v->expect), "vector %s: C says %s, Python says %s", v->name,
              cnc3_result_name(r), v->expect);
    }
}

static void test_every_bit_flip(void) {
    for (size_t i = 0; i < CNC3_VECTOR_COUNT; i++) {
        const struct cnc3_vector *v = &cnc3_vectors[i];
        if (strcmp(v->expect, "valid")) continue;
        uint8_t frame[176];
        unsigned missed = 0;
        for (size_t bit = 0; bit < v->length * 8; bit++) {
            memcpy(frame, v->data, v->length);
            frame[bit / 8] ^= (uint8_t)(1u << (bit % 8));
            if (cnc3_validate_labelled(v->chip_select, frame, v->length) != CNC3_E_CRC) missed++;
        }
        CHECK(!missed, "vector %s: %u single-bit flips not reported as CRC", v->name, missed);
    }
}

static void test_update(unsigned channels, uint16_t mask) {
    struct cnc3_cmd c;
    uint8_t frame[CNC3_CS_CMD_BYTES];
    memset(&c, 0, sizeof c);
    c.opcode = CNC3_OP_UPDATE;
    c.channel_mask = mask;
    c.session = 0x11223344u;
    c.sequence = 42;
    for (unsigned ch = 0; ch < channels; ch++) c.rate[ch] = (ch & 1 ? -1 : 1) * (int32_t)(1000 * (ch + 1));
    c.dout_image = 0x0005;
    CHECK(cnc3_build_cmd(frame, &c) == CNC3_VALID, "%u-channel UPDATE builds", channels);
    for (unsigned ch = 0; ch < CNC3_CHANNELS; ch++) {
        int32_t got = (int32_t)cnc3_get(frame + CNC3_CMD_COMMAND_RATE_0_OFF + 4 * ch, 4);
        CHECK(got == c.rate[ch], "%u-channel rate %u", channels, ch);
    }
    if (channels < CNC3_CHANNELS) {
        c.rate[channels] = 1; /* a rate outside the mask */
        CHECK(cnc3_build_cmd(frame, &c) == CNC3_E_UNMASKED_RATE, "rate outside %u-channel mask rejected", channels);
        c.rate[channels] = 0;
    }
    c.rate[0] = CNC3_MAX_RATE + 1;
    CHECK(cnc3_build_cmd(frame, &c) == CNC3_E_RATE_CLAMP, "rate clamp");
    c.rate[0] = -CNC3_MAX_RATE;
    CHECK(cnc3_build_cmd(frame, &c) == CNC3_VALID, "negative rate limit accepted");
    c.channel_mask = (uint16_t)(mask | 0x1000);
    CHECK(cnc3_build_cmd(frame, &c) == CNC3_E_MASK_WIDTH, "mask bit 12 rejected");
}

static void test_fb_read(void) {
    uint8_t frame[CNC3_CS_FB_BYTES];
    CHECK(cnc3_build_fb_read(frame, 7, 3, 0xFF, 0) == CNC3_VALID, "FB_READ builds");
    CHECK(frame[CNC3_PAYLOAD_OFF] == 3 && frame[CNC3_PAYLOAD_OFF + 1] == 0xFF, "FB_READ payload");
    uint8_t long_payload[CNC3_PAYLOAD_SIZE + 1];
    memset(long_payload, 0, sizeof long_payload);
    CHECK(cnc3_build_fb(frame, CNC3_OP_FB_READ, 0, 1, 0, long_payload, sizeof long_payload) == CNC3_E_LENGTH,
          "oversized payload refused");
    CHECK(cnc3_validate_command(CNC3_CS_FB, frame, 175) == CNC3_E_LENGTH, "short CS_FB");
    CHECK(cnc3_validate_command(CNC3_CS_CMD, frame, sizeof frame) == CNC3_E_LENGTH, "CS_FB frame on CS_CMD");
}

static void test_cnf3(void) {
    struct cnc3_feedback f, d;
    uint8_t frame[CNC3_FB_RESPONSE_CNF3_LEN];
    memset(&f, 0, sizeof f);
    f.state = 0x2B; f.armed_mask = 0x00FF; f.session = 0x11223344u; f.last_sequence = 0x102;
    f.snapshot_ticks = 0xDEADBEEFu; f.fault_word = 0x01000001u; f.installed_mask = 0x0FFF;
    f.step_count[0] = 0xABCDEF; f.step_count[11] = 1; f.encoder_count[5] = 0x800000;
    f.encoder_valid_mask = 0x000F; f.din = 0x123456; f.din_age = 7; f.dout_applied = 0x8001;
    f.ain[2] = -5; f.ain_status = 0x0F; f.port_status[5] = 0x0D; f.mx4_expansion = 0x4F;
    f.safety_power_word = 0x0FFFFFFFu; f.config_generation = 3; f.pendant_inputs = 0x0401;
    cnc3_encode_cnf3(frame, &f);
    CHECK(!memcmp(frame, cnc3_cnf3_reference, sizeof frame), "CNF3 encoding matches the Python reference");
    CHECK(cnc3_decode_cnf3(cnc3_cnf3_reference, sizeof cnc3_cnf3_reference, &d) == CNC3_VALID, "CNF3 decodes");
    CHECK(!memcmp(&d, &f, sizeof d), "CNF3 decode round trip");
    frame[40] ^= 1;
    CHECK(cnc3_decode_cnf3(frame, sizeof frame, &d) == CNC3_E_CRC, "CNF3 CRC");
    CHECK(cnc3_decode_cnf3(cnc3_cns3_reference, sizeof cnc3_cns3_reference, &d) == CNC3_E_LENGTH, "CNS3 as CNF3");
}

static void test_cns3(void) {
    struct cnc3_status s, d;
    uint8_t frame[CNC3_CMD_RESPONSE_CNS3_LEN];
    memset(&s, 0, sizeof s);
    s.state = 0x2B; s.armed_mask = 0x0FFF; s.session = 0x11223344u; s.last_sequence = 0x103; s.snapshot_ticks = 5;
    s.fault_word = 0x00010000u; s.dout_image_in_force = 0x00F0; s.event_seq = 9; s.event_type = 2;
    s.event_source = 11; s.event_ticks = 0x01020304u; s.event_value[0] = 0xFFFFFE; s.event_value[3] = 0x100;
    s.telemetry_source = 0x80; s.telemetry_page = 1; s.telemetry_validity = 3; s.telemetry_card_age_us = 0xFFFF;
    for (unsigned i = 0; i < sizeof s.telemetry_data; i++) s.telemetry_data[i] = (uint8_t)(i + 1);
    s.last_update_interval_us = 1000; s.late_update_count = 2; s.slot_status = 0x00012345u;
    cnc3_encode_cns3(frame, &s);
    CHECK(!memcmp(frame, cnc3_cns3_reference, sizeof frame), "CNS3 encoding matches the Python reference");
    CHECK(cnc3_decode_cns3(cnc3_cns3_reference, sizeof cnc3_cns3_reference, &d) == CNC3_VALID, "CNS3 decodes");
    CHECK(!memcmp(&d, &s, sizeof d), "CNS3 decode round trip");
    frame[0] = 'X';
    cnc3_seal_host(frame, sizeof frame);
    CHECK(cnc3_decode_cns3(frame, sizeof frame, &d) == CNC3_E_MAGIC, "CNS3 magic");
}

static void test_unwrap(void) {
    CHECK(cnc3_unwrap_u24(0, 5) == 5, "unwrap small");
    CHECK(cnc3_unwrap_u24(0xFFFFFE, 1) == 0x1000001, "unwrap forward across wrap");
    CHECK(cnc3_unwrap_u24(0x1000001, 0xFFFFFF) == 0xFFFFFF, "unwrap backward across wrap");
    CHECK(cnc3_unwrap_u24(-3, 0xFFFFFE) == -2, "unwrap negative total");
    int64_t total = 0;
    uint32_t raw = 0;
    for (unsigned i = 0; i < 100000; i++) { /* 100000 x 0x7FFF counts, about 195 wraps */
        raw = (raw + 0x7FFFu) & 0xFFFFFFu;
        total = cnc3_unwrap_u24(total, raw);
    }
    CHECK(total == (int64_t)100000 * 0x7FFF, "unwrap long run");
}

static void test_iol1(void) {
    uint8_t f[CNC3_IOL1_COMMAND_LEN];
    memset(f, 0, sizeof f);
    f[0] = 0xA7; f[1] = 1; f[2] = 2; f[3] = 1;
    cnc3_put(f + CNC3_IOL1_COMMAND_EPOCH_OFF, 2, 9);
    cnc3_put(f + CNC3_IOL1_COMMAND_SEQUENCE_OFF, 2, 4);
    cnc3_seal_iol1(f);
    CHECK(cnc3_validate_iol1_command(f, sizeof f, 2, 1) == CNC3_VALID, "IOL1 valid");
    CHECK(cnc3_validate_iol1_command(f, sizeof f, 3, 1) == CNC3_E_CLASS, "IOL1 class");
    CHECK(cnc3_validate_iol1_command(f, sizeof f, 2, 2) == CNC3_E_SLOT, "IOL1 slot");
    f[CNC3_IOL1_COMMAND_CONTROL_OFF] = 1; /* SYNC with nonzero sequence */
    cnc3_seal_iol1(f);
    CHECK(cnc3_validate_iol1_command(f, sizeof f, -1, -1) == CNC3_E_SEQUENCE, "IOL1 SYNC sequence");
}

int main(void) {
    test_crc();
    test_golden_vectors();
    test_every_bit_flip();
    test_update(8, 0x00FF);
    test_update(12, 0x0FFF);
    test_fb_read();
    test_cnf3();
    test_cns3();
    test_unwrap();
    test_iol1();
    printf("cnc3 codec: %u/%u checks passed (%u golden vectors, spec %s)\n", checks - failures, checks,
           (unsigned)CNC3_VECTOR_COUNT, CNC3_SPEC_REVISION);
    return failures != 0;
}
