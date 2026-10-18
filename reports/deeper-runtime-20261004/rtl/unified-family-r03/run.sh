#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/deeper-runtime-20261004/rtl/unified-family-r03'
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$task_root/work/sim2-map-65aa7a0c3be3"
mkdir "$task_root/work/sim2-map-65aa7a0c3be3/inputs"
cp inputs/*.v "$task_root/work/sim2-map-65aa7a0c3be3/inputs/"
cp synth.ys "$task_root/work/sim2-map-65aa7a0c3be3/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/sim2-map-65aa7a0c3be3; yosys -V > yosys-version.txt; timeout 240 yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
for artifact in "$task_root/work/sim2-map-65aa7a0c3be3/"*
do
 if [ -f "$artifact" ]; then cp "$artifact" .; fi
done
exit "$result"
