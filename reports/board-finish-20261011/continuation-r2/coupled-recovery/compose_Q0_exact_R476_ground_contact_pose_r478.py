"""Actual-filled-only sparse composition with the exact -.4/-.5 FP pose."""
from pathlib import Path
import builtins
H=Path(__file__).resolve().parent;base=H/'compose_Q0_exact_R464_current_filled_only_r466.py'
def scoped_compile(source,filename,mode,*args,**kwargs):
 if isinstance(source,str):
  source=source.replace('Q0-exact-R464-current-filled-only-r466','Q0-exact-R476-ground-contact-pose-r478').replace('Q0-R460-exact-native-owned-operation-r464','Q0-R474-ground-contact-pose-native-r476').replace('3f69aef00ad31bc5bcff19bc1ce80aec1f8afb1efe6fa1d05e08e5d993017e9c','7f46fb8f9a1515ca04c58b7e503adef967ab5a2d4eb03e0f27cb73f38d8c3cd8').replace('3f64ad79fd292c54bca3f25457215b4a25789a09b888f795e1788f6e9eb98d14','b226073ec3597d7115d9216bb1a6ff3c1fd9904d25652cd3d518df216cd1a067').replace('source_R464_receipt_sha256','source_R476_receipt_sha256')
  if "p['x']=round(p['x']-.5,9)"in source:
   source=source.replace("p['x']=round(p['x']-.5,9)","p['x']=round(p['x']-.4,9)").replace('xoff=-.5,yoff=-.5','xoff=-.4,yoff=-.5').replace("fp['x']=229.86","fp['x']=229.96")
 return builtins.compile(source,filename,mode,*args,**kwargs)
ns={'__file__':str(base),'__name__':'__main__','compile':scoped_compile};exec(scoped_compile(base.read_text(),str(base),'exec'),ns)
