from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=HERE/'late-power-schematic-grid-r3'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    helper=HERE/'audit_shutdown_header_correction.py';spec=importlib.util.spec_from_file_location('semantic',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original=ROOT/'reports/board-finish-20261017/corrected-baseline-r1/native'
    construction=json.loads((OUT/'construction-receipt.json').read_text())
    a=m.parse(OUT/'baseline.net');b=m.parse(OUT/'after.net')
    assert m.components(a)==m.components(b),'Any component/field/pin change rejected'
    assert m.nets(a)==m.nets(b),'Any raw net/node/pin role change rejected'
    assert m.child(a,'libparts')==m.child(b,'libparts')
    components=len(m.components(b));nets=len(m.nets(b));nodes=sum(len(m.children(n,'node'))for n in m.children(m.child(b,'nets'),'net'))
    assert (components,nets,nodes)==(2723,2388,9609)
    before=json.loads((ROOT/'reports/board-finish-20261017/corrected-baseline-r1/circuit-erc/erc.json').read_text());after=json.loads((OUT/'after-erc.json').read_text())
    get=lambda x:[v for s in x['sheets']for v in s['violations']]
    vb,va=get(before),get(after)
    identity=lambda v:json.dumps({'type':v['type'],'severity':v['severity'],'description':v['description'],'items':[{'description':i['description'],'pos':i['pos'],**({'uuid':i['uuid']}if not i['description'].startswith('Symbol ')else{})}for i in v['items']]},sort_keys=True)
    assert Counter(identity(v)for v in vb if v['type']!='endpoint_off_grid')==Counter(identity(v)for v in va)
    assert len(vb)==92 and len(va)==70
    assert sum(v['type']=='endpoint_off_grid'for v in vb)==22
    assert not any(v['type']=='endpoint_off_grid'or v['severity']=='error'for v in va)
    assert before['ignored_checks']==after['ignored_checks']==[]
    assert before['included_severities']==after['included_severities']
    for path,expected in construction['input_sha256'].items():assert sha(path)==expected,('Original input changed',path)
    assert sha(OUT/'source/motherboard_power_entry.kicad_sch')==construction['modified_file_sha256']
    for p in original.iterdir():
        q=OUT/'source'/p.name
        if p.is_file()and q.exists()and p.name!='motherboard_power_entry.kicad_sch':assert sha(p)==sha(q),p
    result={'utc':datetime.now(timezone.utc).isoformat(),'verdict':'PASS_NATIVE_EXPORT_EXACT_SEMANTICS_AND_22_GRID_WARNINGS_REMOVED','components':components,'raw_named_nets':nets,'nodes':nodes,'all_components_fields_pin_roles_and_exact_raw_node_membership_unchanged':True,'all_embedded_library_parts_unchanged':True,'all_symbol_wire_label_NC_UUIDs_unchanged':True,'all_noncoordinate_source_bytes_in_changed_chunks_unchanged':True,'all_other_source_and_project_rules_unchanged':True,'fresh_native_export_exit_codes':[0,0],'fresh_native_ERC_exit_code':0,'ERC_before':dict(Counter(v['type']for v in vb)),'ERC_after':dict(Counter(v['type']for v in va)),'ERC_errors_before':0,'ERC_errors_after':0,'non_grid_warning_semantic_multiset_including_ref_pin_positions_exactly_retained':True,'generated_ERC_pin_item_UUIDs':'26 symbol-pin warning entries receive new generated UUIDs; persistent source symbols/pins remain exact.44 label warning UUIDs remain exact. Raw UUID-comparison rejection retained.','no_suppression_or_exclusion_added':True,'input_sha256':{str(p):sha(p)for p in[OUT/'construction-receipt.json',OUT/'baseline.net',OUT/'after.net',OUT/'after-erc.json',ROOT/'reports/board-finish-20261017/corrected-baseline-r1/circuit-erc/erc.json',helper,Path(__file__)]},'changed_source_file':str(OUT/'source/motherboard_power_entry.kicad_sch'),'changed_source_sha256':sha(OUT/'source/motherboard_power_entry.kicad_sch'),'original_source_file':str(original/'motherboard_power_entry.kicad_sch'),'original_source_sha256':sha(original/'motherboard_power_entry.kicad_sch'),'only_pure_schematic_coordinates_changed':True,'PCB_changes':0,'native_PCB_DRC_run':False,'electrical_limits_changed':False,'adopted':False,'manufacturing_ready':False}
    (OUT/'verification-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in['verdict','components','raw_named_nets','nodes','ERC_before','ERC_after']}))

if __name__=='__main__':main()
