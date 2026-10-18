#!/bin/sh
# Rerun the unmodified gateware regression (gateware/tools/run_tests.sh) on a
# byte-identical scratch copy of gateware/rtl, tests and tools, so no build
# output is written into the gateware tree (owned by the gateware group).
# Runs in the WSL distro with its own iverilog/verilator/python3, not in the
# rootfs chroot; the copy lives under the lab rootfs work directory.
# Usage (capture as the CNC1 default-v1/ABI-v2 evidence log):
#   sh cnc1/tools/run_gateware_regression.sh > cnc1/evidence/baseline-regression.log 2>&1
# This is HDL simulation and lint evidence only.
set -eu
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
export CONTROLLER_LAB_ROOTFS="$task_root"
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
gateware="$source_dir/gateware"
work="$task_root/work/cnc1-gateware-regression"
sums() { (cd "$1" && find rtl tests tools -type f ! -path '*/__pycache__/*' | LC_ALL=C sort | xargs sha256sum); }
rm -rf "$work"
mkdir -p "$work/gateware"
before=$(sums "$gateware")
cp -a "$gateware/rtl" "$gateware/tests" "$gateware/tools" "$work/gateware/"
find "$work/gateware" -name __pycache__ -type d -prune -exec rm -rf {} +
test "$(sums "$work/gateware")" = "$before"
status=0
sh "$work/gateware/tools/run_tests.sh" || status=$?
after=$(sums "$gateware")
if [ "$before" != "$after" ]; then
    echo 'cnc1-regression: gateware sources changed during the run; result not usable' >&2
    exit 3
fi
echo "cnc1-regression: ran on a byte-identical copy of gateware/rtl, tests and tools ($(printf '%s\n' "$before" | wc -l) files); sources unchanged during the run; exit $status"
rm -rf "$work"
exit $status
