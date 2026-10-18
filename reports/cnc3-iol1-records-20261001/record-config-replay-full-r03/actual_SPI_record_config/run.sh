#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-records-20261001/record-config-replay-full-r03/actual_SPI_record_config'
mkdir include
cp vendor/Icarus/vpi_user.h include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' vendor/Icarus/_pli_types.h.in > include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Iinclude -I. record_peer_vpi.c iol1.c dic_filter.c -o record_peer_vpi.vpi > c-build.log 2>&1
iverilog -g2012 -s tb_record_config -o record.vvp tb_record_config.sv > rtl-build.log 2>&1
vvp -M . -m record_peer_vpi record.vvp > simulation.log 2>&1
