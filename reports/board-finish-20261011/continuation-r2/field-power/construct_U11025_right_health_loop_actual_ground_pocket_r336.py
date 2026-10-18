"""Preserve shutdown/monitor entirely; extend only the exact right health wall."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_U11025_exact_health_loop_ground_escape_r318.py').read_text(encoding='utf-8')
s=s.replace('U11025-exact-health-loop-ground-escape-r318','U11025-right-health-loop-actual-ground-pocket-r336')
s=s.replace('controller-field-r318-','controller-field-r336-')
a=s.index('DELETE=');end=s.index('\ndef write',a)
s=s[:a]+"DELETE={'8325bd7c-2971-40a7-88e4-4d24b2404b71','d26a6078-f4a0-44b8-9138-ddf692940b64','e70df82a-5f2d-4af2-9dc0-0c2045253f14','73485ae6-bd09-4e06-b6dc-618c037f55c1','e4373f43-4bf8-4252-afdf-b11a56a2c998','ae1f7ba5-1068-4183-b487-c3dba73482b0','e3944b89-76a2-41d2-b5bf-3a0feec1b288','6b8c17ea-bd34-40f4-8e00-7fdd201ac1f3','b45815b7-39e2-4242-8d07-24ca4e0db339'}"+s[end:]
s=s.replace('len(removed)==11','len(removed)==9')
s=s.replace("[(309.3565,153.908),(309.35,151.72),(310.75,151.72),(310.75,153.408),(311.5315,153.408)]","[(311.5315,153.408),(312.53,154.1),(312.53,155.708),(311.5315,155.708)]")
s=s.replace("[(311.0315,154.558),(310.2,154.558),(310.2,152.0)]","[(311.0315,154.558),(311.98,154.558),(311.98,155.10)]")
s=s.replace("'new_tracks':6", "'new_tracks':len(tracks)")
s=s.replace("'exact_raw_health_net':health","'no_shutdown_or_monitor_Cu_owned_or_changed':True,'exact_raw_health_net':health")
exec(compile(s,str(H/'construct_U11025_exact_health_loop_ground_escape_r318.py'),'exec'))
