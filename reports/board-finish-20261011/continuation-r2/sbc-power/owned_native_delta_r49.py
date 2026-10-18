"""Exact frozen owned-Cu deletion ledger reader; rejects unlisted changes."""
import json,hashlib
from pathlib import Path
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def collect(binding,base):
    old_by_kind={kind:{q['uuid']:q for q in base[kind]} for kind in ('tracks','vias')};removed={};recipes=[]
    for spec in binding.get('existing_native_owned_Cu_removal_recipes',[]):
        file=Path(spec['file']);assert sha(file)==spec['sha256'],('changed_owned_removal_recipe',str(file))
        recipe=json.loads(file.read_text());rows=recipe.get('delete_rows',recipe.get('rows'))
        assert isinstance(rows,list) and rows,('missing_explicit_delete_rows',str(file))
        # Legacy R39 uses rows; canonical R45/R48 use delete_rows. No UUID
        # wildcard, domain/net exclusion, or count-only ownership acceptance.
        selected=[]
        for row in rows:
            uid=row['uuid'];kind=row['kind'];assert kind in ('segment','via')
            key='tracks' if kind=='segment' else 'vias';assert uid in old_by_kind[key]
            expected=row.get('expected_geometry',row.get('geometry'));assert isinstance(expected,dict)
            assert expected==old_by_kind[key][uid],('owned_removed_geometry_differs_from_exact_native_base',uid)
            path=Path(row.get('chunk_path',row.get('chunk_file')));digest=row.get('exact_original_chunk_sha256',row.get('chunk_sha256'));assert digest and sha(path)==digest
            raw=row.get('raw_net',expected['net']);assert raw==expected['net']
            normalized={'uuid':uid,'kind':kind,'raw_net':raw,'expected_geometry':expected,'chunk_path':str(path.resolve()),'exact_original_chunk_sha256':digest,
                'authorizing_recipe_file':str(file.resolve()),'authorizing_recipe_sha256':sha(file),'all_outside_shared_contacts_must_be_restored':True}
            if uid in removed:assert removed[uid]['expected_geometry']==expected and removed[uid]['exact_original_chunk_sha256']==digest
            else:removed[uid]=normalized
            selected.append(uid)
        recipes.append({'file':str(file.resolve()),'sha256':sha(file),'exact_removed_UUIDs':selected})
    return removed,recipes
