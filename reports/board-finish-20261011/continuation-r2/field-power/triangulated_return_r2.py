"""Conservative inward simplification before exact constrained path proof."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
path=Path(__file__).with_name('triangulated_return_r1.py')
text=path.read_text(encoding='utf-8').replace("OUT=HERE/'triangulated-return-r1'","OUT=HERE/'triangulated-return-r2'")
old="free=shapely.from_wkb(fp.read_bytes());source="
new="""free_original=shapely.from_wkb(fp.read_bytes());free=free_original.buffer(-.020).simplify(.010,preserve_topology=True);assert free_original.covers(free);parts=[free] if free.geom_type=='Polygon' else list(free.geoms);source_original=unary_union(poly(pad['layers'][layer]));target_original=unary_union([r['shape'] for r in goal if r['layer']==layer]);free=next(q for q in parts if q.intersection(source_original).area>1e-8 and q.intersection(target_original).area>1e-8);print(layer,'simplified vertices',shapely.get_num_coordinates(free),flush=True);source="""
assert old in text;text=text.replace(old,new)
text=text.replace("'core_polygon_exactly_covered':True", "'core_polygon_exactly_covered':True,'conservative_free_simplification':{'inset_mm':.020,'simplification_tolerance_mm':.010,'entire_simplified_area_verified_covered_by_original_free_polygon':True,'original_core_width_mm':2.}")
exec(compile(text,str(path),'exec'))
