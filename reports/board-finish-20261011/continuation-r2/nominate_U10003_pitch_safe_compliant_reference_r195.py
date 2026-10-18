"""Move only the unadopted primary return and reserve new-plane antipads."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_compliant_coupled_clock_fault_ground_planes_r191.py';code=source.read_text().replace('r191','r195')
needle="sig=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');central=joint['replace_only_unadopted_ground_barrel'];raw=central['net']"
assert code.count(needle)==1
replacement="""joint=pickle.loads(pickle.dumps(joint,protocol=5));central={**joint['replace_only_unadopted_ground_barrel'],'x':215.97,'y':143.29};joint['replace_only_unadopted_ground_barrel']=central
 for t in joint['new_tracks']:
  if C.norm(t['net'])==FG and t['b']==[216.04,143.32]:t['b']=[215.97,143.29]
 sig=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');raw=central['net']"""
code=code.replace(needle,replacement)
anchor="compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))";assert code.count(anchor)==1
extra="""
needle="add(N.bounded_buffer(q['shape'].intersection(win),gap),'ACTUAL_FOREIGN_REFERENCE_LAYER_CU'";assert code.count(needle)==1
code=code.replace(needle,"add(N.bounded_buffer(q['shape'].intersection(win),gap+.0001),'ACTUAL_FOREIGN_REFERENCE_LAYER_CU'")
needle="'physical_geometry_changed':False";assert code.count(needle)==1
code=code.replace(needle,needle+",'only_new_reference_plane_foreign_Cu_antipad_extra_reserve_mm':.0001,'R194_three_raw_geometry_failures_retained':True,'primary_return_to_unchanged_clock_via_pitch_mm':Point(central['x'],central['y']).distance(Point(216.68003,143.711969))")
"""
code=code.replace(anchor,extra+'\n'+anchor)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
