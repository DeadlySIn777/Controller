"""One-time readiness documentation correction; no CAD/source/evidence regeneration."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
AUDIT = Path(__file__).resolve().parent
before = json.loads((AUDIT / "before-docs-manifest.json").read_text(encoding="utf-8"))
original = {}
updated = {}
for entry in before["files"]:
    raw = (ROOT / entry["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise SystemExit(f"Concurrent edit; review before proceeding: {entry['path']}")
    original[entry["path"]] = raw
    updated[entry["path"]] = raw.decode("utf-8").replace("\r\n", "\n")


def replace(path, old, new):
    if updated[path].count(old) != 1:
        raise SystemExit(f"Expected one exact text match in {path}: {old[:80]}")
    updated[path] = updated[path].replace(old, new, 1)


def after_title(path, paragraph):
    title, rest = updated[path].split("\n", 1)
    updated[path] = title + "\n\n" + paragraph + "\n" + rest


after_title("PROJECT_MEMORY.md", "**Readiness and AI setup priority (user, 3 October 2026):** Claude owns the active routing work; keep hardware/CAD/routing and the external IS-1 archive untouched during this readiness audit. The user prioritizes an exceptionally easy frontend and an AI CNC setup specialist that completes supported setup accurately without wasting the roughly US$15 API allowance on repeated questions, speculation or retry loops. Treat that allowance as a budget to protect, not a target to spend or a verified cost. Preserve optional AI and a complete offline deterministic path. The [AI setup contract](docs/AI_SETUP_CONTRACT.md) defines exact-profile grounding, saved intake, deterministic calculations/validation, shared UI/CLI/AI transactions, separate deliberate physical commissioning, persistent cost reservations and acceptance cases. It is not implemented firmware. The [fresh reaudit](reports/readiness-reaudit-20261003/README.md) supersedes stale readiness prose and records the unadopted external UI assistant's negation defect. Source26/ROOT104/CAD30 below is the last verified adopted baseline, not a claim about Claude's in-progress routing.")

after_title("docs/BUILD_PLAN.md", "**3 October readiness priority:** while Claude owns routing, advance the common service, exact equipment profiles and [AI-assisted setup acceptance contract](AI_SETUP_CONTRACT.md). Prove one complete supported setup with saved facts, deterministic validation, bounded API spending and guided verification before broadening advertised capability. The [fresh readiness audit](../reports/readiness-reaudit-20261003/README.md) distinguishes current implementation from plans; no routing or target firmware is changed by this update.")

after_title("docs/PLATFORM_ROADMAP.md", "**3 October setup priority:** the user wants a CNC setup specialist and an exceptionally easy frontend, with the roughly US$15 API allowance protected from repeated questions, hallucinated settings and retry loops. The [AI setup contract](AI_SETUP_CONTRACT.md) gives the shared-service workflow, spending controls and acceptance cases. These are requirements, not installed capabilities. See the [readiness reaudit](../reports/readiness-reaudit-20261003/README.md); Claude owns routing during this work.")

after_title("reports/ENGINEERING_STATUS.md", "**Readiness reaudit begun 3 October 2026:** [current findings and fresh checks](readiness-reaudit-20261003/README.md). Claude owns routing; the board figures below describe the last verified adopted Source26/ROOT104/CAD30 baseline. Manufacturing and complete-machine readiness remain false. The public setup service remains a disconnected six-motor fixture, with separate historical XYZ runtime configuration; no integrated AI setup expert, customer frontend or API budget enforcement is implemented in Controller. The [new AI setup acceptance contract](../docs/AI_SETUP_CONTRACT.md) records the user's setup and credit-efficiency priority. The external unadopted UI candidate has a reproduced command-negation defect and is not qualified for reuse.")
replace("reports/ENGINEERING_STATUS.md", "# Controller engineering status — 2 October 2026", "# Controller engineering status — readiness review begun 3 October 2026")

after_title("docs/CURRENT_ACCEPTANCE_GATES.md", "**3 October readiness review:** [fresh audit](../reports/readiness-reaudit-20261003/README.md); Claude owns routing. Board figures refer to the last verified adopted baseline. G26 adds the user's AI setup and API-budget acceptance requirement; no gate is closed by this documentation update.")

old = "The staged record-acquisition mapping exceeds the coarse T20 resource budget and is undergoing implementation optimization; HDL simulation alone does not prove capacity."
new = "The r08 record-acquisition mapping exceeded the coarse T20 resource screen. A later report-local arithmetic-sharing candidate screens at 19,477 LUT4+ADD against 19,728, leaving only 251; the [reaudit](REVIEW_LINK) records its exact scope and remaining integration omissions. It is unadopted and does not establish complete design capacity, vendor fit or timing."
for path in ["PROJECT_MEMORY.md", "docs/BUILD_PLAN.md", "docs/PLATFORM_ROADMAP.md", "reports/ENGINEERING_STATUS.md", "docs/CURRENT_ACCEPTANCE_GATES.md"]:
    link = ("reports/" if path == "PROJECT_MEMORY.md" else "" if path.startswith("reports/") else "../reports/") + "readiness-reaudit-20261003/software-audit.md"
    replace(path, old, new.replace("REVIEW_LINK", link))

replace("docs/BUILD_PLAN.md", "The [current motherboard source cost](../reports/motherboard-cost-20260930/source-980-reviewed/README.md) is partial.", "The [historical 980-part source cost](../reports/motherboard-cost-20260930/source-980-reviewed/README.md) is a preserved subset, superseded for current costing by the Source26 v11 audit above.")

replace("reports/ENGINEERING_STATUS.md", "The [persistent project memory](../PROJECT_MEMORY.md) records the user's included-screen price objective, PCBWay turnkey route, optional AI companion, highly modifiable hardware/firmware, CLI-first configuration and simple guided wiring/setup.", "The [persistent project memory](../PROJECT_MEMORY.md) records the preliminary US$400 controller-assembly reference with separately costed complete screen packages, PCBWay turnkey route, optional AI, editable engineering inputs, CLI-first configuration and simple guided wiring/setup. The earlier included-screen price objective is historical.")
replace("reports/ENGINEERING_STATUS.md", "The earlier terminal-first comparison is historical: a fixed wiring base and removable FPGA card were subsequently confirmed, while the newer one-PCB direction remains a pending architecture clarification rather than a silent waiver.", "The fixed wiring base, removable FPGA/custom cards and pending one-PCB discussion are superseded by the adopted IS-2 active motherboard. Approved commodity modules remain replaceable; soldered regions require whole-motherboard service through retained keyed harness groups, with separate physical verification and service-time evidence.")
replace("reports/ENGINEERING_STATUS.md", "Eight standard motors plus a four-motor plug-in/factory-fitted path, individual enable/alarm and 24 general DI/16 general DO are confirmed requirements;", "All twelve motor interfaces fitted on one active motherboard, at least eight usable motors, individual enable/alarm and 24 general DI/16 general DO are confirmed requirements; the former eight-plus-four custom-card path is historical;")
replace("reports/ENGINEERING_STATUS.md", "One of its 14 source hashes, the host-side `controller_lab/service_health.py`, has changed since; that record is pending re-recording.", "The fresh readiness audit verifies all 14 retained source hashes, including `controller_lab/service_health.py`; the older stale-hash observation is superseded. No target rebuild or flash occurred in that audit.")
replace("reports/ENGINEERING_STATUS.md", "`gateware/tools/record_evidence.py` has no read-only mode: running it rewrites `gateware/validation/manifest.json`, so run it only after a fresh `gateware/tools/run_tests.sh`.", "`python -B gateware/tools/record_evidence.py --check` is read-only. The fresh audit reports an unrecorded `tests/tb_stepgen12_characterization.sv`; it does not repair the old manifest by re-stamping it. Running the recorder without `--check` rewrites `gateware/validation/manifest.json`; use record mode only after a fresh relevant RTL run and preserve the previous evidence.")

replace("docs/CURRENT_ACCEPTANCE_GATES.md", "3,524 required board joins remain.", "3,508 required board joins remain in the last verified ROOT104 baseline.")
replace("docs/CURRENT_ACCEPTANCE_GATES.md", "Source26/ROOT102 has 1,102 incomplete multi-pad nets and 3,524 required joins.", "The last verified Source26/ROOT104 baseline has 1,101 incomplete multi-pad nets and 3,508 required joins.")
replace("docs/CURRENT_ACCEPTANCE_GATES.md", "Each gate needs exact input revision, test method, scope, result and source identity.", "| G26 | AI acts as a grounded CNC setup specialist, produces a validated supported setup efficiently and protects the roughly US$15 API allowance | [AI setup contract](AI_SETUP_CONTRACT.md): exact board/equipment/firmware evidence, saved dependency-aware intake, deterministic calculations and limits, shared UI/CLI/AI preview/commit, separate deliberate commissioning, durable spending reservations and bounded retries; AI01–AI19 with actual cost/quality results and no unsafe accepted action; offline fallback and G10 novice proof | Open. Controller has simulated profiles and bounded separate runtime services; no integrated setup expert, customer frontend, approved physical profile catalog or cost enforcement. External candidate keyword assistant fails negation/intent tests and is not adopted. |\n\nEach gate needs exact input revision, test method, scope, result and source identity.")
replace("docs/CURRENT_ACCEPTANCE_GATES.md", "The recorded working allocation is Codex for schematics, power/protection, connectors, PCB and BOM; Claude for FPGA logic, CNC1 protocol/driver and configuration-service integration.", "The historical allocation was Codex for schematics, power/protection, connectors, PCB and BOM; Claude for FPGA logic, protocol/driver and service integration. The user's 3 October instruction assigns current routing to Claude and this work to Codex readiness/setup review; do not edit or adopt routing during this audit.")

after_title("docs/CONFIGURATION_AND_CLI.md", "**AI setup requirement, 3 October 2026:** the [AI setup execution contract](AI_SETUP_CONTRACT.md) extends this common service with exact-profile grounding, saved intake, deterministic calculations/validation, bounded spending and explicit commissioning authority. The user wants expert setup with minimal repetition and no wasted API allowance. G26 remains open; the current prototype below is not an AI assistant or customer-ready setup service.")
replace("docs/DISPLAY_TIERS.md", "It is the current multi-size sourcing reference; no listed panel is qualified or selected for manufacture.", "It is a dated multi-size sourcing reference; its generated six/eight-motor I/O comparisons are historical and do not cost the adopted all-twelve motherboard. Rebuild the complete-package comparison against the current fitted source before using it for a launch decision. No listed panel is qualified or selected for manufacture.")
replace("manufacturing/release-manifest.json", '"native_zone_or_rulearea_count": 1521,', '"native_zone_or_rulearea_count": 1544,')

path = "manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md"
start = updated[path].index("The reconciled electrical source")
end = updated[path].index("## Files and evidence required")
updated[path] = updated[path][:start] + """**Readiness reconciliation begun 3 October 2026:** Claude owns active routing. The following is the last verified adopted **Source26/ROOT104, published CAD30** baseline, not a claim that in-progress routing is complete. [Fresh audit and provenance checks](../reports/readiness-reaudit-20261003/README.md).

