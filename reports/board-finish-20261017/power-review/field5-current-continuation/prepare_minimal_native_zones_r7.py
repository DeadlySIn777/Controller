"""Six intended zones only, with exact stage3 and genuine R299 source bindings."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
import hashlib,importlib.util,json,re
import shapely
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CON=HERE/'separate-real-corridor-zone-construction-r7';OUT=HERE/'separate-real-corridor-native-r7'
BASE=ROOT/'reports/board-finish-20261017/combined-route-stage-r3/native/board.kicad_pcb';OLD=ROOT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb';hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sp=importlib.util.spec_from_file_location('pcbtext',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
def rows(s):
    result=[]
    for p in([s]if s.geom_type=='Polygon'else list(s.geoms)):
        rr=[]
        for ring in[p.exterior,*p.interiors]:
            cc=[]
            for x,y in list(ring.coords)[:-1]:
                xi,yi=round(x*1e6),round(y*1e6);assert abs(x-xi/1e6)<1e-12 and abs(y-yi/1e6)<1e-12;cc.append([xi,yi])
            rr.append(cc)
        result.append(rr)
    return result
def main():
    assert not OUT.exists();OUT.mkdir();r=json.loads((CON/'receipt.json').read_text());assert sha(BASE)=='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca';raw=BASE.read_bytes();head,chunks,tail=H.split(raw);index={H.chunk_uuid(c):c for c in chunks if H.chunk_uuid(c)};oldindex={H.chunk_uuid(c):c for c in H.split(OLD.read_bytes())[1]if H.chunk_uuid(c)};ids=[r['field_zone_UUID']]+[q['uuid']for q in r['FG_native_negative_splices']];template=r['original_field_zone_UUID_retained_exact'];assert index[template]==oldindex[template]
    minimal=[];data=[]
    for uid in ids:
        addition=uid==ids[0]
        if addition:
            chunk=index[template].replace(('(uuid "'+template+'")').encode(),('(uuid "'+uid+'")').encode(),1);chunk=re.sub(rb'\n\t\t\(name "[^"\n]*"\)',b'\n\t\t(name "FIELD5 In2 real current corridor lateral widening 50um")',chunk,count=1);path=CON/'field-new-real-corridor-intent.wkb';assert uid not in index
        else:
            assert index[uid]==oldindex[uid];chunk=index[uid];path=CON/(uid+'-native-negative-intent.wkb');(OUT/(uid+'-before.exact-native-zone-chunk')).write_bytes(chunk)
        shape=shapely.from_wkb(path.read_bytes());data.append({'uuid':uid,'action':'add'if addition else'replace','polygons_integer_IU':rows(shape),'input_WKB':str(path),'input_WKB_SHA256':sha(path),'before_chunk_SHA256':None if addition else hashlib.sha256(index[uid]).hexdigest()});minimal.append(chunk)
    keep=[c for c in chunks if H.chunk_uuid(c)is None];p=OUT/'minimal-zone-only-input.kicad_pcb';p.write_bytes(head+b''.join(keep)+b''.join(minimal)+tail)
    pins={str(p):sha(p)for p in(BASE,OLD,hp,CON/'receipt.json',Path(__file__))};d={'stage3_board':str(BASE),'stage3_board_SHA256':sha(BASE),'original_FIELD5_zone_UUID_and_chunk_preserved':template,'original_FIELD5_chunk_SHA256':hashlib.sha256(index[template]).hexdigest(),'minimal_native_input':str(p),'minimal_native_input_SHA256':sha(p),'minimal_native_output':str(OUT/'minimal-zone-only-output.kicad_pcb'),'zones':data,'input_sha256':pins,'all_five_FG_before_chunks_equal_genuine_R299':True,'new_holes':0,'fill_called':False,'adopted':False};(OUT/'input.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'zones':len(data),'input':str(p),'stage3':sha(BASE)}))
if __name__=='__main__':main()
