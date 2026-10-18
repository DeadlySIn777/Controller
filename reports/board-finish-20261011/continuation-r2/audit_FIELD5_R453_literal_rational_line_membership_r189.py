"""Independent exact rational classification of the R453 line witness."""
import hashlib,json
from fractions import Fraction as Q
from pathlib import Path
from shapely import from_wkb
H=Path(__file__).resolve().parent
ROOT=H/'field-power/FIELD5-R451-record162-direct-outside-R-witness-attribution-r453'
OUT=H/'FIELD5-R453-independent-literal-rational-witness-classification-r189'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def point(c):return(Q.from_float(float(c[0])),Q.from_float(float(c[1])))
def sub(a,b):return(a[0]-b[0],a[1]-b[1])
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def along(a,b,t):return(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
def ring_location(p,ring):
 x,y=p;inside=False
 for a,b in zip(ring,ring[1:]):
  if cross(sub(b,a),sub(p,a))==0 and min(a[0],b[0])<=x<=max(a[0],b[0]) and min(a[1],b[1])<=y<=max(a[1],b[1]):return'BOUNDARY'
  if(a[1]>y)!=(b[1]>y):
   xin=a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])
   if xin>x:inside=not inside
 return'INTERIOR'if inside else'EXTERIOR'
def location(p,polys):
 boundary=False
 for rings in polys:
  loc=ring_location(p,rings[0])
  if loc=='EXTERIOR':continue
  if loc=='BOUNDARY':boundary=True;continue
  holes=[ring_location(p,r)for r in rings[1:]]
  if'INTERIOR'in holes:continue
  if'BOUNDARY'in holes:boundary=True;continue
  return'INTERIOR'
 return'BOUNDARY'if boundary else'EXTERIOR'
def read_polys(sh):
 if sh.is_empty:return[]
 ps=[sh]if sh.geom_type=='Polygon'else list(sh.geoms)
 assert all(p.geom_type=='Polygon'for p in ps)
 return[[[point(c)for c in p.exterior.coords],*[[point(c)for c in r.coords]for r in p.interiors]]for p in ps]
def split_parameters(a,b,polygons):
 r=sub(b,a);ts={Q(0),Q(1)}
 for polys in polygons.values():
  for rings in polys:
   for ring in rings:
    for c,d in zip(ring,ring[1:]):
     if max(a[0],b[0])<min(c[0],d[0])or min(a[0],b[0])>max(c[0],d[0])or max(a[1],b[1])<min(c[1],d[1])or min(a[1],b[1])>max(c[1],d[1]):continue
     s=sub(d,c);den=cross(r,s);delta=sub(c,a)
     if den:
      t=cross(delta,s)/den;u=cross(delta,r)/den
      if 0<=t<=1 and 0<=u<=1:ts.add(t)
     elif cross(delta,r)==0:
      index=0 if r[0] else 1
      for end in(c,d):
       t=(end[index]-a[index])/r[index]
       if 0<=t<=1:ts.add(t)
 return sorted(ts)
def main():
 assert not OUT.exists();OUT.mkdir();rp=ROOT/'receipt.json';assert sha(rp)=='bf2784e47fdb511f55237562a4656727412908be141f6e341083e468f35c1d2c'
 receipt=json.loads(rp.read_bytes());inputs={};polygons={}
 for name in('P','A','R','after'):
  row=receipt['actual_identity'][name];p=Path(row['file']);assert sha(p)==row['file_sha256'];inputs[name]={'file':str(p),'sha256':sha(p)};polygons[name]=read_polys(from_wkb(p.read_bytes()))
 p=ROOT/'direct_before_outside_R_loss.wkb';assert sha(p)=='851d7ec8'+sha(p)[8:]
 row=receipt['witnesses']['direct_before_outside_R_loss'];assert sha(p)==row['WKB_sha256'];w=from_wkb(p.read_bytes());assert w.geom_type=='LineString'
 coords=[point(c)for c in w.coords];reports=[];bad=0
 for i,(a,b)in enumerate(zip(coords,coords[1:])):
  if a==b:continue
  ts=split_parameters(a,b,polygons);samples=[('BREAKPOINT',t)for t in ts]+[('OPEN_INTERVAL_MIDPOINT',(t+u)/2)for t,u in zip(ts,ts[1:])if t!=u]
  rows=[]
  for kind,t in sorted(samples,key=lambda x:x[1]):
   pnt=along(a,b,t);loc={name:location(pnt,ps)for name,ps in polygons.items()};covered={name:v!='EXTERIOR'for name,v in loc.items()};loss=covered['A']and not covered['R']and not covered['after'];bad+=int(loss)
   rows.append({'kind':kind,'exact_segment_parameter':str(t),'point_mm_approx':[float(c)for c in pnt],'locations':loc,'actual_closed_literal_A_outside_R_outside_after':loss})
  reports.append({'witness_segment':i,'exact_boundary_split_count':len(ts),'rows':rows})
  print('R189_SEGMENT',i,'splits',len(ts),'literal_loss_samples',bad,flush=True)
 result={'verdict':'EXACT_LITERAL_WITNESS_CONTAINS_OUTSIDE_R_LOSS'if bad else'EXACT_LITERAL_WITNESS_HAS_NO_A_OUTSIDE_R_OUTSIDE_AFTER_POINTS','upstream_raw_GE0S_FAILURE_RETAINED':True,'receipt_sha256':sha(rp),'inputs':inputs,'witness_sha256':sha(p),'method':'binary64 WKB vertices interpreted as exact rationals; split each witness segment at every exact P/A/R/after boundary intersection; exact winding including boundaries at all split endpoints and each open interval midpoint','GEOS_boolean_operations_used':0,'geometry_or_precision_or_rules_changed':False,'no_area_or_length_threshold':True,'scope':'only preserved line witness, never a complete polygon subset, old-reference, source or native acceptance proof','literal_loss_classifications':bad,'segments':reports,'adopted':False,'manufacturing_ready':False}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print('R189_COMPLETE',result['verdict'],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
