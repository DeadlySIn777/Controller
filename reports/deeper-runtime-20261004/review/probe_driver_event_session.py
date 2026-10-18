"""Independent copied-C control of the event dedup/ACK boundary after SYNC."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FILES = ["cnc3.c", "cnc3.h", "cnc3_proto.c", "cnc3_proto.h", "cnc3_layout.h", "cnc3_proto_types.h", "cnc3_rules.h"]
TEST = r'''
#include "cnc3.h"
#include <stdio.h>
#include <string.h>
struct endpoint { unsigned post_sync; };
static int exchange(void *context, enum cnc3_cs cs, const uint8_t *tx, uint8_t *rx, size_t n) {
    (void)tx;struct endpoint *e=context;
    if(cs!=CNC3_CS_CMD || n!=CNC3_CS_CMD_BYTES)return -1;
    struct cnc3_status s;memset(&s,0,sizeof s);
    s.session=e->post_sync?18:17;s.event_seq=1;s.event_type=1;
    s.event_source=e->post_sync?1:0;s.event_ticks=e->post_sync?200:100;
    s.telemetry_source=0xff;cnc3_encode_cns3(rx,&s);return 0;
}
int main(void) {
    struct endpoint endpoint={0};struct cnc3_config config;memset(&config,0,sizeof config);
    config.axis_mask=1;config.scale[0]=640;config.maximum_velocity[0]=10;
    for(unsigned i=0;i<4;++i)config.timing[0][i]=250;
    struct cnc3_transport transport={&endpoint,exchange,CNC3_SIM_TRANSPORT_ID};
    struct cnc3_driver driver;cnc3_init(&driver,transport,&config,17);
    driver.discovered=1;driver.state=CNC3_OFF;driver.watchdog_ns=5000000;
    cnc3_write(&driver,0,1000000);
    if(driver.events_stored!=1||driver.probe_events[0]!=1||driver.event_ack!=1)return 2;
    driver.reset=1;cnc3_write(&driver,1000000,1000000);
    unsigned ack_after_sync=driver.event_ack,dedup_after_sync=driver.last_event_seq;
    endpoint.post_sync=1;driver.reset=0;cnc3_write(&driver,2000000,1000000);
    printf("{\"events_stored\":%llu,\"old_probe_events\":%llu,\"new_probe_events\":%llu,\"ack_after_sync\":%u,\"dedup_after_sync\":%u,\"event_ack\":%u,\"history_preserved\":%s,\"new_event_stored\":%s}\n",
      (unsigned long long)driver.events_stored,(unsigned long long)driver.probe_events[0],
      (unsigned long long)driver.probe_events[1],ack_after_sync,dedup_after_sync,driver.event_ack,
      driver.probe_events[0]==1?"true":"false",driver.probe_events[1]==1?"true":"false");
    return 0;
}
'''

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def unix(path):
    p = path.resolve().as_posix()
    return "/mnt/" + p[0].lower() + p[2:]

def main(output):
    output = output.resolve()
    if output.exists() or output.parent != HERE:
        raise ValueError("fresh independent review output in this directory required")
    output.mkdir()
    candidates = {"retained_pre_fix": ROOT / "reports/deeper-runtime-20261004/host/driver-r04/source/cnc3_runtime/src",
                  "current_fixed": ROOT / "cnc3_runtime/src"}
    before = {str(p): sha(p) for source in candidates.values() for p in (source / name for name in FILES)}
    results = {}
    for label, source in candidates.items():
        destination = output / label
        destination.mkdir()
        for name in FILES:
            shutil.copyfile(source / name, destination / name)
        (destination / "control.c").write_text(TEST, encoding="utf8")
        args = ["wsl", "-d", "GarciaMechBuilder", "-u", "root", "--", "clang-22", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", unix(destination / "control.c"), unix(destination / "cnc3.c"), unix(destination / "cnc3_proto.c"), "-lm", "-o", unix(destination / "control")]
        built = subprocess.run(args, capture_output=True, timeout=90)
        (destination / "build.log").write_bytes(built.stdout + built.stderr)
        if built.returncode:
            raise RuntimeError(label + " control failed compilation")
        command = ["wsl", "-d", "GarciaMechBuilder", "-u", "root", "--", unix(destination / "control")]
        executed = subprocess.run(command, capture_output=True, timeout=30)
        (destination / "run.log").write_bytes(executed.stdout + executed.stderr)
        if executed.returncode:
            raise RuntimeError(label + " control failed execution")
        results[label] = {"command": command, "source_sha256": {name: sha(destination / name) for name in FILES}, "build_command": args,
                          "build_exit_code": built.returncode, "execution_exit_code": executed.returncode,
                          "observation": json.loads(executed.stdout), "test_sha256": sha(destination / "control.c"),
                          "binary_sha256": sha(destination / "control"), "build_log_sha256": sha(destination / "build.log"), "run_log_sha256": sha(destination / "run.log")}
    old, fixed = (results[name]["observation"] for name in candidates)
    passed = (not old["new_event_stored"] and old["ack_after_sync"] == 1 and old["dedup_after_sync"] == 1 and
              fixed["new_event_stored"] and fixed["ack_after_sync"] == 0 and fixed["dedup_after_sync"] == 0 and
              fixed["history_preserved"] and fixed["events_stored"] == 2)
    receipt = {"status": "PASS" if passed else "FAIL", "scope": "Actual public cnc3_write() compiled with exact copied C driver/protocol and inert encoded endpoint responses; not actual SPI/RTL or hardware qualification",
               "control": "Pre-SYNC status carries prior event1; after SYNC a different event1 in new session must be stored, prior log retained, and ACK reset0 before the next FB_READ",
               "candidates": results, "inputs_unchanged": all(sha(Path(name)) == digest for name, digest in before.items()),
               "source_sha256": before, "physical_authority": False, "paid_api_calls": 0, "hardware_connections": 0,
               "runner_sha256": sha(Path(__file__))}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": receipt["status"], "old": old, "fixed": fixed, "inputs_unchanged": receipt["inputs_unchanged"]}))
    return 0 if passed and receipt["inputs_unchanged"] else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    raise SystemExit(main(parser.parse_args().out))
