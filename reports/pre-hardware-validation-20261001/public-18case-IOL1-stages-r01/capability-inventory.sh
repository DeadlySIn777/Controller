#!/bin/sh
set -u
for t in python3 gcc g++ clang clang++ ld.lld iverilog vvp verilator ngspice efx_run; do
 p=$(command -v "$t" 2>/dev/null || true); printf 'HOST:%s:%s\n' "$t" "$p"; done
r='/root/.cache/controller-lab-linuxcnc/rootfs'
if test -f "$r/etc/debian_version"; then
 chroot "$r" /bin/sh -c 'for t in gcc g++ yosys halrun linuxcnc ngspice efx_run; do p=$(command -v "$t" 2>/dev/null || true); printf "ROOTFS:%s:%s\n" "$t" "$p"; done'
fi