The source and published board contain **2,688 footprints**: 2,642 purchased fitted parts, 44 bare PCB features and two DNPs. Required motor/I/O and remaining interfaces are represented in source. Recorded native Source26 ERC is **0 errors/70 unsuppressed warnings**, with [exact warning dispositions](../reports/motherboard-erc-20261002/source26-exact-warning-disposition-r01/receipt.json). Source representation does not establish target execution or physical qualification.

The adopted and published native boards share SHA-256 `70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc`: **11,807 track/via items, 1,544 zones/rule areas, 633 fully joined and 1,101 incomplete multi-pad nets, 3,508 required joins**. Recorded regular DRC is **0 errors/0 warnings/no ignored checks**, with zero orphan copper; connectivity completion fails. The **460 × 340 mm, six-layer, 1.6 mm** stackup remains provisional. These native results were not rerun in this readiness audit.

**Source27 reset/health corrections remain staged and unadopted.** Reconcile them with the routing owner's returned successor before electrical/physical release; do not overwrite ongoing routing or silently merge old candidates. The [drill/land audit](../reports/motherboard-pcb-integration-20261002/ROOT103-bypass-PROC-full-drill-SMD-r01/receipt.json) retains **274 vias intersecting 277 same-net paste SMD lands**, a lower bound excluding tangency/registration margins. Correct geometry or qualify the exact filled/capped fabrication and assembly process; tenting and ordinary DRC do not close this issue.

