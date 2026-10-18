"""Separate zero-power-carve nominee using the other adjacent In2 reference."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;s0=H/'construct_di15_zero_power_carve_detour_r76.py';b=s0.read_bytes();s=b.decode().replace('In1','In3').replace('r76','r80').replace('R76','R80')
s=s.replace('DI15_ZERO_POWER_CARVE_IN2_PATH_NOMINATED_SOURCE_REFERENCE_CONSTRUCTION_OPEN','DI15_ZERO_POWER_CARVE_IN2_WITH_ADJACENT_IN3_REFERENCE_NOMINATED_UNQUALIFIED')
s=s.replace('DI15_ZERO_POWER_CARVE_SAVED_TWO_SITE_DETOUR_INCOMPLETE','DI15_ZERO_POWER_CARVE_ADJACENT_IN3_TWO_SITE_DETOUR_INCOMPLETE')
s=s.replace("'actual_existing_ground_not_eroded_or_expanded':True", "'selected_adjacent_In2_reference_layer':'In3.Cu','reference_handoff_between_planes_allowed':False,'actual_existing_ground_not_eroded_or_expanded':True")
dst=H/'construct_di15_zero_power_carve_In3_reference_r80.py';assert not dst.exists();dst.write_text(s);compile(s,str(dst),'exec')
out=H/'prepare-di15-In3-reference-r80.json';assert not out.exists();out.write_text(json.dumps({'source':str(s0),'source_sha256':hashlib.sha256(b).hexdigest(),'derived':str(dst),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'delta':'Use actual source-rooted adjacent In3 for ordinary In2 transport and potential new ground; all power/old native/physical barriers remain hard. No In3 signal route, no plane-reference handoff or electrical/current/native qualification.'},indent=1)+'\n');print(dst)
