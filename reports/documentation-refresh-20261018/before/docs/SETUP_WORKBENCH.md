# Disconnected setup workbench

**Deep upgrade, 4 October 2026:** [current audit and evidence](../reports/deep-upgrade-20261004/README.md) add local source-grounded fact intake, a sixth **Readiness** view, a revision-bound configuration/backup self-check, readable before/after changes, reviewed file-picker backup recovery, working native downloads and identity/draft-bound saves. These remain explicitly disconnected configuration and host checks; physical commissioning and motion-loop testing are unavailable.

In Drive details, open **Enter facts in your own words**, enter explicit logical motor statements and choose **Interpret facts locally**. For example:

```text
Motor m0 has 200 full steps per revolution
Motor m0 microsteps = 16
Motor m0 gear_motor_revolutions = 1
Motor m0 gear_load_revolutions = 1
Motor m0 travel_per_load_revolution = 5 mm
Motor m0 max_velocity_units_per_second = 10 mm/s
```

These are authored demonstration values, not defaults for physical equipment. Use each configured motor's exact `m0`…`m11` identity and its selected units. Review the source quotes, conflicts and unanswered text before adding supported facts to the draft. No value is saved by interpretation, known answers are retained, and unsupported or ambiguous wording needs clarification. Local intake spends no credits. Paid-model follow-up questions are derived from the candidate's actual missing fields, so known answers are not requested again.

**Readiness** identifies the next configuration step and records its exact binding. After saving a reviewed generation, **Run configuration self-check** exercises validation and a real compressed backup roundtrip. Its receipt explicitly excludes physical motion, target execution and physical measurements. Under **Saved setup**, select a local `.tar.zst` backup (maximum 8 MiB), choose its saved generation or working draft, then **Review backup** and inspect the diff before saving. This never extracts files, runs firmware/jobs or restores machine authority.

Additional shared CLI commands are `readiness`, `self-check --expected-revision N`, and `intake --facts-file supplied-facts.txt --expected-revision N`. Intake returns a candidate without changing the store. `status` now includes `draft_binding`; `save --expected-binding binding.json --expected-revision N` can additionally check that exact identity, epoch and original draft digest. The UI uses this binding automatically. Existing explicit revision-only CLI callers retain compatibility.

The default UI uses the user's requested dark/red theme. Dark native form controls, visible focus, readable contrast and labelled status colors apply across the same setup and diagnostic workflow; red branding does not imply machine permission. [Theme and interaction verification](../reports/ui-dark-red-20261004/README.md).

The workbench also exposes **Diagnostics**, a separate authored fault example, compressed support downloads and compressed setup backups. The public `setup diagnostics` and `setup package` commands use the same service. Typed machine observations bind to the saved configuration; missing/stale evidence remains unavailable. [Usage, format, recovery and limits](DIAGNOSTICS_AND_PACKAGES.md) · [One-machine flagship acceptance](FLAGSHIP_WORKFLOW.md).

Implemented 4 October 2026. This is a working local UI, public CLI and common setup service for explicit simulation profiles. It is separate from the historical six-motor/two-encoder configuration fixture and XYZ runtime authority. It does not connect to hardware, select a physical drive, produce physical wiring instructions or commission a machine.

## Open the UI

From the project directory, run:

```powershell
python -B -m controller_config setup --directory .controller-setup-demo serve --port 8766
```

Open `http://127.0.0.1:8766/`. The server binds only to loopback and requires the exact printed address. Choose a profile, enter known mechanics, check the calculated scales and assignments, then save the reviewed generation. The explicitly labelled simulation example is optional; its values are not machine defaults. Draft changes autosave, and switching supported profiles retains their previous answers. Changing mm/in converts travel and velocity with bounded display rounding and invalidates the preview.

Three-axis mill, dual-motor gantry, eight-motor and twelve-motor profiles share the same twelve-motor inventory. Each motor has a distinct enable and alarm. Four ABZ, 24 general DI and 16 general DO assignments are available; the retained DO limits are 0.5 A/channel and 2 A/group of four. Other required IS-2 interfaces are listed as requirements but are not configurable through this fixture. Its SIM terminal labels and 100 kHz ceiling are authored model constraints, never qualified board ratings.

The review shows scales, rate demand, model ceilings, illustrative connections and the exact configuration diff. A stale, foreign or modified plan cannot commit. Repeated commit IDs return the retained result. Restore previews a prior generation and writes a new reviewed generation when the configuration changes; it never restores position, homing, commissioning or permission. The store retains twenty prior generations, one draft per supported profile, one hundred commit results and two hundred audit entries. Export contains local setup facts; it is not the qualified protected cartridge/mirror contract.

## Public CLI

All commands below return structured JSON and use the same service as the UI. Use a dedicated directory; existing stores are not overwritten by initialization. Raw export files are created only at new paths.

