"""Last two ordinary cases: real finite cap overlap at outer land edges."""
from pathlib import Path
P=Path(__file__).resolve().parent
t=(P/'nominate_CM51_real_land_edge_and_shared_ground_routes_r278.py').read_text()
t=t.replace('CM51-real-land-edge-shared-source-ordinary-ground-nominations-r278','CM51-final-two-real-positive-cap-land-edge-nominations-r281')
t=t.replace("s=s.replace('R276','R278')", "s=s.replace('R276','R281')")
t=t.replace("'CM51-physical-routed-ordinary-ground-fullbody-reference-FAIL-retained-r277/only-nominated-discrete.pkl'", "'CM51-final-two-extended-land-edge-source-window-nominations-r280/only-nominated-discrete.pkl'")
t=t.replace("for y in(-.3,.3)", "for y in(-.4,.4,-.425,.425)")
exec(compile(t,str(__file__),'exec'))
