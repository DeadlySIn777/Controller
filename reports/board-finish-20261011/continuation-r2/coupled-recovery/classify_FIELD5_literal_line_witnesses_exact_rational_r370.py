"""Primitive-only Fraction certificate; no GEOS predicates or Boolean waiver."""
from pathlib import Path
import sys,json,hashlib,time
from fractions import Fraction as F
from shapely import from_wkb
H=Path(__file__).resolve().parent;P=H.parent;out=H/'FIELD5-zero-area-line-primitive-rational-certificate-r370';assert not out.exists();out.mkdir();start=time.monotonic()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def fracpt(p):return tuple(F.from_float(float(x))for x in p[:2])
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return(a[0]-b[0],a[1]-b[1])
def rings(s):
 if s.geom_type=='Polygon':return [[list(map(fracpt,s.exterior.coords))]+[list(map(fracpt,r.coords))for r in s.interiors]]
 return[p for x in s.geoms for p in rings(x)]
def lines(s):
 if s.geom_type=='LineString':return[list(map(fracpt,s.coords))]
 if s.geom_type in('MultiLineString','GeometryCollection'):return[q for g in s.geoms for q in lines(g)]
 raise ValueError('Witness must be actual line primitive '+s.geom_type)
def on(p,a,b):return cross(sub(p,a),sub(b,a))==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0])and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def ringloc(p,ring):
 winding=0
 for a,b in zip(ring,ring[1:]):
  if on(p,a,b):return'BOUNDARY'
  c=cross(sub(b,a),sub(p,a))
  if a[1]<=p[1]<b[1]and c>0:winding+=1
  elif b[1]<=p[1]<a[1]and c<0:winding-=1
 return'INTERIOR'if winding else'EXTERIOR'
def locate(p,polys):
 boundary=False
 for rr in polys:
  outer=ringloc(p,rr[0])
  if outer=='EXTERIOR':continue
  holes=[ringloc(p,r)for r in rr[1:]]
  if 'INTERIOR'in holes:continue
  if outer=='INTERIOR'and'BOUNDARY'not in holes:return'INTERIOR'
  boundary=True
 return'BOUNDARY'if boundary else'EXTERIOR'
def param(p,a,b):return(p[0]-a[0])/(b[0]-a[0])if b[0]!=a[0]else(p[1]-a[1])/(b[1]-a[1])
def splits(a,b,polys):
 r=sub(b,a);cuts={F(0),F(1)}
 for rr in polys:
  for ring in rr:
   for c,d in zip(ring,ring[1:]):
    s=sub(d,c);den=cross(r,s)
    if den:
     t=cross(sub(c,a),s)/den;u=cross(sub(c,a),r)/den
     if 0<=t<=1 and 0<=u<=1:cuts.add(t)
    elif cross(sub(c,a),r)==0:
     for p in(c,d):
      if on(p,a,b):cuts.add(param(p,a,b))
 return cuts
def xy(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def rat(v):return str(v.numerator)+'/'+str(v.denominator)
def analyse(label,witness,paths,claim):
 raws={k:Path(v).read_bytes()for k,v in paths.items()};ps={k:rings(from_wkb(v))for k,v in raws.items()};w=from_wkb(witness.read_bytes());rows=[];violations=[]
 for li,line in enumerate(lines(w)):
  for si,(a,b)in enumerate(zip(line,line[1:])):
   assert a!=b;cut=sorted(set().union(*(splits(a,b,p)for p in ps.values())));points=[];intervals=[]
   for t in cut:
    p=xy(a,b,t);loc={k:locate(p,polys)for k,polys in ps.items()};entry={'t':rat(t),'xy_float_display':[float(x)for x in p],'xy_exact_binary_float_rationals':[rat(x)for x in p],'classification':loc};points.append(entry)
    if claim(loc):violations.append({'kind':'vertex','line':li,'segment':si,**entry})
   for l,r in zip(cut,cut[1:]):
    mid=(l+r)/2;p=xy(a,b,mid);loc={k:locate(p,polys)for k,polys in ps.items()};entry={'open_t_interval':[rat(l),rat(r)],'representative_t':rat(mid),'classification':loc,'exact_boundary_intersections_exhaustive':True};intervals.append(entry)
    if claim(loc):violations.append({'kind':'open_segment_interval','line':li,'segment':si,**entry})
   rows.append({'line':li,'segment':si,'actual_witness_endpoint_rationals':[[rat(x)for x in p]for p in(a,b)],'all_exact_boundary_crossings_and_vertices':points,'all_open_intervals':intervals})
 result={'label':label,'witness_file':str(witness),'witness_sha256':sha(witness),'witness_GEOMETRY_type':w.geom_type,'primitive_count':sum(len(s)-1 for s in lines(w)),'input_POLYGON_bindings':{k:{'file':str(paths[k]),'sha256':sha(paths[k]),'ring_count':sum(len(p)for p in ps[k])}for k in ps},'all_actual_segments_and_open_intervals':rows,'true_literal_proposed_boolean_membership_witnesses':violations,'primitive_literal_claim_is_empty':not violations,'no_geometry_mutation_no_GE0S_predicates_no_rounding_no_area_tolerance':True,'original_operational_GE0S_FAIL_preserved':True};put(out/(label+'.json'),result);return result
field=P/'field-power';r445=field/'FIELD5-R385-minimal-R155-immutable-parent-subtractive-rim-restoration-r445';stem='c1d27fa1-452b-4e27-985d-5ad23644d800-In4.Cu-immutable-parent-';paths={k:r445/(stem+'136-'+k+'.wkb')for k in('P','A','R','after')};closed=lambda z:z!='EXTERIOR'
a=analyse('record136-derived-gain-outside-R',r445/'record136-literal-outside-R-gain.wkb',paths,lambda l:closed(l['after'])and not closed(l['A'])and not closed(l['R']))
r453=field/'FIELD5-R451-record162-direct-outside-R-witness-attribution-r453';rr=json.loads((r453/'receipt.json').read_text());put(out/'record162-original-attribution-bound.json',{'original_receipt_sha256':sha(r453/'receipt.json'),'original_receipt':rr});r451=field/'FIELD5-R385-minimal-R155-immutable-parent-raw-FAIL-diagnostic-r451';paths={k:r451/(stem+'162-'+k+'.wkb')for k in('P','A','R','after')};b=analyse('record162-direct-outside-R-loss',r453/'direct_before_outside_R_loss.wkb',paths,lambda l:closed(l['A'])and not closed(l['R'])and not closed(l['after']))
report={'verdict':'EXACT_PRIMITIVE_LINE_CERTIFICATE_READ_ONLY_NO_GATE_WAIVER','record136_primitive_actual_new_gain_outside_R_empty':a['primitive_literal_claim_is_empty'],'record162_primitive_actual_lost_old_Cu_outside_R_empty':b['primitive_literal_claim_is_empty'],'all_original_GE0S_failed_receipts_models_native_source_unchanged':True,'no_operational_FAIL_promoted':True,'no_tolerance_no_snapping_no_model_change':True,'native_jobs':0,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',report);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**report}),flush=True)
