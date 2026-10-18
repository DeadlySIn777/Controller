#ifndef CNC1_SPIDEV_TRANSPORT_H
#define CNC1_SPIDEV_TRANSPORT_H
#include "cnc1.h"
#ifdef __cplusplus
extern "C" {
#endif

/* Laboratory Linux backend. ioctl is synchronous and has no enforced deadline.
 * This must NOT be installed in a qualified cyclic path on the strength of host
 * tests. One calling thread owns a context; all users must honor the device lock.
 * Initialize once, open explicitly, exchange, then close. No automatic reopen. */
#define CNC1_SPIDEV_LAB_MAX_HZ UINT32_C(6250000)
#define CNC1_SPIDEV_CONTEXT_TAG UINT32_C(0x53504931)

struct cnc1_spidev_config {
    const char *device_path; /* Literal /dev/spidevB.C only; no enumeration. */
    uint32_t speed_hz;       /* Positive and <= lab ceiling; not a qualified rate. */
};

/* Test seam. Every callback returns nonnegative success or a negative errno;
 * open returns its fd, transfer ioctl returns bytes, other operations return 0.
 * Production callers normally use cnc1_spidev_open with the Linux wrappers. */
struct cnc1_spidev_ops {
    void *context;
    int (*open_device)(void *, const char *, int);
    int (*verify_character_device)(void *, int);
    int (*lock_device)(void *, int);
    int (*ioctl_device)(void *, int, unsigned long, void *);
    int (*close_device)(void *, int);
};

struct cnc1_spidev {
    uint32_t tag;
    int fd;
    int failed;
    uint32_t configured_speed_hz;
    struct cnc1_spidev_ops ops;
};

void cnc1_spidev_init(struct cnc1_spidev *);
int cnc1_spidev_open(struct cnc1_spidev *, const struct cnc1_spidev_config *);
int cnc1_spidev_open_with_ops(struct cnc1_spidev *, const struct cnc1_spidev_config *,
                            const struct cnc1_spidev_ops *);
int cnc1_spidev_exchange(void *, const uint8_t tx[CNC1_FRAME], uint8_t rx[CNC1_FRAME]);
int cnc1_spidev_close(struct cnc1_spidev *);
struct cnc1_transport cnc1_spidev_transport(struct cnc1_spidev *);
#ifdef __cplusplus
}
#endif
#endif
