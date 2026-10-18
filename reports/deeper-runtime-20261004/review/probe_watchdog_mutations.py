"""Compile the report-local recovery candidate and two exact timing mutations."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):
 s=p.resolve().as_posix();return "/mnt/"+s[0].lower()+s[2:]
def main(candidate,out):
 candidate,out=candidate.resolve(),out.resolve()
 if candidate.parent!=HERE or out.exists() or out.parent!=HERE:raise ValueError("report-local fresh output required")
 before={p.name:sha(p) for p in candidate.iterdir() if p.is_file()};out.mkdir()
 test=(candidate/"control.cpp").read_text(encoding="utf8")
 prefix,suffix=test.rsplit("}",1)
 test=prefix+" return (!fault && !at_clear && !at_99 && at_100) ? 0 : 1;\n}"+suffix
 variants={"candidate":None,
  "wrong_fault_edge":("previous_forced_fault_ && !forced_fault","previous_forced_fault_ && forced_fault"),
  "late_recovery_at_100":("now - idle_since_ >= recovery_","now - idle_since_ > recovery_")}
 observations={}
 for name,change in variants.items():
  directory=out/name;directory.mkdir()
  for filename in ("provider_ledger.hpp","virtual_provider.hpp"):shutil.copyfile(candidate/filename,directory/filename)
  if change:
   path=directory/"virtual_provider.hpp";body=path.read_text(encoding="utf8");assert body.count(change[0])==1
   path.write_text(body.replace(*change),encoding="utf8")
  (directory/"control.cpp").write_text(test,encoding="utf8")
  command=["wsl","-d","GarciaMechBuilder","-u","root","--","clang++-22","-std=c++17","-Wall","-Wextra","-Werror","-O2",unix(directory/"control.cpp"),"-o",unix(directory/"control")]
  compiled=subprocess.run(command,capture_output=True,timeout=90);(directory/"build.log").write_bytes(compiled.stdout+compiled.stderr)
  if compiled.returncode:raise RuntimeError(name+" failed strict compilation; not counted detected")
  run_command=["wsl","-d","GarciaMechBuilder","-u","root","--",unix(directory/"control")]
  executed=subprocess.run(run_command,capture_output=True,timeout=30);(directory/"run.log").write_bytes(executed.stdout+executed.stderr)
  observations[name]={"build_command":command,"run_command":run_command,"build_exit_code":compiled.returncode,"run_exit_code":executed.returncode,
   "observation":json.loads(executed.stdout),"mutation":change,"artifact_sha256":{p.name:sha(p) for p in directory.iterdir() if p.is_file()}}
 passed=observations["candidate"]["run_exit_code"]==0 and all(observations[n]["run_exit_code"]==1 for n in variants if n!="candidate")
 receipt={"status":"PASS" if passed else "FAIL","copied_candidate_source_sha256":before,"candidate_unchanged":all(sha(candidate/n)==v for n,v in before.items()),
  "variants":observations,"scope":"Compiled report-local provider timing candidate and two mutations; no main-source adoption/physical qualification","physical_authority":False,"hardware_connections":0,"paid_api_calls":0,"runner_sha256":sha(Path(__file__))}
 (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf8")
 print(json.dumps({"status":receipt["status"],"compiled_variants":len(variants),"detected_mutations":2 if passed else 0,"candidate_unchanged":receipt["candidate_unchanged"]}))
 return 0 if passed else 1
if __name__=="__main__":
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--candidate",type=Path,required=True);parser.add_argument("--out",type=Path,required=True);args=parser.parse_args();raise SystemExit(main(args.candidate,args.out))
