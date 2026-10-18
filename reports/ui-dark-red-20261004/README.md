# Dark/red UI and setup interaction polish

4 October 2026. Applied the user's dark/red preference to all five setup/diagnostic views. Charcoal surfaces, dark native controls, red selection/actions and visible focus replace the light/teal appearance. Labelled amber warnings, saved/coverage indicators and fault evidence keep separate meanings. The preference is recorded in project memory.

The independent review also found and fixed keyboard focus loss, inaccessible profile selection state and incomplete validation presentation. Profiles now expose their selected state; page navigation focuses its heading; requests expose busy state; action/unit rerenders preserve focus. Drive details shows an expandable complete list linked to the corresponding fields, including closed advanced controls. Unsaved edits immediately discard outdated validation marks; saved backend checks provide the field feedback. Scrolling respects reduced-motion preferences. The local-guide input matches the existing 2,000-character service limit.

## Verification

- [31 relevant host regressions](host-tests.json), [full log](host-tests.log): all pass, no skips/failures/errors; source unchanged throughout. These cover the existing shared service/CLI/HTTP setup and diagnostic contracts. JavaScript syntax check also passed.
- [Browser interaction checks](browser-verification.json): actual keyboard selection, focus restoration, unit conversion, timing rejection/error recovery, optional assignments and reviewed save in a separate authored twelve-motor workspace. No paid provider calls or hardware connection.
- [20 responsive view checks](responsive-checks.json): all five views at verified 390×844, 800×480, 1280×800 and 1920×1080 viewports. No horizontal page overflow; buttons/forms/disclosures are at least 44 CSS pixels high. These are pixel/layout measurements, not qualified physical touchscreen dimensions.
- [Palette contrast](palette-contrast.json): all nine defined text pairs exceed the internal 4.5:1 target; minimum is 5.39:1. Defined control edges pass the 3:1 target. This is a palette check, not a claim of complete accessibility certification or physical display performance.
- [Preservation](preservation.json): 40 backend/existing-preview files and all 6,826 original hardware/firmware/gateware/CNC1 files are unchanged. Existing setup, recorder history and allowance remain intact. Claude retains routing.

## Current screenshots

![Machine setup](screenshots/setup-dark-red-1280.jpg)

[Desktop diagnostics](screenshots/diagnostics-dark-red-1280.jpg) · [Mobile diagnostics](screenshots/diagnostics-dark-red-390.jpg).

The preview remains available at `http://127.0.0.1:8769/`. UI appearance and host/browser checks do not close real-machine commissioning, live telemetry, loaded target timing, physical touchscreen/environment checks or manufacturing gates. The earlier browser saved-download limitation was not retested in this styling pass; [the diagnostics report](../diagnostics-zstd-20261004/README.md) retains its exact status. No new safety or motion authority was added.
