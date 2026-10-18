"""Derive a fresh static constructor from the frozen incomplete R56.

Every correction is explicit; no old file/model/result is modified.
"""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
source=HERE/'construct_di15_In1_reference_strip_r56.py';raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='ebc260f182056e68626e400b68387a9ec0ad2f9e81ea9c6ccecfc9b4212812ee';s=raw.decode()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("directory=HERE/'di15-In1-reference-strip-r56'","directory=HERE/'di15-In1-reference-strip-r64'")
replace("rp=HERE/'di15-root-LG-r18-DI6-bind-r50.json'","rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json'")
replace("e372e8ea1a703619f6c6e1002050624a070d01216b8d26f6f9f16b0de2c8114e","a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be")
replace("pathr=json.loads(A.read(HERE/'di15-In2-physical-reference-diagnostic-r48.json'));pts=pathr['physical_paths_reference_not_qualified'][0]['In2_points_mm']","pathfile=HERE/'di15-neighbor-void-detour-r58.json';pathr=json.loads(A.read(pathfile));assert C.sha(A.read(pathfile))=='4f64d84d0aa6a7577fcf341e8a101c05bdada00b46926b98e4dab7f43ba543c4';pts=pathr['In2_points_mm']")
replace("if L.norm(p['net'])==GND:obstacles.append(sh)","if L.norm(p['net'])==GND:pass # intended own-net hole centre preserved; Q.physical subtracts real drill")
replace("if L.norm(v['net'])==GND:obstacles.append(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))","if L.norm(v['net'])==GND:pass # intended own-net barrel centre remains filled; actual Cu is separately drilled")
replace("preserved_planes=[]", """# Preserve every original foreign fill as hard: no native Cu/fill boundary
 # is withdrawn by this proposal. The only plane carve authority is CORE/FB.
 original_fill_masks=[];owned_ids={z['uuid'] for z in cur['zones']}
 for z in before['zones']:
  n=L.norm(z['net'])
  if n==GND or z['uuid'] in owned_ids:continue
  for sh in L.poly(z['fills'].get('In1.Cu',[])):
   if sh.distance(desired)>.7:continue
   required=max(.15 if domains.get(n)==domains.get(GND) else .6,.25,float(z.get('clearance_mm',.15)))+.025;mask=Z.bounded_buffer(sh,required);obstacles.append(mask)
   if not desired.intersection(mask).is_empty:original_fill_masks.append({'UUID':z['uuid'],'net':z['net'],'local_mm':float(z.get('clearance_mm',.15)),'required_mm':required,'desired_overlap_mm2':desired.intersection(mask).area,'WKB_sha256':C.sha(sh.wkb)})
 preserved_planes=[]""")
replace("len(A.polys([old])) if False else len(GE.records(old))","len(GE.records(old))")
replace("'controller/DI15/reference-r56/'","'controller/DI15/reference-r64/'")
replace("'DI15 ordinary In2 adjacent source reference R56'","'DI15 ordinary In2 adjacent source reference R64'")
replace("'R50_receipt_sha256':C.sha(A.read(rp))","'R62_receipt_sha256':C.sha(A.read(rp))")
replace("'foreign_discrete_obstacle_trims':foreign_rows","'foreign_discrete_obstacle_trims':foreign_rows,'original_foreign_fill_masks_preserved_hard':original_fill_masks,'intended_own_net_ground_barrel_centres_not_drill_subtracted':True,'physical_reference_all_actual_drills_subtracted_by_Q_physical':True")
replace("'root_R20_27_FBG_old_reference_losses_remain_open':True","'corrected_ROOT_safe_R22_authority_exact':True,'pre_DI6_ROOT_safe_R22_outer_reference_pass_is_separate_from_DI6_native_remote_slivers':True")
replace('"""Freeze an exact reference-only coupled proposal; no design adoption.', '"""Corrected R64: actual safe R22 + R58 neighbouring-void detour.\n\nFreeze an exact reference-only coupled proposal; no design adoption.')
target=HERE/'construct_di15_In1_reference_strip_r64.py';assert not target.exists();target.write_text(s,newline='\n');print(json.dumps({'derived_source_sha256':hashlib.sha256(raw).hexdigest(),'created':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
