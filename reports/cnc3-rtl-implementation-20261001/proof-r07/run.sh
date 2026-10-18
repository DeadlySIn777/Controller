#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/proof-r07'
gcc -std=c11 -O1 -Wall -Wextra -Werror oracle/oracle.c oracle/cnc3_proto.c -o oracle/check
oracle/check < oracle-input.txt > oracle-output.txt
iverilog -g2012 -s tb -o validate.vvp '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/cnc3_command_validate.v' validate_tb.sv
vvp validate.vvp
iverilog -g2012 -s tb -o spi.vvp '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/cnc3_command_validate.v' '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/cnc3_spi_transport.v' '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/cnc3_frame_endpoint.v' spi_tb.sv
vvp spi.vvp
iverilog -g2012 -s tb -o pack.vvp '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/cnc3_feedback_pack.v' '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-rtl-implementation-20261001/stage-r01/rtl/cnc3_status_pack.v' pack_tb.sv
vvp pack.vvp
gcc -std=c11 -O1 -Wall -Wextra -Werror oracle/roundtrip.c oracle/cnc3_proto.c -o oracle/roundtrip
oracle/roundtrip < response-input.txt > response-output.txt
