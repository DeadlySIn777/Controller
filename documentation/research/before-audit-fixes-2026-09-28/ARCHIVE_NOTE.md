# Archive: firmware-sources record before audit fixes (2026-09-28)

`firmware-sources.json` here is the record as it stood before the 2026-09-28 audit fix
R1-080. Its build status ("success"), distro ("Alpine 3.24.2") and compiler ("GCC 15.2.0")
were literals written by `record_firmware_sources.py`, not values derived from the build.
The current `research/firmware-sources.json` was regenerated after the build helper was
changed to query the compiler/distro at run time, end each log with `EXIT: <code>` and
write `build-record.json`, and after the audit was rerun against the rebuilt executables
(run identity: build recorded 2026-09-28T19:06:41Z, WSL2 GarciaMechBuilder,
gcc (Alpine 15.2.0) 15.2.0). `grblhal-build-local/` holds the previous build logs,
`build_info.h`, audit `results.json` and `previous-binaries.sha256` (the executables
themselves stay in ignored `research/vendor-src/`). The previous grblHAL_validator
executable is byte-identical to the rebuilt one; grblHAL_sim differs only because its
embedded build-info strings now carry the queried compiler/distro. Pinned upstream
commits and all 17 test outcomes are unchanged. Kept for provenance; do not edit.
