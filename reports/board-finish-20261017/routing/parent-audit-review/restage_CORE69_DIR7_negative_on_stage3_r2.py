"""Restage only the proved native polygon operation, retaining the current fill cache."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import json,hashlib,time,runpy,re
from fractions import Fraction as Q
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
R=runpy.run_path(str(HERE/'construct_coupled_CORE1V2_DIR7_return_window_r2.py'))
K=R['K'];X=R['X'];PACKET=R['OUT'];UID=R['TARGETS'][0]
SOURCE=PROJECT/'reports/board-finish-20261017/combined-route-stage-r3/native/board.kicad_pcb'
OUT=HERE/'coupled-CORE1V2-DIR7-stage3-native-candidate-r2'
EXPECTED='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca'
LG='c1d27fa1-452b-4e27-985d-5ad23644d800'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(v).hexdigest()
def write(name,value):
    f=OUT/name;f.write_text(json.dumps(value,indent=1,allow_nan=False)+'\n',encoding='utf-8');return sha(f)
def polys(raw):return[(a,b,raw[a:b])for a,b,k in R['polygon_spans'](raw)if k==b'polygon']
def shape(raw):
    chunks=polys(raw);assert len(chunks)==1
    points=[(Q(a.decode())*1000000,Q(b.decode())*1000000)for a,b in re.findall(rb'\(xy ([-0-9.eE]+) ([-0-9.eE]+)\)',chunks[0][2])]
    assert all(v.denominator==1 for xy in points for v in xy)
    return Polygon([(int(x),int(y))for x,y in points])
def profile(raw):
    # Numeric normalization is exact rational, with no distance or area tolerance.
    tokens=re.findall(rb'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',raw);pos=0
    def parse():
        nonlocal pos
        t=tokens[pos];pos+=1
        if t==b'(':
            v=[]
            while tokens[pos]!=b')':v.append(parse())
            pos+=1;return v
        if re.fullmatch(rb'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?',t):
            q=Q(t.decode());return ['EXACT_NUMBER',q.numerator,q.denominator]
        return t.decode('utf-8')
    root=parse();assert pos==len(tokens)and root[0]=='zone'
    children=[]
    for child in root[1:]:
        assert isinstance(child,list)
        if child[0]in('polygon','filled_polygon','fill_segments'):continue
        if child[0]=='fill'and len(child)>1 and child[1]=='yes':child=[child[0],*child[2:]]
        children.append(child)
    return children
def literal_nonpolygon(raw):
    result=raw
    for a,b,_ in reversed(polys(raw)):result=result[:a]+result[b:]
    return result
def canonical_ring(sh):
    p=[tuple(map(int,xy))for xy in list(sh.exterior.coords)[:-1]]
    def orientation(q):
        m=min(q);return min(tuple(q[i:]+q[:i])for i,v in enumerate(q)if v==m)
    return min(orientation(p),orientation(list(reversed(p))))
def detailed_subset(before,after):
    assert before.geom_type=='Polygon'and not before.interiors
    raw=[[[tuple(Q(int(v))for v in xy)for xy in before.exterior.coords]]]
    old_edges={(a,b)for a,b in zip(raw[0][0],raw[0][0][1:])};rows=[]
    for i,(a,b)in enumerate(zip(list(after.exterior.coords),list(after.exterior.coords)[1:])):
        a=tuple(Q(int(v))for v in a);b=tuple(Q(int(v))for v in b)
        row={'edge':i,'a_IU':[int(v)for v in a],'b_IU':[int(v)for v in b]}
        if(a,b)in old_edges or(b,a)in old_edges:row['proof']='LITERAL_ORIGINAL_NATIVE_EDGE'
        else:
            ts=X.split_parameters(a,b,{'before':raw});checks=[]
            for t in ts+[(t+u)/2 for t,u in zip(ts,ts[1:])if t!=u]:
                point=X.along(a,b,t);location=X.location(point,raw);assert location!='EXTERIOR'
                checks.append({'parameter':[t.numerator,t.denominator],'point_IU_rationals':[[v.numerator,v.denominator]for v in point],'closed_before_location':location})
            row.update(proof='EXACT_BOUNDARY_SPLIT_ALL_BREAKPOINTS_AND_OPEN_INTERVAL_MIDPOINTS',checks=checks)
        rows.append(row)
    summary=R['exact_subset_boundary_proof'](before,after)
    return {'method':'Exact native-IU Fraction arithmetic; every new boundary split at every original boundary, no area tolerance','summary':summary,'edges':rows}
def main():
    t=time.monotonic();assert not OUT.exists();assert sha(SOURCE)==EXPECTED
    priorfile=PACKET/'receipt.json';prior=json.loads(priorfile.read_bytes());op=prior['operations'][0]
    oldfile=Path(op['old_chunk_file']);newfile=Path(op['new_chunk_file'])
    assert sha(oldfile)==op['old_chunk_SHA256']and sha(newfile)==op['new_chunk_SHA256']
    raw=SOURCE.read_bytes();a=K.C.inventory(raw);old=a[3][UID];original=oldfile.read_bytes();replacement=newfile.read_bytes()
    before=shape(old);originalshape=shape(original);after=shape(replacement)
    assert canonical_ring(before)==canonical_ring(originalshape)
    assert profile(old)==profile(original)==profile(replacement)
    assert len(polys(replacement))==len(polys(old))==1
    lo,hi,oldpolygon=polys(old)[0];newpolygon=polys(replacement)[0][2]
    new=old[:lo]+newpolygon+old[hi:]
    assert literal_nonpolygon(old)==literal_nonpolygon(new)
    assert shape(new).equals(after)and canonical_ring(shape(new))==canonical_ring(after)
    proof=detailed_subset(before,after)
    result=raw.replace(old,new,1);b=K.C.inventory(result)
    assert set(a[3])==set(b[3])and a[0]==b[0]and a[2]==b[2]
    assert all(b[3][u]==v for u,v in a[3].items()if u!=UID)
    assert b[3][LG]==a[3][LG]and literal_nonpolygon(b[3][UID])==literal_nonpolygon(a[3][UID])
    retention=HERE/'CORE1V2-conservative-whole-record-retention-r1/receipt.json';rr=json.loads(retention.read_bytes());trial=rr['trials'][0]
    assert trial['removed_native_zone_actual_fill_record_UUIDs']==[UID]
    assert not trial['old_CORE1V2_group_relationship_losses']and not trial['old_CORE1V2_source_layer_key_losses']and not trial['old_CORE1V2_direct_fill_contact_losses']
    OUT.mkdir();(OUT/'candidate').mkdir();board=OUT/'candidate/board.kicad_pcb';board.write_bytes(result)
    for name,data in(('exact-stage3-before.zone-chunk',old),('exact-stage3-after.zone-chunk',new),('exact-stage3-before-native.polygon-chunk',oldpolygon),('exact-stage3-after-native.polygon-chunk',newpolygon),('exact-stage3-retained-LG.zone-chunk',a[3][LG])):(OUT/name).write_bytes(data)
    proofsha=write('per-edge-native-IU-rational-negative-subset-proof.json',proof)
    lgpolys=polys(a[3][LG]);lgprofile=profile(a[3][LG]);lgproof=write('literal-LG-source-intent-profile-retention.json',{'UUID':LG,'exact_whole_zone_chunk_before_after_SHA256':digest(a[3][LG]),'literal_polygon_chunks_SHA256':[digest(v)for _,_,v in lgpolys],'numeric_exact_native_profile':lgprofile,'all_literal_zone_bytes_retained':True,'fresh_fill_reference_restoration':'OPEN_REQUIRED'})
    opout={'action':'replace_exact_native_polygon_subchunk_in_same_UUID_zone','UUID':UID,'old_zone_chunk_file':str(OUT/'exact-stage3-before.zone-chunk'),'old_zone_chunk_SHA256':digest(old),'new_zone_chunk_file':str(OUT/'exact-stage3-after.zone-chunk'),'new_zone_chunk_SHA256':digest(new),'old_polygon_byte_guard_SHA256':digest(oldpolygon),'new_polygon_SHA256':digest(newpolygon),'all_current_zone_nonpolygon_bytes_including_stale_cached_fills_retained':True,'same_profile_name_UUID_net_layer_priority_island_rule_parameters_exact_numeric':True,'R299_input_and_current_stage3_native_intent_same_exact_IU_ring_up_to_rotation_and_winding':True,'per_edge_proof_SHA256':proofsha,'negative_intent_area_mm2':op['explicit_owned_native_intent_removed']['area_mm2'],'negative_region_native_IU_bounds':op['explicit_owned_native_intent_removed']['bounds_IU'],'negative_region_R299_exact_WKB_SHA256':op['explicit_owned_native_intent_removed']['WKB_SHA256'],'cut_guard_IU':prior['native_cut_guard_IU']}
    manifest=write('reviewable-native-negative-packet.json',{'status':'EXACT_NATIVE_SAME_UUID_NEGATIVE_POLYGON_PACKET_NATIVE_AFTER_REQUIRED','baseline':str(SOURCE),'baseline_SHA256':EXPECTED,'candidate':str(board),'candidate_SHA256':sha(board),'operations':[opout],'all_other_native_chunks_header_tail_exact':True,'unchanged_native_chunk_count':len(a[3])-1,'LG_literal_retention_proof_SHA256':lgproof,'stale_fills_are_not_new_actual_authority':True,'scope':prior['coverage'],'adopted':False})
    rec={'status':'REAL_STAGE3_NATIVE_SAME_UUID_NEGATIVE_POLYGON_HOST_PRECHECK_ONLY_ALL_NATIVE_PHYSICAL_CURRENT_REFERENCE_GATES_OPEN','input_stage3_SHA256':EXPECTED,'candidate_SHA256':sha(board),'manifest_SHA256':manifest,'operations':[opout],'literal_LG_retention_proof_SHA256':lgproof,'source_backed_guard_terms_IU':prior['source_backed_guard_terms_IU'],'old_actual_source_contact_partition_host_proof_scope':{'authority':'Immutable actual R299 cached full Cu; stronger removal of entire CORE69 filled record, all other actual records fixed','receipt':str(retention),'receipt_SHA256':sha(retention),'trial':trial,'conditional_monotonicity':'Any local removed subset retains at least the surviving entire-record-removal copper; native refill can alter other records and must be measured','is_stage3_or_new_native_physical_pass':False},'fresh_native_CPP_fill_all9sources_all_original_physical_relationships_directcontacts_oldbody_positivepour_fullsignalbody_masks_actual109_rules':'OPEN_REQUIRED','CORE_source_signed_load_IR_minwidth_voltage_drop_thermal_barrel_current':'OPEN_REQUIRED','CORE60_RGB_and_other433_parent_reference_losses':'HELD_NO_CLOSURE_CLAIM','native_fill_or_save_calls':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE,priorfile,oldfile,newfile,retention,Path(R['X'].__file__),HERE/'construct_coupled_CORE1V2_DIR7_return_window_r2.py')},'elapsed_seconds':time.monotonic()-t}
    write('receipt.json',rec);assert sha(SOURCE)==EXPECTED
    print(json.dumps({'candidate_SHA256':sha(board),'manifest_SHA256':manifest,'receipt_SHA256':sha(OUT/'receipt.json'),'per_edge_proof_SHA256':proofsha}))
if __name__=='__main__':main()
