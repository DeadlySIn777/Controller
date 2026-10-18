"""Preserve both CORE60 fragments with one native outer contour per zone UUID."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import runpy,json,hashlib,uuid
from pathlib import Path
from shapely import from_wkb
H=Path(__file__).resolve().parent;S=runpy.run_path(str(H/'restage_CORE69_DIR7_negative_on_stage3_r2.py'));R=S['R'];K=S['K']
PRIOR=H/'coupled-CORE60-preserved-fragments-stage3-candidate-r1';OUT=H/'CORE60-single-outer-native-roundtrip-r2';SOURCE=S['SOURCE'];UID='60c95fa7-e6df-530f-a3d3-00d3f96e46bc'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
def main():
    assert not OUT.exists();assert sha(SOURCE)==S['EXPECTED'];raw=SOURCE.read_bytes();head,chunks,tail=K.C.pcbtext.split(raw);iv=K.C.inventory(raw)
    old=iv[3][UID];prior=json.loads((PRIOR/'receipt.json').read_bytes());assert digest(old)==prior['operations'][0]['old_zone_chunk_SHA256']
    pieces=sorted(R['parts'](from_wkb((PRIOR/'exact-retained-fragments-native-IU.wkb').read_bytes())),key=lambda p:(-p.area,p.bounds));assert len(pieces)==2
    OUT.mkdir();records=[];zonechunks=[];lo,hi,_=S['polys'](old)[0]
    for i,poly in enumerate(pieces):
        assert not poly.interiors;uid=UID if i==0 else str(uuid.uuid5(uuid.UUID(UID),'retained-guarded-return-window-fragment/'+digest(poly.wkb)))
        assert i==0 or uid not in iv[3]
        native=old[:lo]+R['render_ring'](poly.exterior).strip()+old[hi:]
        if i:
            native=native.replace(('(uuid "'+UID+'")').encode(),('(uuid "'+uid+'")').encode(),1)
        # Intent-only mini fixture; clear every stale cache, preserving settings.
        for a,b,k in reversed(R['polygon_spans'](native)):
            if k in(b'filled_polygon',b'fill_segments'):native=native[:a]+native[b:]
        native=native.replace(b'\n\t\t(fill yes\n',b'\n\t\t(fill\n',1)
        comparable=native if i==0 else native.replace(('(uuid "'+uid+'")').encode(),('(uuid "'+UID+'")').encode(),1)
        assert S['profile'](comparable)==S['profile'](old)
        path=OUT/(uid+'-input.zone-chunk');path.write_bytes(native);zonechunks.append(native)
        records.append({'UUID':uid,'original_UUID':UID,'action':'replace'if i==0 else'add_child_same_profile','all_real_fragments_kept':True,'native_integer_outer_IU':[[int(x),int(y)]for x,y in list(poly.exterior.coords)[:-1]],'native_holes_IU':[],'area_mm2':poly.area/1e12,'input_zone_chunk':str(path),'input_zone_chunk_SHA256':sha(path)})
    headers=b''.join(c for c in chunks if K.C.pcbtext.chunk_uuid(c)is None)
    mini=OUT/'minimal-single-outer-input.kicad_pcb';mini.write_bytes(head+headers+b''.join(zonechunks)+tail)
    legacy=OUT/'held-multiple-outer-parser-reproduction.kicad_pcb';legacy.write_bytes(head+headers+(PRIOR/'exact-stage3-after.zone-chunk').read_bytes()+tail)
    pins={str(f):sha(f)for f in(Path(__file__),SOURCE,PRIOR/'receipt.json',PRIOR/'exact-retained-fragments-native-IU.wkb',PRIOR/'per-component-per-edge-exact-native-IU-subset-proof.json',PRIOR/'exact-stage3-after.zone-chunk')}
    d={'status':'TWO_REAL_FRAGMENTS_ONE_OUTER_PER_UUID_NATIVE_ROUNDTRIP_PENDING','source':str(SOURCE),'source_SHA256':sha(SOURCE),'original_zone_UUID':UID,'deterministic_child_UUID':records[1]['UUID'],'native_input':str(mini),'native_input_SHA256':sha(mini),'native_saved_output':str(OUT/'minimal-single-outer-native-saved.kicad_pcb'),'held_legacy_fixture':str(legacy),'held_legacy_fixture_SHA256':sha(legacy),'zones':records,'input_SHA256':pins,'fresh_CPP_fill_references_current_IR_minwidth_thermal':'OPEN_REQUIRED','adopted':False}
    (OUT/'input.json').write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8');print(json.dumps({'child_UUID':records[1]['UUID'],'input_SHA256':sha(OUT/'input.json')}))
if __name__=='__main__':main()
