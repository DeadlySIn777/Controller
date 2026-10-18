"""Independent read-only replay of stage4 construction and controlled bad inputs."""
import sys,os
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import hashlib,json,importlib.util,re,runpy
H=Path(__file__).resolve().parent;ROOT=H.parents[3];STAGE=ROOT/'reports/board-finish-20261017';OUT=H/'stage4-independent-construction-review-r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists();OUT.mkdir();A=module('reviewed_stage4_assembler',STAGE/'assemble_coupled_zone_stage_r4.py');Z=module('reviewed_stage4_profile',STAGE/'zone_profile_guard_r1.py');C=module('reviewed_stage4_pcbtext',STAGE.parent/'board-finish-20261011/parity-repair/root106/tools/pcbtext.py')
    parent=A.BASE/'native/board.kicad_pcb';board=A.OUT/'native/board.kicad_pcb';receipt=A.OUT/'construction-receipt.json';expected=A.OUT/'changed-zone-native-contours-expected.json';r=json.loads(receipt.read_bytes());rows=json.loads(expected.read_bytes());byrow={x['UUID']:x for x in rows}
    assert sha(parent)==A.PARENT_SHA==r['parent_SHA256']and sha(board)==r['candidate_SHA256']=='ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55'
    pins={str(f):sha(f)for f in(Path(__file__),STAGE/'assemble_coupled_zone_stage_r4.py',STAGE/'zone_profile_guard_r1.py',parent,board,receipt,expected)}
    for f,v in r['input_SHA256'].items():assert sha(f)==v;pins[f]=v
    ph,pc,pt=C.split(parent.read_bytes());bh,bc,bt=C.split(board.read_bytes());old={C.chunk_uuid(c):c for c in pc if C.chunk_uuid(c)};new={C.chunk_uuid(c):c for c in bc if C.chunk_uuid(c)}
    assert len(old)==sum(bool(C.chunk_uuid(c))for c in pc)and len(new)==sum(bool(C.chunk_uuid(c))for c in bc)
    replaces={x['UUID']for x in rows if x['operation']=='replace'};adds={x['UUID']for x in rows if x['operation']=='add'}
    assert len(replaces)==len(adds)==7 and len(rows)==14 and len(byrow)==14
    assert set(new)==set(old)|adds and ph==bh and pt==bt
    assert all(new[u]==v for u,v in old.items()if u not in replaces)
    assert C.item_counts(board.read_bytes())['zone']==857
    dru=(A.BASE/'native/board.kicad_dru').read_bytes();assert b'zonename'not in dru.lower()and b'.name'not in dru.lower()
    for row in rows:
        uid=row['UUID'];chunk=new[uid];renamed=uid in A.NEW_NAMES
        assert digest(chunk)==row['after_chunk_SHA256']and C.chunk_kind(chunk)=='zone'and C.chunk_uuid(chunk)==uid
        assert Z.profile(chunk,renamed)==Z.profile(old[row['template_UUID']],renamed)
        assert Z.contours(chunk)==row['native_rings_IU']and len(Z.contours(chunk))==row['expected_holes']+1
        assert Z.filled_count(chunk)==row['stale_filled_polygons_in_input']
        if renamed:
            assert row['operation']=='add'and row['family']=='FIELD5_FG'
            names=[x[1]for x in Z.tree(chunk)[1:]if x[0]==b'name'];assert names==[json.dumps(A.NEW_NAMES[uid]).encode()]
            assert all(v.strip(b'"')not in dru for v in names)
    # Independently rebind all pinned packet files, including native hole-role proofs.
    for family,file,want in A.PACKETS:
        assert sha(file)==want;manifest=json.loads(file.read_bytes());pins[str(file)]=want
        for key in('input_sha256','input_SHA256'):
            for f,v in manifest.get(key,{}).items():assert sha(f)==v;pins[f]=v
    controls=[];uid='60c95fa7-e6df-530f-a3d3-00d3f96e46bc';base=new[uid];row=byrow[uid]
    def inspect_control(name,bad,target=uid):
        e=byrow[target];ignored=target in A.NEW_NAMES;original=new[target]
        profile_rejects=Z.profile(bad,ignored)!=Z.profile(old[e['template_UUID']],ignored)
        try:contour_rejects=Z.contours(bad)!=e['native_rings_IU']
        except(AssertionError,ValueError):contour_rejects=True
        hash_rejects=digest(bad)!=e['after_chunk_SHA256'];uuid_rejects=C.chunk_uuid(bad)!=target
        assert bad!=original and(hash_rejects or profile_rejects or contour_rejects or uuid_rejects)
        controls.append({'control':name,'frozen_after_chunk_hash_guard_rejects':hash_rejects,'profile_only_guard_rejects':profile_rejects,'frozen_ordered_native_contours_including_hole_ownership_rejects':contour_rejects,'UUID_identity_guard_rejects':uuid_rejects,'all_guards_were_replayed_in_memory_no_candidate_changed':True})
    inspect_control('wrong_net',base.replace(b'(net "/CORE_1V2")',b'(net "/LOGIC_GND")',1))
    inspect_control('wrong_layer',base.replace(b'(layer "In4.Cu")',b'(layer "In3.Cu")',1))
    inspect_control('wrong_priority',base.replace(b'(priority 124)',b'(priority 125)',1))
    inspect_control('replaced_display_name_changed',re.sub(rb'\(name "(?:\\.|[^"\\])*"\)',b'(name "UNAUTHORIZED RENAMED RETAINED SOURCE")',base,count=1))
    inspect_control('UUID_identity_changed',base.replace(uid.encode(),b'00000000-0000-4000-8000-000000000001',1))
    inspect_control('minimum_width_changed_exact_1nm',base.replace(b'(min_thickness 0.15)',b'(min_thickness 0.150001)',1))
    hp='421b7b98-45ce-5f1b-8de9-5cc585e773c2';q=new[hp];helper=runpy.run_path(str(H/'construct_coupled_CORE1V2_DIR7_return_window_r2.py'));spans=[(a,b)for a,b,k in helper['polygon_spans'](q)if k==b'polygon'];assert len(spans)==15
    (a,b),(c,d)=spans[:2];swapped=q[:a]+q[c:d]+q[b:c]+q[a:b]+q[d:]
    inspect_control('outer_and_hole_swapped_same_ring_count',swapped,hp)
    inspect_control('existing_hole_deleted',q[:c]+q[d:],hp)
    # An extra retained-object UUID change fails both exact old-chunk retention and expected UUID inventory.
    retain=next(u for u in old if u not in replaces and C.chunk_kind(old[u])=='zone');changed=old[retain].replace(retain.encode(),b'00000000-0000-4000-8000-000000000002',1)
    altered=dict(new);del altered[retain];altered[C.chunk_uuid(changed)]=changed
    assert set(altered)!=set(old)|adds and altered.get(retain)!=old[retain]
    controls.append({'control':'extra_UUID_change_on_unowned_old_zone','exact_old_chunk_retention_rejects':True,'expected_UUID_inventory_rejects':True})
    put('executed-failure-controls.json',controls)
    limitations=["profile() deliberately ignores polygon geometry and UUID; hole ownership is protected here by immutable source chunk hash and frozen ordered native contour expectation, not profile or ring count alone", "Construction does not prove fresh native fill, connectivity, contacts, source keys, current, IR, minwidth, thermal or reference recovery", "Six new power display names are explicitly authorized; replaced names remain exact, and the actual DRU has no zone-name selectors"]
    put('receipt.json',{'status':'INDEPENDENT_STAGE4_FROZEN_CONSTRUCTION_AND_EXECUTED_FAILURE_CONTROLS_PASS_ALL_ACTUAL_AFTER_GATES_OPEN','candidate_SHA256':sha(board),'replacements':7,'adds':7,'zones':857,'all_other_old_UUID_chunks_and_header_tail_exact':True,'all14_profiles_and_ordered_native_contours_rebound':True,'duplicate_UUID_inventory_absent_in_current_frozen_board':True,'executed_failure_control_count':len(controls),'hole_ownership_swapped_same_count_rejected_by_frozen_hash_and_frozen_contours_profile_alone_accepts':True,'blocking_finding_for_this_frozen_diagnostic_construction':None,'limitations':limitations,'native_jobs':0,'adopted':False,'input_SHA256':pins})
    assert all(sha(f)==v for f,v in pins.items());print(json.dumps({'receipt_SHA256':sha(OUT/'receipt.json'),'controls':len(controls)}))
if __name__=='__main__':main()
