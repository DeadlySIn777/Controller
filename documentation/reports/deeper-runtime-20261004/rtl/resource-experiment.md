# Event storage resource result

Keep the current banked runtime frozen. The report-local serialized candidates preserve the tested behavior and reduce generic RAM use, but increase LUT use. None closes FPGA resources or has vendor place-and-route or timing evidence.

| Exact mapped source | LUT4 | ADD | FF | RAM5K | Disposition |
|---|---:|---:|---:|---:|---|
| Frozen runtime, unified-family-r04 | 34,493 | 7,776 | 9,900 | 64 | Current integration target; resource closure blocked |
| Serialized r01, mapping-r01 | 36,225 | 7,814 | 9,991 | 8 | Rejected staging-pressure bookkeeping defect |
| Corrected serialized r02, mapping-r01 | 35,754 | 7,814 | 9,991 | 8 | Report-only, not adopted |
| Flat-staging serialized r03, mapping-r02 | 35,757 | 7,814 | 9,991 | 8 | Report-only, not adopted |

All four completed maps used the functional SIM top and reported zero Yosys structural check problems. The default-deny top was not substituted. Each has copied exact inputs and SHA256 manifests. The r03 first mapping and mutation were interrupted during the session gap; their partial artifacts and explicit incomplete receipts remain beside the fresh completed runs.

Corrected r02 passes the 1,190-assertion actual SPI suite, eleven event-storage assertions, seven provider assertions, 10,000 default-deny cycles, three intentional copied-source defect controls, 160,000 differential cycles and 64 staging-pressure accounting checks. R03 repeats the same normal suite, differential and pressure checks, plus the event-acknowledgment mutation. The other two mutation results belong to r02 and are not represented as new r03 runs. These counts overlap and must not be summed into a qualification score.

The pressure control is deliberately faster than legal serial input. It exposed r01's phantom accepted count when a full staging queue rejected an event. Corrected variants advance sequence, occupancy and pointers only when a record is actually accepted, and latch overflow otherwise. Independent review found no further actionable issue in the final staging, clear, collision, prefetch or acknowledgment behavior. The finite staging bound relies on the actual complete-frame transport and one-shot rearm cadence; it is not a general multiwriter FIFO contract.

`serialized-candidate-r02/receipt.json` and `serialized-candidate-r03/receipt.json` bind detailed evidence. `resource-attribution.json` preserves available source attribution for mapped FF/ADD primitives and explicitly marks LUT origins unavailable after ABC technology mapping. The next resource effort must measure changes without weakening capacity, channel count, interlocks or command validation. Physical IOL1 and device integration remain separate open work.
