#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p build
rtl="rtl/cnc_spi_frame.v rtl/cnc_stepgen.v rtl/cnc_encoder.v rtl/cnc_endpoint.v"
iverilog -V 2>&1 | head -n 1
# Default ABI v1 regression (shortened watchdog) and independent Python status decode.
iverilog -g2012 -Wall -s tb_cnc_endpoint -o build/tb_cnc_endpoint $rtl tests/tb_cnc_endpoint.sv
vvp build/tb_cnc_endpoint
python3 tools/protocol.py --check-rtl-status build/status_encoder.hex
# Opt-in ABI v2 (ENABLE_DISCOVERY=1) capability page and its one-shot consumption.
iverilog -g2012 -Wall -s tb_cnc_endpoint_v2 -o build/tb_cnc_endpoint_v2 $rtl tests/tb_cnc_endpoint_v2.sv
vvp build/tb_cnc_endpoint_v2
# Also elaborate production-default top, separately from testbench parameters.
iverilog -g2012 -Wall -s cnc_endpoint -o build/cnc_endpoint $rtl
# The .v sources must also elaborate as plain Verilog-2005 (no SystemVerilog).
iverilog -g2005 -Wall -s cnc_endpoint -o build/cnc_endpoint_v2005 $rtl
iverilog -g2005 -Wall -s cnc_endpoint -Pcnc_endpoint.ENABLE_DISCOVERY=1 -o build/cnc_endpoint_v2005_abi2 $rtl
echo 'Icarus -g2005 elaboration passed for the default ABI1 and ENABLE_DISCOVERY=1 tops'
if command -v verilator >/dev/null 2>&1; then
  verilator --version
  verilator --lint-only -Wall --top-module cnc_endpoint $rtl
  verilator --lint-only -Wall -GENABLE_DISCOVERY=1 --top-module cnc_endpoint $rtl
  verilator --lint-only -Wall --default-language 1364-2005 --top-module cnc_endpoint $rtl
  echo 'Verilator strict lint passed: default, ENABLE_DISCOVERY=1 and 1364-2005 language mode'
else
  echo 'Verilator not installed: second lint check skipped'
fi
