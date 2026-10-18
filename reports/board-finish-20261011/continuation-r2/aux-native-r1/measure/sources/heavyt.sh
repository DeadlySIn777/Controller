#!/bin/sh
# heavyt.sh = heavy.sh with SEPARATE slots (.slots/test-<class>, 1 each) for Claude's own tool tests (added 11 Oct 04:35), so
# agents testing tools can never starve it (added 11 Oct 01:10). The CPU governor caps everything together.
# Cooperative slot limiter for heavy pipeline commands (added 10 Oct 2026 after the CPU-overload crash).
#   sh Z:/pcb-runs/claude-finish/tools/heavy.sh <class> <command> [args...]
# Classes and slots: kicad = 2 at a time (kicad-cli DRC/export, KiCad python zone refills, board load/save
# scripts), gpu = 1 (torch/GPU routers and solvers), wsl = 1 (Icarus/Verilator builds), cpu = 2 (other
# multi-threaded numeric jobs). The command waits for a free slot, runs in the foreground, and the slot is
# released when it ends (also after a crash: slots whose owner pid is dead are reclaimed). The CPU governor
# (tools/cpu_governor.ps1) caps the total CPU independently; this limiter keeps memory and GPU use sane.
set -u
CLASS=${1:?class}; shift
case "$CLASS" in
  kicad) N=1 ;; gpu) N=1 ;; wsl) N=1 ;; cpu) N=1 ;;
  *) echo "heavy.sh: unknown class $CLASS" >&2; exit 2 ;;
esac
DIR=/z/pcb-runs/claude-finish/.slots/test-$CLASS
mkdir -p "$DIR"
SLOT=""
while [ -z "$SLOT" ]; do
  i=1
  while [ $i -le $N ]; do
    S="$DIR/slot$i"
    if mkdir "$S" 2>/dev/null; then
      echo $$ > "$S/pid"; SLOT=$S; break
    fi
    # reclaim a slot whose owner died
    OWNER=$(cat "$S/pid" 2>/dev/null || echo "")
    if [ -n "$OWNER" ] && ! kill -0 "$OWNER" 2>/dev/null; then rm -rf "$S"; continue; fi
    i=$((i + 1))
  done
  [ -n "$SLOT" ] || sleep 5
done
trap 'rm -rf "$SLOT"' EXIT INT TERM
"$@"
RC=$?
exit $RC
