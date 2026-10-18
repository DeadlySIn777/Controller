#define _GNU_SOURCE
#include "spidev_transport.h"
#include <errno.h>
#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
#define CHECK(condition) do { checks++; if (!(condition)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #condition); exit(1); } } while (0)
struct fake {
    int opens, closes, locks, verified, config_calls, transfers;
    int open_error, verify_error, lock_error, close_error, fail_config_call;
    int return_bytes, readback_override;
    uint32_t written_speed;
    uint8_t expected_tx[CNC1_FRAME];
};
static int mock_open(void *context, const char *path, int flags) {
    struct fake *f = context; f->opens++;
    CHECK(!strcmp(path, "/dev/spidev2.1"));
    CHECK(flags == (O_RDWR | O_CLOEXEC | O_NOFOLLOW));
    return f->open_error ? f->open_error : 17;
}
static int mock_verify(void *context, int fd) {
    struct fake *f = context; f->verified++; CHECK(fd == 17);
    return f->verify_error;
}
static int mock_lock(void *context, int fd) {
    struct fake *f = context; f->locks++; CHECK(fd == 17);
    CHECK(f->verified == 1); return f->lock_error;
}
static int mock_close(void *context, int fd) {
    struct fake *f = context; f->closes++; CHECK(fd == 17);
    return f->close_error;
}
static int mock_ioctl(void *context, int fd, unsigned long request, void *data) {
    struct fake *f = context; CHECK(fd == 17); CHECK(f->locks == 1);
    if (request == SPI_IOC_MESSAGE(1)) {
        f->transfers++;
        const struct spi_ioc_transfer *transfer = data;
        CHECK(transfer->len == CNC1_FRAME);
        CHECK(transfer->bits_per_word == 8 && transfer->cs_change == 0);
        CHECK(transfer->delay_usecs == 0 && transfer->tx_nbits == 0 && transfer->rx_nbits == 0);
        CHECK(transfer->speed_hz == (f->readback_override == 5 ? 500000u : f->written_speed));
        CHECK(!memcmp((void *)(uintptr_t)transfer->tx_buf, f->expected_tx, CNC1_FRAME));
        /* Write even on failure: caller must never expose partial/stale data. */
        memset((void *)(uintptr_t)transfer->rx_buf, 0xa5, CNC1_FRAME);
        return f->return_bytes;
    }
    f->config_calls++;
    if (f->config_calls == f->fail_config_call) return -EIO;
    const unsigned long expected[] = {
        SPI_IOC_WR_MODE32, SPI_IOC_WR_BITS_PER_WORD, SPI_IOC_WR_LSB_FIRST,
        SPI_IOC_WR_MAX_SPEED_HZ, SPI_IOC_RD_MODE32, SPI_IOC_RD_BITS_PER_WORD,
        SPI_IOC_RD_LSB_FIRST, SPI_IOC_RD_MAX_SPEED_HZ
    };
    CHECK(f->config_calls <= 8 && request == expected[f->config_calls - 1]);
    if (request == SPI_IOC_WR_MODE32) CHECK(*(uint32_t *)data == SPI_MODE_0);
    if (request == SPI_IOC_WR_BITS_PER_WORD) CHECK(*(uint8_t *)data == 8);
    if (request == SPI_IOC_WR_LSB_FIRST) CHECK(*(uint8_t *)data == 0);
    if (request == SPI_IOC_WR_MAX_SPEED_HZ) f->written_speed = *(uint32_t *)data;
    if (request == SPI_IOC_RD_MODE32) *(uint32_t *)data = f->readback_override == 1 ? SPI_MODE_3 : SPI_MODE_0;
    if (request == SPI_IOC_RD_BITS_PER_WORD) *(uint8_t *)data = f->readback_override == 2 ? 16 : 8;
    if (request == SPI_IOC_RD_LSB_FIRST) *(uint8_t *)data = f->readback_override == 3 ? 1 : 0;
    if (request == SPI_IOC_RD_MAX_SPEED_HZ) {
        *(uint32_t *)data = f->readback_override == 4 ? f->written_speed + 1 :
                           f->readback_override == 5 ? 500000 :
                           f->readback_override == 6 ? 0 : f->written_speed;
    }
    return 0;
}
static struct cnc1_spidev_ops operations(struct fake *f) {
    const struct cnc1_spidev_ops ops = {f, mock_open, mock_verify, mock_lock, mock_ioctl, mock_close};
    return ops;
}
static void reset(struct fake *f, struct cnc1_spidev *port) {
    memset(f, 0, sizeof(*f)); f->return_bytes = CNC1_FRAME;
    for (unsigned i = 0; i < CNC1_FRAME; i++) f->expected_tx[i] = (uint8_t)i;
    cnc1_spidev_init(port);
}
static int open_fake(struct fake *f, struct cnc1_spidev *port) {
    const struct cnc1_spidev_config config = {"/dev/spidev2.1", 1000000};
    const struct cnc1_spidev_ops ops = operations(f);
    return cnc1_spidev_open_with_ops(port, &config, &ops);
}
static int uniform(const uint8_t *data, uint8_t expected) {
    for (unsigned i = 0; i < CNC1_FRAME; i++) if (data[i] != expected) return 0;
    return 1;
}
static void invalid_configuration(void) {
    const char *bad[] = {NULL, "", "/dev/spidev", "/dev/spidev2", "/dev/spidev.1",
        "/dev/spidev2.", "/dev/spidev-2.1", "/dev/spidev2.1/other", "../dev/spidev2.1",
        "/tmp/spidev2.1", "/dev/spidev2.1 ", "/dev/spidev2.1\n"};
    struct cnc1_spidev port; struct fake f; reset(&f, &port);
    struct cnc1_spidev_ops ops = operations(&f);
    struct cnc1_spidev_config config = {"/dev/spidev2.1", 1000000};
    for (unsigned i = 0; i < sizeof(bad)/sizeof(bad[0]); i++) {
        config.device_path = bad[i];
        CHECK(cnc1_spidev_open_with_ops(&port, &config, &ops) == -EINVAL);
    }
    config.device_path = "/dev/spidev2.1";
    char unterminated[64]; memset(unterminated, '1', sizeof(unterminated));
    memcpy(unterminated, "/dev/spidev", 11); config.device_path = unterminated;
    CHECK(cnc1_spidev_open_with_ops(&port, &config, &ops) == -EINVAL);
    config.device_path = "/dev/spidev2.1";
    config.speed_hz = 0; CHECK(cnc1_spidev_open_with_ops(&port, &config, &ops) == -EINVAL);
    config.speed_hz = CNC1_SPIDEV_LAB_MAX_HZ + 1;
    CHECK(cnc1_spidev_open_with_ops(&port, &config, &ops) == -EINVAL);
    config.speed_hz = 1000000;
    CHECK(cnc1_spidev_open_with_ops(NULL, &config, &ops) == -EINVAL);
    CHECK(cnc1_spidev_open_with_ops(&port, NULL, &ops) == -EINVAL);
    CHECK(cnc1_spidev_open_with_ops(&port, &config, NULL) == -EINVAL);
    ops.ioctl_device = NULL;
    CHECK(cnc1_spidev_open_with_ops(&port, &config, &ops) == -EINVAL);
    CHECK(f.opens == 0 && f.closes == 0);
    /* Exercise the real-wrapper entry without opening any path. */
    CHECK(cnc1_spidev_open(&port, NULL) == -EINVAL);
    puts("PASS configuration rejects before any device open");
}
static void setup_failures(void) {
    struct cnc1_spidev port; struct fake f;
    reset(&f, &port); f.open_error = -ENOENT;
    CHECK(open_fake(&f, &port) == -ENOENT && f.closes == 0 && port.fd == -1);
    reset(&f, &port); f.verify_error = -ENODEV;
    CHECK(open_fake(&f, &port) == -ENODEV && f.closes == 1 && !f.locks && port.fd == -1);
    reset(&f, &port); f.lock_error = -EWOULDBLOCK;
    CHECK(open_fake(&f, &port) == -EWOULDBLOCK && f.closes == 1 && !f.config_calls);
    for (int call = 1; call <= 8; call++) {
        reset(&f, &port); f.fail_config_call = call; f.close_error = -EINTR;
        CHECK(open_fake(&f, &port) == -EIO && f.closes == 1 && port.fd == -1);
        CHECK(cnc1_spidev_close(&port) == 0 && f.closes == 1);
    }
    const int mismatches[] = {1, 2, 3, 4, 6};
    for (unsigned i = 0; i < sizeof(mismatches)/sizeof(mismatches[0]); i++) {
        reset(&f, &port); f.readback_override = mismatches[i];
        CHECK(open_fake(&f, &port) == -EPROTO && f.closes == 1 && port.fd == -1);
    }
    puts("PASS device type/lock/configuration failures close exactly once");
}
static void transfer_success(void) {
    struct cnc1_spidev port; struct fake f; uint8_t receive[CNC1_FRAME];
    reset(&f, &port); CHECK(open_fake(&f, &port) == 0);
    CHECK(open_fake(&f, &port) == -EBUSY && f.opens == 1);
    struct cnc1_transport transport = cnc1_spidev_transport(&port);
    CHECK(transport.context == &port);
    CHECK(transport.exchange(transport.context, f.expected_tx, receive) == 0);
    CHECK(uniform(receive, 0xa5) && f.transfers == 1);
    memcpy(receive, f.expected_tx, sizeof(receive));
    CHECK(cnc1_spidev_exchange(&port, receive, receive) == 0 && uniform(receive, 0xa5));
    uint8_t overlap[CNC1_FRAME + 1]; memcpy(overlap, f.expected_tx, CNC1_FRAME);
    CHECK(cnc1_spidev_exchange(&port, overlap, overlap + 1) == 0 && uniform(overlap + 1, 0xa5));
    CHECK(cnc1_spidev_close(&port) == 0 && f.closes == 1);
    CHECK(cnc1_spidev_exchange(&port, f.expected_tx, receive) == -ENOTCONN);
    CHECK(uniform(receive, 0) && f.transfers == 3);
    memset(&f, 0, sizeof(f)); f.return_bytes = CNC1_FRAME;
    CHECK(open_fake(&f, &port) == 0 && !port.failed);
    CHECK(cnc1_spidev_exchange(&port, f.expected_tx, receive) == 0);
    CHECK(cnc1_spidev_close(&port) == 0 && f.closes == 1);
    reset(&f, &port); f.readback_override = 5;
    CHECK(open_fake(&f, &port) == 0 && port.configured_speed_hz == 500000);
    CHECK(cnc1_spidev_exchange(&port, f.expected_tx, receive) == 0);
    CHECK(cnc1_spidev_close(&port) == 0);
    puts("PASS single fixed full-duplex message and aliased buffers");
}
static void transfer_failures(void) {
    const int failures[] = {-EINTR, -EIO, -ENODEV, -ETIMEDOUT, 0, 63, 65};
    struct cnc1_spidev port; struct fake f; uint8_t receive[CNC1_FRAME];
    for (unsigned i = 0; i < sizeof(failures)/sizeof(failures[0]); i++) {
        reset(&f, &port); CHECK(open_fake(&f, &port) == 0);
        f.return_bytes = failures[i]; memset(receive, 0xff, sizeof(receive));
        CHECK(cnc1_spidev_exchange(&port, f.expected_tx, receive) == (failures[i] < 0 ? failures[i] : -EIO));
        CHECK(uniform(receive, 0) && f.transfers == 1 && port.failed);
        f.return_bytes = CNC1_FRAME;
        CHECK(cnc1_spidev_exchange(&port, f.expected_tx, receive) == -EPIPE && f.transfers == 1);
        CHECK(cnc1_spidev_close(&port) == 0 && f.closes == 1);
    }
    reset(&f, &port); CHECK(open_fake(&f, &port) == 0);
    CHECK(cnc1_spidev_exchange(&port, f.expected_tx, NULL) == -EINVAL && !f.transfers);
    CHECK(cnc1_spidev_exchange(&port, NULL, receive) == -EINVAL && !f.transfers && uniform(receive, 0));
    CHECK(cnc1_spidev_exchange(NULL, f.expected_tx, receive) == -EINVAL && uniform(receive, 0));
    f.close_error = -EINTR;
    CHECK(cnc1_spidev_close(&port) == -EINTR && f.closes == 1);
    CHECK(cnc1_spidev_close(&port) == 0 && f.closes == 1);
    puts("PASS partial/error results clear feedback, latch failure and never replay");
}
int main(void) {
    invalid_configuration(); setup_failures(); transfer_success(); transfer_failures();
    printf("PASS %u assertions; all device operations mocked; no physical SPI opened\n", checks);
    return 0;
}
