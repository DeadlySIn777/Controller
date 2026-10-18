#define _GNU_SOURCE
#include "spidev_transport.h"
#include <errno.h>
#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <string.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>

static int linux_open(void *unused, const char *path, int flags) {
    (void)unused;
    int result = open(path, flags);
    return result < 0 ? -errno : result;
}
static int linux_character(void *unused, int fd) {
    (void)unused;
    struct stat status;
    if (fstat(fd, &status) < 0) return -errno;
    return S_ISCHR(status.st_mode) ? 0 : -ENODEV;
}
static int linux_lock(void *unused, int fd) {
    (void)unused;
    return flock(fd, LOCK_EX | LOCK_NB) < 0 ? -errno : 0;
}
static int linux_ioctl(void *unused, int fd, unsigned long request, void *data) {
    (void)unused;
    int result = ioctl(fd, request, data);
    return result < 0 ? -errno : result;
}
static int linux_close(void *unused, int fd) {
    (void)unused;
    /* Do not retry close on EINTR: on Linux fd reuse could close another file. */
    return close(fd) < 0 ? -errno : 0;
}

void cnc1_spidev_init(struct cnc1_spidev *port) {
    if (!port) return;
    memset(port, 0, sizeof(*port));
    port->tag = CNC1_SPIDEV_CONTEXT_TAG;
    port->fd = -1;
}

static int valid_path(const char *path) {
    if (!path) return 0;
    size_t length = strnlen(path, 64);
    if (length >= 64 || strncmp(path, "/dev/spidev", 11)) return 0;
    const char *cursor = path + 11;
    if (*cursor < '0' || *cursor > '9') return 0;
    while (*cursor >= '0' && *cursor <= '9') cursor++;
    if (*cursor++ != '.' || *cursor < '0' || *cursor > '9') return 0;
    while (*cursor >= '0' && *cursor <= '9') cursor++;
    return !*cursor;
}

int cnc1_spidev_close(struct cnc1_spidev *port) {
    if (!port || port->tag != CNC1_SPIDEV_CONTEXT_TAG) return -EINVAL;
    if (port->fd < 0) return 0;
    int fd = port->fd;
    port->fd = -1;
    port->failed = 1;
    port->configured_speed_hz = 0;
    return port->ops.close_device(port->ops.context, fd);
}

static int configure(struct cnc1_spidev *port, unsigned long request, void *data) {
    int result = port->ops.ioctl_device(port->ops.context, port->fd, request, data);
    return result <= 0 ? result : -EIO;
}

int cnc1_spidev_open_with_ops(struct cnc1_spidev *port,
                            const struct cnc1_spidev_config *config,
                            const struct cnc1_spidev_ops *ops) {
    if (!port || port->tag != CNC1_SPIDEV_CONTEXT_TAG) return -EINVAL;
    if (port->fd >= 0) return -EBUSY;
    if (!config || !valid_path(config->device_path) || !config->speed_hz ||
        config->speed_hz > CNC1_SPIDEV_LAB_MAX_HZ || !ops ||
        !ops->open_device || !ops->verify_character_device || !ops->lock_device ||
        !ops->ioctl_device || !ops->close_device) return -EINVAL;
    port->ops = *ops;
    port->failed = 1;
    port->configured_speed_hz = 0;
    int result = port->ops.open_device(port->ops.context, config->device_path,
                                      O_RDWR | O_CLOEXEC | O_NOFOLLOW);
    if (result < 0) return result;
    port->fd = result;
    result = port->ops.verify_character_device(port->ops.context, port->fd);
    if (result) goto failed;
    result = port->ops.lock_device(port->ops.context, port->fd);
    if (result) goto failed;
    uint32_t mode = SPI_MODE_0, speed = config->speed_hz;
    uint8_t bits = 8, lsb = 0;
#define CONFIG(request, value) do { result = configure(port, request, &(value)); if (result) goto failed; } while (0)
    CONFIG(SPI_IOC_WR_MODE32, mode);
    CONFIG(SPI_IOC_WR_BITS_PER_WORD, bits);
    CONFIG(SPI_IOC_WR_LSB_FIRST, lsb);
    CONFIG(SPI_IOC_WR_MAX_SPEED_HZ, speed);
    CONFIG(SPI_IOC_RD_MODE32, mode);
    CONFIG(SPI_IOC_RD_BITS_PER_WORD, bits);
    CONFIG(SPI_IOC_RD_LSB_FIRST, lsb);
    CONFIG(SPI_IOC_RD_MAX_SPEED_HZ, speed);
#undef CONFIG
    if (mode != SPI_MODE_0 || bits != 8 || lsb || !speed || speed > config->speed_hz) {
        result = -EPROTO;
        goto failed;
    }
    port->configured_speed_hz = speed;
    port->failed = 0;
    return 0;
failed:
    (void)cnc1_spidev_close(port);
    return result < 0 ? result : -EIO;
}

int cnc1_spidev_open(struct cnc1_spidev *port, const struct cnc1_spidev_config *config) {
    const struct cnc1_spidev_ops operations = {
        NULL, linux_open, linux_character, linux_lock, linux_ioctl, linux_close
    };
    return cnc1_spidev_open_with_ops(port, config, &operations);
}

int cnc1_spidev_exchange(void *context, const uint8_t tx[CNC1_FRAME],
                        uint8_t rx[CNC1_FRAME]) {
    struct cnc1_spidev *port = context;
    if (!rx) return -EINVAL;
    /* Copy first: identical/overlapping tx and rx buffers remain well-defined. */
    uint8_t outgoing[CNC1_FRAME], incoming[CNC1_FRAME] = {0};
    if (tx) memcpy(outgoing, tx, sizeof(outgoing));
    memset(rx, 0, CNC1_FRAME);
    if (!port || port->tag != CNC1_SPIDEV_CONTEXT_TAG || !tx) return -EINVAL;
    if (port->fd < 0) return -ENOTCONN;
    if (port->failed) return -EPIPE;
    struct spi_ioc_transfer transfer;
    memset(&transfer, 0, sizeof(transfer));
    transfer.tx_buf = (uintptr_t)outgoing;
    transfer.rx_buf = (uintptr_t)incoming;
    transfer.len = CNC1_FRAME;
    transfer.speed_hz = port->configured_speed_hz;
    transfer.bits_per_word = 8;
    /* One message/one transfer: full duplex, no split write/read or mid-frame CS. */
    int result = port->ops.ioctl_device(port->ops.context, port->fd,
                                       SPI_IOC_MESSAGE(1), &transfer);
    if (result != CNC1_FRAME) {
        port->failed = 1;
        /* EINTR may mean a command was transmitted. Never replay it here. */
        return result < 0 ? result : -EIO;
    }
    memcpy(rx, incoming, CNC1_FRAME);
    return 0;
}

struct cnc1_transport cnc1_spidev_transport(struct cnc1_spidev *port) {
    const struct cnc1_transport transport = {port, cnc1_spidev_exchange};
    return transport;
}
