"""Try relocating only the unadopted primary ground to serve both signals."""
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_U10003_clock_actual_source_return_faces_r198.py'
prefix=src.read_text().split("compile(code,str(source),'exec');")[0];exec(compile(prefix,str(src),'exec'))
code=code.replace('clock-current-source-pitch-bound-return-faces-r198','clock-fault-shared-ground-return-faces-r207')
needle=" ports=[next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f')];"
assert code.count(needle)==1
replacement="""
 primary='ef759308-e664-5253-b016-ff17794eac74';signal=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');oldprimary=next(v for v in h['vias']if v['uuid']==primary)
 h={**h,'vias':[v for v in h['vias']if v['uuid']!=primary]};full={**full,'vias':h['vias']};ports=[next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f')];
"""
code=code.replace(needle,replacement)
needle="near=legal.intersection(pt.buffer(1.0,quad_segs=256)).difference(pt.buffer(.90,quad_segs=256))"
assert code.count(needle)==1
code=code.replace(needle,needle+";sp=Point(signal['x'],signal['y']);near=near.intersection(sp.buffer(1.0,quad_segs=256)).difference(sp.buffer(.90,quad_segs=256))")
code=code.replace("'signal_distance_mm':site.distance(pt)","'signal_distance_mm':site.distance(pt),'other_fault_signal_distance_mm':site.distance(sp),'only_unadopted_primary_ground_relocation':oldprimary")
code=code.replace("'original_or_new_Cu_deleted':False","'readonly_withdrawal_only_unadopted_primary_ground_for_relocation':primary,'original_Cu_deleted':False")
exec(compile(code,str(src),'exec'))
