#!/bin/sh
# Measure ONE saved revision the same way every time (unchanged rules, uncapped connectivity):
#   sh step_measure.sh <revision.kicad_pcb> <out dir> [project dir with board.kicad_pro.good, board.kicad_dru, fp-lib-table, sch.net, *.pretty]
# On a copy: net_partitions.py --refill (per-net pad partitions, API unconnected count) and kicad-cli DRC
# --refill-zones --severity-all --all-track-errors --schematic-parity. Writes <out>/partitions.json,
# <out>/drc.json, <out>/summary.json (counts by category and severity; totals EXCLUDING unconnected items and the
# uncapped unconnected count from the API reported separately), <out>/sha256.txt (board + project files).
# Heavy steps go through the slot limiter; the CPU governor confines them.
set -u
REV=$1; O=$2; P=${3:-/z/pcb-runs/claude-finish/integrate}
T=/z/pcb-runs/claude-finish/tools
HV=${HEAVY:-heavy.sh}   # integration steps export HEAVY=heavym.sh (reserved slots); agents get the shared slots
KPY="/c/Program Files/KiCad/10.0/bin/python.exe"
KCLI="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
mkdir -p "$O/copy"
cp "$P/board.kicad_pro.good" "$O/copy/board.kicad_pro"
cp "$P/board.kicad_dru" "$P/fp-lib-table" "$P/sch.net" "$O/copy/"
for d in "$P"/*.pretty; do [ -d "$O/copy/$(basename "$d")" ] || cp -r "$d" "$O/copy/"; done
cp "$REV" "$O/copy/board.kicad_pcb"; chmod u+w "$O/copy/board.kicad_pcb"
sha256sum "$REV" "$O/copy/board.kicad_pro" "$O/copy/board.kicad_dru" "$O/copy/sch.net" "$O/copy/fp-lib-table" > "$O/sha256.txt"
sh "$T/$HV" kicad "$KPY" "C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261011/continuation-r2/native_final_partitions_contract_r2.py" "Z:/pcb-runs/claude-finish/tools/net_partitions.py" "C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261011/continuation-r2/SAFE-exploratory-native-trial-r9/native-postfill-via-obligations.json" "$O/copy/board.kicad_pcb" "$O/partitions.json" --refill > "$O/partitions.log" 2>&1 \
  || { echo "net_partitions failed (see $O/partitions.log)"; exit 1; }
(cd "$O/copy" && sh "$T/$HV" kicad "$KCLI" pcb drc --format json --severity-all --all-track-errors --schematic-parity \
   --refill-zones -o "$O/drc.json" board.kicad_pcb > "$O/drc.log" 2>&1)
[ -s "$O/drc.json" ] || { echo "DRC produced no report (see $O/drc.log)"; exit 1; }
C:/Python314/python.exe "$T/step_summary.py" "$O"
