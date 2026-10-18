# IOL1 r0.4 powered-off buffer correction

The three quad buffers now use exact active Nexperia 74LVC125APW,118. The retained TI r0.3 source remains under before-r03 and the original frozen-inputs. TI Rev T has no IOFF specification; the previous family-based claim is withdrawn. Nexperia Rev12 explicitly specifies partial-power protection and ±20 µA maximum IOFF at VCC=0, VI or VO=5.5 V, −40…125°C.

All 100 physical footprints, 342 pads, directions, net names and TSSOP geometry remain unchanged. Primary pin table and package review match. Native XML passes; native ERC has zero errors/warnings and no ignored checks. Fresh 38 control, 43 operator, 36 output, 28 input and 24 motor tests pass (169 total), and the frozen input hashes are unchanged.

IOFF at zero supply does not establish all intermediate brownout behavior, loaded SPI timing or assembled recovery policy. Target firmware and physical qualification remain open; no fabrication release is made.
