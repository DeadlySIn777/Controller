"""Adversarial controls against the actual compiled startup C reader."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

probe,source=sys.argv[1:]
original=Path(source).read_text();manifest=json.loads(original);checks=[]
def check_case(name,text,accept=False):
    with tempfile.TemporaryDirectory(prefix="manifest-control-") as temporary:
        path=Path(temporary)/"input.json";path.write_text(text)
        result=subprocess.run([probe,str(path)],capture_output=True,text=True)
        passed=(result.returncode==0)==accept
        checks.append({"case":name,"status":"PASS" if passed else "FAIL","exit_code":result.returncode})
        if not passed:raise AssertionError(name)
def mutation(name,edit):
    candidate=copy.deepcopy(manifest);edit(candidate);check_case(name,json.dumps(candidate))
check_case("reviewed valid numeric baseline",original,True)
for name,body in (("leading zero",original.replace('"active_mask": 4095','"active_mask": 04095')),
                  ("hex integer",original.replace('"active_mask": 4095','"active_mask": 0xfff')),
                  ("trailing decimal",original.replace('"active_mask": 4095','"active_mask": 4095.')),
                  ("duplicate ordinary key",original.replace('"active_mask": 4095','"active_mask": 4095, "active_mask": 4095')),
                  ("escaped alias key",original.replace('"active_mask": 4095','"active_mask": 4095, "active_\\u006dask": 4095')),
                  ("trailing payload",original+' {}')):
    # The eight-channel fixture is also supported by deriving replacements.
    if body==original and name!="trailing payload":
        body=body.replace('"active_mask": 255',{'leading zero':'"active_mask": 0255','hex integer':'"active_mask": 0xff','trailing decimal':'"active_mask": 255.','duplicate ordinary key':'"active_mask": 255, "active_mask": 255','escaped alias key':'"active_mask": 255, "active_\\u006dask": 255'}[name])
    check_case(name,body)
mutation("physical backend forbidden",lambda m:m.update(physical_backend_allowed=True))
mutation("explicit simulation required",lambda m:m.update(simulation_only=False))
mutation("manufacturing promotion forbidden",lambda m:m.update(physical_commissioning_complete=True))
mutation("wrong endpoint build",lambda m:m['simulation_context'].update(gateware_build_id=1))
mutation("empty immutable digest",lambda m:m['simulation_context'].update(source_digest='0'*64))
mutation("nonfinite velocity",lambda m:m['cnc3_host']['max_velocity'].__setitem__(0,float('nan')))
mutation("timing too short",lambda m:m['cnc3_host']['timing_ticks'][0].__setitem__(0,99))
mutation("DDS high low carry bound",lambda m:m['cnc3_host']['max_velocity'].__setitem__(0,156.1))
mutation("unsupported fifth encoder",lambda m:m['cnc3_host'].update(required_encoder_mask=31))
mutation("fabricated expansion class",lambda m:m['cnc3_host'].update(encoder_expansion_class=1))
mutation("configured encoder period mismatch",lambda m:m['configured_io']['encoders'][0].update(counts_per_revolution=4000))
print(json.dumps({"status":"PASS","checks":checks}))
