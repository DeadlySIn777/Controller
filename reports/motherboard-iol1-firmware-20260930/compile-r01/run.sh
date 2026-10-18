#!/bin/sh
set -eu
cd "$(dirname "$0")/../../../firmware/motherboard_iol1_readonly"
clang --version
for slot in 0 1 2 3
do
 clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -Oz -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -Ivendor/ST -Ivendor/ARM -DNODE_SLOT=$slot -c target.c -o /tmp/cnc-readonly-build/target$slot.o
done
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -Oz -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections -c iol1.c -o /tmp/cnc-readonly-build/iol1.o
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -c startup.S -o /tmp/cnc-readonly-build/startup.o
for slot in 0 1 2 3
do
 ld.lld -T stm32g031.ld --gc-sections -Map=/tmp/cnc-readonly-build/node$slot.map /tmp/cnc-readonly-build/startup.o /tmp/cnc-readonly-build/iol1.o /tmp/cnc-readonly-build/target$slot.o -o /tmp/cnc-readonly-build/node$slot.elf
 size /tmp/cnc-readonly-build/node$slot.elf
 clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -Oz -S -ffreestanding -fno-builtin -Ivendor/ST -Ivendor/ARM -DNODE_SLOT=$slot target.c -o /tmp/cnc-readonly-build/target$slot.s
 objcopy -I elf32-little -O binary /tmp/cnc-readonly-build/node$slot.elf /tmp/cnc-readonly-build/node$slot.bin
done
