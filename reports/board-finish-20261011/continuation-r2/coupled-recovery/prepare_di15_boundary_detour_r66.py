"""Create a fresh static R66 constructor, preserving every old fill boundary."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;source=HERE/'construct_di15_neighbor_void_detour_r58.py';raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='cae8c9b5b48bc231456fbc26c79f77ba332caf6505b8eed1b418b5ce8014c32d';s=raw.decode()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("out=HERE/'di15-neighbor-void-detour-r58.json'","out=HERE/'di15-original-boundary-detour-r66.json'")
replace("rp=HERE/'di15-root-LG-r18-DI6-bind-r50.json'","rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json'")
replace("e372e8ea1a703619f6c6e1002050624a070d01216b8d26f6f9f16b0de2c8114e","a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be")
replace("for z in h['rule_areas']:","""# Original filled Cu of every foreign net remains hard, including the
 # explicit FIELD_B_0V native In1 cross-domain piece. No stale void credit.
 original_rows=[];owned_ids={z['uuid'] for z in cur['zones']}
 for z in cur['after']['zones']:
  n=L.norm(z['net'])
  if n==GND or z['uuid'] in owned_ids:continue
  for sh in L.poly(z['fills'].get('In1.Cu',[])):
   if sh.distance(win)>1:continue
   gap=max(.15 if domain.get(n)==domain.get(GND) else .6,.25,float(z.get('clearance_mm',.15)))+.025;obs.append(sh.buffer(gap,quad_segs=128));original_rows.append({'UUID':z['uuid'],'net':z['net'],'local_mm':float(z.get('clearance_mm',.15)),'required_mm':gap,'WKB_sha256':C.sha(sh.wkb)})
 for z in h['rule_areas']:""")
replace("cache=HERE/'di15-neighbor-void-detour-r58-geometry.pkl'","cache=HERE/'di15-original-boundary-detour-r66-geometry.pkl'")
replace("'R50_receipt_sha256':C.sha(A.read(rp))","'R62_receipt_sha256':C.sha(A.read(rp))")
replace("'R56_incomplete_masks_preserved_not_adopted':True","'R56_R64_incomplete_masks_preserved_not_adopted':True,'all_original_foreign_fill_boundaries_preserved_hard':original_rows")
replace("DI15_R58_NEIGHBOR_VOID_AVOIDING_COMPONENTS","DI15_R66_ORIGINAL_BOUNDARY_AVOIDING_COMPONENTS")
replace('"""Correct physical In2 path around real neighboring reference voids.','"""Correct physical In2 path around unchanged native field boundaries.')
target=HERE/'construct_di15_original_boundary_detour_r66.py';assert not target.exists();target.write_text(s,newline='\n');print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'created':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
