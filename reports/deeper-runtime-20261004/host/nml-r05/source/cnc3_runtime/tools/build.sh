#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
evidence=$1
run_key=$2
case "$run_key" in *[!a-f0-9]*|'') exit 2;; esac
work=/work/deeper-cnc3-$run_key
test ! -e "$task_root$work"
test -f "$task_root/usr/include/linuxcnc/hal.h"
mkdir -p "$task_root$work/build/verilator-include"
cp -a "$evidence/source" "$task_root$work/source"
cp -a "$evidence/configuration" "$task_root$work/configuration"
cp -a /usr/share/verilator/include/. "$task_root$work/build/verilator-include/"
verilator --cc -Wall -Wno-fatal --top-module cnc3_runtime_sim \
 --Mdir "$task_root$work/build/obj" "$task_root$work/source/gateware/v3/runtime/"*.v
chroot "$task_root" /bin/sh -s -- "$work" "$run_key" <<'BUILD'
set -eu
cd "$1"
for file in cnc3 cnc3_proto manifest; do
 gcc -std=c11 -O2 -fPIC -Wall -Wextra -Werror -pedantic -Wshadow -Isource/cnc3_runtime/src -c "source/cnc3_runtime/src/$file.c" -o "build/$file.o"
done
g++ -std=c++17 -O2 -fPIC -pthread -Wall -Wextra -Werror -Isource/cnc3_runtime/src -isystem build/obj -isystem build/verilator-include -isystem build/verilator-include/vltstd -c source/cnc3_runtime/src/sim_transport.cpp -o build/transport.o
for source in build/obj/*.cpp build/verilator-include/verilated.cpp build/verilator-include/verilated_threads.cpp; do
 g++ -std=c++17 -O2 -fPIC -pthread -Ibuild/obj -Ibuild/verilator-include -Ibuild/verilator-include/vltstd -c "$source" -o "build/$(basename "$source" .cpp).o"
done
module=c3rt_$(printf %.20s "$2")
gcc -std=gnu11 -O2 -fPIC -Wall -Wextra -Werror -DRTAPI -DRTAPI_USPACE "-DCNC3_SIM_MODULE_NAME=\"$module\"" -I/usr/include/linuxcnc -Isource/cnc3_runtime/src -c source/cnc3_runtime/src/hal_cnc3_sim.c -o build/hal.o
g++ -shared -pthread -o "build/$module.so" build/hal.o build/cnc3.o build/cnc3_proto.o build/manifest.o build/transport.o build/Vcnc3_runtime_sim*.o build/verilated*.o -lm
g++ -std=c++17 -O2 -pthread -Wall -Wextra -Werror -Isource/cnc3_runtime/src -c source/cnc3_runtime/tests/driver_spi.cpp -o build/test.o
g++ -pthread -o build/driver-spi build/test.o build/cnc3.o build/cnc3_proto.o build/manifest.o build/transport.o build/Vcnc3_runtime_sim*.o build/verilated*.o -lm
gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -Isource/cnc3_runtime/src source/cnc3_runtime/tests/manifest_probe.c build/manifest.o -lm -o build/manifest-probe
dpkg-query -W gcc g++ linuxcnc-uspace linuxcnc-uspace-dev > build/packages.tsv
BUILD
chown -R 1000:1000 "$task_root$work"
chmod 755 "$task_root$work/source/cnc3_runtime/integration.py"
cp "$task_root$work/build/packages.tsv" "$evidence/packages.tsv"
cp "$task_root$work/build/"*.so "$evidence/"
cp "$task_root$work/build/driver-spi" "$evidence/"
