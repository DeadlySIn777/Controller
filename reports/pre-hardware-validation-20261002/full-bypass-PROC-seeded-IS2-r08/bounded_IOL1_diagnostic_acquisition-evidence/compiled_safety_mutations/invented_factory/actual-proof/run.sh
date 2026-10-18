#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/bounded_IOL1_diagnostic_acquisition-evidence/compiled_safety_mutations/invented_factory/actual-proof'
mkdir vpi-include
cp originals/vpi_user.h vpi-include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' originals/_pli_types.h.in > vpi-include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include peer_cached_vpi.c originals/iol1.c -o peer_cached_vpi.vpi > vpi-build.log 2>&1
iverilog -g2012 -s tb_iol1_acquisition -o acquisition.vvp cnc_iol1_acquisition_master.v cnc_iol1_diagnostic_acquisition.v peer.sv tb_iol1_acquisition.sv > rtl-build.log 2>&1
vvp -M . -m peer_cached_vpi acquisition.vvp > simulation.log 2>&1
