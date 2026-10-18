#!/bin/sh
set -eu
task_root=/root/.cache/controller-lab-linuxcnc/rootfs
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test -f "$task_root/usr/lib/linuxcnc/modules/cnc1_sim.so"
mkdir -p "$source_dir/evidence"
cp -a "$source_dir/profiles" "$task_root/work/cnc1/"
cp "$source_dir/__init__.py" "$source_dir/integration.py" "$task_root/work/cnc1/"
cp -a "$(dirname "$source_dir")/controller_config" "$task_root/work/"
mkdir -p "$task_root/work/cnc1/evidence"
chown -R 1000:1000 "$task_root/work/cnc1"
chmod 755 "$task_root/work/cnc1/profiles/sim/display-client"
CNC1_RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4())')
export CNC1_RUN_ID
set +e
timeout 150 unshare --mount --pid --ipc --net --fork --kill-child sh -c '
    task_root=/root/.cache/controller-lab-linuxcnc/rootfs
    mount -t proc proc "$task_root/proc"
    mount -t tmpfs tmpfs "$task_root/dev/shm"
    chmod 1777 "$task_root/dev/shm"
    chroot "$task_root" /usr/sbin/runuser -u cnclab -- /bin/sh -c "cd /work; unset DISPLAY; export PYTHONPATH=/work CNC1_ALLOW_RTL_SIMULATION=1; exec linuxcnc -r /work/cnc1/profiles/sim/controller.ini"
' > "$source_dir/evidence/linuxcnc.log" 2>&1
result=$?
set -e
for output in "$task_root/work/cnc1/evidence/"*.json; do test -f "$output" && cp "$output" "$source_dir/evidence/"; done
cat "$source_dir/evidence/linuxcnc.log"
test "$result" -eq 0
python3 - "$source_dir/evidence/linuxcnc.json" <<'PY'
import json,os,sys
r=json.load(open(sys.argv[1])); assert r['success'] and r['run_id']==os.environ['CNC1_RUN_ID'],r
PY
