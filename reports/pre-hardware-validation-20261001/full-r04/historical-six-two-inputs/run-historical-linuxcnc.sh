#!/bin/sh
set -eu
cd "$(dirname "$0")"
r='/root/.cache/controller-lab-linuxcnc/rootfs'
backup="$r/work/pre-hardware-module-bdaa97c92f78094c"
mkdir -p "$backup"
m="$r/usr/lib/linuxcnc/modules/cnc1_sim.so"
if test -f "$m"; then cp "$m" "$backup/cnc1_sim.so"; fi
restore() { if test -f "$backup/cnc1_sim.so"; then cp "$backup/cnc1_sim.so" "$m"; else rm -f "$m"; fi; }
trap restore EXIT HUP INT TERM
sh cnc1/tools/build.sh
sh cnc1/tools/run_linuxcnc.sh
