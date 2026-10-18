"""Copied-header control: fault clearance must restart virtual idle recovery."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEST = r'''
#include "virtual_provider.hpp"
#include <cstdio>
int main(){
 cnc3_sim::VirtualWatchdog watchdog(550000,100);
 for(unsigned t=0;t<10000;++t)watchdog.tick(t,false,false,false);
 bool fault=false;for(unsigned t=10000;t<10010;++t)fault=watchdog.tick(t,false,false,true);
 bool at_clear=watchdog.tick(10010,false,false,false);
 bool at_99=false;for(unsigned t=10011;t<=10109;++t)at_99=watchdog.tick(t,false,false,false);
 bool at_100=watchdog.tick(10110,false,false,false);
 std::printf("{\"fault_observed_unhealthy\":%s,\"healthy_at_clear\":%s,\"healthy_at_99\":%s,\"healthy_at_100\":%s}\n",fault?"false":"true",at_clear?"true":"false",at_99?"true":"false",at_100?"true":"false");
}
'''
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unix(path):
 p=path.resolve().as_posix();return "/mnt/"+p[0].lower()+p[2:]
def main(out,fix_copy=False):
 out=out.resolve()
 if out.exists() or out.parent!=HERE:raise ValueError("fresh review output required")
 out.mkdir();sources=[ROOT/"cnc3_runtime/providers"/name for name in ("provider_ledger.hpp","virtual_provider.hpp")]
 before={str(p):sha(p) for p in sources}
 for path in sources:shutil.copyfile(path,out/path.name)
 if fix_copy:
  header=out/"virtual_provider.hpp";text=header.read_text(encoding="utf8")
  old="bool previous_request_ = false, previous_progress_ = false, healthy_ = true;"
  new="bool previous_request_ = false, previous_progress_ = false, previous_forced_fault_ = false, healthy_ = true;"
  assert text.count(old)==1;text=text.replace(old,new)
  old="if (!request && previous_request_) idle_since_ = now;"
  new="if (!request && (previous_request_ || (previous_forced_fault_ && !forced_fault))) idle_since_ = now;"
  assert text.count(old)==1;text=text.replace(old,new)
  old="previous_request_ = request; previous_progress_ = progress;"
  new="previous_request_ = request; previous_progress_ = progress; previous_forced_fault_ = forced_fault;"
  assert text.count(old)==1;text=text.replace(old,new)
  old="previous_request_ = previous_progress_ = false; healthy_ = true;"
  new="previous_request_ = previous_progress_ = previous_forced_fault_ = false; healthy_ = true;"
  assert text.count(old)==1;text=text.replace(old,new)
  header.write_text(text,encoding="utf8")
 (out/"control.cpp").write_text(TEST,encoding="utf8")
 build=["wsl","-d","GarciaMechBuilder","-u","root","--","clang++-22","-std=c++17","-Wall","-Wextra","-Werror","-O2",unix(out/"control.cpp"),"-o",unix(out/"control")]
 built=subprocess.run(build,capture_output=True,timeout=90);(out/"build.log").write_bytes(built.stdout+built.stderr)
 if built.returncode:raise RuntimeError("control compilation failed")
 command=["wsl","-d","GarciaMechBuilder","-u","root","--",unix(out/"control")]
 run=subprocess.run(command,capture_output=True,timeout=30);(out/"run.log").write_bytes(run.stdout+run.stderr)
 if run.returncode:raise RuntimeError("control execution failed")
 observation=json.loads(run.stdout)
 proper=observation["fault_observed_unhealthy"] and not observation["healthy_at_clear"] and not observation["healthy_at_99"] and observation["healthy_at_100"]
 receipt={"status":"RECOVERY_DELAY_HONORED" if proper else "IDLE_FAULT_CLEARANCE_RECOVERS_TOO_EARLY","observation":observation,"source_sha256":before,
  "inputs_unchanged":all(sha(Path(p))==v for p,v in before.items()),"build_command":build,"execution_command":command,
  "build_exit_code":built.returncode,"execution_exit_code":run.returncode,"artifact_sha256":{p.name:sha(p) for p in out.iterdir() if p.is_file()},
  "scope":"Actual public VirtualWatchdog execution compiled from copied headers; idle before/during fault; not physical timing or RTL integration","copied_candidate_fix":fix_copy,"physical_authority":False,"hardware_connections":0,"paid_api_calls":0,"runner_sha256":sha(Path(__file__))}
 (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf8");print(json.dumps({"status":receipt["status"],"observation":observation,"inputs_unchanged":receipt["inputs_unchanged"]}))
if __name__=="__main__":
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",type=Path,required=True);parser.add_argument("--fix-copy",action="store_true");args=parser.parse_args();main(args.out,args.fix_copy)
