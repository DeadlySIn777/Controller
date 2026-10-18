#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-records-20261001/record-config-replay-full-r02/compiled_authority_and_integrity_mutations/rejected_frame_feeds_timer'
gcc -O2 -std=c11 -Wall -Wextra -Werror -I. iol1.c dic_filter.c board_record.c test_record_config.c -o mutated > build.log 2>&1
set +e
./mutated '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-records-20261001/record-config-replay-full-r02/compiled_authority_and_integrity_mutations/fixtures.bin' > execute.log 2>&1
r=$?
printf '%s\n' "$r" > exit.txt
exit 0
