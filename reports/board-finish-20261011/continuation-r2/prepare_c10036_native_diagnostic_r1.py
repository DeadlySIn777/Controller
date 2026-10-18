"""Derive an exact C10036 coupled diagnostic from the completed IO3 workflow."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,code):
    p=H/name;assert not p.exists();compile(code,str(p),'exec');p.write_text(code,encoding='utf-8');return p
source=H/'stage_io3_native_diagnostic_r2.py';s=source.read_text()
start=s.index("    recipe=H/'sbc-power/")
end=s.index("    assert len(removed)==2",start)
block='''    recipe=H/'coupled-recovery/c10036-native-owned-ledger-r32/receipt.json'
    assert sha(recipe)=='017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb'
    r=json.loads(recipe.read_bytes());zones_recipe=Path(r['recipe_path'])
    assert sha(zones_recipe)==r['recipe_sha256']=='016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e'
    assert sha(Path(r['independent_audit_path']))==r['independent_audit_sha256']=='b4cd12824af78c21a2d52f2c785ca1f7b3cfef3790158e18ee49832f01456038'
    assert sha(Path(r['fresh_source_netlist']))==r['fresh_source_netlist_sha256']=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
    stage=H/'field-power-native-trial-r1';parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb'
    assert sha(parent)==r['source_parent_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    inv=NC.C.inventory(parent.read_bytes());removed={};new={};zone_ids=set();chunk_inputs=[]
    for row in r['rows']:
        p=Path(row['exact_chunk_path']);assert sha(p)==row['exact_chunk_sha256'];chunk_inputs.append(p)
        if row['action']=='remove':removed[row['uuid']]=p.read_bytes()
        elif row['action']=='add':
            new[row['uuid']]=p.read_bytes()
            if row['kind']=='zone':zone_ids.add(row['uuid'])
        else:raise ValueError('Unknown exact operation')
'''
s=s[:start]+block+s[end:]
s=s.replace("OUT=H/'io3-native-diagnostic-r2'","OUT=H/'c10036-native-diagnostic-r1'")
s=s.replace('assert len(removed)==2 and len(new)==4','assert len(removed)==6 and len(new)==9')
clockline="    assert hashlib.sha256(inv[4][r['exact_retained_CM_clock_uuid']]).hexdigest()==r['exact_retained_CM_clock_chunk_sha256']\n"
assert s.count(clockline)==1;s=s.replace(clockline,'')
old="write(zspec,{'candidate_sha256':sha(board),'zones':[{'uuid':q['uuid'],'raw_net':q['raw_net'],'layer':q['layer'],'rings_IU':q['outline_integer_nm']} for q in zr['native_zone_rows']]})"
new="""zone_uuid=next(iter(zone_ids));zone_ast=parse(new[zone_uuid].decode());rings=[[[iu(p[1]),iu(p[2])] for p in child(poly,'pts')[1:]] for poly in ns['children'](zone_ast,'polygon')];zs=r['new_reference_zone_settings'];assert len(rings)==1
    write(zspec,{'candidate_sha256':sha(board),'zones':[{'uuid':zone_uuid,'raw_net':zs['raw_net'],'layer':zs['layer'],'rings_IU':rings,'declared_native_settings':{'priority':zs['priority'],'local_clearance_IU':iu(zs['local_clearance_mm']),'minimum_thickness_IU':iu(zs['minimum_thickness_mm']),'thermal_gap_IU':150000,'thermal_spoke_IU':300000,'island_removal_mode':1}}]})"""
assert s.count(old)==1;s=s.replace(old,new)
for old,new in [('native_io3_scoped_refill_r1.py','native_c10036_scoped_refill_r1.py'),('native_io3_selected_zone_contract_r1.py','native_declared_selected_zone_contract_r2.py'),('IO3','C10036'),('exact2_owned_Cu_deleted','exact6_owned_Cu_deleted'),('exact3_owned_Cu_added','exact8_owned_Cu_added'),('selected_new_C10036_zone_added','selected_new_FBG_reference_zone_added'),('exact2-owned-track replacement and one C10036 plane only; other R38 power proposals excluded','exact6 owned track replacement, six tracks/two vias/one FBG reference zone; other power proposals excluded'),('F_In1_actual_flash_gate','F_B_In4_actual_flash_gate')]:s=s.replace(old,new)
driver=put('stage_c10036_native_diagnostic_r1.py',s)
zone_source=H/'native_io3_selected_zone_contract_r1.py';z=zone_source.read_text();needle="        for key,value in wanted.items():"
assert z.count(needle)==1;z=z.replace(needle,"        declared=exp['declared_native_settings'];assert set(declared)=={'priority','local_clearance_IU','minimum_thickness_IU','thermal_gap_IU','thermal_spoke_IU','island_removal_mode'}\n        wanted.update(declared)\n"+needle)
zh=put('native_declared_selected_zone_contract_r2.py',z)
fill_source=H/'native_io3_scoped_refill_r1.py';f=fill_source.read_text().replace("raw='/IO_3V3'","raw='/motherboard_do{slash}FIELD_B_0V'")
f=f.replace('IO3','FBG').replace('IO3 only','FBG only')
fh=put('native_c10036_scoped_refill_r1.py',f)
receipt=H/'c10036-native-diagnostic-derivation-r1.json';assert not receipt.exists()
receipt.write_text(json.dumps({'inputs':{str(p):sha(p) for p in (source,zone_source,fill_source)},'derived':{str(p):sha(p) for p in (driver,zh,fh)},'scope':'exact C10036 R32 coupled 6-delete/8-discrete-add/1-reference-zone, matching eedf sidecars; .25 declared local settings; selected actual FIELD_B_0V refill only; all other source and Cu contracts retained','existing_test_slot_only':True,'whole_board_and_final_mutual_current_qualification':'OPEN'},indent=1)+'\n')
print(json.dumps({'driver':str(driver),'sha256':sha(driver)}))
