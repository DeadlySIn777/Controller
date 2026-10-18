#!/bin/sh
set -eu
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
test -f "$task_root/etc/debian_version"
task_work=/work/cnc3-audit-1d9a63d30af44b1d9b9bcb0b61b6ece4
test ! -e "$task_root$task_work"
mkdir -p "$task_root$task_work"
cp -a /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/audit-2026-09-30/CNC3_BRANCH_CHECKS/inputs/cnc3 "$task_root$task_work/cnc3"
export CONTROLLER_LAB_ROOTFS="$task_root" CNC3_AUDIT_WORK="$task_work"
unshare --mount --pid --net --fork --kill-child sh -c 'mount -t proc proc "$CONTROLLER_LAB_ROOTFS/proc"; exec chroot "$CONTROLLER_LAB_ROOTFS" sh -c "gcc --version; ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 sh $CNC3_AUDIT_WORK/cnc3/tools/host_tests.sh $CNC3_AUDIT_WORK/build"'
cp -a "$task_root$task_work/build" /mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/audit-2026-09-30/CNC3_BRANCH_CHECKS/build-artifacts
