"""Read the actual native rectangle courtyard; retain unsupported R23 result."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'census_CDone_actual_current_B_anchors_own_source_returns_r23.py';text=old.read_text();out=H/'FPGA-CDONE-isolated-producer-current-B-anchor-own-SOURCE-return-census-r23'
assert out.exists()and not(out/'receipt.json').exists();(out/'reader-failure.json').write_text(json.dumps({'reason':'Courtyard reader handled fp_line/fp_poly but omitted modern native fp_rect; no scope or candidate produced','native_jobs':0,'adopted':False},indent=1)+'\n')
text=text.replace('FPGA-CDONE-isolated-producer-current-B-anchor-own-SOURCE-return-census-r23','FPGA-CDONE-actual-native-courtyard-current-anchor-return-census-r24')
before=" courtyard=unary_union(polygons+list(polygonize(lines)));"
insert=""" for rect in children(fp,'fp_rect'):
  if atom(rect,'layer')=='F.CrtYd':
   aa=child(rect,'start')[1:3];bb=child(rect,'end')[1:3];polygons.append(box(loc[0]+min(float(aa[0]),float(bb[0])),loc[1]+min(float(aa[1]),float(bb[1])),loc[0]+max(float(aa[0]),float(bb[0])),loc[1]+max(float(aa[1]),float(bb[1]))))
 put('native-footprint-courtyard-primitive-schema.json',[{'kind':p[0],'layer':atom(p,'layer')}for p in fp[1:]if isinstance(p,list)and p[0].startswith('fp_')and atom(p,'layer')and 'CrtYd'in atom(p,'layer')])
 courtyard=unary_union(polygons+list(polygonize(lines)));"""
assert before in text;text=text.replace(before,insert)
dest=H/'census_CDone_actual_native_rect_courtyard_r24.generated.py';assert not dest.exists();dest.write_text(text)
(H/'CDONE-r24-native-courtyard-reader-correction.json').write_text(json.dumps({'source_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'generated_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'geometric_scope_from_actual_native_courtyard_only':True,'no_approximate_invented_part_bbox':True},indent=1)+'\n')
exec(compile(text,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
