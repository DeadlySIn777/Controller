"""Exact planar arrangement audit of the six preserved raw reference witnesses."""
import hashlib,json,sys
from fractions import Fraction as Q
from pathlib import Path
from shapely import from_wkb
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import audit_FIELD5_R453_literal_rational_line_membership_r189 as X
OUT=H/'U10003-old-reference-exact-rational-arrangement-r212'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edges(ps):return[(a,b)for rings in ps for ring in rings for a,b in zip(ring,ring[1:])if a!=b]
def overlap_box(a,b,lo,hi):return not(max(a[0],b[0])<lo[0]or min(a[0],b[0])>hi[0]or max(a[1],b[1])<lo[1]or min(a[1],b[1])>hi[1])
def main():
 assert not OUT.exists();OUT.mkdir();rp=H/'U10003-old-antipad-individual-source-array-diagnosis-r210/receipt.json';assert sha(rp)=='cd4db8c1edcb8b54f249cf3b6d1756882a8c2018aa25bd2c6a1fb3d7218378a2'
 r=json.loads(rp.read_bytes());polygons={};inputs=[]
 for row in r['actual_individual_source_rows']:
  p=Path(row['file']);assert sha(p)==row['individual_actual_drilled_shape_WKB_sha256'];polygons[row['side']+'_'+row['UUID']]=X.read_polys(from_wkb(p.read_bytes()));inputs.append({'file':str(p),'sha256':sha(p)})
 wp=H/'U10003-R196-unchanged-net-physical-identity-and-strict-oldrefs-r199/3aabe7ec-baf5-4304-ac89-079b0a62e545-direct-old-reference-loss.wkb';assert sha(wp)==r['raw_reference_loss_sha256'];wpolys=X.read_polys(from_wkb(wp.read_bytes()));reports=[];allbad=[]
 sourceedges=[e for ps in polygons.values()for e in edges(ps)]
 for wi,w in enumerate(wpolys):
  local={**polygons,'witness':[w]};allcoords=[p for ring in w for p in ring];lo=tuple(min(p[k]for p in allcoords)for k in(0,1));hi=tuple(max(p[k]for p in allcoords)for k in(0,1));boundaries=edges([w])+[e for e in sourceedges if overlap_box(*e,lo,hi)]
  splitps={'nearby_boundaries':[[[a,b,a]]for a,b in boundaries]};seen=set();counts={'boundary_vertices':0,'open_interval_midpoints':0,'adjacent_face_points':0};bad=[]
  def check(p,kind):
   if p in seen:return
   seen.add(p);counts[kind]+=1;loc={k:X.location(p,ps)for k,ps in local.items()};inside=loc['witness']!='EXTERIOR';before=any(v!='EXTERIOR'for k,v in loc.items()if k.startswith('before_'));after=any(v!='EXTERIOR'for k,v in loc.items()if k.startswith('after_'))
   if inside and before and not after:bad.append({'kind':kind,'point_exact':[str(x)for x in p],'point_mm_approx':[float(x)for x in p],'locations':loc})
  for a,b in boundaries:
   ts=X.split_parameters(a,b,splitps)
   for t in ts:check(X.along(a,b,t),'boundary_vertices')
   for t,u in zip(ts,ts[1:]):
    if t==u:continue
    m=X.along(a,b,(t+u)/2);check(m,'open_interval_midpoints');delta=X.sub(b,a);normal=(-delta[1],delta[0]);scale=max(abs(x)for x in normal)
    for sign in(-1,1):
     end=(m[0]+sign*normal[0]/scale/1000,m[1]+sign*normal[1]/scale/1000);crossings=X.split_parameters(m,end,splitps);positive=[x for x in crossings if x>0];step=min(positive)/2 if positive else Q(1);check(X.along(m,end,step),'adjacent_face_points')
  row={'witness_polygon':wi,'exact_arrangement_edges':len(boundaries),'point_counts':counts,'literal_loss_points':bad};reports.append(row);allbad+=bad;print('R212_WITNESS',wi,'points',sum(counts.values()),'loss',len(bad),flush=True)
 result={'verdict':'EXACT_RAW_WITNESS_HAS_REAL_SOURCE_LOSS'if allbad else'EXACT_ARRANGEMENT_RAW_WITNESS_BEFORE_SOURCE_SUPPORT_PRESERVED_BY_INDIVIDUAL_AFTER_SOURCE','source_receipt_sha256':sha(rp),'inputs':inputs,'witness_sha256':sha(wp),'raw_GE0S_reference_failure_preserved':True,'source_or_geometry_or_precision_or_area_or_rules_changed':False,'GEOS_boolean_operations_used':0,'method':'Every witness edge and every source boundary with overlapping exact bounds is split at all exact rational intersections. Every split vertex and interval midpoint is classified. Both adjacent faces are sampled along exact perpendicular rays stopped before the nearest exact boundary intersection. All witness-bounded faces, line boundaries and vertices are represented; winding in individual actual source polygons uses literal binary64 vertices as rational numbers. No area or length tolerance.','scope':'only six raw R199 witness polygons and their individual actual J3-rooted source support; does not clear any other reference or native/current gate','reports':reports,'literal_loss_classification_count':len(allbad),'adopted':False,'manufacturing_ready':False}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R212_COMPLETE',len(allbad),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
