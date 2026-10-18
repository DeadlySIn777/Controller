"""Previously untested F-port set, same exact source/fullbody reference gates."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/nominate_R353_IO3_existing_annulus_actual_source_fullbody_reference_r362.py'
t=p.read_text(encoding='utf-8')
needle="exec(compile(s,str(__file__),'exec'))"
assert t.count(needle)==1
extra=r'''
s=s.replace('r362','r364').replace('R362','R364')
s=s.replace("rank={'In3.Cu':0,'In2.Cu':1,'B.Cu':2,'F.Cu':3}","rank={'F.Cu':0}")
s=s.replace('pairs=pairs[:48]','pairs=pairs[:32]')
s=s.replace('for width in(.5,.75,1.0):','for width in(.5,):')
s=s.replace('for radius in(1.0,3.0):','for radius in(3.0,10.0):')
s=s.replace("radius=(v['d']/2 if observed else v['drill']/2)+.25+.025;caps.append(Point(v['x'],v['y']).buffer(radius,quad_segs=128));portcaps.append({'UUID':v['uuid'],'actual_reference_layer_annulus':observed,'own_original_radius_mm':radius})", "ownradius=(v['d']/2 if observed else v['drill']/2)+.25+.025;caps.append(Point(v['x'],v['y']).buffer(ownradius,quad_segs=128));portcaps.append({'UUID':v['uuid'],'actual_reference_layer_annulus':observed,'own_original_radius_mm':ownradius})")
'''
t=t.replace(needle,extra+'\n'+needle)
exec(compile(t,str(__file__),'exec'))
