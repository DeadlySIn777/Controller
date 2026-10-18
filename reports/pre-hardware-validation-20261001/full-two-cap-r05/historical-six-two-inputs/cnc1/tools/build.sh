#!/bin/sh
set -eu
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
export CONTROLLER_LAB_ROOTFS="$task_root"
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
project_dir=$(dirname "$source_dir")
test -f "$task_root/etc/debian_version"
# Build from the checked-in sources only: stale Verilator split files or objects
# from an earlier RTL revision would otherwise be globbed into the link below.
rm -rf "$task_root/work/cnc1/build" "$task_root/work/cnc1/src" "$task_root/work/cnc1/tests"
mkdir -p "$task_root/work/cnc1/build" "$source_dir/build" "$source_dir/evidence"
cp -a "$source_dir/src" "$task_root/work/cnc1/"
cp -a "$source_dir/tests" "$task_root/work/cnc1/"
mkdir -p "$task_root/work/cnc1/build/verilator-include"
cp -a /usr/share/verilator/include/. "$task_root/work/cnc1/build/verilator-include/"
verilator --cc -Wall -GENABLE_DISCOVERY=1 --top-module cnc_endpoint \
  --Mdir "$task_root/work/cnc1/build/obj_dir" \
  "$project_dir/gateware/rtl/cnc_endpoint.v" "$project_dir/gateware/rtl/cnc_spi_frame.v" \
  "$project_dir/gateware/rtl/cnc_stepgen.v" "$project_dir/gateware/rtl/cnc_encoder.v"
chroot "$task_root" sh -c '
  set -eu
  cd /work/cnc1
  gcc -std=c11 -O2 -fPIC -Wall -Wextra -Werror -pedantic -Isrc -c src/cnc1.c -o build/cnc1.o
  gcc -std=gnu11 -O2 -fPIC -Wall -Wextra -Werror -DRTAPI -DRTAPI_USPACE -I/usr/include/linuxcnc -Isrc -c src/hal_cnc1.c -o build/hal_cnc1.o
  g++ -std=c++17 -O2 -fPIC -pthread -Isrc -Ibuild/obj_dir -Ibuild/verilator-include -Ibuild/verilator-include/vltstd \
    -c src/sim_transport.cpp -o build/sim_transport.o
  for source in build/obj_dir/*.cpp build/verilator-include/verilated.cpp build/verilator-include/verilated_threads.cpp; do
    g++ -std=c++17 -O2 -fPIC -pthread -Ibuild/obj_dir -Ibuild/verilator-include -Ibuild/verilator-include/vltstd -c "$source" -o "build/$(basename "$source" .cpp).o"
  done
  g++ -shared -pthread -o build/cnc1_sim.so build/hal_cnc1.o build/cnc1.o build/sim_transport.o build/Vcnc_endpoint*.o build/verilated*.o -lm
  gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -Isrc -c tests/test_driver.c -o build/test_driver.test.o
  g++ -pthread -o build/test_driver build/test_driver.test.o build/cnc1.o build/sim_transport.o build/Vcnc_endpoint*.o build/verilated*.o -lm
  ./build/test_driver
  cp build/cnc1_sim.so /usr/lib/linuxcnc/modules/cnc1_sim.so
'
cp "$task_root/work/cnc1/build/cnc1_sim.so" "$source_dir/build/"
chroot "$task_root" dpkg-query -W gcc g++ linuxcnc-uspace linuxcnc-uspace-dev > "$source_dir/evidence/build-packages.tsv"
