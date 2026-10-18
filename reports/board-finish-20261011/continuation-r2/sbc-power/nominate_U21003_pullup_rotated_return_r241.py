"""Bounded resistor rotation avoids the untouched quiet R21005 divider."""
from pathlib import Path
P=Path(__file__).resolve().parent;prior=P/'nominate_U21003_C21003_coupled_return_escape_r235.py';s=prior.read_text();start=s.index("exec(compile(s,str(__file__),'exec'))")
s=s[:start]+"""s=s.replace('U21003-C21003-translated-paired-return-nominees-r235','U21003-cap-pullup-rotated-return-nominees-r241').replace('U21003-coupled-return-r235:','U21003-coupled-return-r241:').replace('R235_','R241_').replace('from shapely.affinity import translate','from shapely.affinity import translate,rotate')
mark=\" fp=next(q for q in h['footprints']if q['ref']=='C21003')\"
assert mark in s
extra=''' rfp=next(q for q in h['footprints']if q['ref']=='R21001');rx,ry=rfp['x'],rfp['y'];assert(rx,ry)==(332.196,146.863);rfold=copy.deepcopy(rfp)
 for pad in h['pads']:
  if pad['ref']!='R21001':continue
  old=copy.deepcopy(pad);xy=rotate(Point(pad['x'],pad['y']),-90,origin=(rx,ry));pad['x']=round(xy.x-.25,6);pad['y']=round(xy.y+.7,6);assert pad.get('hole')is None
  pad['layers']={l:GP.G.records(set_precision(translate(rotate(unary_union(C.poly(rs)),-90,origin=(rx,ry)),-.25,.7),1e-6,mode='pointwise'))for l,rs in pad['layers'].items()};poses.append({'kind':'pad','UUID':pad['uuid'],'ref':'R21001','pin':pad['num'],'raw_net':pad['net'],'original':old,'replacement':copy.deepcopy(pad)})
  bridge.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R21001-R241-exact-old-terminal:'+pad['num'])),'net':pad['net'],'layer':'F.Cu','w':.2 if pad['num']=='1'else .3,'a':[old['x'],old['y']],'b':[pad['x'],pad['y']]})
 rfp['x']=round(rx-.25,6);rfp['y']=round(ry+.7,6);rfp['courtyard']={side:GP.G.records(set_precision(translate(rotate(unary_union(C.poly(rs)),-90,origin=(rx,ry)),-.25,.7),1e-6,mode='pointwise'))for side,rs in rfp['courtyard'].items()};poses.append({'kind':'footprint','ref':'R21001','original':rfold,'replacement':copy.deepcopy(rfp),'translation_mm':[-.25,.7],'original_native_root_angle_deg':-90.,'target_native_root_angle_deg':0.,'actual_geometry_rotation_deg':-90.,'native_root_pose_only_replacement_and_source_pad_local_AST_obligations':'OPEN'})
'''
s=s.replace(mark,extra+mark).replace('assert len(poses)==3','assert len(poses)==6').replace(\"'exact_new_B_bridges':bridge\",\"'exact_new_pad_terminal_bridges':bridge\")
exec(compile(s,str(__file__),'exec'))
"""
exec(compile(s,str(__file__),'exec'))
