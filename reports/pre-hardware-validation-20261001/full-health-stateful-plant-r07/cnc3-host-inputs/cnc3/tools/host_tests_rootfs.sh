#!/bin/sh
# SPDX-License-Identifier: LicenseRef-Proprietary
# Run cnc3/tools/host_tests.sh inside the isolated Debian rootfs (glibc gcc with AddressSanitizer,
# LeakSanitizer and UndefinedBehaviorSanitizer), in private mount/pid/net namespaces with its own
# /proc, copying only the cnc3 sources into its own work directory. No network, no devices.
set -eu
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
export CONTROLLER_LAB_ROOTFS="$task_root"
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test -f "$task_root/etc/debian_version"
rm -rf "$task_root/work/pre-hardware-cnc3-a75b098519cedb29"
mkdir -p "$task_root/work/pre-hardware-cnc3-a75b098519cedb29"
cp -a "$source_dir/src" "$source_dir/model" "$source_dir/tests" "$source_dir/tools" "$task_root/work/pre-hardware-cnc3-a75b098519cedb29/"
unshare --mount --pid --net --fork --kill-child sh -c '
  task_root=$CONTROLLER_LAB_ROOTFS
  mount -t proc proc "$task_root/proc"
  exec chroot "$task_root" sh -c "gcc --version | head -1; ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 sh /work/pre-hardware-cnc3-a75b098519cedb29/tools/host_tests.sh /work/pre-hardware-cnc3-a75b098519cedb29/build"
'
