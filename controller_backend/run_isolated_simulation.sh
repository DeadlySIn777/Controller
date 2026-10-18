#!/bin/sh
# Dedicated userspace LinuxCNC proof. No host devices or network enter the namespace.
set -eu
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
export CONTROLLER_LAB_ROOTFS="$task_root"
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
test -x "$task_root/usr/bin/linuxcnc"
test -f "$source_dir/profiles/sim/manifest.json"
CONTROLLER_LAB_RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4())')
export CONTROLLER_LAB_RUN_ID
mkdir -p "$task_root/work" "$source_dir/evidence"
# Start from the checked-in package only: discard the previous run's work copy
# (LinuxCNC parameter/position files, stale modules) and host-side caches.
rm -rf "$task_root/work/controller_backend"
cp -a "$source_dir" "$task_root/work/"
rm -rf "$task_root/work/controller_backend/evidence" "$task_root/work/controller_backend/.runtime"
rm -f "$task_root/work/controller_backend/profiles/sim/"*.var* "$task_root/work/controller_backend/profiles/sim/position.txt"
find "$task_root/work/controller_backend" -name __pycache__ -type d -prune -exec rm -rf {} +
mkdir -p "$task_root/work/controller_backend/evidence"
chown -R 1000:1000 "$task_root/work/controller_backend"
chmod 755 "$task_root/work/controller_backend/profiles/sim/display-client"
set +e
timeout 120 unshare --mount --pid --ipc --net --fork --kill-child sh -c '
    task_root=$CONTROLLER_LAB_ROOTFS
    mount -t proc proc "$task_root/proc"
    mount -t tmpfs tmpfs "$task_root/dev/shm"
    chmod 1777 "$task_root/dev/shm"
    chroot "$task_root" /usr/sbin/runuser -u cnclab -- /bin/sh -c "cd /work; unset DISPLAY; export PYTHONPATH=/work CONTROLLER_LAB_ALLOW_SIMULATION=1; exec linuxcnc -r /work/controller_backend/profiles/sim/controller.ini"
' > "$source_dir/evidence/linuxcnc-raw.log" 2>&1
result=$?
set -e
for output in "$task_root/work/controller_backend/evidence/"*.json; do
    test -f "$output" && cp "$output" "$source_dir/evidence/"
done
cp "$(dirname -- "$task_root")/debian-rootfs-source.json" "$source_dir/evidence/"
chroot "$task_root" dpkg-query -W > "$source_dir/evidence/debian-packages.tsv"
cat "$source_dir/evidence/linuxcnc-raw.log"
if [ "$result" -eq 0 ]; then
    python3 - "$source_dir/evidence/linuxcnc-simulation.json" <<'PY'
import json, os, sys
report = json.load(open(sys.argv[1]))
assert report["success"] is True and report["run_id"] == os.environ["CONTROLLER_LAB_RUN_ID"], "Missing fresh passing runtime evidence"
PY
fi
exit "$result"
