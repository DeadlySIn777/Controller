# Parent motion-card oscillator footprint assignment

30 September 2026. The exact **ASE-50.000MHZ-L-C-T** can receive the existing native **Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm** assignment in the parent circuit as a dimension/pin-mapping candidate. Its copper/paste corner treatment and assembly process remain unqualified. This closes an absent schematic/BOM footprint assignment; it does not qualify the board for manufacture.

The freshly downloaded [Abracon ASE datasheet](https://abracon.com/Oscillators/ASEseries.pdf), revision 18 February 2022, is byte-identical to the retained project source: SHA-256 `5f5a3070e85cac34ace32dc6dfbec8066f5b09e63e19ca7084fb208296e261f1`. Page 3 resolves the exact suffixes: L is −40 to +85 °C, C is ±50 ppm, and T is a 1,000-piece reel. These component options do not establish a controller environmental rating. Page 5 supplies the package and recommended land dimensions and explicitly applies the same pin configuration/land pattern across the series frequency-dependent outlines.

| Checked fact | Manufacturer drawing / native comparison |
|---|---|
| Package envelope | Nominal 3.2 × 2.5 mm, ±0.2 mm in each direction; maximum 3.4 × 2.7 × 1.2 mm |
| Land dimensions / center spacing | 1.3 × 1.1 mm / 2.10 × 1.65 mm; all four native pads agree |
| Top-side pin orientation | Pin 1 lower left, pin 2 lower right, pin 3 upper right, pin 4 upper left; native F.Fab pin-1 chamfer agrees with the drawing's location marker |
| Pin functions / fitted source nets | 1 standby → IO_3V3; 2 return/case → LOGIC_GND; 3 clock output → FPGA_CLK_SOURCE; 4 supply → IO_3V3 |
| Native courtyard | −2.1, −1.75 to +2.1, +1.75 mm; encloses maximum body and all actual copper extents |
| Bypass source | C37 / parent C1037 is the existing 10 nF source between supply and return, with Y1 as its placement target; placement/routing quality remains open |

Native KiCad 10 inspection confirms four unique pad numbers, their exact positions and sizes, the real symbol pin names, and both child and parent exported net connections. The manufacturer draws rectangular recommended lands; the stock pads are rounded rectangles with 0.25 mm corner radius. They retain the recommended outer extents but have **3.75178% less area**. Stock F.Mask/F.Paste layers inherit those rounded shapes unless a later process changes them. This difference is retained explicitly in the ledger and parent part metadata. No manufacturer stencil approval is claimed; corner treatment, mask registration, paste apertures and assembled joint/reflow acceptance still need qualification.

The parent builder reads [the guarded proposal ledger](../../../hardware/motion_card/oscillator-footprint-promotion.json) and assigns only Y1001's footprint property/metadata when its exact MPN, inherited blank footprint and four source nets still match. It also hashes the retained/current manufacturer PDF, native-footprint snapshot and independent receipt. Historical `hardware/fpga_core` sources stay untouched. The stock footprint is already used by the published placement candidate, so root's next integration must retain existing pad/copper geometry and models, and remove the obsolete placement-only classification for this part.

[Native inspection receipt](review.json) preserves 39 protected inputs; [guard receipt](guard-review.json) preserves 41. The valid proposal loads, and six controls reject a wrong MPN, reversed pin mapping, another footprint, a false process-approval claim, hidden rounded-land difference and stale manufacturer hash. No parent generator, schematic ERC, PCB DRC, fabrication export or physical measurement was run by this task. Root owns regeneration and the subsequent native circuit/board checks.

Primary PDF and native-footprint snapshots are retained under [sources](sources/). The installed stock footprint SHA-256 is `fd7279d6b50d0370d11a93ac2f4e145e58901c4f51109bdb2f06d4c1d10bbe5e`. Its STEP association remains separate from the earlier sourced envelope/model and does not prove assembled fit.
