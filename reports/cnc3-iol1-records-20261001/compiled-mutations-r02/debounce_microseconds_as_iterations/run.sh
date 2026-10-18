#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-records-20261001/compiled-mutations-r02/debounce_microseconds_as_iterations'
gcc -O2 -std=c11 -Wall -Wextra -Werror -I. iol1.c dic_filter.c board_record.c test_record_config.c -o mutated > build.log 2>&1
set +e
./mutated '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-records-20261001/compiled-mutations-r02/fixtures.bin' > execute.log 2>&1
r=$?
printf '%s\n' "$r" > exit.txt
exit 0
