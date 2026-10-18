"""Preserve R439 empty-polygon failure; search only real landing pieces."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent
failed=H/'U10009-source-component-guided-wider-ordinary-landing-nomination-r439'
if failed.exists()and not(failed/'failure.json').exists():
 (failed/'failure.json').write_text(json.dumps({'verdict':'CONSTRUCTOR_FAILURE_EMPTY_POLYGON_WAS_PASSED_TO_NEAREST_POINTS','error':'ValueError: The first input geometry is empty','native_jobs':0,'model_emitted':False,'adopted':False},indent=1)+'\n',encoding='utf-8')
owner=H/'nominate_U10009_source_component_guided_landing_r439.py'
ns={'__file__':str(owner),'__name__':'_load_guided_landing_without_run'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('source-component-guided-wider-ordinary-landing-nomination-r439','source-component-guided-nonempty-ordinary-landing-nomination-r441')
s=s.replace("def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']", "def polys(s):return []if s.is_empty else[s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]")
s=s.replace("vid+'/inner/R439/'+layer", "vid+'/inner/R441/'+layer")
s=s.replace("'source_component_guided_new_landing':True", "'source_component_guided_new_landing':True,'R439_empty_polygon_failure_preserved':True")
exec(compile(s,str(H/'nominate_U10009_retained_lower_VS_barrel_r397.py'),'exec'))
