"""Locate the exact router import warnings without modifying native geometry."""
from pathlib import Path
import sys,json,collections,hashlib
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01'))
import shapely
from shapely.geometry import Polygon
from shapely.validation import explain_validity
import hardware_route_selected_additive_r02 as e
OUT=ROOT/'reports/freerouting-evaluation-20261002/DSN-actual-polygon-inspection-r01'
assert not OUT.exists();OUT.mkdir(parents=True)
PRE=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-visual-selected-DSN-r01'
raw=e.parse((PRE/'native.dsn').read_text(encoding='utf8'));tree=e.parse((PRE/'selected.dsn').read_text(encoding='utf8'))
native={e.dump(k)for k in e.children(e.child(raw,'structure'),'keepout')}
bad=[];counts=collections.Counter();allr=[]
def pts(poly):return[(float(poly[i]),float(poly[i+1]))for i in range(3,len(poly),2)]
for index,k in enumerate(e.children(e.child(tree,'structure'),'keepout')):
 poly=e.child(k,'polygon')
 if poly is None:continue
 outer=pts(poly);holes=[pts(e.child(w,'polygon'))for w in e.children(k,'window')]
 phase='inherited_native_export_keepout'if e.dump(k)in native else 'actual_filled_copper_or_reference_void'
 geom=Polygon(outer,holes);counts[(phase,'valid'if geom.is_valid and geom.area>0 else 'invalid')]+=1
 if not geom.is_valid or not geom.area:
  row=dict(index=index,phase=phase,layer=e.value(poly[1]),outer_vertices=len(outer),holes=len(holes),area_um2=geom.area,bounds_um=list(geom.bounds),reason=explain_validity(geom),outer_points_um=outer if len(outer)<=100 else None,definition_sha256=hashlib.sha256(e.dump(k).encode()).hexdigest())
  bad.append(row)
allr=dict(input_sha256={str(PRE/n):e.sha(PRE/n)for n in('native.dsn','selected.dsn','base.kicad_pcb')},shapely_version=shapely.__version__,GEOS_version=shapely.geos_version_string,counts=[dict(phase=p,status=s,count=c)for(p,s),c in counts.items()],invalid=bad,native_geometry_changed=False,router_acceptance_claimed=False)
e.write(OUT/'inspection.json',allr)
print(json.dumps(dict(invalid=len(bad),counts=allr['counts'],samples=bad[:8])))
