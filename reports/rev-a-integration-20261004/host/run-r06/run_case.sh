#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
work=$1
module=$2
case_name=$3
case "$work" in /work/rev-a-host-20261004-*) ;; *)exit 2;; esac
mount -t proc proc "$task_root/proc"
mount -t tmpfs tmpfs "$task_root/dev/shm"
chmod 1777 "$task_root/dev/shm"
if test "$case_name" = denied; then allow=0; else allow=1; fi
chroot "$task_root" /usr/sbin/runuser -u cnclab -- /bin/sh -c '
  cd "$1"
  export CNC3_ALLOW_DISCONNECTED_RTL_SIMULATION="$4"
  export RTAPI_FIFO_PATH="$1/.rtapi_$3_fifo"
  unset DISPLAY
  exec python3 hal_runtime.py --module "$2" --case "$3"
' sh "$work" "$module" "$case_name" "$allow"
