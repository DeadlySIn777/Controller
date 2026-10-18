#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-integrated-records-20261002/record-acquisition-full-r02/actual_previous_command_tuple_controls/use_current_chunk_for_previous_reply/run'
mkdir vpi-include
cp originals/vpi_user.h vpi-include/
sed 's/# undef HAVE_INTTYPES_H/# define HAVE_INTTYPES_H 1/' originals/_pli_types.h.in > vpi-include/_pli_types.h
gcc -O2 -shared -fPIC -std=c11 -Wall -Wextra -Werror -Ivpi-include peer_cached_vpi.c target/iol1.c target/board_record.c -o peer_cached_vpi.vpi > vpi-build.log 2>&1
iverilog -g2012 -Wall -s tb_record_acquisition -o acquisition.vvp cnc_iol1_record_master.v cnc_iol1_record_acquisition.v cnc_mbr2_stream_checker.v peer.sv tb_record_acquisition.sv > rtl-build.log 2>&1
vvp -M . -m peer_cached_vpi acquisition.vvp > simulation.log 2>&1
