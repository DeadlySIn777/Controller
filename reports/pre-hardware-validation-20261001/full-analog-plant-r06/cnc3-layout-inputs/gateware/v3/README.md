# gateware/v3 — IS-1 motion-card endpoint

Interface specification revision IS-1 (`docs/CONTROLLER_INTERFACE_SPEC.md`, `docs/interface-spec/`,
`spec/*.json`) is the contract. The historical six-joint v1/v2 endpoint in `gateware/rtl` is unchanged.

## Shared reference codec (implemented)

`tools/protocol_v3.py` is the single protocol reference used by the RTL testbench, the C driver
(`cnc3/`) and the I/O-card tests. It reads every layout, frame length, opcode, chip-select
assignment and CRC parameter from `spec/protocol.json` at run time. Field and opcode acceptance
rules are derived from the spec's rule phrases (`derive_field_rules`, `derive_opcode_rules`),
and `tests/test_protocol_v3_reference.py` pins what is derived. A reworded spec phrase therefore
fails a test instead of silently changing behaviour.

| Command | What it does |
|---|---|
| `python gateware/v3/tools/protocol_v3.py --check` | CRC known answers, round trip of every IS-1 vector, every golden vector against its expected result |
| `python gateware/v3/tools/protocol_v3.py --vectors gateware/v3/vectors/protocol_v3_vectors.json` | regenerate the golden vectors (valid and malformed frames, 8- and 12-channel UPDATE and CONFIGURE) |
| `python gateware/v3/tools/gen_c_layout.py [--check]` | generate or verify `cnc3/src/cnc3_layout.h` (offsets), `cnc3/src/cnc3_rules.h` (rule tables) and `cnc3/tests/cnc3_vectors.h` |
| `python -m unittest discover -s tests -p test_protocol_v3_reference.py` | host tests of the codec |

The checks are structural. Rules that depend on endpoint state (current session, next sequence,
armed state, installed channels, configured clamps) belong to the endpoint and the driver. The
endpoint reference model in `cnc3/model/` exercises them.

## Interpretations of IS-1 made by the codec (to confirm in the next spec revision)

1. **SELFTEST byte 16.** Section 3.4 puts the self-test selector in CS_CMD byte 16. The `rate_0`
   rule ("zero … for every other opcode") also covers that byte. The codec treats byte 16 as owned by
   SELFTEST; bytes 17–19 must still be zero.
2. **Blank channel-1 rules.** In the CONFIGURE_IO page-1 table, rows such as `probe1_filter_ticks` and
   `freq1_no_signal_ms` have empty rules. The codec applies the corresponding channel-0 rule, following
   the table's "as probe0" convention.
3. **Structural versus semantic CONFIGURE rejection.** A frame that breaks a structural rule is a
   rejected host frame (LINK). A well-formed CONFIGURE that is invalid only against endpoint state
   (required mask outside the installed set, unknown module class) sets CONFIG_REJECTED and clears
   `config_valid`. It does not also latch LINK. The endpoint model follows this reading.
4. **JSON over Markdown.** Where a Markdown table differs from `spec/protocol.json`, the JSON is used.

## Not implemented yet in this tree

The RTL, its testbench, synthesis and pin plan. Place-and-route and timing on the Efinix T20F256
need Efinix Efinity, which is not installed; that is a named blocker, not a result.
