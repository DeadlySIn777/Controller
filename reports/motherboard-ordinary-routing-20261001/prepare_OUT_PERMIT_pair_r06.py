"""Use unchanged ordinary manifest for another actual short permission pair."""
from pathlib import Path
p=Path(__file__).parent;s=(p/'route_root81_one_pair_doglegs_r05.py').read_text()
s=s.replace("{'U17003.6','U17004.5'}","{'R14401.1','U14402.1'}")
s=s.replace("assert name=='/motherboard_status/OBS8_INVERTED'","assert name=='/mc_permission/OUT_PERMIT'")
s=s.replace('motherboard-OBS8-common-In1-candidate.kicad_pcb','motherboard-OUT-PERMIT-common-In1-candidate.kicad_pcb')
(p/'route_root81_OUT_PERMIT_pair_r06.py').write_text(s);compile(s,str(p/'route_root81_OUT_PERMIT_pair_r06.py'),'exec')
