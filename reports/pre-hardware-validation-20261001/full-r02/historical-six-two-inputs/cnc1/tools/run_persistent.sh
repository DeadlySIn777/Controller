#!/bin/sh
set -eu
task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}
export CONTROLLER_LAB_ROOTFS="$task_root"
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
project_dir=$(dirname "$source_dir")
test -f "$task_root/usr/lib/linuxcnc/modules/cnc1_sim.so"
mkdir -p "$source_dir/evidence/persistent" "$task_root/work/cnc1"
# Start from the checked-in package only. Keep build/ (build.sh output) and the
# run-id-keyed persistence-runs/, but discard the previous run's work copy:
# LinuxCNC parameter/position files, stale evidence JSON, orchestrators,
# controller_config modules and Python caches.
rm -rf "$task_root/work/cnc1/profiles" "$task_root/work/cnc1/evidence" "$task_root/work/controller_config"
rm -f "$task_root/work/cnc1/__init__.py" "$task_root/work/cnc1/integration.py" "$task_root/work/cnc1/persistent_integration.py"
find "$task_root/work/cnc1" -name __pycache__ -type d -prune -exec rm -rf {} +
mkdir -p "$task_root/work/cnc1/evidence/persistent"
cp -a "$source_dir/profiles" "$task_root/work/cnc1/"
rm -f "$task_root/work/cnc1/profiles/sim/"*.var* "$task_root/work/cnc1/profiles/sim/position.txt"
test ! -e "$task_root/work/cnc1/profiles/sim/simulation.var"
cp "$source_dir/__init__.py" "$source_dir/persistent_integration.py" "$task_root/work/cnc1/"
cp -a "$project_dir/controller_config" "$task_root/work/"
chmod 755 "$task_root/work/cnc1/profiles/sim/display-client"
CNC1_RUN_ID=$(python3 -c 'import uuid; print(uuid.uuid4())')
export CNC1_RUN_ID
CNC1_PROFILE_SHA256=$(python3 - "$task_root/work/cnc1/profiles/sim" <<'PY'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]);print(hashlib.sha256((p/'controller.ini').read_bytes()+(p/'simulation.hal').read_bytes()).hexdigest())
PY
)
export CNC1_PROFILE_SHA256
store_base=/work/cnc1/persistence-runs/$CNC1_RUN_ID
mkdir -p "$task_root$store_base/main"
chown -R 1000:1000 "$task_root/work/cnc1"
for scenario in initialize restart_interrupt recover missing corrupt foreign profile caps rollback; do
    CNC1_PERSISTENCE_SCENARIO=$scenario
    case "$scenario" in initialize|restart_interrupt|recover) directory=$store_base/main;; *) directory=$store_base/$scenario;; esac
    CNC1_PERSISTENCE_DIRECTORY=$directory
    export CNC1_PERSISTENCE_SCENARIO CNC1_PERSISTENCE_DIRECTORY
    if test "$scenario" = missing; then mkdir -p "$task_root$directory"; chown 1000:1000 "$task_root$directory"; fi
    set +e
    timeout 100 unshare --mount --pid --ipc --net --fork --kill-child sh -c '
        task_root=$CONTROLLER_LAB_ROOTFS
        mount -t proc proc "$task_root/proc"
        mount -t tmpfs tmpfs "$task_root/dev/shm"
        chmod 1777 "$task_root/dev/shm"
        chroot "$task_root" /usr/sbin/runuser -u cnclab -- /bin/sh -c "cd /work; unset DISPLAY CNC1_ALLOW_VOLATILE_CONFIG; export PYTHONPATH=/work CNC1_ALLOW_RTL_SIMULATION=1; exec linuxcnc -r /work/cnc1/profiles/sim/controller.ini"
    ' > "$source_dir/evidence/persistent/$scenario.log" 2>&1
    result=$?
    set -e
    cat "$source_dir/evidence/persistent/$scenario.log"
    test "$result" -eq 0
    cp "$task_root/work/cnc1/evidence/persistent/$scenario.json" "$source_dir/evidence/persistent/"
    python3 - "$source_dir/evidence/persistent/$scenario.json" <<'PY'
import json,os,sys
r=json.load(open(sys.argv[1]));assert r['success'] and r['run_id']==os.environ['CNC1_RUN_ID'],r
PY
    if test "$scenario" = initialize; then cp "$task_root$store_base/main/authority.json" "$task_root$store_base/old-authority.json"; fi
    if test "$scenario" = recover; then
        python3 - "$task_root$store_base" <<'PY'
import json,pathlib,sys,shutil,hashlib
p=pathlib.Path(sys.argv[1])
def seal(value):
    value.pop('sha256',None)
    value['sha256']=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    return value
for name in ('corrupt','foreign','profile','caps','rollback'):
    d=p/name;d.mkdir()
    shutil.copy2(p/'main/authority.json',d/'authority.json');shutil.copy2(p/'main/generation-witness.json',d/'generation-witness.json')
    if name=='corrupt':(d/'authority.json').write_text('{corrupt');continue
    if name=='rollback':shutil.copy2(p/'old-authority.json',d/'authority.json');continue
    value=json.loads((d/'authority.json').read_text());record=value['committed']
    if name=='foreign':record['machine_id']='393e2a66-b026-4543-943e-8bff02e70fa1'
    if name=='profile':record['profile_sha256']='b'*64
    if name=='caps':record['capabilities']['step_channels']=8
    value['committed']=seal(record);(d/'authority.json').write_text(json.dumps(seal(value)))
PY
        chown -R 1000:1000 "$task_root$store_base"
    fi
done
cp "$task_root$store_base/main/authority.json" "$source_dir/evidence/persistent/final-authority.json"
cp "$task_root$store_base/main/generation-witness.json" "$source_dir/evidence/persistent/final-witness.json"
python3 - "$source_dir/evidence/persistent" <<'PY'
import json,os,pathlib,sys
p=pathlib.Path(sys.argv[1]);names=('initialize','restart_interrupt','recover','missing','corrupt','foreign','profile','caps','rollback')
runs=[json.loads((p/(name+'.json')).read_text()) for name in names]
report={'run_id':os.environ['CNC1_RUN_ID'],'profile_sha256':os.environ['CNC1_PROFILE_SHA256'],'separate_linuxcnc_launches':len(runs),'checks':sum(len(r['checks']) for r in runs),'success':all(r['success'] for r in runs),'scenarios':[{'scenario':r['scenario'],'checks':len(r['checks']),'wall_seconds':r['wall_seconds'],'simulated_seconds':r['simulated_seconds']} for r in runs]}
(p/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
PY
