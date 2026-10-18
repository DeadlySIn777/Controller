"""Run the two host policy suites and capture their logs as CNC1 evidence.

Run from anywhere: python cnc1/tools/run_host_tests.py
Equivalent to running, from the workspace root,
  python -m unittest discover -s tests -p test_runtime_configuration.py -v > cnc1/evidence/runtime-service-tests.log 2>&1
  python -m unittest discover -s tests -p test_persistent_runtime.py -v > cnc1/evidence/persistent/host-policy-tests.log 2>&1
except that stdout and stderr are combined in order and written with LF line
endings (the logs are hashed byte-for-byte by record_evidence.py). These are
host tests with an adapter double, not actual-runtime evidence. Exits non-zero
if either suite fails; the log is still written.
"""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SUITES = (('test_runtime_configuration.py', 'cnc1/evidence/runtime-service-tests.log'),
          ('test_persistent_runtime.py', 'cnc1/evidence/persistent/host-policy-tests.log'))


def main():
    status = 0
    for pattern, log in SUITES:
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v'],
                                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        text = result.stdout.decode('utf-8').replace('\r\n', '\n')
        with open(ROOT / log, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(text)
        print(f'{pattern}: exit {result.returncode}; {text.strip().splitlines()[-1] if text.strip() else "no output"}')
        status = status or result.returncode
    return status


if __name__ == '__main__':
    sys.exit(main())
