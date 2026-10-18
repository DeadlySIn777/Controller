"""Preserve the actual monitor aperture while opening a real ordinary pocket."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_U11025_exact_health_loop_ground_escape_r318.py').read_text(encoding='utf-8')
s=s.replace('U11025-exact-health-loop-ground-escape-r318','U11025-health-shutdown-monitor-aperture-preserved-r328')
s=s.replace('controller-field-r318-','controller-field-r328-')
s=s.replace("def write(f,v):", "DELETE |= {'49f60b2b-9524-48cc-b682-b86a22d65d69','3e1eb85c-6b18-4042-a060-a090b4ac915e'}\ndef write(f,v):")
s=s.replace("assert len(removed)==11 and all(t['net']==health and t['layer']=='F.Cu' and t['w']==.2 for t in removed)","shdn=next(t['net'] for t in removed if t['uuid']=='49f60b2b-9524-48cc-b682-b86a22d65d69');assert len(removed)==13 and all(t['net'] in (health,shdn) and t['layer']=='F.Cu' and t['w']==.2 for t in removed)")
s=s.replace("[(309.3565,153.908),(309.35,151.72),(310.75,151.72),(310.75,153.408),(311.5315,153.408)]","[(309.3565,153.908),(309.22,151.35),(310.4,151.35),(310.4,153.0),(311.5315,153.408)]")
s=s.replace("[(311.0315,154.558),(310.2,154.558),(310.2,152.0)]","[(311.0315,154.558),(310.2,154.558),(310.2,153.36),(309.8,153.36),(309.8,151.9)]")
s=s.replace("tracks=[]\n for net,pts", "tracks=[]\n routes.append((shdn,[(308.85,151.25),(308.5,151.25),(308.5,149.6),(310.05,149.6),(310.05,150.95)],.2,'shutdown-bend'))\n for net,pts")
s=s.replace("'new_tracks':6", "'new_tracks':len(tracks)")
s=s.replace("'exact_raw_health_net':health", "'exact_raw_shutdown_net':shdn,'shutdown_original_and_new_width_mm':.2,'shutdown_unchanged_outside_endpoints_mm':[[308.85,151.25],[310.05,150.95]],'exact_raw_health_net':health")
exec(compile(s,str(H/'construct_U11025_exact_health_loop_ground_escape_r318.py'),'exec'))
