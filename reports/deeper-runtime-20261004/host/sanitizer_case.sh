#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
work=$1
case_name=$2
case "$work" in /work/deeper-cnc3-sanitizer-*) ;; *)exit 2;;esac
mount -t proc proc "$task_root/proc"
if test "$case_name" = driver;then
 exec chroot "$task_root" /usr/bin/env ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 "$work/bin/driver-spi" "$work/configuration/runtime.json"
elif test "$case_name" = reader;then
 exec chroot "$task_root" /usr/bin/env ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 python3 "$work/source/cnc3_runtime/tests/manifest_controls.py" "$work/bin/manifest-probe" "$work/configuration/runtime.json"
else exit 2;fi
