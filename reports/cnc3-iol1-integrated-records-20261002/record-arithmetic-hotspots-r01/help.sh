#!/bin/sh
set -eu
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs yosys -Q -T -p "help synth_efinix"'
