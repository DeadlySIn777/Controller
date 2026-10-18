# Vendor FPGA qualification: BLOCKED — NOT FPGA PASS

4 October 2026. The exact current source and adopted Source26/CAD30 both select
**U1001 T20F256I4**, a soldered FBGA256 candidate with industrial temperature
designator I and speed grade4. Neither source is vendor-fitted. The historical
six/two synthesis discussion mentioning T20F256C4 is not a device selection for
this qualification. No board, routing, RTL, firmware, frontend or existing
configuration was changed.

The canonical [receipt](../../../WORKSPACE_REFERENCES.md#artifact-a4647e6795e8caa4) is BLOCKED. Efinity synthesis, placement,
routing and static timing were **not executed**. No bitstream or placeholder
Efinity project/constraint file was generated. No license content was read,
hashed, printed or sent to a vendor.

## Installed-tool evidence

[Preflight r03](../../../WORKSPACE_REFERENCES.md#artifact-a5b25285128f24fb) completed with all15 inspected source
hashes unchanged. Discovery checked Windows PATH, HKLM/HKCU uninstall registry,
and bounded directory names under `C:\`, the current user profile, Program Files,
Program Files(x86) and LocalAppData through depth2. The
[Windows inventory](../../../WORKSPACE_REFERENCES.md#artifact-731ec89c8390a298) records its exact roots,
errors and limits. No matching vendor executable, registered package or vendor
installation directory was found. Permission-denied directories and unrelated
portable-install locations are not claimed to have been exhaustively searched.

[GarciaMechBuilder inventory](../../../WORKSPACE_REFERENCES.md#artifact-d400d175c086e670) checked PATH and
directory names under `/opt`, `/usr/local`, `/home` and `/root` through depth5.
It found existing Yosys Efinix netlist artifacts, no Efinity installation
directory or command. The Docker Desktop distro was listed, not searched as a
vendor build environment. Vendor/license environment **names only** were
inspected; none were set on these two execution surfaces. License availability
and validation remain **not demonstrated**, rather than an assertion that no
license exists anywhere. The existing isolated Debian lab provides actual
Yosys0.52, ABC and Efinix mapping models; their binary/model hashes are recorded.

## Grounded pin and clock evidence

The [current source ledger](../../../WORKSPACE_REFERENCES.md#artifact-73443cf413414638)
and [adopted source ledger](../../../WORKSPACE_REFERENCES.md#artifact-cbd04208f284daca)
bind the native U1001 netlist and official workbook-derived ball data. All256
native balls are accounted for. Of195 GPIO,147 are wired:135 user functions,
including the clock, plus12 reserved configuration GPIO.48 GPIO are unconnected.
The JSON design dictionary omits20 unused LVDS GPIO and REF_RES; these21 balls
are explicitly unconnected in the full native netlist. This is not a missing
pad or a permission to reuse a reserved pin. Both source ledgers assign the same
FPGA functions.

All14 VCCIO supply pads are assigned nominal `IO_3V3`. The source supports all12
STEP/DIR/enable/alarm groups, four ABZ inputs, four IOL1 SPI lanes and other
IS2 functions. The ledger records their exact balls, bank names, configuration
roles, LVDS aliases and native nets. These are **source observations**. No
Interface Designer legality check, pad defaults, drive/slew qualification or
board electrical measurement has been performed.

`FPGA_CLK_50M` is U1001 H3 / GPIOL_24_CLK0 / BANK1B, clock regionL1. Native source
connects Y1001 `ASE-50.000MHZ-L-C-T` through R1001 33R. The nominal design period
is20ns. The retained ASE primary sheet identifies L as−40..85°C and C as±50ppm;
that does not measure clock accuracy, board loading, jitter or timing margin.
No applied SDC was found. `CORE_HZ=50MHz` and a mapped GBUFCE are not static
timing closure.

The [project-artifact search](../../../WORKSPACE_REFERENCES.md#artifact-e5b1eba4d40348d8) searched
gateware/hardware/reports/tools for SDC/XDC/QSF, peripheral/pad XML, vendor
project names, and Efinity project XML headers. It found no recognized vendor
project or applied timing/pin constraint artifact. KiCad netlist XML is not an
Efinity project.

## Executed family screens and their limits

Fresh [current structural CNC3 mapping](../../../WORKSPACE_REFERENCES.md#artifact-cafdc4f979a25ace)
passes checked synthesis, hierarchy/driver checks and mapped latch exclusion:
7,020 EFX_LUT4,2,882 EFX_ADD,5,889 EFX_FF and one EFX_GBUFCE. The five current
RTL inputs stayed unchanged. It exposes25 ports with4,287 bit positions,
including wide internal feedback/status/request buses; it is not a physical
motherboard wrapper. It does not implement stateful session permission,
twelve-channel motion providers or the complete IS2 profile.

The separately executed [current IOL1 bringup](../../../WORKSPACE_REFERENCES.md#artifact-c2a5999b39bd37bd)
maps7,936 LUT4,2,840 ADD,5,512 FF and one GBUFCE. Its scope is the historical
six-motion/two-encoder boundary plus four read-only diagnostic IOL1 lanes. It
does not complete twelve-axis IS2. The older report-local twelve-motion/record
arithmetic candidate and separate CAP3 candidate remain unadopted and omit
full identity/provider/output/analog authority integration. No primitive sum
or percentage is used to promote any candidate to device fit.

## Exact work needed to unblock

1. Make a real Efinity installation with T20 support and its patch/version
   identity available. Activate/validate its entitlement locally without
   recording license secrets. The published
   [installation guide](https://www.efinixinc.com/support/docsdl.php?pn=UG-EFN-INSTALL&s=ef)
   documents supported Windows/WSL environments; no installer or account change
   was attempted here.
2. Adopt one complete source-bound IS2 CNC3 motherboard wrapper that consumes
   internal buses and implements the actual required providers. Select
   T20F256I4 explicitly, without changing ABI/rate limits or creating fake
   integrated-region presence. Bind exact source, parameters and all pad nets
   to the real Interface Designer project.
3. Verify bank voltages, reserved/configuration pins, single-ended use of LVDS
   pads, output polarity/defaults and clock/GBUF legality. Complete grounded
   SDC: primary clock and worst-case clock uncertainty, external SPI input and
   output delays, generated clocks if present, reset recovery/removal and
   synchronizer/CDC constraints. Record path-specific justified exceptions;
   broad false paths must not hide acquisition or inhibit obligations.
4. Execute the documented interface/map/pnr and `sta_tclsh` stages on that exact
   project and installation; preserve reports, constraints, source/tool hashes
   and logs. The
   [official CLI guide](https://www.efinixinc.com/support/docsdl.php?pn=UG-EFN-CLI&s=ef)
   distinguishes these stages from programming. Inspect routed setup/hold and
   recovery/removal, rejected/ignored constraints, unconstrained endpoints,
   resource/IO warnings and placement/routing completion. The
   [timing guide](https://www.efinixinc.com/support/docsdl.php?pn=UG-EFN-TIMING&s=ef)
   explains SDC and timing review. Successful process exit alone is insufficient.

Those outputs can support FPGA PASS only for the included complete target and
constraints. Target execution, physical SPI/clock/inhibit/pulse measurements,
power-fail defaults, board routing/DRC and full-load commissioning remain
separate gates. Source26/ROOT104/CAD30 remains the adopted board; Claude owns
new routing.
