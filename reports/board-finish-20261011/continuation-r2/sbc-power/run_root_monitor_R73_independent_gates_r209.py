"""One confined host slot for the requested root monitor independent gates."""
from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parent;mp=P.parent/'SAFE-monitor-real-source-reference-patch-r73/model.pkl'
for name in ('audit_root_monitor_R73_all_geometry_r206.py','audit_root_monitor_R73_owned_copper_r207.py','audit_root_monitor_R73_contacts_sources_refs_r208.py'):
 f=P/name;print('R73_INDEPENDENT_GATE_START',name,flush=True);sys.argv=[str(f),str(mp)];runpy.run_path(str(f),run_name='__main__')
