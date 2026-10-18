#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
work=$1
case "$work" in /work/deeper-cnc3-sanitizer-*) ;; *)exit 2;;esac
mount -t proc proc "$task_root/proc"
exec chroot "$task_root" /usr/bin/env ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 python3 "$work/strict_reader.py" "$work/source/cnc3_runtime/tests/manifest_controls.py" "$work/bin/manifest-probe" "$work/configuration/runtime.json"
