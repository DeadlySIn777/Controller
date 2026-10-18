# Audit record, 28 September 2026

| File | Contents | Evidence class |
|---|---|---|
| [AUDIT_REPORT.md](AUDIT_REPORT.md) | Scope, method, headline counts, fixes by subsystem, regenerated evidence, open items and PCBWay readiness (not ready) | summary of the records below |
| [findings-ledger.json](findings-ledger.json) | 154 confirmed findings (including the seven repair-review issues) with outcome and fix/evidence location; 51 rejected candidates with reasons | source inspection plus the checks named per entry |
| [ELECTRICAL_HANDOFF.md](ELECTRICAL_HANDOFF.md) | Open electrical/hardware items, re-checked against the live hardware files at 2026-09-28T21:25Z | source inspection and datasheet desk work |
| [part-selections.json](part-selections.json) | Candidate exact MPNs from desk research for ledger rows marked `required_unselected` | datasheet and manufacturer/distributor page inspection only |
| [python-tests.txt](python-tests.txt) | Raw output of `python -m unittest discover -s tests -v` (579 tests, OK, 5 skipped) | host tests; working-tree observation |

`part-selections.json` is **not integrated** into `hardware/electrical-design.json`. Selecting an MPN does not qualify a circuit. Adopt a part only through `tools/hardware_build_design.py` and the regeneration sequence in `ELECTRICAL_HANDOFF.md`. Two of its records are superseded by later Codex blocks:

- The TPS386000 supervisor is superseded by LTC2962 in `hardware/power_sequence`.
- The TPS62160 support values are superseded by TPS62901 in `hardware/logic_power`.

Nothing in this folder is a fabrication file, and nothing here is ready for manufacture.
