"""Fresh successor using actual physical pin and layer-key schema."""
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'diagnose_U10003_exact_logic_wall_native_topology_r205.py'
code=src.read_text().replace('native-topology-r205','native-topology-r206').replace("r['num']","r['pin']").replace('keys=K.F.discrete_keys','keys=K.keys').replace("{('track',uid)}","{k for k in keys(xs)if k[0]=='track'and k[1]==uid}")
compile(code,str(src),'exec');exec(compile(code,str(src),'exec'))
