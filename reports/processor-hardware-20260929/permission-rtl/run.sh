#!/bin/sh
set -eu
cd "$(dirname "$0")"
iverilog -V > tool-version.txt 2>&1
iverilog -g2012 -Wall -s tb_permission_connection -o simulation \
  inputs/gateware/rtl/cnc_endpoint.v inputs/gateware/rtl/cnc_spi_frame.v \
  inputs/gateware/rtl/cnc_stepgen.v inputs/gateware/rtl/cnc_encoder.v \
  inputs/gateware/board_review/tb_permission_connection.sv > build.log 2>&1
vvp simulation > run.log 2>&1
