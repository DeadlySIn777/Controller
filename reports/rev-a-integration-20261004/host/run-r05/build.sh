#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
source_dir=$1
run_key=$2
case "$run_key" in *[!a-f0-9]*|'') exit 2;; esac
work=/work/rev-a-host-20261004-$run_key
test ! -e "$task_root$work"
test -f "$task_root/usr/include/linuxcnc/hal.h"
mkdir -p "$task_root$work/build/verilator-include"
cp -a "$source_dir/inputs" "$task_root$work/inputs"
cp -a "$source_dir/src" "$task_root$work/src"
cp "$source_dir/hal_runtime.py" "$task_root$work/hal_runtime.py"
cp -a /usr/share/verilator/include/. "$task_root$work/build/verilator-include/"
verilator --cc -Wall -Wno-fatal --top-module cnc3_motion_spi \
  --Mdir "$task_root$work/build/obj" "$task_root$work/inputs/rtl/"*.v
chroot "$task_root" /bin/sh -s -- "$work" "$run_key" <<'BUILD'
set -eu
cd "$1"
gcc -std=c11 -O2 -fPIC -Wall -Wextra -Werror -pedantic -Wconversion -Wshadow -Iinputs/driver -c inputs/driver/cnc3.c -o build/driver.o
gcc -std=c11 -O2 -fPIC -Wall -Wextra -Werror -pedantic -Wconversion -Wshadow -Iinputs/driver -c inputs/originals/cnc3.c -o build/original-driver.o
gcc -std=c11 -O2 -fPIC -Wall -Wextra -Werror -pedantic -Wconversion -Wshadow -Iinputs/driver -c inputs/driver/cnc3_proto.c -o build/codec.o
g++ -std=c++17 -O2 -fPIC -pthread -Wall -Wextra -Werror -Isrc -Iinputs/driver -isystem build/obj -isystem build/verilator-include -isystem build/verilator-include/vltstd -c src/rtl_transport.cpp -o build/transport.o
for source in build/obj/*.cpp build/verilator-include/verilated.cpp build/verilator-include/verilated_threads.cpp; do
  g++ -std=c++17 -O2 -fPIC -pthread -Ibuild/obj -Ibuild/verilator-include -Ibuild/verilator-include/vltstd -c "$source" -o "build/$(basename "$source" .cpp).o"
done
for variant in IS2 IS1; do
  module=c3rf_${variant}_$(printf %.20s "$2")
  gcc -std=gnu11 -O2 -fPIC -Wall -Wextra -Werror -DRTAPI -DRTAPI_USPACE "-DCNC3_REFUSAL_MODULE_NAME=\"$module\"" -I/usr/include/linuxcnc -Iinputs/driver -Isrc -c src/hal_cnc3_refusal.c -o "build/hal-$variant.o"
  driver=build/driver.o
  if test "$variant" = IS1; then driver=build/original-driver.o; fi
  g++ -shared -pthread -o "build/$module.so" "build/hal-$variant.o" "$driver" build/codec.o build/transport.o build/Vcnc3_motion_spi*.o build/verilated*.o -lm
done
dpkg-query -W gcc g++ linuxcnc-uspace linuxcnc-uspace-dev > build/packages.tsv
BUILD
chown -R 1000:1000 "$task_root$work"
cp -a "$task_root$work/build/obj" "$source_dir/generated"
cp "$task_root$work/build/packages.tsv" "$source_dir/packages.tsv"
cp "$task_root$work/build/"*.so "$source_dir/"
