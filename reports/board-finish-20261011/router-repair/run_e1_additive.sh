#!/bin/sh
# Explicit root-authorized native runner. It never starts a GPU or alters E1/shared boards/tools.
# sh run_e1_additive.sh <exact-base-board> <native-base-partitions.json> <isolated-work-dir>
set -eu
BASE=$1; PART=$2; W=$3
T=/z/pcb-runs/claude-finish/tools
P=/z/pcb-runs/claude-finish/integrate
S=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
KPY="/c/Program Files/KiCad/10.0/bin/python.exe"
KCLI="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
PY=C:/Python314/python.exe
HV=${HEAVY:-heavyt.sh}
mkdir -p "$W/base" "$W/preflight" "$W/filtered"
W=$(CDPATH= cd -- "$W" && pwd)
case "$W" in
  "$S"/*) ;;
  *) printf 'Work directory must be an isolated child of %s\n' "$S" >&2; exit 2 ;;
esac
TIMES="$W/times.tsv"
timed() {
  label=$1; shift
  started=$(date +%s)
  set +e
  "$@"
  rc=$?
  set -e
  printf '%s\t%s\t%s\t%s\n' "$label" "$started" "$(date +%s)" "$rc" >> "$TIMES"
  return "$rc"
}
for d in base preflight filtered; do
  cp "$P/board.kicad_pro.good" "$W/$d/board.kicad_pro"
  cp "$P/board.kicad_dru" "$P/fp-lib-table" "$P/sch.net" "$W/$d/"
  for lib in "$P"/*.pretty; do
    [ -d "$W/$d/$(basename "$lib")" ] || cp -r "$lib" "$W/$d/"
  done
done
cp "$BASE" "$W/base/board.kicad_pcb"
chmod u+w "$W/base/board.kicad_pcb"
timed collect "$PY" -B "$S/extract_e1.py" --base-board "$(cygpath -m "$W/base/board.kicad_pcb")" \
  --partitions "$(cygpath -m "$PART")" --jobs "$(cygpath -m "$S/e1-frozen/jobs.json")" \
  --checkpoint "$(cygpath -m "$S/e1-frozen/checkpoint.json")" --catalog "$(cygpath -m "$S/source-catalog.json")" \
  --out "$(cygpath -m "$W/manifest.json")" > "$W/collect.log" 2>&1
timed stage sh "$T/$HV" kicad "$KPY" "$S/native_group_gate.py" stage --board "$W/base/board.kicad_pcb" \
  --manifest "$W/manifest.json" --ledger "$W/ledger.json" --out "$W/preflight/board.kicad_pcb" \
  --receipt "$W/stage-receipt.json" > "$W/stage.log" 2>&1
# Native DRC runs only on the prospective disposable copy; every original UUID is retained.
timed native-preflight sh "$T/$HV" kicad "$KCLI" pcb drc --format json --severity-all --all-track-errors \
  --refill-zones --save-board -o "$W/preflight/drc.json" "$W/preflight/board.kicad_pcb" > "$W/preflight.log" 2>&1
timed filter sh "$T/$HV" kicad "$KPY" "$S/native_group_gate.py" filter --board "$W/preflight/board.kicad_pcb" \
  --manifest "$W/manifest.json" --ledger "$W/ledger.json" --drc "$W/preflight/drc.json" \
  --out "$W/filtered/board.kicad_pcb" --receipt "$W/filter-receipt.json" > "$W/filter.log" 2>&1
timed measure env HEAVY="$HV" sh "$T/step_measure.sh" "$W/filtered/board.kicad_pcb" "$W/measure" "$P" > "$W/measure.log" 2>&1
timed partition-diff "$PY" -B "$T/partition_diff.py" "$(cygpath -m "$PART")" \
  "$(cygpath -m "$W/measure/partitions.json")" "$(cygpath -m "$W/partition_diff.json")" > "$W/partition-diff.log" 2>&1
printf 'E1 additive candidate measured; review filter-receipt.json, measure/summary.json and partition_diff.json. No adoption performed.\n'
