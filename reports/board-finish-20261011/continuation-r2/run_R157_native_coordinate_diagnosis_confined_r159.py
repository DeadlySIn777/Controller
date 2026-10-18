"""Use the existing test-only KiCad slot; inherit the host CPU reservation."""
import os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
cmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(H/'diagnose_R157_exact_native_zone_coordinates_r158.py')]
raise SystemExit(subprocess.run(cmd,env=env).returncode)
