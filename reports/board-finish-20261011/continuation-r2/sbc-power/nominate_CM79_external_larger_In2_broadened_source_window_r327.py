"""Retain R326 no-route evidence; broaden only the declared finite window."""
from pathlib import Path
p=Path(__file__).with_name('nominate_CM79_external_larger_port_actual_In2_source_route_r326.py')
s=p.read_text(encoding='utf-8').replace('nominations-r326','nominations-r327').replace('R326_ROUTE','R327_ROUTE').replace('R326_COMPLETE','R327_COMPLETE')
s=s.replace('region=box(104,158,144,214)','region=box(90,145,175,225)').replace('[104,158,144,214]','[90,145,175,225]')
s=s.replace("'same_free_face_count':len(relevant)","'same_free_face_count':len(relevant),'free_face_bounds':[list(face.bounds)for face in relevant],'free_face_distance_to_actual_source_mm':[face.distance(target)for face in relevant],'available_actual_source_overlap_mm2':[face.intersection(buf(target,.624995)).area for face in relevant]")
s=s.replace("faces=RF.parts(free);tests=[]", "faces=RF.parts(free);put(O/'all-hard-free-component-and-actual-source-summary.json',{'all_free_component_count':len(faces),'actual_source_target_bounds_mm':list(target.bounds),'actual_source_target_area_mm2':target.area,'free_components':[{'bounds_mm':list(face.bounds),'area_mm2':face.area,'actual_source_distance_mm':face.distance(target)}for face in faces]});tests=[]")
s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir()", "started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-read-only-nomination.py').write_text(s,encoding='utf-8')")
exec(compile(s,str(__file__),'exec'))
