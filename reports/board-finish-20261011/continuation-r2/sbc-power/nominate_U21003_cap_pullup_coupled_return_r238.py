"""Two local same-source poses, preserving both one-wire resistor terminals."""
from pathlib import Path
P=Path(__file__).resolve().parent;prior=P/'nominate_U21003_C21003_coupled_return_escape_r235.py';s=prior.read_text()
# Execute the same preserved constructor through its explicit derivative;
# additional edits are made to its effective source before evaluation.
start=s.index("exec(compile(s,str(__file__),'exec'))")
s=s[:start]+"""s=s.replace('U21003-C21003-translated-paired-return-nominees-r235','U21003-cap-pullup-translated-return-nominees-r238').replace('U21003-coupled-return-r235:','U21003-coupled-return-r238:').replace('R235_','R238_')
mark=\" fp=next(q for q in h['footprints']if q['ref']=='C21003')\"
assert mark in s
extra=''' for pad in h['pads']:
  if pad['ref']!='R21001':continue
  old=copy.deepcopy(pad);pad['x']=round(pad['x']+2.,6);assert pad.get('hole')is None
  pad['layers']={l:GP.G.records(set_precision(translate(unary_union(C.poly(rs)),2.,0.),1e-6,mode='pointwise'))for l,rs in pad['layers'].items()};poses.append({'kind':'pad','UUID':pad['uuid'],'ref':'R21001','pin':pad['num'],'raw_net':pad['net'],'original':old,'replacement':copy.deepcopy(pad)})
  if pad['num']=='1':points=[[old['x'],old['y']],[old['x'],147.160000],[pad['x'],147.160000],[pad['x'],pad['y']]];width=.2
  else:points=[[old['x'],old['y']],[pad['x'],pad['y']]];width=.3
  for i,(aa,bb)in enumerate(zip(points,points[1:])):bridge.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R21001-R238-preserved-terminal:'+pad['num']+':'+str(i))),'net':pad['net'],'layer':'F.Cu','w':width,'a':aa,'b':bb})
 rfp=next(q for q in h['footprints']if q['ref']=='R21001');rfold=copy.deepcopy(rfp);rfp['x']=round(rfp['x']+2.,6);rfp['courtyard']={side:GP.G.records(set_precision(translate(unary_union(C.poly(rs)),2.,0.),1e-6,mode='pointwise'))for side,rs in rfp['courtyard'].items()};poses.append({'kind':'footprint','ref':'R21001','original':rfold,'replacement':copy.deepcopy(rfp),'translation_mm':[2.,0.]})
'''
s=s.replace(mark,extra+mark).replace('assert len(poses)==3','assert len(poses)==6')
exec(compile(s,str(__file__),'exec'))
"""
exec(compile(s,str(__file__),'exec'))
