# Controller documentation publication — 18 October 2026

This is a documentation-only snapshot of the Controller engineering workspace, added alongside the existing public board-review package at the user's request.

Start with the [documentation index](docs/README.md), [project briefing](PROJECT_BRIEFING.md) and [engineering status](reports/ENGINEERING_STATUS.md). The repository's [board-review entry](../README.md) still describes its original native baseline/staged files and their evidence.

The active product contract is one active motherboard with a soldered FPGA, all twelve fitted motor interfaces with individual enable/alarm, four base ABZ, 24 general DI and 16 smart DO plus the other retained interfaces. Required electrical/motion limits, offline entitlements, protected settings recovery and deliberate inhibited restart remain. Routing, physical-wrapper FPGA implementation/timing and complete electrical/physical/manufacturing qualification are open.

## Included scope and provenance

The snapshot includes all current topic guides, root project guidance, component READMEs, top-level research/report records and Markdown evidence reached from those documents. Dated studies retain their stated source/profile/result scope. The generated feature catalogue keeps F001–F200 and proposal wording unchanged.

[PUBLICATION_MANIFEST.json](PUBLICATION_MANIFEST.json) records original workspace document hashes, published hashes and link transformations. For portable reading, local links to included Markdown use the corresponding published path. Links to unprovided code, raw measurements, large CAD/evidence artifacts, local backups or unresolved historical anchors point to the explicit [workspace reference register](WORKSPACE_REFERENCES.md). Those transformations do not add missing engineering evidence. Original workspace files are not changed by publication.

The full source/configuration repository is required to execute the documented CLI or tests. This snapshot does not ship those implementations or authorize a physical machine. The existing board-review files remain separately available at their original paths.

This upload adds no software/hardware licence grant, fabrication release, supplier order, firmware flash or physical qualification. No credentials or machine settings are included.
