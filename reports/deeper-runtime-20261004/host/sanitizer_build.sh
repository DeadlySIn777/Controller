#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
evidence=$1
work=$2
case "$work" in /work/deeper-cnc3-sanitizer-*) ;; *)exit 2;;esac
test ! -e "$task_root$work"
mkdir -p "$task_root$work/build/verilator-include"
cp -a "$evidence/source" "$task_root$work/source"
cp -a "$evidence/configuration" "$task_root$work/configuration"
cp -a /usr/share/verilator/include/. "$task_root$work/build/verilator-include/"
verilator --cc -Wall -Wno-fatal --top-module cnc3_runtime_sim --Mdir "$task_root$work/build/obj" "$task_root$work/source/gateware/v3/runtime/"*.v
chroot "$task_root" /bin/sh -s -- "$work" <<'BUILD'
set -eu
cd "$1"
flags='-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer'
for file in cnc3 cnc3_proto manifest;do
 gcc -std=c11 $flags -Wall -Wextra -Werror -pedantic -Wshadow -Isource/cnc3_runtime/src -c "source/cnc3_runtime/src/$file.c" -o "build/$file.o"
done
g++ -std=c++17 $flags -pthread -Wall -Wextra -Werror -Isource/cnc3_runtime/src -isystem build/obj -isystem build/verilator-include -isystem build/verilator-include/vltstd -c source/cnc3_runtime/src/sim_transport.cpp -o build/transport.o
for source in build/obj/*.cpp build/verilator-include/verilated.cpp build/verilator-include/verilated_threads.cpp;do
 g++ -std=c++17 $flags -pthread -Ibuild/obj -Ibuild/verilator-include -Ibuild/verilator-include/vltstd -c "$source" -o "build/$(basename "$source" .cpp).o"
done
g++ -std=c++17 $flags -pthread -Wall -Wextra -Werror -Isource/cnc3_runtime/src -c source/cnc3_runtime/tests/driver_spi.cpp -o build/test.o
g++ $flags -pthread -o build/driver-spi build/test.o build/cnc3.o build/cnc3_proto.o build/manifest.o build/transport.o build/Vcnc3_runtime_sim*.o build/verilated*.o -lm
gcc -std=c11 $flags -Wall -Wextra -Werror -pedantic -Isource/cnc3_runtime/src source/cnc3_runtime/tests/manifest_probe.c build/manifest.o -lm -o build/manifest-probe
dpkg-query -W gcc g++ linuxcnc-uspace linuxcnc-uspace-dev > build/packages.tsv
BUILD
cp "$task_root$work/build/packages.tsv" "$evidence/packages.tsv"
cp "$task_root$work/build/driver-spi" "$evidence/"
cp "$task_root$work/build/manifest-probe" "$evidence/"
