"""Explicit two-track shutdown bend + complete health loop; endpoints retained."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_U11025_exact_health_loop_ground_escape_r318.py').read_text(encoding='utf-8')
s=s.replace('U11025-exact-health-loop-ground-escape-r318','U11025-health-shutdown-upper-pocket-r324')
s=s.replace('controller-field-r318-','controller-field-r324-')
s=s.replace("def write(f,v):", "DELETE |= {'49f60b2b-9524-48cc-b682-b86a22d65d69','3e1eb85c-6b18-4042-a060-a090b4ac915e'}\ndef write(f,v):")
s=s.replace("assert len(removed)==11 and all(t['net']==health and t['layer']=='F.Cu' and t['w']==.2 for t in removed)","shdn=next(t['net'] for t in removed if t['uuid']=='49f60b2b-9524-48cc-b682-b86a22d65d69');assert len(removed)==13 and all(t['net'] in (health,shdn) and t['layer']=='F.Cu' and t['w']==.2 for t in removed)")
s=s.replace('151.72','151.35').replace('(310.2,152.0)','(310.2,151.9)')
s=s.replace("tracks=[]\n for net,pts", "tracks=[]\n routes.append((shdn,[(308.85,151.25),(308.85,150.84),(310.05,150.84),(310.05,150.95)],.2,'shutdown-bend'))\n for net,pts")
s=s.replace("'new_tracks':6", "'new_tracks':len(tracks)")
s=s.replace("'exact_raw_health_net':health", "'exact_raw_shutdown_net':shdn,'shutdown_original_and_new_width_mm':.2,'shutdown_unchanged_outside_endpoints_mm':[[308.85,151.25],[310.05,150.95]],'exact_raw_health_net':health")
exec(compile(s,str(H/'construct_U11025_exact_health_loop_ground_escape_r318.py'),'exec'))
