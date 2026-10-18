#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p build
iverilog -V 2>&1 | head -n 1
iverilog -g2012 -Wall -s tb_cnc_endpoint -o build/tb_cnc_endpoint \
  rtl/cnc_spi_frame.v rtl/cnc_stepgen.v rtl/cnc_encoder.v rtl/cnc_endpoint.v tests/tb_cnc_endpoint.sv
vvp build/tb_cnc_endpoint
python3 tools/protocol.py --check-rtl-status build/status_encoder.hex
# Also elaborate production-default top, separately from testbench parameters.
iverilog -g2012 -Wall -s cnc_endpoint -o build/cnc_endpoint \
  rtl/cnc_spi_frame.v rtl/cnc_stepgen.v rtl/cnc_encoder.v rtl/cnc_endpoint.v
if command -v verilator >/dev/null 2>&1; then
  verilator --version
  verilator --lint-only -Wall --top-module cnc_endpoint \
    rtl/cnc_spi_frame.v rtl/cnc_stepgen.v rtl/cnc_encoder.v rtl/cnc_endpoint.v
else
  echo 'Verilator not installed: second lint check skipped'
fi
