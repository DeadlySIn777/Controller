"""Read only exact bound extra-flash hypotheses for unchanged native barrels."""
import json,hashlib
from pathlib import Path
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def canonical(q):return json.loads(json.dumps(q))
def collect(binding,base,h):
    before={q['uuid']:q for q in base['vias']};after={q['uuid']:q for q in h['vias']};rows={};recipes=[]
    for spec in binding.get('existing_native_owned_additional_flash_recipes',[]):
        f=Path(spec['file']);assert sha(f)==spec['sha256'];r=json.loads(f.read_text());uid=r['via_uuid']
        assert uid not in rows and uid in before and uid in after
        assert r['parent_native_board_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
        assert canonical(before[uid])==r['expected_original_host_geometry']
        assert canonical(after[uid])==r['expected_prospective_host_geometry'],('undeclared_extra_flash_host_or_geometry_change',uid)
        extra=r['prospective_additional_flash_layer'];old=before[uid];new=after[uid]
        assert extra in old['span'] and extra not in old['flashed']
        assert set(new['flashed'])==set(old['flashed'])|{extra} and new['prospective_new_flash_requires_native_refill']==extra
        assert {k:v for k,v in new.items() if k not in ('flashed','prospective_new_flash_requires_native_refill')}=={k:v for k,v in old.items() if k!='flashed'}
        assert r['original_actual_native_flash_mask']==old['flashed'] and r['required_native_postfill_flash_mask']==new['flashed']
        assert r['same_serialized_existing_via_UUID_net_position_diameter_drill'] and r['no_new_drill_and_no_native_layer_span_change']
        chunk=Path(r['original_native_via_chunk_file']);assert sha(chunk)==r['original_native_via_chunk_sha256']
        marker=r['actual_source_marker'];pad=next(q for q in h['pads'] if q['uuid']==marker['physical_pad_UUID'])
        assert (pad['ref'],pad['num'],pad['net'])==(marker['ref'],marker['pin'],marker['raw_net']) and new['net']==marker['raw_net']==r['net_raw']
        rows[uid]={**r,'explicit_ledger_file':str(f.resolve()),'explicit_ledger_sha256':sha(f)}
        recipes.append({'file':str(f.resolve()),'sha256':sha(f),'exact_existing_via_UUID':uid,'additional_layer':extra,'native_actual_flash_and_source_contact_current_gates':'OPEN'})
    return rows,recipes
