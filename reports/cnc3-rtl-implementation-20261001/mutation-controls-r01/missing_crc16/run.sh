#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/mutation-controls-r01/missing_crc16'
iverilog -g2012 -s tb -o simulation *.v '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/proof-r04/spi_tb.sv'
vvp simulation
