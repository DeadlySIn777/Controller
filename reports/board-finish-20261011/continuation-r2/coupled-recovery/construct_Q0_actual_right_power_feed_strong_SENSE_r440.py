"""Correct the lost power-feed selector and exact unflashed SENSE support.

This derives a new exploratory constructor from frozen R426.  No source,
board, native run, existing receipt, or shared current model is modified.
"""
from pathlib import Path
import builtins, hashlib, json
H=Path(__file__).resolve().parent
base=H/'construct_Q0_SENSE_In2_Q0_In3_coupled_r426.py'
patches=[]
def scoped_compile(source,filename,mode,*args,**kwargs):
 if isinstance(source,str):
  source=source.replace('Q0-SENSE-In2-Q0-In3-coupled-r426','Q0-actual-right-power-feed-strong-SENSE-r440')
  old="power_ok=route_attachments('POWER-only-7bb-original-feed-node-to-real-source-rooted-retained-F-Cu',POWER,'F.Cu',refs['In1.Cu'],Point(228.45,158.35),powerTarget.buffer(-.02,quad_segs=128),tracks)"
  if old in source:
   source=source.replace(old,"power_ok=route_attachments('POWER-7bb-RIGHT-lost-feed-node-to-real-source-rooted-retained-F-Cu',POWER,'F.Cu',refs['In1.Cu'],Point(229.45,159.35),powerTarget.buffer(-.02,quad_segs=128),tracks)")
   patches.append({'kind':'actual_lost_power_feed_selector','native_removed_axis_mm':[[228.45,158.35],[229.45,159.35]],'lost_group_feed_mm':[229.45,159.35],'source_root':['U11017','1'],'lost_original_contacts':['U10004.4','30a2a2a0-d11c-40f8-b311-248feab3fa8a','eafc8ee5-fe97-4602-bf9c-f859ae7a7815']})
  old=".replace('.575','.525').replace('RETAINED_FLT','RETAINED_SENSE')"
  if old in source:
   source=source.replace(old,".replace('.575','.375').replace('RETAINED_FLT','RETAINED_SENSE')")
   patches.append({'kind':'exact_unflashed_reference_layer_SENSE_width','original_required_actual_masks':['F.Cu','B.Cu'],'reference_planes':['In1.Cu','In4.Cu'],'actual_reference_width_mm':.2,'exact_own_radius_mm':.375,'new_used_mask_nomination':['In2.Cu'],'unused_flags_unchanged':True})
  if 'powerWithout7bb=' in source:
   (H/'Q0-actual-right-power-feed-strong-SENSE-r440-derived-constructor.py').write_text(source)
 return builtins.compile(source,filename,mode,*args,**kwargs)
ns={'__file__':str(base),'__name__':'__main__','compile':scoped_compile}
exec(scoped_compile(base.read_text(),str(base),'exec'),ns)
out=H/'Q0-actual-right-power-feed-strong-SENSE-r440'
(out/'explicit-constructor-correction-ledger.json').write_text(json.dumps({'frozen_R426_script_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'patches':patches,'prior_partial_independent_R438_FAILED_preserved':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
