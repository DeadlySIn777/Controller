# Full controller project publication — 18 October 2026

This repository now includes the complete Git-visible controller source/design project alongside its original public board-review package. The user requested the full project after the documentation reconciliation.

## Source and design

Canonical software, firmware, gateware, configuration/schema examples, tests/tools, native hardware/revisions, manufacturing requirements and research files are published at their original workspace-relative paths. Existing proprietary and third-party notices remain; no new licence grant is added. The [documentation index](docs/README.md), [briefing](PROJECT_BRIEFING.md) and [engineering status](reports/ENGINEERING_STATUS.md) describe the current implementation and open gates.

The [original board-review snapshot](BOARD_REVIEW.md), board/, routing/, evidence/, archives/ and original MANIFEST.json remain unchanged. The earlier documentation/ subtree is a dated documentation-only snapshot; the root project paths are the canonical full-source publication.

## Exact engineering evidence

The local report tree is approximately 161 GB, including source-bound model caches, native CAD checkpoints, raw geometry and historical failed attempts. Small human-readable/source/report records are browsable under reports/. Oversized and raw evidence is packaged separately as exact compressed release archives with SHA-256 file/blob manifests and safe restoration tooling. Publication receipts identify completed assets and their hashes; an archive is complete only when all manifest-listed parts have uploaded and verified.

The archives include the model caches used as exact audit inputs. They must not be treated as disposable proof or substituted with placeholders. The complete evidence tree is restored into a separate directory using the supplied verifier; restoration neither executes imported objects nor changes existing machine files.

Git internals, machine-local .claude permissions, installed/downloaded vendor runtimes and temporary tool work under tmp/, bytecode/build caches and source-ignored private runtime/simulation-position files remain local under the existing project ignore contract. These are not controller source or newly validated evidence. Machine configurations are not modified by publication.

## Verification boundary

This upload is a byte-preserving source/evidence publication, not a new compilation, synthesis, ERC/DRC, physical measurement or manufacturing release. All twelve fitted interfaces and actual electrical/motion limits remain required. Physical-wrapper FPGA implementation/timing, routing/current/assembly closure, complete target/runtime qualification and manufacture remain open.
