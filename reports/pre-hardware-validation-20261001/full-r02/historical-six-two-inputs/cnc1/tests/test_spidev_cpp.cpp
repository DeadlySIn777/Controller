#include "spidev_transport.h"
/* Link the actual C object through its public C++ header; no device is opened. */
int main() {
    cnc1_spidev port;
    cnc1_spidev_init(&port);
    auto transport = cnc1_spidev_transport(&port);
    return transport.context != &port || cnc1_spidev_close(&port);
}
