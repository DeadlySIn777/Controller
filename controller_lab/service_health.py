"""Encode diagnostic observations for the ESP helper; opens no serial/network port."""
import struct
import zlib


def encode_health(*, boot_id, sequence, completed_cycle_counter, uptime_ms,
                  reported_disarmed, reported_fault):
    """completed_cycle_counter must represent backend progress, never UI polling.

    Pass zero until a real backend progress source exists. This message grants
    no motion, reset, recovery or machine-enable authority, even with valid CRC.

    Host cadence (documentation only; this function does not send or time
    anything). The ESP helper judges freshness in its own local processing time
    (when it parses a frame), with strict comparisons (age < deadline):

    - Send accepted frames well under 1000 ms apart (SH_LINK_TIMEOUT_MS for
      link_fresh); 4-10 Hz is recommended. An exact 1 Hz sender sits on the
      strict boundary and flaps between fresh and stale.
    - Frames showing a forward completed_cycle_counter change must be under
      500 ms apart (SH_PROGRESS_TIMEOUT_MS) for backend_progress_fresh. A
      heartbeat with an unchanged counter keeps only link_fresh.
    - The first frame of a new boot_id is only a baseline and never reports
      progress.

    These are advisory diagnostic deadlines, not machine limits, and are not
    qualified on hardware. See firmware/esp32_service/README.md.
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