Full power/return, complete 20 ms inhibit/defaults, actual CNC3/HAL/local-I/O authority, record trust/provisioning, analog chain, exact FPGA vendor fit/timing, mechanics, target load and physical/EMC/thermal qualification remain unfinished. The later report-local FPGA resource optimization is not an adopted complete device implementation. Gerbers, drills, production CPL/drawings, programming/test bundle and final stackup have not been released. **Manufacturing readiness remains false.** Historical six-joint/two-encoder runtime is not twelve proven coordinated axes.

The immutable [Source26 partial cost audit v11](../reports/motherboard-cost-20260930/source-r26-2688-complete-cost-v11/README.md) prices 105 exact MPNs; **185 MPNs/720 purchased fitted pieces remain unpriced**. Known-priced consumed parts per board at **1/10/100 are US$1,091.51/$877.37/$796.51**. Purchased modules, displays, fabrication, assembly, programming/test, enclosure and packaging remain separate unknowns. Complete manufactured controller/package totals remain unknown; this is not a PCBWay quotation. Earlier 980-part and CAD21 figures are preserved in [the pre-audit checklist](../reports/readiness-reaudit-20261003/before-docs/manufacturing/PCBWAY_SUBMISSION_CHECKLIST.md).

""" + updated[path][end:]

updated["docs/CURRENT_ACCEPTANCE_GATES.md"] = updated["docs/CURRENT_ACCEPTANCE_GATES.md"].replace("\n\n| G26", "\n| G26")
changed = []
for path, value in updated.items():
    data = value.encode("utf-8")
    (ROOT / path).write_bytes(data)
    changed.append({"path": path, "before_sha256": hashlib.sha256(original[path]).hexdigest(), "after_sha256": hashlib.sha256(data).hexdigest()})
(AUDIT / "readiness-doc-changes.json").write_text(json.dumps({"scope": "Readiness docs/metadata only; no status promoted; no source/CAD modifications", "files": changed}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"changed": len(changed), "cad_or_source_changes": 0}))
