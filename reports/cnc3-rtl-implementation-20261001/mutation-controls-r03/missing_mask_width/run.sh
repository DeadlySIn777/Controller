#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/mutation-controls-r03/missing_mask_width'
iverilog -g2012 -s tb -o simulation *.v '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/proof-r06/validate_tb.sv'
vvp simulation
