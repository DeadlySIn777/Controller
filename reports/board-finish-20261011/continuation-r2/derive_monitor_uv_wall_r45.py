"""Preserve the exact voltage-monitor route while opening its ground pocket."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_field_health_wall_reroute_r34.py';dst=H/'nominate_monitor_uv_wall_r45.py'
assert not dst.exists();t=src.read_text()
for a,b in {
 'field-health-wall-reroute-r34':'field-monitor-uv-wall-reroute-r45',
 'e4373f43-4bf8-4252-afdf-b11a56a2c998':'b7ddd466-0bed-4b5a-968d-9ef0ce166364',
 'box(307,150,317,159)':'box(341,54,352,65)',
 'controller-health-wall-r34/':'controller-monitor-wall-r45/',
 'controller-health-wall-r34':'controller-monitor-wall-r45',
 'controller-health-wall':'controller-monitor-wall',
 'controller-health':'controller-monitor',
 "'controller-health-wall-r34/'":"'controller-monitor-wall-r45/'",
 "'controller-health-wall-r34/":"'controller-monitor-wall-r45/",
 'R34_DETOUR':'R45_DETOUR',
 'R34_LOCAL_PADS':'R45_LOCAL_PADS',
 "p['ref']=='U11025'":"p['ref']=='R9026'"
}.items():
 if a in t:t=t.replace(a,b)
old="for dx in (.1,.2,.3,.4,.45,.48,.49,.50,.51,.52,.53,.54,.55):"
assert old in t;t=t.replace(old,"for dx in (.05,.1,.15,.2,.25,.3,.35,.4,.45,.5,.55,.6,.7,.8,1.,1.2,1.5,2.,-.1,-.2,-.3):")
old="x=round(old['a'][0]+dx,6);points=[old['a'],[x,old['a'][1]],[x,old['b'][1]],old['b']]"
assert old in t;t=t.replace(old,"x=round((old['a'][0]+old['b'][0])/2+dx*.7714,6);y=round((old['a'][1]+old['b'][1])/2+dx*.6364,6);points=[old['a'],[x,y],old['b']]")
t=t.replace("'STRICT_SAME_F_HEALTH_WALL_NOMINEE_REFERENCE_CONTACT_SOURCE_NATIVE_OPEN'","'STRICT_SAME_F_MONITOR_WALL_NOMINEE_REFERENCE_CONTACT_SOURCE_NATIVE_OPEN'")
t=t.replace("'controller-health-wall-r34/'","'controller-monitor-wall-r45/'")
compile(t,str(dst),'exec');dst.write_text(t)
(H/'monitor-uv-r45-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'scope':'exact UV track two endpoints, ordinary .20 F triangular detours, full existing pads/Cu/drills/native rules/source reference unchanged','board_written':False,'adopted':False},indent=1)+'\n')
print(dst)
