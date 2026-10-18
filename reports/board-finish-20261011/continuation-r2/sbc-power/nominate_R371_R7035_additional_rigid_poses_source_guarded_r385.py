"""Additional 0.2 mm rigid poses outside the completed small translation window."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/exact-expanded-small-R7035-rigid-rotation-screen-r383.py'
s=p.read_text(encoding='utf-8').replace('r383','r385').replace('R383','R385')
s=s.replace('localBox=box(79,19,90,31)','localBox=box(75,16,95,35)').replace("'local_clip_bounds':[79,19,90,31]","'local_clip_bounds':[75,16,95,35]")
old="poses=sorted([(angle,round(dx*.1,6),round(dy*.1,6))for angle in (0,-90,90,180)for dx in range(-15,16)for dy in range(-18,19)if angle or dx or dy],key=lambda v:(math.hypot(v[1],v[2])+.05*abs(v[0])/90,v[2]<0,abs(v[1]),abs(v[0])))"
new="poses=sorted([(angle,round(dx*.2,6),round(dy*.2,6))for angle in (0,-90,90,180)for dx in range(-20,21)for dy in range(-15,16)if abs(dx*.2)>1.5 or abs(dy*.2)>1.8],key=lambda v:(math.hypot(v[1],v[2])+.05*abs(v[0])/90,v[2]<0,abs(v[1]),abs(v[0])))"
assert old in s;s=s.replace(old,new)
s=s.replace("'bounded_translation_candidate_count':len(poses)", "'additional_rigid_candidate_count':len(poses),'completed_small_R383_window_not_repeated':True")
(H/'sbc-power/exact-expanded-additional-R7035-rigid-pose-screen-r385.py').write_text(s,encoding='utf-8')
exec(compile(s,str(__file__),'exec'))
