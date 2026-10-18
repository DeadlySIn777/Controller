#!/bin/sh
set -eu
cd '/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/deeper-runtime-20261004/rtl/serialized-candidate-r03/mapping-r01'
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$task_root/work/sim2-map-f8555ebbf90b"
mkdir "$task_root/work/sim2-map-f8555ebbf90b/inputs"
cp inputs/*.v "$task_root/work/sim2-map-f8555ebbf90b/inputs/"
cp synth.ys "$task_root/work/sim2-map-f8555ebbf90b/synth.ys"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/sim2-map-f8555ebbf90b; yosys -V > yosys-version.txt; timeout -k 5 600 yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
for artifact in "$task_root/work/sim2-map-f8555ebbf90b/"*
do
 if [ -f "$artifact" ]; then cp "$artifact" .; fi
done
exit "$result"
