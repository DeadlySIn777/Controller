#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-acquisition-20261001/actual-target-acquisition-r01'
iverilog-vpi peer_cached_vpi.c originals/iol1.c > vpi-build.log 2>&1
iverilog -g2012 -s tb_iol1_acquisition -o acquisition.vvp cnc_iol1_acquisition_master.v cnc_iol1_diagnostic_acquisition.v peer.sv tb_iol1_acquisition.sv > rtl-build.log 2>&1
vvp -M . -m peer_cached_vpi acquisition.vvp > simulation.log 2>&1
