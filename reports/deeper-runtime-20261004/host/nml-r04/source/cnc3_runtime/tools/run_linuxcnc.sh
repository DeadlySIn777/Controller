#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
work=$1
module=$2
case "$work" in /work/deeper-cnc3-*) ;; *)exit 2;; esac
mount -t proc proc "$task_root/proc"
mount -t tmpfs tmpfs "$task_root/dev/shm"
chmod 1777 "$task_root/dev/shm"
chroot "$task_root" /usr/sbin/runuser -u cnclab -- /bin/sh -c '
 set -eu
 cd "$1"
 export CNC3_ALLOW_DISCONNECTED_RTL_SIMULATION=1
 export CNC3_SIM_MANIFEST="$1/configuration/runtime.json"
 export CNC3_SIM_STORE="$1/configuration/setup.json"
 export CNC3_SIM_VERIFIER="$1/source/tools/prepare_cnc3_sim2.py"
 export RTAPI_FIFO_PATH="$1/.rtapi_fifo"
 unset DISPLAY
 python3 "$1/source/cnc3_runtime/profile.py" --manifest "$CNC3_SIM_MANIFEST" --store "$CNC3_SIM_STORE" --module "$2" --output "$1/profile" --observation "$1/linuxcnc.json"
 exec linuxcnc -r "$1/profile/sim2.ini"
' sh "$work" "$module"
