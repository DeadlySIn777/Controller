Interface specification revision: IS-1

# 05 — Service contract: setup, validation, preview, export and updates

Section 05 of interface specification IS-1, added 29 September 2026 in the repair round so that the setup-and-repair and preview requirements (product direction C1–C3, C8, C9) are designed in the same way as the I/O and diagnostics requirements. Machine-readable companion: [`spec/service.json`](../../spec/service.json) (`"spec_revision": "IS-1"`), checked by `tools/interface_spec_validate.py`.

**Status.** This is an interface definition. The configuration and diagnostics service, the setup routes, the validator, the preview and the update machinery are **not implemented**. Nothing here is measured, released or ready for manufacture. The existing `controller_config` recovery commands in the repository remain the baseline this contract extends.

## 1. Principles

- One service contract behind the CLI, the configuration schema and the UI.
- The AI proposes; a deterministic validator decides. Nothing is applied without validation, a preview/diff and a reversible commit.
- Unknown information produces a specific **question**, never an invented setting. An AI answer to a question is a proposal and is validated like any other input.
- Every function in this section works offline, without internet and without AI credit. The expert editor and ordinary offline setup are always available; AI is never mandatory.
- Measured facts and diagnoses are separate record types (section 04 section 12.1).

## 2. `hw.modules`

One object per slot key (`psm`, `cmc`, `mc`, `mia`, `mx4`, `eia`, `ex8`, `dic`, `doa`, `dob`, `acc`, `esc`, `scart`, `xs`): presence, power-good, accepted, class (the `cnc1.module.<slot>.*` pins of section 01), the decoded MIR-1 record, temperature with validity and age, a compatibility verdict (`compatible`, `update_required`, `weaker_capability`, `unqualified`, `incompatible`, `unidentified`) and the list of checks required before re-enabling (section 02 section 13, filtered by the active configuration).

## 3. Two equally usable setup routes

| Route | Input | Steps | Output |
|---|---|---|---|
| CAD | Assembly with kinematic joints (STEP AP242 with kinematic constraints and URDF first; others listed per release) | Import; identify moving groups (rigid bodies joined by prismatic or revolute joints); propose an axis assignment per group; wire and verify the reference channels; confirm orientation by a low-speed jog per axis (gantry groups together); verify travel by homing and a soft-limit check | Machine profile + moving model |
| No CAD | Layout choice (gantry router XYYZ, fixed-gantry mill, knee mill, lathe XZ, plasma table XYYZ, five-axis trunnion XYZAC, twelve-motor multi-head) and a few dimensions (travel per axis, gantry width, Z clearance, table size, rotary centre offsets, tool length reference) | Generate a simplified moving model (boxes and cylinders), then the same verification steps | Same machine profile and moving-group records |

A moving group records: id, parts, joint type, direction, travel, proposed axis, proposed channels, a confidence and the model features it came from (evidence). Both routes end in the same profile, validator and verification steps.

## 4. Device profiles and the question rule

Drive, sensor, spindle and output-device profiles list their required fields in `service.json` (for a drive: enable behaviour, voltage and current, isolation; step rate and timing; alarm type and normal state; enable settle time; cable loop resistance for NC-5V wiring; the independent stop path of exception E1; and the evidence document). A verified profile generates the terminal-by-terminal wiring list and the configuration together, from `spec/terminals.json` and the allocation rules. Any required field without a verified value becomes a question object (subject, field, why it is needed, options, the actions it blocks), and the profile stays unverified and cannot be applied.

## 5. Validator rules

Every rule below runs before anything is applied; any failure blocks the change. Rule texts are in `service.json`.

| Group | Rules |
|---|---|
| Electrical | V-EL-01 enable wiring mode; V-EL-02 NC-5V loop resistance and independent stop path; V-EL-03 alarm polarity; V-EL-04 DO continuous and bank limits; V-EL-05 output fault states; V-EL-06 DO peak above 0.62 A needs a relay; V-EL-07 sourcing terminal limits; V-EL-08 no bus-only spindle run path; V-EL-09 XS1.3 scope; V-EL-10 PWM off at low; V-EL-11 AO safe at 0 V; V-EL-12 reset/arm mode; V-EL-13 contactor/STO feedback; V-EL-14 plasma rules |
| Channel allocation | V-CH-01 no double use; V-CH-02 expansion identified; V-CH-03 pendant label; V-CH-04 one writer per HAL pin; V-CH-05 one feedback source per joint; V-CH-06 gantry homing; V-CH-07 joint-indexed unhome, indexers as extra joints; V-CH-08 one probe-input writer |
| Motion limits | V-ML-01 step rate; V-ML-02 step timing and enable settle; V-ML-03 velocity and acceleration; V-ML-04 soft limits; V-ML-05 following-error limits |
| Timing | V-TM-01 DI/AI stale limits 250–440 µs; V-TM-02 per-source stale limits |

