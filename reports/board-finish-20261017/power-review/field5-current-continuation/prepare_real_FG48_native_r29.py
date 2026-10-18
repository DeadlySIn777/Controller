"""Exact native one-outer source roles for the real FG48 bridge diagnostic."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
import hashlib,importlib.util,json,uuid
import shapely
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CON=HERE/'real-FG48-LG-plane-stitch-host-r28';OUT=HERE/'real-FG48-native-single-outer-r29';BASE=ROOT/'reports/board-finish-20261017/combined-route-stage-r3/native/board.kicad_pcb';OLD=ROOT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb';hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sp=importlib.util.spec_from_file_location('pcbtext',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
def main():
 assert not OUT.exists();OUT.mkdir();r=json.loads((CON/'receipt.json').read_text());assert 'GATES_PASS'in r['status'];assert sha(BASE)=='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca';head,cc,tail=H.split(BASE.read_bytes());index={H.chunk_uuid(c):c for c in cc if H.chunk_uuid(c)};oi={H.chunk_uuid(c):c for c in H.split(OLD.read_bytes())[1]if H.chunk_uuid(c)};rows=[];minimal=[];files=[BASE,OLD,CON/'receipt.json',hp,Path(__file__)]
 for edit in r['explicit_LG_source_plane_only_targets']:
  zid=edit['uuid'];assert index[zid]==oi[zid];source=CON/(zid+'-native-negative-intent.wkb');files.append(source);shape=shapely.from_wkb(source.read_bytes());pp=sorted(([shape]if shape.geom_type=='Polygon'else list(shape.geoms)),key=lambda p:(-p.area,p.bounds))
  for i,p in enumerate(pp):
   uid=zid if i==0 else str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/R299/FG48-2mm-stitch/LG-source/'+zid+'/'+str(i)));chunk=index[zid]
   if i:assert uid not in index;chunk=chunk.replace(('(uuid "'+zid+'")').encode(),('(uuid "'+uid+'")').encode(),1)
   rings=[]
   for ring in[p.exterior,*p.interiors]:
    rr=[]
    for x,y in list(ring.coords)[:-1]:
     xi,yi=round(x*1e6),round(y*1e6);assert abs(x-xi/1e6)<1e-12 and abs(y-yi/1e6)<1e-12;rr.append([xi,yi])
    rings.append(rr)
   row={'uuid':uid,'action':'replace'if i==0 else'add','template_UUID':zid,'family_original_UUID':zid,'polygons_integer_IU':[rings],'part_source_area_mm2':p.area,'native_profile_and_name_exact_to_original_except_new_UUID':True,'input_WKB':str(source),'input_WKB_SHA256':sha(source)}
   if not i:row['before_chunk_SHA256']=hashlib.sha256(index[zid]).hexdigest()
   rows.append(row);minimal.append(chunk)
  (OUT/(zid+'-before.exact-native-zone-chunk')).write_bytes(index[zid])
 q=OUT/'minimal-zone-only-input.kicad_pcb';q.write_bytes(head+b''.join(c for c in cc if H.chunk_uuid(c)is None)+b''.join(minimal)+tail);d={'stage3_board':str(BASE),'stage3_board_SHA256':sha(BASE),'minimal_native_input':str(q),'minimal_native_input_SHA256':sha(q),'minimal_native_output':str(OUT/'minimal-zone-only-output.kicad_pcb'),'zones':rows,'input_sha256':{str(p):sha(p)for p in files},'all_real_source_parts_retained_no_tiny_area_waiver':True,'new_holes':0,'native_fill_called':False,'adopted':False};(OUT/'input.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'source_parts':len(rows),'parts':[{k:v for k,v in x.items()if k in('uuid','action','part_source_area_mm2')}for x in rows]}))
if __name__=='__main__':main()
