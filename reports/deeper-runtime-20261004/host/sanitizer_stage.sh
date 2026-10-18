#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
evidence=$1
work=$2
case "$work" in /work/deeper-cnc3-sanitizer-*) ;; *)exit 2;;esac
test ! -e "$task_root$work"
mkdir -p "$task_root$work"
cp -a "$evidence/source" "$task_root$work/source"
cp -a "$evidence/configuration" "$task_root$work/configuration"
cp -a "$evidence/bin" "$task_root$work/bin"
chmod 755 "$task_root$work/bin/driver-spi" "$task_root$work/bin/manifest-probe"
sha256sum "$task_root$work/bin/driver-spi" "$task_root$work/bin/manifest-probe"
