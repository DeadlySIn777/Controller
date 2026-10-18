"""Seal the independent read-only configuration-contract review."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 output=HERE/"setup-review-r01.json"
 if output.exists():raise ValueError("sealed review must not be overwritten")
 execution_path=ROOT/"reports/deeper-runtime-20261004/setup/run-r06/receipt.json"
 execution=json.loads(execution_path.read_text(encoding="utf8"))
 control_path=HERE/"source-closure-control-r02.json"
 control=json.loads(control_path.read_text(encoding="utf8"))
 bindings=[]
 for name,digest in execution["source_sha256"].items():
  path=ROOT/name;assert sha(path)==digest and execution["source_sha256_after"][name]==digest
  bindings.append({"path":name,"sha256":digest,"matches_root_execution_before_and_after":True})
 for name,digest in control["source_sha256"].items():
  path=Path(name);assert sha(path)==digest
  if path.relative_to(ROOT).as_posix() not in {b["path"] for b in bindings}:
   bindings.append({"path":path.relative_to(ROOT).as_posix(),"sha256":digest,"matches_independent_control":True})
 log=execution_path.with_name("tests.log");assert sha(log)==execution["log_sha256"]
 assert execution["status"]=="PASS" and execution["tests_run"]==15 and execution["failures"]==execution["errors"]==execution["skipped"]==0
 assert control["status"]=="LIBRARY_REJECTED_SELF_SELECTED_SUBSET" and control["complete_expected_closure_accepted"]
 assert control["trusted_expected_closure_argument_is_required"] and control["trusted_runtime_closure_binds_controller_lab_initializer"] and control["inputs_unchanged"]
 artifacts=[execution_path,log,control_path,HERE/"probe_configuration_source_closure.py"]
 receipt={"schema_version":1,"kind":"independent_sim2_configuration_contract_review","utc":datetime.now(timezone.utc).isoformat(),"status":"PASS_WITHIN_READ_ONLY_SETUP_SCOPE",
  "reviewed_source_sha256":bindings,"artifact_sha256":{p.relative_to(ROOT).as_posix():sha(p) for p in artifacts},
  "execution_attribution":{"root_captured_tests":15,"reviewer_reran_full_suite":False,"reviewer_executed_inert_library_source_closure_control":True},
  "findings":[{"issue":"Library previously allowed its manifest to self-select the source set; trusted runtime set also omitted controller_lab/__init__.py","resolution":"Root requires expected_source_files as a mandatory keyword and includes executed package initializer; independent two-source resealed subset control rejects it while accepting full closure","current_status":"CLOSED"}],
  "reviewed_contracts":["Exact store/epoch/revision/generation/configuration/draft binding from one atomic saved snapshot; fresh verification refuses intervening settings change",
   "Saved derived mechanics/wiring recomputed independently; disconnected guards must exactly match",
   "Nanosecond timing rounds upward; 100..1023 core ticks and conservative DDS carry/period limits refuse excess without clamping",
   "Inch-to-mm scale/velocity conversion preserves chosen mechanics; numeric resource indices remain exact through M9/M10 ordering",
   "Explicit unmeasured encoder N to motor N with one AB edge per STEP and matching counts; unsupported ratio/polarity rejected",
   "Source-set closure is supplied by the trusted runner, bounded/canonical/relative and full-SHA bound; resealed altered manifests fail fresh recomputation",
   "CLI writes only a new report manifest; verification never changes setup; existing-output refusal covered by captured root test"],
  "boundaries":["The 32-bit identifiers are context selectors, not authentication; this review does not authenticate arbitrary caller-supplied verifier scripts or source roots",
   "Reviewed user selections and lab encoder mapping are unmeasured; generated host settings do not qualify machine kinematics, electrical ratings, physical readiness or manufacture",
   "This review binds current setup sources and root execution evidence; actual C driver/SPI/RTL/provider and LinuxCNC task qualification are separately scoped"],
  "source_edits_by_reviewer":0,"existing_settings_changes_by_reviewer":0,"physical_authority":False,"physical_commissioning_complete":False,"hardware_connections":0,"paid_api_calls":0,"runner_sha256":sha(Path(__file__))}
 with output.open("x",encoding="utf8") as file:json.dump(receipt,file,indent=2);file.write("\n")
 print(json.dumps({"status":receipt["status"],"sources_checked":len(bindings),"sha256":sha(output)}))
if __name__=="__main__":main()