```powershell
python -B -m controller_config setup --directory .controller-setup-demo capabilities
python -B -m controller_config setup --directory .controller-setup-demo schema
python -B -m controller_config setup --directory .controller-setup-demo profiles
python -B -m controller_config setup --directory .controller-setup-demo init
python -B -m controller_config setup --directory .controller-setup-demo template sim-machine-12motor --output my-draft.json
python -B -m controller_config setup --directory .controller-setup-demo status
```

Edit the draft with known simulation facts. To exercise a fully authored example instead, use `example sim-machine-12motor --output example-draft.json`. Save with the revision returned by `status`, for example `save my-draft.json --expected-revision 0` for a still-empty initialized store. Never assume zero for an existing workspace.

Then use `preview --output my-plan.json`, inspect the plan, and `commit my-plan.json --request-id my-unique-review-id`. Use the same ID and plan after a lost acknowledgment, or query `request-result my-unique-review-id`. `restore-preview 1 --output restore-plan.json` previews a retained generation; it still needs commit. Other commands are `assist --question "What remains?"`, `audit`, `export my-export.json`, `budget`, and `restart-epoch --expected-revision N`. Restarting the local epoch invalidates outstanding previews; it is not a hardware reset.

Local guidance is deterministic. It reports missing facts and validation blockers and explains the scale formula. It never calls a model or sends a machine command. A damaged budget ledger disables paid assistance while leaving a valid offline setup usable; the budget file is preserved for reconciliation.

## Optional AI extraction

Paid AI is disabled by default. No model, price, key, network request or account balance is inferred. An administrator must provide an explicitly approved provider configuration with:

- `schema_version: 1`, `approved: true`, and `provider: "openai"`;
- exact `model` and `model_version` labels;
- `pricing_source` at an official OpenAI HTTPS documentation domain and a timezone-aware `valid_until`;
- bounded integer `max_input_tokens` and `max_output_tokens`;
- `pricing` containing `currency: "USD"`, a `version`, integer `microdollars_per_million_tokens` for `input_tokens`, `cached_input_tokens` and `output_tokens`, and `microdollars_per_tool_call` containing the explicitly approved `input_token_count` fee, including zero if appropriate.

One dollar is 1,000,000 microdollars. Supply an approved configuration through `serve --provider-config approved-ai.json` to expose the optional UI card, or use `advise --provider-config approved-ai.json --facts-file supplied-facts.txt --expected-revision N --allow-paid`. The real transport reads `OPENAI_API_KEY` only for an explicitly requested paid operation. Never put a key in a browser field, command argument, configuration export or this repository.

The UI explains that the supplied facts and saved draft go to OpenAI. One action reserves the maximum permitted cost, counts the exact input, and sends at most one bounded generation request. There are no automatic retries or repair loops. Identical version-bound advice is reused. The result may propose only currently missing mechanical values grounded in complete supported positive statements for the exact logical motor, mechanical field and configured unit. Wrong-motor/field, ambiguous, negated, conditional and conflicting statements are refused; a number appearing somewhere in a quote is insufficient. It cannot change electrical limits, terminals, existing answers or authority. Source statements remain unverified user claims, and the candidate must be reviewed, saved to the draft and validated by the service. Follow-up questions come from actual missing fields; raw provider questions are kept in source inspection.

The ledger has an immutable per-session ceiling of at most US$15, integer arithmetic, atomic reservations and process locks. Unknown billing keeps the reservation unavailable. Provider-reported token usage produces a provisional formula estimate; it is not a final invoice. `budget-settle REQUEST_ID --actual-microdollars AMOUNT --evidence-id EVIDENCE` is a trusted operator reconciliation command for actual billing evidence. It is not a model tool. An excessive actual charge is recorded and freezes further spending. The ledger is local to one host/session, not a global account limit or distributed OneDrive lock.

The implementation follows the official [input-token counting](https://developers.openai.com/api/docs/guides/token-counting) and [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) contracts. Only injected provider responses have been tested here. Live model suitability, pricing, billing reconciliation, cost per successful setup and reference-machine accuracy remain unqualified.

## Evidence and remaining integration

See the [implementation and verification record](../reports/readiness-fixes-20261004/README.md). Host tests and browser checks are distinct from target compilation, actual LinuxCNC/RTL integration, vendor FPGA fit/timing, circuit/board checks and physical measurements. G26 and the other production acceptance gates remain open. The production checker now consumes all 26 gates and their bound evidence.

The next product work needs an exact approved physical machine/equipment catalog, real identity and telemetry, full-runtime configuration integration, a bounded commissioning workflow, protected settings/entitlement recovery, and paid-model plus novice-user evaluation. Claude retains PCB routing ownership.
