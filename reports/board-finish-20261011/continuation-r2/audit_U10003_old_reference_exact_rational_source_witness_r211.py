"""Classify literal old-reference witness vertices without a precision waiver."""
import hashlib,json,pickle,sys
from fractions import Fraction
from pathlib import Path
from shapely import from_wkb
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import audit_FIELD5_R453_literal_rational_line_membership_r189 as X
OUT=H/'U10003-old-reference-exact-rational-source-witness-r211'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):
 if s.is_empty:return []
 if s.geom_type=='Polygon':return [s]
 return [p for g in getattr(s,'geoms',[])for p in parts(g)]
def main():
 assert not OUT.exists();OUT.mkdir()
 rp=H/'U10003-old-antipad-individual-source-array-diagnosis-r210/receipt.json';assert sha(rp)=='cd4db8c1edcb8b54f249cf3b6d1756882a8c2018aa25bd2c6a1fb3d7218378a2'
 r=json.loads(rp.read_bytes());polys={}
 for row in r['actual_individual_source_rows']:
  p=Path(row['file']);assert sha(p)==row['individual_actual_drilled_shape_WKB_sha256'];polys[row['side']+'_'+row['UUID']]=X.read_polys(from_wkb(p.read_bytes()))
 wp=H/'U10003-R196-unchanged-net-physical-identity-and-strict-oldrefs-r199/3aabe7ec-baf5-4304-ac89-079b0a62e545-direct-old-reference-loss.wkb';assert sha(wp)==r['raw_reference_loss_sha256'];w=from_wkb(wp.read_bytes());rows=[]
 for i,poly in enumerate(parts(w)):
  coords=[X.point(c)for c in list(poly.exterior.coords)[:-1]];p=(sum(c[0]for c in coords)/len(coords),sum(c[1]for c in coords)/len(coords));loc={k:X.location(p,v)for k,v in polys.items()};insidebefore=any(v!='EXTERIOR'for k,v in loc.items()if k.startswith('before_'));insideafter=any(v!='EXTERIOR'for k,v in loc.items()if k.startswith('after_'))
  row={'witness_polygon':i,'exact_vertex_average_point':[str(c)for c in p],'point_mm_approx':[float(c)for c in p],'individual_source_locations':loc,'actual_literal_before_source_outside_after':insidebefore and not insideafter};rows.append(row);print('R211_WITNESS',i,row['actual_literal_before_source_outside_after'],flush=True)
 mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';assert sha(mp)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5';g,h,b,q,full=pickle.loads(mp.read_bytes());padids={p['uuid']for p in h['pads']if p['ref']=='R10007'};pose={'footprint':next(f for f in h['footprints']if f['ref']=='R10007'),'pads':[p for p in h['pads']if p['uuid']in padids]};(OUT/'R10007-exact-current-pose-and-pads.json').write_text(json.dumps(pose,indent=1)+'\n')
 result={'verdict':'POINT_CLASSIFICATION_ONLY_RAW_FULL_REFERENCE_FAILURE_RETAINED','input_receipt_sha256':sha(rp),'witness_sha256':sha(wp),'GEOS_boolean_operations_used_for_classification':0,'method':'exact Fraction binary64 polygon vertices and exact vertex-average witness points; exact winding in each individual real source polygon; point test is not complete polygon subset proof','points':rows,'no_precision_area_or_rule_change':True,'adopted':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R211_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
