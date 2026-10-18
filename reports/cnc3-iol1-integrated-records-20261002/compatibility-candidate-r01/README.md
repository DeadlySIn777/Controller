# Frozen diagnostic RTL × actual record/config target compatibility

This staged wrapper replays the exact diagnostic acquisition RTL against the actual r03 target protocol C. Blank records retain major0 and the existing read-only wire behavior. An actual signed developer-fixture MBR2 record is selected by the real target integrity/UID function and produces major1; the frozen major0 FPGA master must reject it. The fixture does not authenticate a real board or grant ACTIVE.

The record/config replay is also rerun freshly. The frozen FPGA diagnostic master still only sends SYNC/POLL; the separate record stage exercises CONFIG/IDENT. This aggregate does not imply combined CONFIG/IDENT support, real factory programming or MCU MMIO timing.
