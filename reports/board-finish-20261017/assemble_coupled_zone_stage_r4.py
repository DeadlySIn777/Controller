"""Compose exact power and CORE negative packets; all physical AFTER gates stay open."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
BASE=H/'combined-route-stage-r3'
OUT=H/'combined-route-stage-r4'
PARENT_SHA='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca'
PACKETS=[
 ('CORE69',H/'routing/parent-audit-review/coupled-CORE1V2-DIR7-stage3-native-candidate-r2/reviewable-native-negative-packet.json','61d072c7a603994ddc869a67c7cca07ae552bc9d760abac2c7dca18179304f55'),
 ('CORE60',H/'routing/parent-audit-review/coupled-CORE60-single-outer-stage3-native-candidate-r2/reviewable-native-negative-packet.json','aed68290918ac2c08582adfb9420ec5d46d9fc24cc0b44061bd5b3e01b4082b2'),
 ('FIELD5_FG',H/'power-review/field5-current-continuation/single-outer-power-diagnostic-packet-r11/manifest.json','da4a009b719aea70705ea08218637921187fb2147c3708a539a254b1ee763f6a')]
NEW_NAMES={
 '18ea00fc-4858-53d4-9904-cfa17216dc37':'FIELD5 real current corridor 50um part 1',
 '1caa042f-811c-5df6-a615-6ffdb5070d7f':'FIELD5 real current corridor 50um part 2',
 '927fa219-51b0-5598-89c9-870d8a23318f':'FIELD5 real current corridor 50um part 3',
 'b4df4c8c-5da3-51c2-a492-4ca24b98c6da':'FIELD5 real current corridor 50um part 4',
 'acd2f929-9c73-5f15-aeb4-c7a573192e9a':'FIELD5 real current corridor 50um part 5',
 'a6dd8d65-35fb-5511-b2b0-eabf7097495b':'FIELD_GND retained source region part 2'}


def sha(p):
    with Path(p).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    assert not OUT.exists()
    source=BASE/'native/board.kicad_pcb';assert sha(source)==PARENT_SHA
    helper=H.parent/'board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
    C=module('coupled_native_pcbtext',helper);Z=module('coupled_native_zone_profiles',H/'zone_profile_guard_r1.py')
    head,chunks,tail=C.split(source.read_bytes());old={C.chunk_uuid(c):c for c in chunks if C.chunk_uuid(c)}
    pins={str(p):sha(p) for p in [Path(__file__),helper,H/'zone_profile_guard_r1.py',BASE/'all-copper-expected.json']}
    dru=BASE/'native/board.kicad_dru';rules=dru.read_bytes();pins[str(dru)]=sha(dru)
    assert b'zonename' not in rules.lower() and b'.name' not in rules.lower()
    replace,add,rows={},{},[]
    for family,p,digest in PACKETS:
        assert sha(p)==digest;pins[str(p)]=digest;j=json.loads(p.read_bytes())
        assert j.get('baseline_SHA256',j.get('parent_SHA256'))==PARENT_SHA
        for path,v in j.get('input_sha256',{}).items():assert sha(path)==v;pins[path]=v
        for op in j['operations']:
            uid=op['UUID'];assert uid not in replace and uid not in add
            action=op['action']
            if action=='replace_exact_native_polygon_subchunk_in_same_UUID_zone':
                before=Path(op['old_zone_chunk_file']);after=Path(op['new_zone_chunk_file']);bs=op['old_zone_chunk_SHA256'];ns=op['new_zone_chunk_SHA256'];is_add=False;template=uid
            else:
                after=Path(op.get('file',op.get('after_file')));ns=op.get('SHA256',op.get('after_SHA256'))
                is_add=action in ('add','add_deterministic_same_profile_child_zone')
                assert is_add or action in ('replace','replace_exact_owned_zone')
                before=None if is_add else Path(op['before_file']);bs=op.get('before_SHA256')
                template=op.get('template_UUID',op.get('family_original_UUID'))
            assert sha(after)==ns;pins[str(after)]=ns;new=after.read_bytes()
            assert C.chunk_kind(new)=='zone' and C.chunk_uuid(new)==uid
            renamed=uid in NEW_NAMES
            if renamed:
                assert is_add and family=='FIELD5_FG'
                new_name=[x[1] for x in Z.tree(new)[1:] if x[0]==b'name']
                assert new_name==[json.dumps(NEW_NAMES[uid]).encode()]
                old_name=[x[1] for x in Z.tree(old[template])[1:] if x[0]==b'name']
                assert all(x.strip(b'"') not in rules for x in old_name+new_name)
            assert template in old and Z.profile(new,renamed)==Z.profile(old[template],renamed),(family,uid,'profile mismatch')
            rings=Z.contours(new)
            if family=='CORE60':assert len(rings)==1 and Z.filled_count(new)==0
            if family=='FIELD5_FG':assert len(rings)==1+op['native_hole_count'] and Z.filled_count(new)==0
            if is_add:
                assert uid not in old;add[uid]=new
            else:
                assert sha(before)==bs and old[uid]==before.read_bytes();pins[str(before)]=bs;replace[uid]=new
            rows.append({'family':family,'UUID':uid,'operation':'add' if is_add else 'replace','template_UUID':template,
                'after_chunk_SHA256':ns,'native_rings_IU':rings,'expected_holes':len(rings)-1,
                'stale_filled_polygons_in_input':Z.filled_count(new),'electrical_profile_fields_equal':True,
                'explicit_new_display_name':NEW_NAMES.get(uid)})
    assert (len(replace),len(add))==(7,7)
    assert set(replace)=={'69c62b44-c4ad-55f0-bf91-575b93a0b295','60c95fa7-e6df-530f-a3d3-00d3f96e46bc',
        '421b7b98-45ce-5f1b-8de9-5cc585e773c2','1707b21c-c26b-57a8-8fbf-83e94e04798b','eea7e934-b85e-5fa4-9ba4-5edebc7c76cc',
        '2ecf275f-68a9-50b9-911d-4ce14c83115c','7c8d8d67-604a-59a5-8095-6316cb152001'}
    newraw=head+b''.join(replace.get(C.chunk_uuid(c),c) for c in chunks)+b''.join(add.values())+tail
    nh,nc,nt=C.split(newraw);now={C.chunk_uuid(c):c for c in nc if C.chunk_uuid(c)}
    assert head==nh and tail==nt and set(now)==set(old)|set(add)
    assert all(now[u]==c for u,c in old.items() if u not in replace)
    assert all(C.chunk_kind(old[u])=='zone' for u in replace)
    for kind in ('segment','via','arc','footprint','gr_line','gr_arc'):
        assert [c for c in chunks if C.chunk_kind(c)==kind]==[c for c in nc if C.chunk_kind(c)==kind]
    assert C.item_counts(newraw)['zone']==857
    beforefiles={str(p.relative_to(BASE/'native')):sha(p) for p in (BASE/'native').rglob('*') if p.is_file() and p.suffix!='.lck'}
    assert all(sha(p)==v for p,v in pins.items())
    OUT.mkdir();shutil.copytree(BASE/'native',OUT/'native',ignore=shutil.ignore_patterns('*.lck','__pycache__'))
    board=OUT/'native/board.kicad_pcb';board.write_bytes(newraw)
    assert all(sha(OUT/'native'/n)==v for n,v in beforefiles.items() if n!='board.kicad_pcb')
    assert all(sha(BASE/'native'/n)==v for n,v in beforefiles.items())
    expected=copy.deepcopy(json.loads((BASE/'all-copper-expected.json').read_bytes()));expected['board_sha256']=sha(board)
    (OUT/'all-copper-expected.json').write_text(json.dumps(expected,indent=1)+'\n')
    (OUT/'changed-zone-native-contours-expected.json').write_text(json.dumps(rows,indent=1)+'\n')
    record={'status':'EXACT_COUPLED_POWER_AND_CORE_ZONE_DIAGNOSTIC_COMPOSED_ALL_NATIVE_AFTER_ELECTRICAL_GATES_OPEN',
        'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'parent_SHA256':PARENT_SHA,'candidate_SHA256':sha(board),
        'zone_replacements':7,'new_single_outer_zones':7,'total_zones_and_rule_areas':857,
        'new_or_changed_discrete_Cu_pads_footprints_board_outline_source':0,'all_other_old_UUID_chunks_byte_exact':len(old)-len(replace),
        'profiles_preserved_numeric_exact_with_explicit_new_names':True,'explicit_new_zone_display_names':NEW_NAMES,
        'custom_rules_do_not_select_on_changed_names':True,'new_join_count':'UNMEASURED',
        'native_full_fill_DRC_all9sources_contacts_references_masks_minwidth_IR_thermal_SI_signed_FIELD5_FG_current':'OPEN_REQUIRED',
        'FIELD5_common_electrode_squares':{'old_In4':87.888937,'current_In2':307.533030,'prospective_widened_In2':292.047576},
        'FIELD5_voltage_budget_closed':False,'all12_fitted_motor_and_other_load_limits_retained':True,
        'CORE_repair_scope':'only guarded CORE69/DIR7 and CORE60/RGB source-intent windows; inherited other reference failures remain',
        'current_live_stage1_input_and_job_untouched':True,'input_SHA256':pins,'parent_native_file_SHA256':beforefiles,
        'native_jobs_launched':0,'adopted':False,'manufacturing_ready':False}
    (OUT/'construction-receipt.json').write_text(json.dumps(record,indent=1)+'\n')
    print(json.dumps({k:record[k] for k in ('status','candidate_SHA256','zone_replacements','new_single_outer_zones')}))


if __name__=='__main__':main()
