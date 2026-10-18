import sys,runpy,hashlib,difflib
sys.dont_write_bytecode=True
from pathlib import Path
H=Path(__file__).resolve().parent
r=runpy.run_path(str(H/'restage_CORE69_DIR7_negative_on_stage3_r1.py'))
source=r['SOURCE'].read_bytes();uid=r['UID'];old=(r['PACKET']/(uid+'-exact-before.zone-chunk')).read_bytes()
new=r['K'].C.inventory(source)[3][uid]
sha=lambda v:hashlib.sha256(v).hexdigest()
print('CHUNK',len(old),sha(old),len(new),sha(new))
print('\n'.join(list(difflib.unified_diff(old.decode().splitlines(),new.decode().splitlines(),fromfile='R299',tofile='stage3',n=3))[:100]))
import re
from fractions import Fraction as Q
from shapely.geometry import Polygon
recipe=runpy.run_path(str(H/'construct_coupled_CORE1V2_DIR7_return_window_r2.py'))
def shape(raw):
    spans=[(a,b)for a,b,k in recipe['polygon_spans'](raw)if k==b'polygon'];assert len(spans)==1
    a,b=spans[0];points=[(Q(x.decode())*1000000,Q(y.decode())*1000000)for x,y in re.findall(rb'\(xy ([-0-9.eE]+) ([-0-9.eE]+)\)',raw[a:b])]
    assert all(v.denominator==1 for xy in points for v in xy)
    return Polygon([(int(x),int(y))for x,y in points])
a,b=shape(old),shape(new)
print('INTENT',len(a.exterior.coords),a.area/1e12,len(b.exterior.coords),b.area/1e12,'EQUAL',a.equals(b),'DELTA',a.symmetric_difference(b).area/1e12)
try:
 print('OLD_CONTAINS_STAGE3',recipe['exact_subset_boundary_proof'](a,b))
 print('STAGE3_CONTAINS_OLD',recipe['exact_subset_boundary_proof'](b,a))
except Exception as e:print('EXACT_RELATION_HELD',type(e).__name__,str(e))
