"""Preserve R278; extend only the final two finite land-edge route windows."""
from pathlib import Path
P=Path(__file__).resolve().parent
t=(P/'nominate_CM51_real_land_edge_and_shared_ground_routes_r278.py').read_text()
t=t.replace('CM51-real-land-edge-shared-source-ordinary-ground-nominations-r278','CM51-final-two-extended-land-edge-source-window-nominations-r280')
t=t.replace("s=s.replace('R276','R278')", "s=s.replace('R276','R280')")
t=t.replace("'CM51-physical-routed-ordinary-ground-fullbody-reference-FAIL-retained-r277/only-nominated-discrete.pkl'", "'CM51-real-land-edge-shared-source-ordinary-ground-nominations-r278/only-nominated-discrete.pkl'")
t=t.replace("for r in(2.,4.,8.)", "for r in(16.,25.,40.)")
exec(compile(t,str(__file__),'exec'))
