"""Minimal old7bb branch feed bypass plus ordinary FLT dive, <=3 legs each."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_power_wall_SENSE_dive_coupled_r404.py'
code=base.read_text().replace('Q0-power-wall-SENSE-dive-coupled-r404','Q0-power-left-source-bypass-FLT-dive-r418')
old="exec(compile(prefix,str(base),'exec'))"
new="prefix=prefix.replace('groupsfile=', \"newvias.append({'uuid':'FLT-source','net':FLT,'x':229.0479,'y':158.581,'d':.5,'drill':.2,'flashed':list(K.LAYERS)})\\ngroupsfile=\",1)\nexec(compile(prefix,str(base),'exec'))"
assert old in code;code=code.replace(old,new,1)
code=code.replace("('SENSE-source','b88b7a49-a1ea-458a-9195-d0a46a3a7f66'),", "('SENSE-source','b88b7a49-a1ea-458a-9195-d0a46a3a7f66'),('FLT-source','retained-SENSE-return'),")
start=code.index("power_ok=route_attachments(");end=code.index("ground_ok=route_attachments(",start)
replacement="""powerWithout7bb={**current,'tracks':[t for t in current['tracks']if t['uuid']!='7bb3c794-cbe6-40a7-abfb-5a3ab7df28ff']}
_,powerGroups=K.physical(powerWithout7bb,POWER,K.hole_context(powerWithout7bb));powerRoot=K.root(powerGroups,'U11017','1');powerTarget=unary_union([r['shape']for r in powerRoot if r['layer']=='F.Cu'and r['kind']!='fill']);assert not powerTarget.is_empty
power_ok=route_attachments('POWER-only-7bb-original-feed-node-to-real-source-rooted-retained-F-Cu',POWER,'F.Cu',refs['In1.Cu'],Point(228.45,158.35),powerTarget.buffer(-.02,quad_segs=128),tracks)
fltNew=next(v for v in newvias if v['uuid']=='FLT-source');fltIn4Own,fltIn4Ledger=support_FLT(K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,oldFLTvia,GND,FLT,'In4.Cu');fltIn4Ledger['used_signal_layer']='In3.Cu';put(out/'retained-FLT-In3-exact-native-own-support.json',fltIn4Ledger)
fltFown=newOwn(fltNew,'In1.Cu');fltIown=newOwn(fltNew,'In4.Cu');fltF=route_attachments('FLT-F-original-feed-to-new-ordinary-dive',FLT,'F.Cu',refs['In1.Cu'].union(fltFown),Point(229.35,158.45),Point(fltNew['x'],fltNew['y']),tracks,qualified_new_own=fltFown)
fltInner=route_attachments('FLT-In3-to-retained-original-all6-barrel',FLT,'In3.Cu',refs['In4.Cu'].union(fltIown).union(fltIn4Own),Point(fltNew['x'],fltNew['y']),Point(oldFLTvia['x'],oldFLTvia['y']),tracks,qualified_new_own=fltIown.union(fltIn4Own));flt_ok=fltF and fltInner
"""
code=code[:start]+replacement+code[end:];exec(compile(code,str(base),'exec'))
