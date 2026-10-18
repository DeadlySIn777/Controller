"""Encode diagnostic observations for the ESP helper; opens no serial/network port."""
import struct
import zlib


def encode_health(*, boot_id, sequence, completed_cycle_counter, uptime_ms,
                  reported_disarmed, reported_fault):
    """completed_cycle_counter must represent backend progress, never UI polling.

    Pass zero until a real backend progress source exists. This message grants
    no motion, reset, recovery or machine-enable authority, even with valid CRC.
    """
    for name, value, upper, lower in (
        ('boot_id', boot_id, 2**64-1, 1), ('sequence', sequence, 2**32-1, 0),
        ('completed_cycle_counter', completed_cycle_counter, 2**32-1, 0),
        ('uptime_ms', uptime_ms, 2**64-1, 0),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f'{name} outside integer range')
    if type(reported_disarmed) is not bool or type(reported_fault) is not bool:
        raise ValueError('reported flags must be Boolean')
    flags = int(reported_disarmed) | (int(reported_fault) << 1)
    prefix = struct.pack('<4sBBHQIIQI', b'ESV1', 1, 1, 28, boot_id,
                         sequence, completed_cycle_counter, uptime_ms, flags)
    return prefix + struct.pack('<I', zlib.crc32(prefix))
