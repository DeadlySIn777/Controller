# Independent publication audit follow-up — 18 October 2026

Scope: focused checks against Git objects at **945fb7179d0fade3c28eabd96b7bf0c2dca9a6b9**, followed by a small source-only publication supplement. This does not rerun the independent 126,703-entry classifier, native KiCad, host/target builds, HDL simulation or physical qualification. The supplied v-file references and ephemeral per-entry sandbox are not accessible local audit inputs here; aggregate totals remain attributed to the independent audit.

## Findings traced

| Group | Focused result | Treatment |
| --- | --- | --- |
| Original root MANIFEST.json | Three root paths differ: README.md, .gitignore **and .gitattributes**. All three recorded hashes match original publication commit 121ac528. | At 945fb717 these are intentional publication replacements. Subsequent upstream commit ae4e6dd43 and tip b0670abb already refresh the board-review metadata bindings; all four current root/BOARD_REVIEW bindings checked there match. Preserve those upstream changes and the original record in Git history. |
| cnc1/evidence/manifest.json | 64 recorded entries checked against the audited Git tree: 60 match, 4 source hashes differ, 0 missing. | Explicitly known stale for current sources. No current-source CNC1 acceptance claim or re-stamp. |
| Prior-recorded-milestone manifest | 62 recorded entries checked: 12 match, 50 differ, 0 missing. | Historical revision record; root-relative names refer to its recorded source versions, not all current files. |
| F.Cu | Traced source_floor_SHA256/F.Cu in a receipt to producer lines 64–65: hashlib.sha256(sh.wkb), over a per-layer in-memory geometry union. | This example is a content/object hash keyed by a layer name, not a file named F.Cu. It does not establish a missing CAD layer export. Do not synthesize a file to satisfy a tolerant path parser. |
| startup.S and linker inputs | The previous readable-report extension filter omitted small assembly and linker source. A sample startup.S matches its retained 2d983a79… receipt hash exactly. | Upload 92 assembly files and 86 linker scripts, byte-for-byte, with a source-supplement manifest. |
| peer_cached_vpi.vpi / acquisition.vvp | Examined local generated artifacts match the cited retained receipt hashes, but are not source/CAD/readable records. | Keep generated executable/raw history local under the owner's explicit upload choice. Their absence still means those run closures cannot be fully rechecked from the clone alone. |

The F.Cu trace is a representative demonstrated classification correction, not proof that every missing-layer label in the independent classifier has the same schema. Other missing entries require their actual manifest pointer, base directory, source version and inclusion policy. Basenames or a 64-character string alone do not establish file identity.

## Evidence and publication rules

[focused-checks.json](focused-checks.json) records the focused conclusions. [cnc1-record-check.json](cnc1-record-check.json) lists every difference from the two CNC1 records. [source-supplement.json](source-supplement.json) lists the 178 exact supplemental source paths and hashes.

This follow-up changes no historical engineering receipt or existing capture manifest. The latest upstream board-review MANIFEST.json revisions are preserved. A fresh publication scope record does not turn known-stale engineering results into current-source passes. Sources must be revalidated with the relevant engineering toolchain before a new CNC1 evidence manifest can be recorded.

The publication remains **source/CAD/readable evidence with raw cache history local**. No complete build/run closure or CAD/manufacturing qualification is inferred from file hashes. Source inspection, host tests, target compilation, HDL simulation, FPGA mapping, circuit ERC, native board DRC/connectivity and physical measurement retain separate scopes.

## Concurrent publication updates

While preparing the supplement, GitHub advanced through additional board/router publications to b0670abb466af93e715ca175911a6fbb34e78702. This follow-up is applied on top of that commit, preserving every unrelated upstream path. FULL_SOURCE_MANIFEST.json and BROWSABLE_EVIDENCE_MANIFEST.json retain their 945fb717 capture bytes; use their capture revision rather than interpreting them as perpetual assertions about later root prose. PUBLICATION_SCOPE.json supplies the fresh metadata scope.
