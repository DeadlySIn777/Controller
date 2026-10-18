"""Strict frozen same-UUID Cu replacements; all unlisted changes rejected."""
import json,hashlib
from pathlib import Path
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def canonical_record(q):return json.loads(json.dumps(q))
def collect(binding,base,h):
    before={kind:{q['uuid']:q for q in base[kind]} for kind in ('tracks','vias')};after={kind:{q['uuid']:q for q in h[kind]} for kind in before}
    rows=[];owned={};recipes=[]
    for spec in binding.get('existing_native_owned_Cu_replacement_recipes',[]):
        file=Path(spec['file']);assert sha(file)==spec['sha256'];recipe=json.loads(file.read_text());rs=recipe['replacement_rows'];assert rs
        assert recipe['parent_native_board_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
        author=Path(recipe['authorizing_recipe_file']);assert sha(author)==recipe['authorizing_recipe_sha256'];frozen=json.loads(author.read_text());bound={q['uuid']:q for q in frozen['exact_original_replacements']};selected=[]
        for r in rs:
            kind=r['kind'];uid=r['uuid'];assert kind in ('segment','via');key='tracks' if kind=='segment' else 'vias'
            assert uid not in owned and uid in before[key] and uid in after[key]
            assert canonical_record(before[key][uid])==r['expected_original_geometry']
            assert canonical_record(after[key][uid])==r['expected_replacement_geometry'],('unqualified_existing_replacement_geometry_or_unknown_metadata',uid)
            assert r['raw_net']==before[key][uid]['net']==after[key][uid]['net'];assert r['same_existing_UUID_replacement_not_addition'] and r['every_other_AST_node_and_serialized_byte_unchanged']
            original=Path(r['original_chunk_file']);replacement=Path(r['replacement_chunk_file']);assert sha(original)==r['original_chunk_sha256'] and sha(replacement)==r['replacement_chunk_sha256']
            assert r['authorizing_recipe_file']==str(author.resolve()) and r['authorizing_recipe_sha256']==sha(author)
            original_bound=bound[uid];assert original_bound['replacement_geometry']==r['expected_replacement_geometry'];assert original_bound['original_chunk_sha256']==sha(original) and original_bound['replacement_chunk_sha256']==sha(replacement)
            assert r['exact_native_changed_fields']==(['end'] if kind=='segment' else ['at'])
            if kind=='via':
                assert r['original_actual_native_flash_mask']==before[key][uid]['flashed'];assert r['required_post_refill_retained_flash_mask']==after[key][uid]['flashed']==before[key][uid]['flashed']
                assert after[key][uid]['mask_provenance']==r['host_only_mask_provenance_change_authorized_literal']
            owned[uid]=r;rows.append(r);selected.append(uid)
        recipes.append({'file':str(file.resolve()),'sha256':sha(file),'exact_replaced_existing_UUIDs':selected,'only_explicit_declared_fields_changed':True,'joint_source_contact_reference_current_native_gates':'OPEN'})
    return rows,owned,recipes
