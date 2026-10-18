# Full controller project publication — 18 October 2026

The project owner requested the full source/design upload after documentation reconciliation, then explicitly selected: **upload source, CAD and readable evidence; keep raw caches local**.

## Published source and design

Canonical software, firmware, gateware, configuration/schema examples, tests/tools, native hardware/revisions, manufacturing requirements and research files are published at their original workspace-relative paths. The full source copy covers 5,207 files and approximately 915 MB before Git compression. Existing proprietary and third-party notices remain; no new licence grant is added.

[Full source manifest](FULL_SOURCE_MANIFEST.json) records exact published Git blob IDs and SHA-256 values. These preserve original stored bytes; a platform's checkout attributes can still affect working-copy line endings. The local source workspace remains unchanged by upload.

The [documentation index](docs/README.md), [briefing](PROJECT_BRIEFING.md) and [engineering status](reports/ENGINEERING_STATUS.md) describe current implementation and open gates. All 37 topic guides were reviewed; 36 manually maintained guides were reconciled and the generated F001–F200 catalogue remained unchanged and passed its consistency check.

## Readable engineering evidence

The repository includes **79,690 small readable/source report files**, approximately 1.13 GB before Git compression. [Browsable evidence manifest](BROWSABLE_EVIDENCE_MANIFEST.json) records their exact blob IDs and hashes. It covers text, logs, receipts, bounded structured records and source/native schematic/library inputs up to 256 KiB per selected file. This is an explicit browseable subset of the complete historical evidence tree.

The approximately 161 GB historical report tree, including source-bound PKL models, raw WKB geometry, large structured/native checkpoint data and complete raw run closures, remains local at the user's direction. No release archives are being uploaded. Missing large workspace-only references must not be treated as uploaded or newly validated evidence. Local source/evidence manifests retain their original scope; this upload does not replace them.

The earlier [documentation-only snapshot](documentation/PUBLICATION.md) has an explicit workspace-reference register for portable reading. The root project paths are the canonical full-source publication.

## Existing board review and local exclusions

The [original board-review snapshot](BOARD_REVIEW.md), board/, routing/, evidence/, archives/ and original MANIFEST.json remain unchanged. This includes the existing cached native baseline/staged ZIPs and published editable board package.

Git internals, machine-local .claude permissions, credentials, private runtime/customer stores, temporary downloaded vendor/tool work, and existing ignored bytecode/build/runtime files remain local. These exclusions follow the project source/publication contract. Original machine configurations, live/adopted boards and the external IS-1 archive are not modified.

## Verification boundary

High-confidence credential scans found no matching keys/tokens in selected canonical source text, selected report text up to 10 MB and text entries in the five canonical hardware ZIPs. Media/binary payloads have a separate scope. Documentation file links, fences and generated-catalogue consistency were checked. Source and report manifests record the published bytes; original board-review paths were independently compared to the prior remote commit.

This upload runs no new compilation, synthesis, ERC/DRC or physical measurement. All twelve fitted interfaces and actual electrical/motion limits remain required. Physical-wrapper FPGA implementation/timing, routing/current/assembly closure, complete target/runtime qualification and manufacturing readiness remain open.
