"""Exact rational nm² proof for two floating boundary-distance diagnostics."""
from pathlib import Path
import pickle,json,hashlib,sys
from decimal import Decimal
from fractions import Fraction
from shapely.geometry import Point
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
O=H/'sbc-power/SAFE-exact-integer-boundary-apertures-r155'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nm(x):
 v=Decimal(str(x))*1000000;assert v==v.to_integral_value(),('not_exact_native_integer_nm',x);return int(v)
def dist2(P,A,B):
 ax,ay=A[0]-P[0],A[1]-P[1];dx,dy=B[0]-A[0],B[1]-A[1];length=dx*dx+dy*dy
 if not length:return Fraction(ax*ax+ay*ay)
 dot=-(ax*dx+ay*dy)
 if dot<=0:return Fraction(ax*ax+ay*ay)
 if dot>=length:
  bx,by=B[0]-P[0],B[1]-P[1];return Fraction(bx*bx+by*by)
 return Fraction((ax*dy-ay*dx)**2,length)
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/safe-owned-zone-normalization-r149/model.pkl';g,h,b,z,c=pickle.loads(mp.read_bytes());rf=H/'sbc-power/SAFE-independent-true-geometry-r152/receipt.json';r=json.loads(rf.read_bytes());assert r['model_sha256']==sha(mp)
 rows=[]
 for e in r['errors']:
  if e['gate']!='NEW_via_hole_every_SMD_Cu':continue
  v=next(v for v in h['vias'] if v['uuid']==e['owned_UUID']);p=next(p for p in h['pads'] if p['uuid']==e['other_UUID']);P=(nm(v['x']),nm(v['y']));pieces=[]
  for layer,ps in p['layers'].items():
   for shape in C.poly(ps):
    assert not shape.covers(Point(v['x'],v['y']))
    ds=[]
    for ring in [shape.exterior,*shape.interiors]:
     points=[(nm(x),nm(y)) for x,y in ring.coords]
     for a,bb in zip(points,points[1:]):ds.append(dist2(P,a,bb))
    d=min(ds);req=Fraction(nm(v['drill']),2)+275000
    pieces.append({'layer':layer,'exact_distance_squared_nm2_numerator':d.numerator,'exact_distance_squared_nm2_denominator':d.denominator,'required_center_distance_nm_numerator':req.numerator,'required_center_distance_nm_denominator':req.denominator,'exact_squared_comparison_PASS':d>=req*req,'exact_equality_on_required_boundary':d==req*req,'actual_native_polygon_sha256':hashlib.sha256(shape.wkb).hexdigest()})
  rows.append({'original_float_diagnostic':e,'via_exact_record':v,'SMD_ref':p['ref'],'SMD_pin':p['num'],'pad_UUID':p['uuid'],'integer_point_nm':P,'actual_native_polygon_pieces':pieces,'PASS':bool(pieces) and all(q['exact_squared_comparison_PASS'] for q in pieces)})
 assert len(rows)==2
 receipt={'verdict':'PASS_EXACT_INTEGER_NM_BOUNDARY_APERTURES' if all(r['PASS'] for r in rows) else 'FAIL_EXACT_INTEGER_NM_BOUNDARY_APERTURES','model_sha256':sha(mp),'source_independent_float_gate_sha256':sha(rf),'rows':rows,'required_hole_to_every_SMD_Cu_mm':.275,'no_tolerance_or_coordinate_or_geometry_change':True,'no_native_or_planning_rule_waiver':True,'native_jobs':0,'board_written':False}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('SAFE_INTEGER_APERTURES',receipt['verdict'],[(r['SMD_ref'],r['SMD_pin'],r['PASS'],[p['exact_equality_on_required_boundary'] for p in r['actual_native_polygon_pieces']]) for r in rows],sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
