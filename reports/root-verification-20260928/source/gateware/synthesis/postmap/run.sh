#!/bin/sh
# Functional mapped-netlist simulation, isolated from active CNC1 development.
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
synthesis_dir=$(dirname "$source_dir")
task_root=${CONTROLLER_SYNTH_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
task_work="$task_root/work/fpga-postmap-abi2"
test -x "$task_root/usr/bin/yosys"
python3 "$synthesis_dir/record_results.py" --check
mkdir -p "$source_dir/results" "$task_work/input" "$task_work/results" "$task_work/build/verilator-include"
cp "$source_dir/input/"* "$task_work/input/"
cp "$synthesis_dir/results/cnc_endpoint_efinix.json" "$task_work/input/"
cp "$task_root/usr/share/yosys/efinix/cells_sim.v" "$source_dir/input/efinix_cells_sim.v"
cp "$source_dir/input/efinix_cells_sim.v" "$task_work/input/"
cp -a /usr/share/verilator/include/. "$task_work/build/verilator-include/"
export CONTROLLER_SYNTH_ROOTFS="$task_root"
unshare --mount --propagation private --pid --fork --kill-child sh -c '
  set -eu
  task_root=$CONTROLLER_SYNTH_ROOTFS
  mount -t proc proc "$task_root/proc"
  chroot "$task_root" sh -c "cd /work/fpga-postmap-abi2; yosys -Q -T -p \"read_json input/cnc_endpoint_efinix.json; write_verilog -noattr results/mapped.v\" > results/export.log 2>&1"
'
cp "$task_work/results/mapped.v" "$source_dir/results/"
# Preserve all upstream model/generated-netlist warnings; none are suppressed.
# Wno-fatal permits known model width/unused diagnostics, documented in the report.
verilator --cc -Wall -Wno-fatal --top-module cnc_endpoint --output-split 10000 \
  --Mdir "$task_work/build/obj_dir" "$task_work/results/mapped.v" \
  "$task_work/input/efinix_cells_sim.v" > "$source_dir/results/verilator.log" 2>&1
chroot "$task_root" sh -c '
  set -eu
  cd /work/fpga-postmap-abi2
  gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -Iinput -c input/cnc1.c -o build/cnc1.o
  gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic -Iinput -c input/test_driver.c -o build/test_driver.o
  g++ -std=c++17 -O2 -pthread -Iinput -Ibuild/obj_dir -Ibuild/verilator-include -Ibuild/verilator-include/vltstd -c input/sim_transport.cpp -o build/sim_transport.o
  for source in build/obj_dir/*.cpp build/verilator-include/verilated.cpp build/verilator-include/verilated_threads.cpp; do
    g++ -std=c++17 -O2 -pthread -Ibuild/obj_dir -Ibuild/verilator-include -Ibuild/verilator-include/vltstd -c "$source" -o "build/$(basename "$source" .cpp).o"
  done
  g++ -pthread -o build/test_mapped build/test_driver.o build/cnc1.o build/sim_transport.o build/Vcnc_endpoint*.o build/verilated*.o -lm
' > "$source_dir/results/build.log" 2>&1
set +e
timeout 180 chroot "$task_root" sh -c 'cd /work/fpga-postmap-abi2; ./build/test_mapped' > "$source_dir/results/tests.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$source_dir/results/exit-status.txt"
cp "$task_work/results/export.log" "$source_dir/results/"
chroot "$task_root" dpkg-query -W gcc g++ yosys yosys-abc > "$source_dir/results/packages.tsv"
sha256sum "$task_work/build/test_mapped" > "$source_dir/results/test-binary.sha256"
verilator --version > "$source_dir/results/verilator-version.txt"
test "$result" -eq 0
python3 "$source_dir/record_results.py"
tail -1 "$source_dir/results/tests.log"
