# Independent native routing-connectivity review

30 September 2026. Read-only verification of the 203-part revision-05 placement, selected-routing copy and published revision-06 route candidate. [The retained receipt](review.json) captures ten unchanged/copied inputs, six version-pinned primary KiCad source files, exact pad/copper geometry, per-net physical clusters, negative controls and a fresh native DRC report. The original and published PCB/project files were not modified.

## Why both DRC reports showed 499

KiCad **10.0.4** hardcodes a maximum of **499 reported unconnected-item violations**. Its DRC engine assigns this category limit at each run; the connectivity provider stops emitting entries when it is exhausted. The limit also applies to clearance violations. This explains why a baseline connection can be absent from the truncated list and why adding actual copper can leave the reported count unchanged. `--all-track-errors` affects track reporting; it does not override this limit. No cap override exists in the inspected CLI help/current source. [KiCad DRC engine](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.4/pcbnew/drc/drc_engine.cpp), [connectivity provider](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.4/pcbnew/drc/drc_test_provider_connectivity.cpp).

The suitable measurement is the native connectivity engine's uncapped `GetUnconnectedCount(False)`, after `BuildConnectivity()`. It counts all missing ratsnest edges, including hidden edges; it is not a count of disconnected pads. Per-pad copper clusters separately establish whether a specific path is physically joined. [KiCad connectivity implementation](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.4/pcbnew/connectivity/connectivity_data.cpp).

| Inspected board | Footprints / pads | Track/via items | Uncapped missing ratsnest edges |
|---|---:|---:|---:|
| Published revision 05 placement | 203 / 867 | 0 | **569** |
| Selected-routing copy | 203 / 867 | 272 | **518** |
| Published revision 06, selected +power routing | 203 / 867 | 296 | **508** |

Selected routing therefore closed **51 actual copper joins**; the ten power connections then closed ten more. All three pad geometry/net inventories match exactly. This includes position, dimensions, drill, orientation, shape, pad attributes and copper-layer masks, not merely component counts. Snapshot board hashes are in the receipt.

## Physical path verification

The 41 selected nets originally required 62 pad-cluster joins. The routed copy and published revision 06 have **30 fully connected selected nets** and **11 selected nets with one remaining join each**. Their counts and each actual source-pad cluster are stored in the receipt. No imported copper cluster lacks a source pad. No claim is made that all 41 nets are finished.

Verification uses native `GetConnectedItems(source_pad)`, which returns the source pad's geometric copper cluster. It does **not** use `GetNetItems`, which would merely collect unrelated items sharing a net assignment. A net is complete only if every intended source pad belongs to the same physical cluster. The API checks the actual pad/trace/via copper geometry and layers. [KiCad native cluster search](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.4/pcbnew/connectivity/connectivity_data.cpp).

`BASE_FIRST` provides a concrete check: U4001 pin 4 at **(152.1375, 49.9500) mm** reaches U4002 pin 1 at **(159.3625, 48.0500) mm** through three F.Cu segments. On the no-copper baseline it does not reach that destination, even though both pads already share the net name. Two unsaved in-memory negative controls retain net assignments but break the copper:

- Moving those three joining segments 20 mm causes the native path check to fail and changes the missing-edge count from 518 to **519**.
- Moving only the diagonal segment to B.Cu, without transition vias, causes the path check to fail and changes the count to **520**.

Both controls were applied only to temporary in-memory boards; neither mutated board was saved. The original and retained-copy hashes remain intact. These controls show that the path check detects geometry and layer breaks rather than accepting matching net membership.

## Remaining selected joins on revision 06

The following are the closest **real pad centers** between each pair of disconnected clusters. They identify intended joins; they are not clearance-approved route centerlines. The receipt also records all pads in each cluster and the existing imported trace geometry.

| Net | From pad and coordinate, mm | To pad and coordinate, mm |
|---|---|---|
| WD_M_OK | U3005.6 (206.1375, 21.0500) | R3009.1 (174.1750, 34.0000) |
| WD_M_SET1_BUF | R3011.1 (156.1750, 39.0000) | U4017.2 (168.6000, 70.7500) |
| WD_O_OK | R3010.1 (187.1750, 15.0000) | U4004.3 (178.3625, 49.9500) |
| WD_O_SET1_BUF | U3007.4 (183.8375, 34.6500) | U3002.5 (185.4000, 21.9750) |
| ARM_O_Q | U4006.5 (199.9000, 49.7500) | U4008.1 (149.8625, 59.0500) |
| PERMIT_OUT_DRIVE | U4009.3 (159.1000, 60.2500) | R4018.1 (205.1750, 82.0000) |
| PERMIT_OUT_REQ | U4009.6 (161.9000, 60.2500) | R4007.1 (191.1750, 78.0000) |
| TAMPER_CLEAR_N | R4012.1 (163.1750, 82.0000) | U4002.6 (161.6375, 48.0500) |
| WD_M_TRIP_CLEAR_N | U4019.7 (190.4000, 70.7500) | U4014.6 (209.4000, 60.2500) |
| WD_M_TRIP_Q | U4017.1 (168.6000, 70.2500) | U4014.5 (209.4000, 60.7500) |
| WD_M_HEALTH_RAW | R3001.2 (163.0000, 20.1750) | U3001.8 (159.4000, 20.0250) |

In particular, WD_M_OK still isolates its buffer output; WD_M_SET1_BUF isolates the sticky-trip OR input; WD_O_SET1_BUF isolates timer SET1; and WD_M_HEALTH_RAW separates the wired-AND timer health outputs from the pull-up/buffer. Those are real unfinished circuit paths, not merely reporting artifacts.

## Fresh DRC and limits

The fresh native DRC on a retained revision-06 copy reports **499 unconnected items**, **ten library-context warnings**, and no other reported violation categories. The copy deliberately lacks the published directory's complete custom-library context; those warnings do not establish ten copper defects. The separate uncapped result is **508**, so the unconnected report remains censored. Full-card routing is unfinished; source component fit, electrical loading, full FPGA connectivity/timing, all rail/ground planes and physical qualification remain separate gates. This receipt is native geometric connectivity evidence, not a full-board DRC pass or manufacturing release.

Reproduction: run the retained `analyze.py` with KiCad's bundled Python against the declared immutable inputs; it refuses to overwrite an existing completed receipt. Use a separately named review directory for any later board revision. Source hashes and version-tagged primary files make the observation reproducible without changing preferences, disabling checks or editing the published PCB.
