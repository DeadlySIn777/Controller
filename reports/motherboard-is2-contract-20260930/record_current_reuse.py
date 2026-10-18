"""Snapshot exact current MC net names for IS-2 reuse; no source writes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main()->None:
    target=HERE/'current-mc-reuse-reference.json'
    if target.exists():
        raise SystemExit('Refusing to overwrite the recorded MC reuse snapshot.')
    paths=[ROOT/'hardware/motion_card/assembly-map.json',ROOT/'hardware/motion_card/design.json',
           ROOT/'hardware/motion_card/netlist.xml',ROOT/'hardware/fpga_core/pin-allocation.json',
           ROOT/'hardware/mc_permission/design.json',ROOT/'hardware/mc_motor_buffers/design.json']
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in paths}
    for p in paths:
        q=HERE/'current-mc-inputs'/p.relative_to(ROOT)
        q.parent.mkdir(parents=True,exist_ok=True)
        if q.exists():
            # Retain an already captured identical source after an interrupted
            # first record; a differing source requires a new report directory.
            assert sha(p)==sha(q), f'Archived reuse source changed: {p}'
        else:
            shutil.copyfile(p,q)
        assert sha(p)==sha(q)
    assembly=json.loads(paths[0].read_text())
    req=json.loads((ROOT/'hardware/motherboard/requirements.json').read_text())
    tree=ET.parse(paths[2])
    nets={n.attrib['name']:[{'reference':x.attrib['ref'],'pin':x.attrib['pin']} for x in n.findall('node')]
          for n in tree.findall('./nets/net')}
    desired={t['resource']['signal'] for t in req['terminal_function_mapping']
             if t['scope']=='motherboard_standard' and t['resource'].get('kind')=='fpga_pin'}
    aliases=assembly['aliases']['fpga_core']
    actual_fpga={n for n,connections in nets.items() if any(x['reference']=='U1001' for x in connections)}
    # Only explicit archived alias names are accepted. Field names must not be guessed.
    field_refs=[]
    reverse={new:old for old,new in aliases.items()}
    for name in sorted(desired):
        # KiCad native XML preserves the root slash and child-sheet namespace.
        # Test only the explicit root and known fpga_core sheet labels; never
        # accept a suffix match from an unrelated child sheet.
        test_names=['/'+name,'/fpga_core/'+name]
        if name in reverse:
            test_names.extend(['/'+reverse[name],'/fpga_core/'+reverse[name]])
        direct=next((candidate for candidate in test_names if candidate in actual_fpga),None)
        field_refs.append({'logical_fpga_signal':name,'current_MC_native_net':direct,
                           'FPGA_connection_in_native_XML':direct is not None,
                           'native_nodes':nets.get(direct,[]) if direct else [],
                           'production_pin_qualified':False,
                           'note':'Native XML source connectivity is not full PCB connectivity, vendor fit, or a working field interface.'})
    permissions=json.loads(paths[4].read_text())
    buffers=json.loads(paths[5].read_text())
    report={
        'schema_version':1,'date':'2026-09-30','status':'source_reuse_reference_only',
        'source_hashes_sha256':hashes,'sources_unchanged':all(sha(p)==hashes[str(p.relative_to(ROOT)).replace('\\','/')] for p in paths),
        'requirements_sha256':sha(ROOT/'hardware/motherboard/requirements.json'),
        'native_xml_path':'hardware/motion_card/netlist.xml','FPGA_reference':'U1001',
        'MC_shared_interface_nets':[{'net':name,'native_net':'/'+name,
                                     'native_nodes':nets.get('/'+name,[]),
                                     'current_native_XML_contains_net':'/'+name in nets,
                                     'IS2_production_assignment_approved':False}
                                    for name in assembly['interface_nets']],
        'explicit_parent_aliases':assembly['aliases'],
        'base_direct_field_signal_references':field_refs,
        'base_direct_signal_count':len(field_refs),
        'base_direct_signals_present_at_FPGA_in_MC_XML':sum(x['FPGA_connection_in_native_XML'] for x in field_refs),
        'base_direct_signals_not_present_at_FPGA_in_MC_XML':[x['logical_fpga_signal'] for x in field_refs if not x['FPGA_connection_in_native_XML']],
        'permission_boundary_inputs_reference':permissions['boundary_inputs'],
        'permission_boundary_outputs_reference':permissions['boundary_outputs'],
        'permission_open_gates_reference':permissions['open_gates'],
        'motor_buffer_boundary_inputs_reference':buffers['boundary_inputs'],
        'motor_buffer_boundary_outputs_reference':buffers['boundary_outputs'],
        'bank_B_contract_reference':buffers['boe_contract'],
        'motor_receiver_contract_reference':buffers['receiver_contract'],
        'warnings':[
            'Reference snapshot only. No CAD/gateware/source net was changed.',
            'Native XML connections are schematic/source evidence, not routed physical connections.',
            'MC card names and handoff endpoints are historical physical labels to revise with explicit IS-2 onboard health semantics; do not assert nonexistent removable cards are healthy.',
            'Existing candidate FPGA balls must be reconciled with all required motherboard signal/bank/voltage assignments and vendor fit.',
        ],
    }
    assert report['sources_unchanged'] and len(field_refs)==77
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','sources_unchanged','base_direct_signal_count','base_direct_signals_present_at_FPGA_in_MC_XML','base_direct_signals_not_present_at_FPGA_in_MC_XML']},indent=2))


if __name__=='__main__':
    main()
