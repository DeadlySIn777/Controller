#ifndef SERVICE_HEALTH_H
#define SERVICE_HEALTH_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define SH_FRAME_BYTES 40u
#define SH_HOST_DISARMED 1u
#define SH_HOST_FAULT 2u
#define SH_KNOWN_FLAGS 3u

/* Advisory diagnostic freshness deadlines used by the ESP-IDF application.
 * Both are measured in local processing time (when the frame is parsed, not
 * when its bytes reached the UART) and compared strictly (age < deadline).
 * They were chosen for this diagnostic helper; they are not measured or
 * approved machine limits and are not the FPGA/TPS3431 motion watchdog.
 * link_fresh: an accepted frame (valid CRC and a new, higher sequence) was
 *   parsed less than SH_LINK_TIMEOUT_MS ago. A sender must therefore deliver
 *   accepted frames with gaps well below 1000 ms; 4-10 Hz is recommended and
 *   an exact 1 Hz sender sits on the strict boundary and will flap.
 * backend_progress_fresh: link_fresh AND an accepted frame from the same
 *   host boot carried a forward completed-cycle counter change (difference
 *   1..2^31-1 modulo 2^32) less than SH_PROGRESS_TIMEOUT_MS ago. Accepted
 *   frames carrying a counter advance must therefore be spaced well below
 *   500 ms (at 4 Hz every frame must show an advance; at 10 Hz at least every
 *   fourth frame). The first frame of a new boot identity
 *   is only a baseline. Replayed or duplicate sequences renew neither. */
#define SH_LINK_TIMEOUT_MS 1000u
#define SH_PROGRESS_TIMEOUT_MS 500u

/* Read-only diagnostic state. None of these flags grant machine authority. */
typedef struct {
    bool seen;
    bool progress_seen;
    uint64_t host_boot;
    uint64_t host_uptime;
    uint64_t last_frame_ms;
    uint64_t last_progress_ms;
    uint32_t sequence;
    uint32_t progress;
    uint32_t flags;
    uint32_t accepted;
    uint32_t rejected;
    uint8_t rx[SH_FRAME_BYTES];
    size_t used;
} sh_state;

typedef struct {
    bool host_seen;
    bool link_fresh;
    bool backend_progress_fresh;
    bool host_reported_disarmed;
    bool host_reported_fault;
    bool motion_authority; /* Always false in this service firmware. */
} sh_snapshot;

void sh_init(sh_state *state);
uint32_t sh_crc32(const uint8_t *data, size_t length);
bool sh_accept(sh_state *state, const uint8_t *frame, size_t length, uint64_t now_ms);
void sh_feed(sh_state *state, uint8_t byte, uint64_t now_ms);
sh_snapshot sh_observe(const sh_state *state, uint64_t now_ms,
                       uint32_t link_timeout_ms, uint32_t progress_timeout_ms);
#endif
