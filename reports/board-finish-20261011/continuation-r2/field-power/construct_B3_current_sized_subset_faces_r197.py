"""Only the two additional legal widths for the complete 90 mA B3 policy."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_B3_exact_subset_faces_r188.py').read_text(encoding='utf-8').replace('r188','r197').replace('R188','R197').replace('new="""','new=r"""')
needle="exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))"
prefix,suffix=s.rsplit(needle,1)
extra=r'''s=s.replace('for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):','for margin in(25.,140.,None):\n    for width in(.25,.20):')
'''
s=prefix+extra+needle+suffix
monitor=r'''monitor=H.parent/'field-monitor-R9026-rotation-source-termination-r66/owned-delta.pkl'
assert sha(monitor)=='2669504846249102a6afe479c78f627b7729d0992c48bc64f79a330f431149c5'
md=pickle.loads(monitor.read_bytes());hard['discrete']['tracks']+=md['tracks'];hard['discrete']['vias']+=md['vias']
for pad in md['new_R9026_pads']:
 for layer,rs in pad['layers'].items():
  for sh in C.poly(rs):hard['planes'].append({'uuid':'MONITOR_NATIVE_POSE_PENDING_'+pad['uuid'],'net':pad['net'],'layer':layer,'shape':sh,'clearance_mm':.15})
bindings.append({'file':str(monitor.resolve()),'sha256':sha(monitor),'scope':'Later monitor physical bodies hard only; native exported pad polygons/source gates remain separate'})
'''
injection='s=s.replace("bindings=[]\\nmask=", "bindings=[]\\n"+'+repr(monitor)+'+"mask=")\n'
last="exec(compile(s,str(H/'construct_B3_preserving_exact_old_IO3_r177.py'),'exec'))"
assert s.count(last)==1;s=s.replace(last,injection+last)
exec(compile(s,str(H/'construct_B3_exact_subset_faces_r188.py'),'exec'))
