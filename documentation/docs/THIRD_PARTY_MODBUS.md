# Third-party Modbus devices and replaceable adapters

**Documentation review: 18 October 2026.** Reconciled with [engineering status](../reports/ENGINEERING_STATUS.md) and the [17 October finishing evidence](../reports/board-finish-20261017/README.md). Use the [documentation index](README.md) for current contracts and historical records.

28 September 2026, updated 29 September 2026. Requirement from the [supplied note](../WORKSPACE_REFERENCES.md#artifact-4788c65340fa8938): support ordinary third-party USB/RS-485 adapters, Modbus RTU accessories and Modbus TCP devices. Customers may buy supported hardware from their preferred retailer, including Amazon. They should not need our proprietary VFD board merely to send commands to a compatible serial-controlled spindle drive. A complete tested kit may include a preferred adapter or accessory for convenience and support, but the commercial offer must publish tested alternatives and must not require customers to buy ordinary peripherals from us.

This is an integration plan. No physical adapter, VFD or relay module is qualified by the evidence cited here. The active one-motherboard architecture retains its required RS-485/CAN and full fitted motor/I/O scope; a retail adapter is an optional supported connection choice, not a replacement for required motherboard capabilities. A marketplace title, USB identity or working read transaction does not establish complete compatibility.

## Hardware and software approach

| Connection | Proposed use | Product work |
|---|---|---|
| Controller USB → supported RS-485 adapter → VFD | Run/direction/speed requests and supported status | Qualify exact adapter and VFD revision; profile and setup instructions; command ownership, freshness and communication-loss behavior |
| Onboard isolated RS-485 represented in the integrated motherboard source | Same intended functions without an external dongle | Reconcile exact transceiver/supply/protection/connector, fitted costs and software profile with current source; schematic representation is distinct from target execution and physical qualification |
| Separate RS-485 accessory bus | Relays, ordinary I/O, lubrication requests, lights and suitable measurements | Device-specific timing and startup/loss policies; prevent accessory retries from monopolizing the spindle link |
| Modbus TCP device or gateway | Supported network I/O or access to a documented downstream device | Explicit endpoint/device identity, timeouts and register map; gateway behavior must be qualified |

LinuxCNC 2.9 documents MB2HAL as a non-real-time HAL component with serial/TCP links and supported read/write transactions. It is a candidate implementation underneath generated configuration. Its maximum update-rate setting is a ceiling, not a deadline guarantee. We still need to implement the product's configuration and fault supervision. [LinuxCNC MB2HAL](https://linuxcnc.org/docs/2.9/html/drivers/mb2hal.html)

Use a device-specific driver where required. LinuxCNC's `hy_vfd` supports a defined Huanyang serial interface and documents drive-side selection of serial run/frequency control. That does not establish that every drive sold as Huanyang uses the same protocol or settings. [LinuxCNC hy_vfd](https://linuxcnc.org/docs/2.9/html/man/man1/hy_vfd.1.html)

Waveshare's Modbus RTU Relay (D), for example, has a published RS-485/register interface, eight relay channels and eight digital inputs. It is a documentation candidate, not a qualified accessory or a blanket approval of its loads/startup behavior. [Manufacturer interface documentation](https://www.waveshare.com/wiki/Modbus_RTU_Relay_%28D%29)

## Device profile contract

Extend the implemented [common configuration service/UI/CLI](SETUP_WORKBENCH.md) with a versioned Modbus device profile; live Modbus discovery and write supervision remain product integration work. The device profile must record:

- Exact manufacturer/model, hardware and firmware revision range, manual revision, profile author/version and qualification evidence. Keep verified profiles distinct from unqualified generic imports.
- Connection binding: persistent adapter serial identity where reliable, otherwise an explicitly assigned physical USB path; USB vendor/product identifiers alone cannot distinguish identical adapters. Never rely on the transient name `/dev/ttyUSB0` as the saved identity.
- Transport: RTU serial parameters and addressed device, or TCP endpoint/port/unit mapping and any gateway. Reserve controller ownership of each bus; conflicting masters or duplicate addresses require correction.
- Register map: zero-based protocol addresses versus manual notation, function codes, widths, signedness, word/byte order, scale, engineering units, valid ranges and read/write permissions.
- Meaning: requested speed, reported speed, drive ready, communication healthy and spindle-at-speed are separate values. Label observed versus inferred state and include timestamps/quality.
- Writes: explicit allowed setpoints, state transitions, prerequisites, limits, ownership, expiry and whether a command can be retried. Do not issue broadcast writes or arbitrary register scans during discovery.
- Timing: bounded queue length, polling budget, transaction timeouts, maximum acceptable sample age and expected device-local communication-loss response. Repeated unchanged values are not proof of a successful new transaction.
- Electrical/installation requirements: exact RS-485 terminal meanings, reference/shield treatment, isolation and power domains, termination/biasing instructions and load interface. Adapter isolation specifications need verification; optical-looking components in a listing are not evidence.
- Startup, unplug/replug, reboot and restore policy; tests for missing, incompatible and changed equipment. A replacement adapter requires explicit rebinding when identity is ambiguous.

Profile data must be declarative. Importing a profile cannot run scripts or silently issue writes. It can be previewed, validated, versioned and rolled back through the same CLI/API used by the touchscreen and assistant.

## Guided workflow

1. Detect a supported transport adapter; show that the downstream equipment remains unidentified.
2. Select the exact device profile and show the necessary wiring and device-keypad settings.
3. Bind address/port identity and perform only the profile's approved read-only connection test. If there is no unique model-identification register, retain the operator-confirmed model as such.
4. Present supported signals in machine language and propose assignments: main spindle, work light, coolant contactor request or lubrication request. Validate limits and duplicate ownership.
5. Apply the reviewed configuration while disarmed; discard previous queued commands. Test outputs only through a separate deliberate commissioning action with the required machine conditions.
6. Display communication age, device faults, command status and next diagnostic steps. Save a portable configuration with profile/manual references and the verified installation evidence.

Command names such as `device discover --read-only`, `device inspect`, `device test-read`, `profile validate` and `config diff/apply` are proposed additions to [cncctl](CONFIGURATION_AND_CLI.md), not available product commands today.

## Timing and fault boundary

Modbus belongs on the non-real-time side. Keep STEP/DIR generation, spindle-angle/index feedback, fast probe capture and plasma height-feedback timing on the FPGA or a qualified deterministic extension. A polled VFD speed estimate cannot replace angle/index capture for threading.

The machine's fault policy must work when the serial cable cannot carry a stop request. Qualify device-local timeout behavior and the independent hardware inhibition/stop arrangement appropriate to the machine. Ordinary relay outputs and an application watchdog are not a certified safety system. Some outputs may latch across power or communication changes; verify the exact device rather than assuming power-off means every contact is open.

On link loss, mark values invalid according to their age, cancel commands still queued at the controller and initiate the profile's defined response. Reject expired requests before dispatch. **An already-transmitted write may still execute:** ordinary Modbus devices need not support deadlines, epochs or cancellation. Treat a timed-out or interrupted write as execution-uncertain, suppress blind retries, and rely on the qualified device-local response and independent inhibition where required. A host-side queue rule cannot recall bytes already delivered to a drive or gateway.

Reconnection establishes a new controller command session, reads actual state and requires deliberate reauthorization before any run request. Do not replay remembered spindle, coolant or relay commands merely because the port returned. Restart/resume must distinguish the requested command, device acknowledgment and actual physical behavior; a readback alone cannot undo an action already performed.

## Acceptance work before advertising support

| Case | Evidence required |
|---|---|
| Known adapter and supported device | Read-only identification/setup, correct scaling, allowed writes only and matching feedback; record exact revisions |
| Wrong address/model/baud or duplicate binding | Actionable error without output activation; no guessed register writes |
| Conversion boundaries | Units, signed values, word order, limits and invalid/nonfinite values handled consistently |
| Link unplugged, device loses power, delayed replies | Freshness expires; stale unsent requests are rejected; in-flight writes remain execution-uncertain; no blind retry/replay; device timeout and independent machine response demonstrated |
| Adapter replacement, USB renumbering, service reboot | Correct device remains bound or requires explicit rebinding; no automatic run/output replay |
| Bus overload or failed accessory | Measured behavior satisfies each declared monitoring budget; spindle link not held behind unrelated accessory retries |
| Output startup/communication failure | Exact contact/drive states verified, including latching behavior and device-local timeout settings |
| UI/CLI/assistant parity | Same validation results, diffs, evidence requirements and command authority through each interface |

Start with a disconnected device emulator and generated configuration review. Qualify a small published compatibility list using named hardware later. Retain a documented generic-profile path for advanced users without labeling those installations verified.

The published compatibility list is part of the product boundary: it names exact adapter/device revisions, wiring, configuration, test evidence and restrictions. A customer-supplied item on that list follows the same profile and commissioning path as the kit item. An unlisted or changed item remains customer-qualified and does not inherit the tested support claim.
