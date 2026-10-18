"""Decompose native single-outer ZONE records without changing physical support."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
import hashlib,importlib.util,json,re,uuid
import shapely
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CON=HERE/'separate-real-corridor-zone-construction-r7';OUT=HERE/'single-outer-real-corridor-native-r9';BASE=ROOT/'reports/board-finish-20261017/combined-route-stage-r3/native/board.kicad_pcb';OLD=ROOT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb';hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sp=importlib.util.spec_from_file_location('pcbtext',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
def parts(s):return sorted(([s]if s.geom_type=='Polygon'else list(s.geoms)),key=lambda p:(-p.area,p.bounds))
def integer_poly(p):
    rings=[]
    for ring in[p.exterior,*p.interiors]:
        row=[]
        for x,y in list(ring.coords)[:-1]:
            xi,yi=round(x*1e6),round(y*1e6);assert abs(x-xi/1e6)<1e-12 and abs(y-yi/1e6)<1e-12;row.append([xi,yi])
        rings.append(row)
    return rings
def main():
    assert not OUT.exists();OUT.mkdir();r=json.loads((CON/'receipt.json').read_text());assert sha(BASE)=='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca';raw=BASE.read_bytes();head,chunks,tail=H.split(raw);index={H.chunk_uuid(c):c for c in chunks if H.chunk_uuid(c)};oldindex={H.chunk_uuid(c):c for c in H.split(OLD.read_bytes())[1]if H.chunk_uuid(c)};template=r['original_field_zone_UUID_retained_exact'];assert index[template]==oldindex[template];data=[];minimal=[]
    families=[(r['field_zone_UUID'],template,CON/'field-new-real-corridor-intent.wkb',True)]+[(q['uuid'],q['uuid'],CON/(q['uuid']+'-native-negative-intent.wkb'),False)for q in r['FG_native_negative_splices']]
    for family,original,path,newfield in families:
        assert index[original]==oldindex[original];shape=shapely.from_wkb(path.read_bytes());pp=parts(shape);assert pp
        for i,p in enumerate(pp):
            uid=family if i==0 else str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/R299/native-single-outer/'+family+'/'+str(i)));action='add'if newfield or i else'replace';chunk=index[original]
            if action=='add':assert uid not in index;chunk=chunk.replace(('(uuid "'+original+'")').encode(),('(uuid "'+uid+'")').encode(),1);chunk=re.sub(rb'\n\t\t\(name "[^"\n]*"\)',('\n\t\t(name "'+('FIELD5 real current corridor 50um'if newfield else'FIELD_GND retained source region')+' part '+str(i+1)+'")').encode(),chunk,count=1)
            else:(OUT/(uid+'-before.exact-native-zone-chunk')).write_bytes(chunk)
            minimal.append(chunk);data.append({'uuid':uid,'family_original_UUID':family,'template_UUID':original,'action':action,'polygons_integer_IU':[integer_poly(p)],'input_WKB':str(path),'input_WKB_SHA256':sha(path),'part_area_mm2':p.area,'before_chunk_SHA256':hashlib.sha256(index[uid]).hexdigest()if action=='replace'else None})
    q=OUT/'minimal-zone-only-input.kicad_pcb';q.write_bytes(head+b''.join(c for c in chunks if H.chunk_uuid(c)is None)+b''.join(minimal)+tail)
    pins={str(p):sha(p)for p in(BASE,OLD,hp,CON/'receipt.json',Path(__file__))};d={'stage3_board':str(BASE),'stage3_board_SHA256':sha(BASE),'original_FIELD5_zone_UUID_and_chunk_preserved':template,'original_FIELD5_chunk_SHA256':hashlib.sha256(index[template]).hexdigest(),'minimal_native_input':str(q),'minimal_native_input_SHA256':sha(q),'minimal_native_output':str(OUT/'minimal-zone-only-output.kicad_pcb'),'zones':data,'input_sha256':pins,'all_five_FG_before_chunks_equal_genuine_R299':True,'all_finite_support_parts_retained_no_shape_dropped':True,'new_holes':0,'fill_called':False,'adopted':False};(OUT/'input.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'single_outer_zones':len(data),'adds':sum(x['action']=='add'for x in data),'replacements':sum(x['action']=='replace'for x in data)}))
if __name__=='__main__':main()
