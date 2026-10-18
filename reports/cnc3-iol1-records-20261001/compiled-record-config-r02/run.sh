#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/cnc3-iol1-records-20261001/compiled-record-config-r02'
gcc --version > gcc-version.txt
clang --version > clang-version.txt
ld.lld --version > linker-version.txt
flags='-O2 -std=c11 -Wall -Wextra -Werror'
gcc $flags -Iinputs inputs/iol1.c inputs/dic_filter.c inputs/board_record.c inputs/test_record_config.c -o host-record-config
./host-record-config fixtures.bin > host-checks.log
gcc -O1 -g -std=c11 -Wall -Wextra -Werror -fsanitize=undefined,address -fno-omit-frame-pointer -Iinputs inputs/iol1.c inputs/dic_filter.c inputs/board_record.c inputs/test_record_config.c -o sanitized-record-config
./sanitized-record-config fixtures.bin > sanitizer-checks.log
aflags='--target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -O2 -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections'
for source in iol1 dic_filter board_record
do clang $aflags -Iinputs -c inputs/$source.c -o $source.o;done
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -c inputs/startup.S -o startup.o
for slot in 0 1 2 3
do
 clang $aflags -Iinputs -Iinputs/vendor/ST -Iinputs/vendor/ARM -DNODE_SLOT=$slot -c inputs/target.c -o target$slot.o
 ld.lld -T inputs/stm32g031.ld --gc-sections -Map=node$slot.map startup.o iol1.o dic_filter.o board_record.o target$slot.o -o node$slot.elf
 readelf -h -l -S -s node$slot.elf > node$slot-elf-review.txt
 size node$slot.elf >> sizes.txt
 objcopy -I elf32-little -O binary node$slot.elf node$slot.bin
done
