"""Real negative owned-FG prototype; no LG cache substitution or waiver."""
import os,sys
sys.dont_write_bytecode=True
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,math,time,gc
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2';P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
B=OLD/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
for d in (OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
from emit_logic_zones_r1 import ring as render_ring
K=N.K;L=N.L;FG='/motherboard_motors/FIELD_GND';UID='ff5ffe1e-111b-5951-957a-dfd8894ca90c'
SOURCE=OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/copy/board.kicad_pcb'
OUT=HERE/'owned-FG-negative-four-conflicts-intent-only-r4';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()

def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def info(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def save(label,s):
    r=info(s);f=OUT/(label+'.wkb');f.write_bytes(s.wkb);r['file']=str(f);return r
def integer_replay(shape):
    pieces=[]
    for p in K.RF.parts(shape):
        convert=lambda r:[(round(x*1e6)/1e6,round(y*1e6)/1e6)for x,y in r.coords]
        q=Polygon(convert(p.exterior),[convert(r)for r in p.interiors]);assert q.is_valid
        pieces.append(q)
    return unary_union(pieces)
def polygon_spans(raw):
    spans=[];depth=0;start=None;quoted=False;escape=False
    for i,c in enumerate(raw):
        if quoted:
            if escape:escape=False
            elif c==92:escape=True
            elif c==34:quoted=False
            continue
        if c==34:quoted=True;continue
        if c==40:
            if depth==1:start=i
            depth+=1
        elif c==41:
            depth-=1
            if depth==1:
                token=raw[start+1:i].split(None,1)[0]
                if token in(b'polygon',b'filled_polygon',b'fill_segments'):spans.append((start,i+1,token))
    assert depth==0;return spans

def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    h=pickle.loads((P/'actual-combined-full-after-model.pkl').read_bytes())
    zone=next(z for z in h['zones']if z['uuid']==UID);assert L.norm(zone['net'])==FG and zone['layers']==['In1.Cu']
    intended=unary_union(L.poly(N.O.polys(zone['outline'])));physical=unary_union(L.poly(zone['fills']['In1.Cu']))
    assert intended.geom_type=='Polygon'
    files=[P/('oldref-'+u+'.wkb')for u in('942659fe-dca8-4a36-af79-d5a05f611887','028ef3d3-2b43-440e-a40f-06eeffe3d727','2598f69f-b3cf-49d3-b1d2-4aec82df028b','f9b50d70-650b-42a2-9071-cc19903a46e2')]
    raw_required=[from_wkb(f.read_bytes())for f in files];required=unary_union([shape.boundary for shape in raw_required]);save('required-prior-LG-reference-boundaries-all-components',required)
    raw=SOURCE.read_bytes();inventory=K.C.inventory(raw);oldchunk=inventory[3][UID];(OUT/'exact-before-ff5ffe.zone-chunk').write_bytes(oldchunk)
    trials=[]
    for guard in(.600001,):
        label='guard-'+str(round(guard*1e6));cut=K.Z.bounded_buffer(required,guard);shape=intended.difference(cut);reserves=[]
        for iteration in range(8):
            final=integer_replay(shape);gain=final.difference(intended)
            if gain.is_empty:break
            reserve=K.Z.bounded_buffer(gain,.0001);reserves.append({'iteration':iteration,'raw_serialize_gain':save(label+'-serialize-gain-'+str(iteration),gain),'explicit_additional_negative':save(label+'-extra-negative-'+str(iteration),reserve)})
            shape=final.difference(reserve)
        else:raise AssertionError('No zero-gain native integer construction')
        assert final.difference(intended).is_empty and final.geom_type=='Polygon'
        negative=intended.difference(final)
        assert all(cut.covers(shape)for shape in raw_required), 'Every raw witness component must be enclosed'
        negative_info=save(label+'-explicit-owned-native-negative',negative)
        touched=[]
        for z in h['zones']:
            if z['uuid']!=UID:continue
            for record_index,oldshape in enumerate(L.poly(z['fills']['In1.Cu'])):
                if oldshape.intersects(negative):touched.append({'record':record_index,'record_SHA256':hashlib.sha256(oldshape.wkb).hexdigest(),'negative_intersection_area_mm2':oldshape.intersection(negative).area})
        # Canonical native integer outline replaces polygon children only.
        spans=polygon_spans(oldchunk);assert spans and all(kind==b'polygon'for _,_,kind in spans)
        insertion=(render_ring(final.exterior)+''.join(render_ring(r)for r in final.interiors)).encode()
        first=spans[0][0];updated=oldchunk
        for a,b,kind in reversed(spans):updated=updated[:a]+updated[b:]
        updated=updated[:first]+insertion+updated[first:]
        assert K.C.pcbtext.chunk_uuid(updated)==UID and K.C.pcbtext.chunk_kind(updated)=='zone'
        chunk=OUT/(label+'-same-UUID-negative-only.zone-chunk');chunk.write_bytes(updated)
        assert raw.count(oldchunk)==1
        native=raw.replace(oldchunk,updated,1);(OUT/'candidate').mkdir();board=OUT/'candidate/board.kicad_pcb';board.write_bytes(native)
        inv2=K.C.inventory(native);assert set(inv2[3])==set(inventory[3])
        assert inventory[0]==inv2[0] and inventory[2]==inv2[2]
        unchanged=[u for u,ch in inventory[3].items()if u!=UID and inv2[3][u]==ch];assert len(unchanged)==len(inventory[3])-1
        trial={'guard_mm':guard,'status':'HELD_NATIVE_INTENT_ONLY_NO_CURRENT_CONTACT_REFERENCE_OR_NATIVE_PASS','current_owned_zone_UUID':UID,'same_original_native_profile_and_UUID':True,'zero_intended_Cu_gained':final.difference(intended).is_empty,'after_intended':save(label+'-after-intended',final),'explicit_negative':negative_info,'all_four_raw_witness_files_enclosed_by_clearance_cutter':True,'serialization_extra_negative_reserves':reserves,'current_actual_native_fill_records_geometrically_touched':touched,'chunk_file':str(chunk),'chunk_SHA256':sha(chunk),'board_file':str(board),'board_SHA256':sha(board),'unchanged_other_native_chunks':len(unchanged),'no_LG_proposed_fill_or_cap_substitution':True,'source_rooted_FG_relationships_contacts_reference_and_current':'HELD_REQUIRES_ACTUAL_NATIVE_REFILL_NO_PLANNING_CLAIM','all472_parent_raw_losses':'HELD_NO_CLOSURE_CLAIM','actual_fresh_native_LG_FG_refill_required':True}
        trials.append(trial);put('trial-progress.json',trials)
    put('receipt.json',{'status':'REAL_OWNED_FG_NEGATIVE_NATIVE_INTENT_ONLY_ALL_PHYSICAL_GATES_HELD','trials':trials,'no_existing_Cu_chunks_holes_pads_source_or_adopted_files_changed':True,'no_actual_LG_refill_performed_or_claimed':True,'native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE,P/'actual-graph-cache-receipt.json',P/'actual-combined-full-after-model.pkl',P/'actual-combined-full-after-all-net-groups.pkl',*files)},'elapsed_seconds':time.monotonic()-st})
    print('FG_RETREAT_COMPLETE',sha(OUT/'receipt.json'),flush=True)

if __name__=='__main__':main()
