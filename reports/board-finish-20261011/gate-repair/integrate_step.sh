#!/bin/sh
# One gated integration step on the working board (unchanged rules, uncapped connectivity, committed revisions):
#   sh integrate_step.sh <label> <producer.sh> [producer args...]
# The producer is called as: sh producer.sh <in.kicad_pcb> <applied.kicad_pcb> <partitions.json of IN> <work dir> [args]
# and must write only into its work dir. Then: measure the applied board (tools/step_measure.sh) and report against
# the latest committed revision (tools/step_report.py). If no DRC error category increased, the applied board is
# committed as is. Otherwise tools/remove_new_errors.py removes only the step's own error copper (and its own
# dangling remnants), the result is measured again and committed only if the gate passes. Revisions are read-only.
set -u
if ! ps -ef 2>/dev/null | awk -v p="$PPID" '$2==p' | grep -q run_queue.sh; then
  echo "integrate_step.sh refuses: only integrate/run_queue.sh may commit to the working board (parent $PPID)"; exit 2
fi
export HEAVY=heavym.sh   # step_measure.sh and producers that honour HEAVY use the integration-only slots
LABEL=$1; PROD=$2; shift 2
I=/z/pcb-runs/claude-finish/integrate
IW=Z:/pcb-runs/claude-finish/integrate
T=/z/pcb-runs/claude-finish/tools
KPY="/c/Program Files/KiCad/10.0/bin/python.exe"
PY=C:/Python314/python.exe
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$I/steps.log"; }
PREV_M=$I/baseline-r00; PREV_B=$I/revs/r00-checkpoint.kicad_pcb; LAST=r00
for s in $(grep -oE "r[0-9]{2}-[a-z0-9-]+ COMMITTED" "$I/steps.log" | awk '{print $1}'); do
  PREV_M=$I/measure/$s; PREV_B=$I/revs/$s.kicad_pcb; LAST=$s
done
N=$(( $(echo "$LAST" | cut -c2-3 | sed 's/^0//') + 1 ))
S=$(printf "r%02d" $N)-$LABEL
W=$I/work/$S; M=$I/measure/$S; M2=$I/measure/$S-repaired
mkdir -p "$W" "$M"
log "$S start from $LAST $(sha256sum "$PREV_B" | cut -c1-16) producer $(basename "$PROD") $*"
sh "$PROD" "$PREV_B" "$W/applied.kicad_pcb" "$(cygpath -m "$PREV_M/partitions.json")" "$W" "$@" || { log "$S producer failed"; exit 1; }
[ -s "$W/applied.kicad_pcb" ] || { log "$S producer wrote no board"; exit 1; }
sh "$T/step_measure.sh" "$W/applied.kicad_pcb" "$M" "$I" > "$M/measure.out" 2>&1 || { log "$S measure failed"; exit 1; }
NOTE="Producer $(basename "$PROD") $* (sha256 $(sha256sum "$PROD" | cut -c1-16)); input $LAST."
$PY "$T/step_report.py" "$(cygpath -m "$PREV_M")" "$(cygpath -m "$M")" "$S" "$(cygpath -m "$M/report.json")" --note "$NOTE" > "$M/report.out" 2>&1
G=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['gate'])" "$(cygpath -m "$M/report.json")")
OUTB=$W/applied.kicad_pcb; OUTM=$M
if [ "$G" != "PASS" ]; then
  log "$S applied board adds DRC errors: removing only this step's error copper"
  sh "$T/heavym.sh" kicad "$KPY" "$T/remove_new_errors.py" "$PREV_B" "$W/applied.kicad_pcb" "$M/drc.json" "$W/out.kicad_pcb" \
     "$W/remove_new_errors.json" > "$W/remove.log" 2>&1 || { log "$S remove_new_errors failed"; exit 1; }
  log "$S targeted removal: $(tail -1 "$W/remove.log")"
  mkdir -p "$M2"
  sh "$T/step_measure.sh" "$W/out.kicad_pcb" "$M2" "$I" > "$M2/measure.out" 2>&1 || { log "$S measure (repaired) failed"; exit 1; }
  NOTE="$NOTE Then tools/remove_new_errors.py removed only this step's error copper (work/$S/remove_new_errors.json)."
  OUTB=$W/out.kicad_pcb; OUTM=$M2
fi
$PY "$T/step_report.py" "$(cygpath -m "$PREV_M")" "$(cygpath -m "$OUTM")" "$S" "$(cygpath -m "$OUTM/report.json")" --md "$IW/LEDGER-steps.md" \
  --note "$NOTE" | tee -a "$I/steps.log"
G=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['gate'])" "$(cygpath -m "$OUTM/report.json")")
NET=$($PY -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['connections_completed']-r['connections_lost'])" "$(cygpath -m "$OUTM/report.json")")
LOST=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['connections_lost'])" "$(cygpath -m "$OUTM/report.json")")
case "$LABEL" in
  cleanup*) if [ "$LOST" -gt 0 ]; then G="FAIL-lost-$LOST"; fi ;;   # clean-up steps must not lose any connection
esac
if [ "$G" = "PASS" ]; then
  # Final board/receipt check applies to every label, after any targeted cleanup.
  if ! $PY "$T/partition_guard.py" "$(cygpath -m "$PREV_M/partitions.json")" \
      "$(cygpath -m "$OUTM/partitions.json")" --before-board "$(cygpath -m "$PREV_B")" \
      --after-board "$(cygpath -m "$OUTB")" --out "$(cygpath -m "$OUTM/connectivity_guard.json")" \
      > "$OUTM/connectivity_guard.out" 2>&1; then
    log "$S REJECTED by connectivity guard (board unchanged; $OUTM/connectivity_guard.json)"
    exit 1
  fi
  [ "$OUTM" = "$M" ] || { rm -rf "$M.applied"; mv "$M" "$M.applied"; mv "$M2" "$M"; }
  cp "$OUTB" "$I/revs/$S.kicad_pcb"
  powershell.exe -NoProfile -Command "Set-ItemProperty -LiteralPath '$(cygpath -w "$I/revs/$S.kicad_pcb")' -Name IsReadOnly -Value \$true" > /dev/null 2>&1
  cp "$OUTB" "$I/board.kicad_pcb"
  log "$S COMMITTED $(sha256sum "$I/revs/$S.kicad_pcb" | cut -c1-64) net connections +$NET"
else
  log "$S REJECTED by the gate (gate=$G; board unchanged)"; exit 1
fi