The allocation-level rules (V-CH-01 to V-CH-08, V-EL-04, V-EL-06, V-EL-08, V-EL-09, V-TM-01, V-TM-02) are already enforced on the six IS-1 allocation sheets by `tools/interface_spec_validate.py`; `service.json` `spec_validator_coverage` names the check function for each.

Apply flow: propose → validate → preview and diff → commit as a new generation (write, verify, switch pointer; the previous generation stays) → required checks before re-enabling → rollback on request or on a failed check.

## 6. Preview data contract

| Field | Source | Label rule |
|---|---|---|
| Commanded position | `joint.J.pos-cmd` and the axis commanded positions | Always labelled "commanded" |
| Measured position | `cnc1.encoder.K.position` for joints whose allocation lists an encoder | A joint without feedback is labelled "commanded position (no feedback)" |
| Disagreement | measured − commanded per joint | Warn above 0.5 × the joint's FERROR, alarm colour above 1.0 × FERROR (LinuxCNC itself faults there) |
| Feedback state | `cnc1.encoder.K.valid`, `cnc1.feedback-valid`, value age | Invalid, or older than 3 ms (3 servo periods), is drawn as stale, never as a position |
| Homed | `halui.joint.J.is-homed` | Unhomed joints marked |
| Travel limits | INI `[JOINT_J]` MIN/MAX_LIMIT and limit-switch states | Working envelope drawn |
| Active tool | `halui.tool.number` and the tool table | Tool geometry from the table |
| Work offset | LinuxCNC status `g5x_index`, `g5x_offset` | Active offset named |

Clearance warnings are computed only between components that are modeled and registered in the machine model. The preview never claims to prevent collisions. The disagreement display is also how an open or shorted encoder line shows up, since IS-1 has no electrical line-fault detection (section 04 section 13).

## 7. Export, import and updates

- **Export:** machine bundle v1, a tar archive with `manifest.json` first (format, version, spec revision, creation time, controller serial, path/sha256/size of every file) and the machine profile, device profiles, terminal allocation, calibration and commissioning records, preview model and the generated INI/HAL (informational; regenerated on import). **Import:** verify the hashes, validate, preview and diff, commit as a new generation, run the required checks.
- **Update states and power loss:**

| Item | States | Power removed at any state |
|---|---|---|
| Host image (A/B) | IDLE, DOWNLOADED, VERIFIED, STAGED, TRIAL_BOOT, COMMITTED, ROLLED_BACK | Boots the last committed slot; a failed trial boot falls back |
| Card firmware | IDLE, BOOTLOADER, ERASING, WRITING, VERIFYING, COMMITTED | Card restarts in its bootloader with outputs off; the service resumes from the local package (section 01 section 4.8) |
| Gateware | IDLE, CRESET_HELD, WRITING, VERIFYING, COMMITTED | CDONE low keeps every permission off; the host restores the flash again |
| ESP firmware | IDLE, WRITING_OTA, VERIFYING, COMMITTED, ROLLED_BACK | Previous OTA slot boots |
| Configuration | COMMITTED_N, WRITING_N+1, VERIFYING_N+1, COMMITTED_N+1 | A torn write leaves generation N active |

## 8. Offline operation and tests

Ordinary operation, local diagnostics and the history ring, saved previews, configuration recovery and export, module replacement and re-verification, and setup on both routes work with no network and no AI credit. Required tests: every update type interrupted by power removal at every state; setup, repair and export with network and AI removed; adversarial proposals (over-rating, double allocation, stale proposal) refused; a profile with a missing field yields a question. The usability target (8 of 10 first-time users reach a verified low-speed jog within 15 minutes on an already-wired reference machine) stays in the master document, section 11, row C4.

## 9. Blockers

The service is software and can be written and tested on the host without hardware. The usability study, the timed replacement and the end-to-end demonstration need the prototype set and a reference machine (master document section 12).

---

Interface specification revision IS-1. Nothing in this section is implemented, measured or ready for release.
