#include "service_health.h"
#include <string.h>

static uint32_t read32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static uint64_t read64(const uint8_t *p) {
    return (uint64_t)read32(p) | ((uint64_t)read32(p + 4) << 32);
}
static void increment(uint32_t *value) {
    if (*value != UINT32_MAX) ++*value;
}
void sh_init(sh_state *state) { memset(state, 0, sizeof(*state)); }
uint32_t sh_crc32(const uint8_t *data, size_t length) {
    uint32_t crc = UINT32_MAX;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((crc & 1u) ? UINT32_C(0xedb88320) : 0u);
    }
    return ~crc;
}

bool sh_accept(sh_state *s, const uint8_t *frame, size_t length, uint64_t now_ms) {
    if (frame == NULL || length != SH_FRAME_BYTES || memcmp(frame, "ESV1", 4) != 0 ||
        frame[4] != 1 || frame[5] != 1 || frame[6] != 28 || frame[7] != 0 ||
        read32(frame + 36) != sh_crc32(frame, 36)) {
        increment(&s->rejected);
        return false;
    }
    const uint64_t boot = read64(frame + 8), uptime = read64(frame + 24);
    const uint32_t seq = read32(frame + 16), progress = read32(frame + 20);
    const uint32_t flags = read32(frame + 32);
    if (!boot || (flags & ~SH_KNOWN_FLAGS) ||
        (s->seen && now_ms < s->last_frame_ms)) {
        increment(&s->rejected);
        return false;
    }
    const bool same_boot = s->seen && boot == s->host_boot;
    /* Sequence never wraps in one host boot. A restart creates a new identity.
       CRC is corruption detection, not authentication of the UART sender. */
    if (same_boot && (seq <= s->sequence || uptime < s->host_uptime)) {
        increment(&s->rejected);
        return false;
    }
    const uint32_t progress_delta = progress - s->progress;
    if (same_boot && progress_delta >= UINT32_C(0x80000000)) {
        increment(&s->rejected);
        return false;
    }
    if (!same_boot) {
        /* One sample establishes a baseline, not proof that a cycle advanced. */
        s->progress_seen = false;
        s->last_progress_ms = now_ms;
    } else if (progress_delta != 0) {
        s->progress_seen = true;
        s->last_progress_ms = now_ms;
    }
    s->seen = true;
    s->host_boot = boot;
    s->host_uptime = uptime;
    s->sequence = seq;
    s->progress = progress;
    s->flags = flags;
    s->last_frame_ms = now_ms;
    increment(&s->accepted);
    return true;
}

void sh_feed(sh_state *s, uint8_t byte, uint64_t now_ms) {
    s->rx[s->used++] = byte;
    /* Sliding prefix search also recovers from noise and truncated frames. */
    while (s->used && memcmp(s->rx, "ESV1", s->used < 4 ? s->used : 4) != 0) {
        --s->used;
        memmove(s->rx, s->rx + 1, s->used);
    }
    if (s->used == SH_FRAME_BYTES) {
        if (sh_accept(s, s->rx, SH_FRAME_BYTES, now_ms)) s->used = 0;
        else {
            --s->used;
            memmove(s->rx, s->rx + 1, s->used);
            while (s->used && memcmp(s->rx, "ESV1", s->used < 4 ? s->used : 4) != 0) {
                --s->used;
                memmove(s->rx, s->rx + 1, s->used);
            }
        }
    }
}

sh_snapshot sh_observe(const sh_state *s, uint64_t now_ms,
                       uint32_t link_timeout_ms, uint32_t progress_timeout_ms) {
    const bool link = s->seen && link_timeout_ms > 0 &&
        now_ms >= s->last_frame_ms && now_ms - s->last_frame_ms < link_timeout_ms;
    const bool progress = link && s->progress_seen && progress_timeout_ms > 0 &&
        now_ms >= s->last_progress_ms && now_ms - s->last_progress_ms < progress_timeout_ms;
    return (sh_snapshot){s->seen, link, progress,
        link && (s->flags & SH_HOST_DISARMED) != 0,
        link && (s->flags & SH_HOST_FAULT) != 0, false};
}
