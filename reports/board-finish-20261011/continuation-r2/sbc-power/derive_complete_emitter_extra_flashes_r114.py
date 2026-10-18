"""Derive emitter support for strictly bound unchanged-barrel extra flashes."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
s=(H/'emit_complete_power_recipe_r101.py').read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace('import owned_native_cu_replacements_r100 as CR','import owned_native_cu_replacements_r100 as CR\nimport owned_native_additional_flashes_r113 as EF')
replace("OUT=L.OUT/'complete-power-native-recipe-r101'", "OUT=L.OUT/'complete-power-native-recipe-r114'")
replace("    assert not set(owned_removed)&set(owned_Cu_replaced),'Existing item cannot be both removed and replaced'", """    assert not set(owned_removed)&set(owned_Cu_replaced),'Existing item cannot be both removed and replaced'
    extra_flash_rows,extra_flash_recipes=EF.collect(binding,base,h)
    assert not set(extra_flash_rows)&(set(owned_removed)|set(owned_Cu_replaced)), 'Extra flash cannot hide a deleted or moved barrel'""")
start=s.index('            if extra is not None or booleanflag is not None:')
end=s.index("            if kind=='pads' and uid in owned_FP_pads:",start)
s=s[:start]+'''            if extra is not None or booleanflag is not None:
                if uid in extra_flash_rows:
                    er=extra_flash_rows[uid]
                    assert kind=='vias' and booleanflag is None and extra==er['prospective_additional_flash_layer']
                    assert EF.canonical(prior)==er['expected_original_host_geometry'] and EF.canonical(now)==er['expected_prospective_host_geometry']
                    consumed['prospective_new_flash_requires_native_refill']=now.pop('prospective_new_flash_requires_native_refill')
                    ledger_file=er['explicit_ledger_file'];ledger_sha=er['explicit_ledger_sha256']
                else:
                    assert kind=='vias' and uid==logicledger['existing_via_UUID']
                    assert prior['flashed']==logicledger['existing_native_flash_mask']
                    assert extra is None or extra==logicledger['prospective_additional_flash_layer']
                    assert booleanflag is None or booleanflag is True
                    if extra is not None:consumed['prospective_new_flash_requires_native_refill']=now.pop('prospective_new_flash_requires_native_refill')
                    if booleanflag is not None:consumed['prospective_extra_flash_native_required']=now.pop('prospective_extra_flash_native_required')
                    extra=logicledger['prospective_additional_flash_layer'];ledger_file=str(logicreceipt.resolve());ledger_sha=sha(logicreceipt)
            if extra is not None:
                assert kind=='vias' and extra not in prior['flashed'] and set(now['flashed'])==set(prior['flashed'])|{extra}
                prospective_flashes.append({'uuid':uid,'original_native_flashes':prior['flashed'],'required_after_refill':now['flashed'],'same_existing_serialized_via':True,'exact_consumed_prospective_metadata':consumed,'explicit_ledger_file':ledger_file,'explicit_ledger_sha256':ledger_sha});now['flashed']=prior['flashed']
'''+s[end:]
replace("    receipt.update({'native_existing_owned_Cu_replacement_rows':", "    receipt.update({'existing_native_owned_additional_flash_recipes':extra_flash_recipes,'no_unknown_prospective_mask_metadata_cleared':True})\n    receipt.update({'native_existing_owned_Cu_replacement_rows':")
out=H/'emit_complete_power_recipe_r114.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
print('EXTRA_FLASH_EMITTER_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
