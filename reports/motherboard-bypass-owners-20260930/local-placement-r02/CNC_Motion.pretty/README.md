# Motion-card footprint sources

`T20F256_Efinix_NSMD.kicad_mod` is a review candidate derived from the KiCad community footprint `Package_BGA:TFBGA-256_13x13mm_Layout16x16_P0.8mm`. Its 256 pad names, positions, orientation and nominal package outline are preserved. Copper diameter is changed from 0.32 to 0.35 mm; the retained 0.075 mm radial mask margin produces a 0.50 mm opening. These dimensions follow Efinix's Trion Packaging User Guide v5.3, Table 12, page 58.

The source and modified files' SHA256 values, current manufacturer ball-map comparison, and native KiCad geometry results are recorded in [mechanical.json](../mechanical.json) and [PACKAGE_GEOMETRY_CHECK.json](../../../reports/board-completion-20260930/PACKAGE_GEOMETRY_CHECK.json). The accompanying [LICENSE.md](LICENSE.md) preserves the KiCad library's CC-BY-SA 4.0 license and design exception. This attribution does not change the controller application's commercial licensing policy.

The model is a source-dimension visualization envelope, not a manufacturer STEP model. It uses nominal/basic 13 mm X/Y and 1.14 mm maximum package height. It does not represent the complete lateral tolerance envelope, assembled solder joints or reflow stand-off. A generated KiCad project must copy the model to `3dmodels/T20F256_source_envelope.wrl` beneath its project directory or remap `${KIPRJMOD}` appropriately.

Footprint verification does not qualify escape routing, stack-up, via technology, mask registration, stencil/paste, reflow or assembly inspection. No manufacturing approval is implied.
