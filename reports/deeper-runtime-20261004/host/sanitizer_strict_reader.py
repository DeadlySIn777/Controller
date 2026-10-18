"""Do not mistake sanitizer crashes for expected configuration refusals."""
import json
from pathlib import Path
import runpy
import subprocess
import sys

script,probe,manifest=sys.argv[1:]
real_run=subprocess.run
observations=[]
def strict_run(*args,**kwargs):
    result=real_run(*args,**kwargs)
    if result.returncode not in (0,1):raise AssertionError(f'unexpected child exit {result.returncode}: {result.stderr}')
    expected='ACCEPTED' if result.returncode==0 else 'REFUSED'
    if result.stdout.strip()!=expected or result.stderr:
        raise AssertionError(f'configuration result or sanitizer diagnostic: {result.stdout!r} {result.stderr!r}')
    observations.append({'exit_code':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr})
    return result
subprocess.run=strict_run
sys.argv=[script,probe,manifest]
runpy.run_path(script,run_name='__main__')
assert len(observations)==18
print(json.dumps({'status':'PASS','strict_child_signatures':observations,'sanitizer_diagnostics':0}))
