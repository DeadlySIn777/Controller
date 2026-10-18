#!/bin/sh
set -eu
cd "$(dirname "$0")"
src=inputs/firmware/motherboard_iol1_readonly
clang --version > clang-version.txt
ld.lld --version > linker-version.txt
gcc --version > host-gcc-version.txt
flags="--target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -O2 -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections"
clang $flags -c $src/iol1.c -o iol1.o
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -c $src/startup.S -o startup.o
for slot in 0 1 2 3
do
 clang $flags -I$src/vendor/ST -I$src/vendor/ARM -DNODE_SLOT=$slot -c $src/target.c -o target$slot.o
 clang $flags -S -I$src/vendor/ST -I$src/vendor/ARM -DNODE_SLOT=$slot $src/target.c -o target$slot.s
 ld.lld -T $src/stm32g031.ld --gc-sections -Map=node$slot.map startup.o iol1.o target$slot.o -o node$slot.elf
 readelf -h -l -S -s node$slot.elf > node$slot-elf-review.txt
 size node$slot.elf >> sizes.txt
 objcopy -I elf32-little -O binary node$slot.elf node$slot.bin
done
gcc -O2 -std=c11 -Wall -Wextra -Werror $src/iol1.c $src/test_protocol.c -o host-protocol
./host-protocol > host-protocol.log
gcc -O1 -g -fsanitize=undefined,address -fno-omit-frame-pointer -std=c11 -Wall -Wextra -Werror $src/iol1.c $src/test_protocol.c -o sanitized-protocol
./sanitized-protocol > sanitized-protocol.log
gcc -O2 -std=c11 -Wall -Wextra -Werror -Ibefore before/iol1.c late_poll_control.c -o old-late-poll
./old-late-poll 1 > late-poll-before.log
gcc -O2 -std=c11 -Wall -Wextra -Werror -I$src $src/iol1.c late_poll_control.c -o new-late-poll
./new-late-poll 0 > late-poll-after.log

gcc -O2 -std=c11 -Wall -Wextra -Werror -Icache-before cache-before/iol1.c cache_lifecycle_control.c -o old-cache-lifecycle
./old-cache-lifecycle 1 > cache-lifecycle-before.log
gcc -O2 -std=c11 -Wall -Wextra -Werror -DCACHE_API_POINTER -I$src $src/iol1.c cache_lifecycle_control.c -o new-cache-lifecycle
./new-cache-lifecycle 0 > cache-lifecycle-after.log
