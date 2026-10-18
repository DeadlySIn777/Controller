#!/bin/sh
# Called only inside new PID/mount namespace; no host mount is changed.
set -eu
task_rootfs=$1
task_binary=$2
mount --make-rprivate /
mount -t proc proc "$task_rootfs/proc"
exec chroot "$task_rootfs" "$task_binary"
