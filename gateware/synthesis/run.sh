#!/bin/sh
# Run inside WSL GarciaMechBuilder. Uses only the existing isolated Debian rootfs.
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
gateware_dir=$(dirname "$source_dir")
task_root=${CONTROLLER_SYNTH_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
test -x "$task_root/usr/bin/yosys"
test -f "$task_root/etc/debian_version"
task_work="$task_root/work/fpga-synthesis"
# Remove earlier generated results so only this run's files are copied back.
rm -rf "$task_work/results" "$task_work/rtl"
mkdir -p "$task_work/rtl" "$task_work/results" "$source_dir/results" "$source_dir/input"
cp "$gateware_dir/rtl/cnc_endpoint.v" "$gateware_dir/rtl/cnc_spi_frame.v" \
   "$gateware_dir/rtl/cnc_stepgen.v" "$gateware_dir/rtl/cnc_encoder.v" "$task_work/rtl/"
cp "$source_dir/synth.ys" "$source_dir/cdc_check.ys" "$task_work/"
cp "$task_work/rtl/"*.v "$source_dir/input/"
verilator --lint-only -Wall -GENABLE_DISCOVERY=1 --top-module cnc_endpoint \
  "$task_work/rtl/cnc_endpoint.v" "$task_work/rtl/cnc_spi_frame.v" \
  "$task_work/rtl/cnc_stepgen.v" "$task_work/rtl/cnc_encoder.v" > "$source_dir/results/verilator.log" 2>&1
export CONTROLLER_SYNTH_ROOTFS="$task_root"
set +e
timeout 240 unshare --mount --propagation private --pid --fork --kill-child sh -c '
  set -eu
  task_root=$CONTROLLER_SYNTH_ROOTFS
  mount -t proc proc "$task_root/proc"
  chroot "$task_root" sh -c "cd /work/fpga-synthesis; yosys -Q -T -p \"help synth_efinix\" > results/backend-help.txt; yosys -V > results/yosys-version.txt; sha256sum /usr/bin/yosys /usr/bin/yosys-abc /usr/share/yosys/efinix/* /usr/share/yosys/techmap.v > results/tool-files.sha256; yosys -Q -T -s synth.ys > results/synthesis.log 2>&1 && yosys -Q -T -s cdc_check.ys > results/cdc-check.log 2>&1"
'
result=$?
set -e
cp "$task_work/results/"* "$source_dir/results/"
chroot "$task_root" dpkg-query -W yosys yosys-abc > "$source_dir/results/packages.tsv"
# dpkg's Installed-Size metadata (KiB) for the tools added to the isolated rootfs.
chroot "$task_root" dpkg-query -W -f='${Package}\t${Version}\t${Installed-Size}\n' yosys yosys-abc python3-click > "$source_dir/results/package-sizes.tsv"
verilator --version > "$source_dir/results/verilator-version.txt"
printf '%s\n' "$result" > "$source_dir/results/exit-status.txt"
test "$result" -eq 0
python3 "$source_dir/record_results.py"
printf 'Efinix-family synthesis completed; results in %s/results\n' "$source_dir"
