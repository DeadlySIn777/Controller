"""R274 successor: first try the connector inter-row interior, preserve R274."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM51_ordinary_outward_ground_fanouts_r274.py').read_text()
s=s.replace('CM51-ordinary-outward-ground-fanout-nominations-r274','CM51-ordinary-inward-first-ground-fanout-nominations-r275').replace('R274','R275')
s=s.replace("for off in(.75,1.,1.25,1.5,1.75,2.,2.5,3.,4.,5.,7.5,10.):", "for off in(-.75,-1.,-1.25,-1.5,-1.75,-2.,.75,1.,1.25,1.5,1.75,2.,2.5,3.):")
# The exact frozen R271 source groups are nomination authority only. A latest
# joint host source/contact/reference rebind remains required before integration.
exec(compile(s,str(__file__),'exec'))
