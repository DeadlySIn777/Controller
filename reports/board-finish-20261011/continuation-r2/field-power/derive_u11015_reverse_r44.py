"""Fix valid ILIM dive first; route ground and DVDT around its real Cu."""
from pathlib import Path
P=Path(__file__).resolve().parent;s=(P/'repair_u11015_mutual_r36.py').read_text()
s=s.replace("OUT=HERE/'u11015-three-net-mutual-fix-r36'", "OUT=HERE/'u11015-reverse-companion-repair-r44'")
needle="g={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};rec,trees=F.build({**g,'zones':[]})"
replace="""g={**g,'tracks':[t for t in g['tracks'] if t['uuid'] not in removed]};seedpath=HERE/'u11015-three-net-inner-ILIM-repair-r32';seedr=json.loads((seedpath/'receipt.json').read_text());assert sha(seedpath/'proposed-discrete.pkl')==seedr['proposed_discrete_sha256'];seed=pickle.loads((seedpath/'proposed-discrete.pkl').read_bytes());fixed_vias=[q for q in seed['vias'] if q['net']=='/motherboard_power_entry/AUX24_A_ILIM'];fixed_tracks=[q for q in seed['tracks'] if q['net']=='/motherboard_power_entry/AUX24_A_ILIM'];assert len(fixed_vias)==2 and len(fixed_tracks)==3
 for t in fixed_tracks:
  if t['layer']=='B.Cu':
   source_pin=('U11015','7') if t['uuid']=='64d60863-d80a-5e18-87f4-2c6c1881d62c' else ('R11056','1');p0=next(q for q in g['pads'] if(q['ref'],q['num'])==source_pin);sh=unary_union(C.poly(p0['layers']['B.Cu']));v=min(fixed_vias,key=lambda v:Point(v['x'],v['y']).distance(sh));t['a']=[round(sh.centroid.x,6),round(sh.centroid.y,6)];t['b']=[v['x'],v['y']]
 g={**g,'tracks':g['tracks']+fixed_tracks,'vias':g['vias']+fixed_vias};rec,trees=F.build({**g,'zones':[]})"""
assert needle in s;s=s.replace(needle,replace)
s=s.replace("newvias=[];newtracks=[];newcu=[];newzones=[];rows=[]", "newvias=fixed_vias[:];newtracks=fixed_tracks[:];newcu=[];newzones=[];rows=[]")
start=s.index("         ir=restore_ilim(rr['body'],disk)");end=s.index("         dr=restore_dvdt",start)
s=s[:start]+"""         ir={'points':[],'body':unary_union([q['shape'] for q in rec['B.Cu'] if q['uuid'] in {t['uuid'] for t in fixed_tracks}|{v['uuid'] for v in fixed_vias}]),'width_mm':.2,'length_mm':sum(LineString([t['a'],t['b']]).length for t in fixed_tracks),'inner_layer':'In3.Cu','native_flash_required':{'via_UUIDs':[v['uuid'] for v in fixed_vias],'layers':['B.Cu','In3.Cu']},'reverse_order_fixed_ILIM_via_UUIDs':[v['uuid'] for v in fixed_vias],'reverse_order_fixed_ILIM_segment_UUIDs':[t['uuid'] for t in fixed_tracks]}
         pending_signal_cu=[]
""" +s[end:]
s=s.replace("controller-U11015-three-net-inner-r36/", "controller-U11015-reverse-companion-r44/")
s=s.replace("'ILIM_restore_segment_UUIDs':irids", "'ILIM_restore_segment_UUIDs':[t['uuid'] for t in fixed_tracks]+irids")
needle=" (OUT/'proposed-discrete.pkl').write_bytes" # final writes already checkpoint includes seeded objects
s=s.replace("'signal_via_annuIi_clear_every_new_ground_stub_Cu':True", "'signal_via_annuIi_clear_every_new_ground_stub_Cu':True,'R36_incomplete_receipt_sha256':sha(HERE/'u11015-three-net-mutual-fix-r36/receipt.json'),'ILIM_fixed_before_ground_and_DVDT_search':True")
s=s.replace("(OUT/(uid+'.via-chunk')).write_text", "(OUT/(uid+'.via-chunk')).write_text")
# Seed chunk rendering is deferred to the native emitter after the independent joint gate.
(P/'repair_u11015_reverse_r44.py').write_text(s,encoding='utf-8');compile(s,'repair_u11015_reverse_r44.py','exec');print('derived',len(s))
