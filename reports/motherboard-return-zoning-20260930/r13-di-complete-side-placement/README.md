# DI placement correction: native candidate, routing incomplete

This exact candidate relocates the twelve complete DI pairs (120 existing parts) into clear cells. In the prior population, field RSENSE/CIN parts occupied the logic side, logic biases occupied the field side, and other AI/safety/IOL1 circuits occupied the space needed for a correct local correction. The fixed-isolator placement trial is retained as rejected r07 evidence.

Native KiCad DRC now reports **zero regular violations and no ignored checks**. All 2,688 source footprints and 9,498 fitted pads are independently accounted for. The candidate retains 7,354 track/via pieces and the original five zone definitions, with **4,916 uncapped missing joins** and no orphan copper. It is not routed or ready for manufacture.

The bounded transaction moves exactly U8001–U8012, R8001–R8024, R8101–R8124, R8201–R8224, C8001–C8024 and C8101–C8112. It removes 577 obsolete dedicated DI pieces, 102 proved obsolete field-return leaf tracks and 18 obsolete single-layer return vias. Native graph checks stop at existing pad/via/junction boundaries; all unrelated actual FIELD_B physical-pad clusters remain identical. All original 327 footprints and retained core copper remain unchanged. Native lands, pin nets and pad UUIDs remain exact.

TI ISO1212 Figure/layout requirements were checked against actual pads: every external RTHR end is at least 6.0 mm from its own device/CIN/RSENSE, exceeding the 4 mm target; each logic bypass is 1.825 mm from the actual VCC pin. CIN is owned by SENSE16/11 and field ground14/9; logic VCC is pin2, logic grounds1/8 and pin7 is NC. Return-loop routing and the required independent floating SUB copper remain separate unfinished work.

The exact twelve reserved cell polygons and the current mate/power reservation hashes are in `reserved-di-cells.json`. `di-layout-delta.json` supplies the complete 120-reference/697-copper-UUID merge scope. `receipt.json` and `independent-connectivity/review.json` contain native results; 59 focused DI host cases and six native zone-regression cases passed. The issued script's old introductory sentence that describes fixed isolators is superseded by its actual 120-reference transaction and this receipt; no fixed-isolator trial was adopted.

Root integration must merge this bounded delta with its separately reviewed current mechanical, capacitor and power poses before regenerating whole-board domain maps and planes.
