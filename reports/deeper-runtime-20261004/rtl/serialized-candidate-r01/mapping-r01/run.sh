#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/deeper-runtime-20261004/rtl/serialized-candidate-r01/mapping-r01'
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$task_root/work/sim2-map-3ca6e371c05f"
mkdir "$task_root/work/sim2-map-3ca6e371c05f/inputs"
cp inputs/*.v "$task_root/work/sim2-map-3ca6e371c05f/inputs/"
cp synth.ys "$task_root/work/sim2-map-3ca6e371c05f/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/sim2-map-3ca6e371c05f; yosys -V > yosys-version.txt; timeout -k 5 600 yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
for artifact in "$task_root/work/sim2-map-3ca6e371c05f/"*
do
 if [ -f "$artifact" ]; then cp "$artifact" .; fi
done
exit "$result"
