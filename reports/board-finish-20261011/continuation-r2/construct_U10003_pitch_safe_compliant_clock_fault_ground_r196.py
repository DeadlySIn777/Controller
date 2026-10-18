"""Fresh R195-bound successor; preserve failed R192/R194 diagnostics."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'construct_U10003_exact_compliant_clock_fault_ground_r192.py';code=source.read_text().replace('r192','r196').replace('r191','r195').replace('1d089c22833bf2acfb18118df07e44f5966a5049fc6082899a7ac2e086f21470','cd97621c39300992c764d627920a8ecaec7ff77405b3c9141ec4a22dc7bb1fe9')
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
