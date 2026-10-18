"""Construct a literal existing-IO3 body mask; simplified faces never add space."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
from shapely.geometry import box,LineString
from shapely.ops import unary_union,nearest_points
import tri_route as T
from inventory import sha
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_declared_settings_projection_r58 as P
O=H/'exact-original-IO3-preservation-spine-r164'
def polys(x):return [x] if x.geom_type=='Polygon' else [p for p in getattr(x,'geoms',[]) if p.geom_type=='Polygon']
def write(name,x):(O/name).write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();R=H/'paired-regional-six-regulated-full-contact-audit-r142';old=pickle.loads((R/'ROOT_R22-regional-groups.pkl').read_bytes())['/IO_3V3'];new=pickle.loads((R/'REG_R130-regional-groups.pkl').read_bytes())['/IO_3V3']
 A=unary_union([q['shape'] for q in old[0] if q['kind']=='fill' and q['layer']=='In2.Cu']);start=unary_union([q['shape'] for q in new[5] if q['layer']=='In2.Cu']);end=unary_union([q['shape'] for q in new[0] if q['layer']=='In2.Cu']);aa,bb=nearest_points(start,end)
 rows=[];answer=None
 write('initial-endpoint-diagnostic.json',{'parent_receipt_sha256':sha(R/'receipt.json'),'start_bounds':list(start.bounds),'end_bounds':list(end.bounds),'global_nearest_start':list(aa.coords),'global_nearest_end':list(bb.coords),'nearest_distance_mm':aa.distance(bb),'start_rows':[{'kind':q['kind'],'uuid':q['uuid'],'bounds':list(q['shape'].bounds)} for q in new[5] if q['layer']=='In2.Cu']})
 for margin in (60.,100.,None):
  mask=A if margin is None else A.intersection(box(min(aa.x,bb.x)-margin,min(aa.y,bb.y)-margin,max(aa.x,bb.x)+margin,max(aa.y,bb.y)+margin))
  for width in (.3,.25,.2):
   free=mask.buffer(-width/2-.00002)
   for part in sorted(polys(free),key=lambda q:-q.area):
    if part.intersection(start).is_empty or part.intersection(end).is_empty:continue
    for tol in (.02,.005,0.):
     reduced=part if not tol else part.buffer(-tol*1.01).simplify(tol,preserve_topology=True).intersection(part)
     assert part.covers(reduced)
     for face in sorted(polys(reduced),key=lambda q:-q.area):
      sa=face.intersection(start);sb=face.intersection(end)
      if sa.is_empty or sb.is_empty:continue
      pa,pb=nearest_points(sa,sb);line=LineString([pa,pb]);body=P.bounded_buffer(line,width/2)
      route_info={'method':'literal_direct_coverage'}
      print('R164 face',margin,width,tol,'coords',len(face.exterior.coords)+sum(len(r.coords) for r in face.interiors),'endpoints',list(pa.coords),list(pb.coords),flush=True)
      if not A.covers(body):
       try:points,route_info=T.route(face,tuple(pa.coords[0]),tuple(pb.coords[0]))
       except (AssertionError,ValueError) as e:rows.append({'margin':margin,'width':width,'tol':tol,'reason':str(e)});write('checkpoint.json',rows);continue
       line=LineString([[round(x,6),round(y,6)] for x,y in points]);body=P.bounded_buffer(line,width/2)
      row={'margin':margin,'width':width,'tol':tol,'search':route_info,'complete_centerline_in_untouched_free':part.covers(line),'complete_body_in_original_IO3':A.covers(body),'start_overlap_mm2':body.intersection(start).area,'end_overlap_mm2':body.intersection(end).area};rows.append(row);write('checkpoint.json',rows)
      if row['complete_centerline_in_untouched_free'] and row['complete_body_in_original_IO3'] and row['start_overlap_mm2']>1e-8 and row['end_overlap_mm2']>1e-8:answer=(line,body,row);break
     if answer:break
    if answer:break
   if answer:break
  if answer:break
 if answer:
  line,body,row=answer;(O/'exact-old-IO3-retained-spine-mask.wkb').write_bytes(body.wkb);(O/'original-IO3-source-fill-union.wkb').write_bytes(A.wkb)
  write('receipt.json',{'verdict':'CONSTRUCTED_LITERAL_OLD_IO3_RETENTION_MASK_NOT_NEW_CU','parent_receipt_sha256':sha(R/'receipt.json'),'mask_sha256':sha(O/'exact-old-IO3-retained-spine-mask.wkb'),'original_fill_union_sha256':sha(O/'original-IO3-source-fill-union.wkb'),'points_mm':list(line.coords),'length_mm':line.length,'mask_bounds_mm':list(body.bounds),'complete_body_literal_old_source_fill_coverage':True,'search':row,'new_Cu_added':False,'old_native_definitions_modified':False})
 else:write('receipt.json',{'verdict':'NO_EXACT_MASK_CONSTRUCTED','attempts':rows,'new_Cu_added':False})
 print('R164 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
