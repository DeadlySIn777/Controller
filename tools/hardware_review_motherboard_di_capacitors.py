"""Exact native owners for all 36 DI capacitors; no board/source mutation."""
from pathlib import Path
import argparse,json
from hardware_map_motherboard_domains import native,sha,write,ROOT,SEEDS


def owners(parts,nodes,nc):
    rows=[]
    for index in range(12):
        iso=f'U{8001+index}'
        if parts[iso]['mpn']!='ISO1212DBQR':raise ValueError('Unreviewed DI isolator')
        if (iso,'7')not in nc or nodes[iso,'1']!=SEEDS['LOGIC'] or nodes[iso,'8']!=SEEDS['LOGIC']:
            raise ValueError('Actual logic GND/NC mapping changed')
        for slot,(sense,ground)in enumerate([('16','14'),('11','9')]):
            channel=2*index+slot;ref=f'C{8001+channel}'
            if nodes[ref,'1']!=nodes[iso,sense]or nodes[ref,'2']!=nodes[iso,ground]or nodes[ref,'2']!=SEEDS['FIELD_B']:
                raise ValueError('CIN true SENSE or paired field return mismatch '+ref)
            rows.append(dict(block='motherboard_di',ref=ref,mpn=parts[ref]['mpn'],footprint=parts[ref]['footprint'],
                value=parts[ref]['value'],role='field SENSE filter (not VCC bypass)',category='field_filter',owner_ref=iso,additional_owners=[],
                capacitor_pins={p:nodes[ref,p] for p in ['1','2']},
                actual_owner_endpoints={'1':[dict(ref=iso,pin=sense,net=nodes[iso,sense])],
                    '2':[dict(ref=iso,pin=ground,net=nodes[iso,ground])]},
                engineering_pad_to_owner_target_mm=3.,numeric_target_is_manufacturer_limit=False,
                manufacturer_layout_requirement='CIN close to actual SENSE pin; external high-voltage RTHR end >=4mm from device pins/CIN/RSENSE',
                return_strategy='Own FIELD_B_0V return only; preserve distinct logic and floating SUB domains',
                effective_capacitance_qualified=False,layout_qualified=False))
        ref=f'C{8101+index}'
        if nodes[ref,'1']!=nodes[iso,'2']or nodes[ref,'1']!='/IO_3V3'or nodes[ref,'2']!=SEEDS['LOGIC']:
            raise ValueError('Logic bypass actual VCC/return mapping changed '+ref)
        rows.append(dict(block='motherboard_di',ref=ref,mpn=parts[ref]['mpn'],footprint=parts[ref]['footprint'],
            value=parts[ref]['value'],role='logic VCC bypass',category='local_bypass',owner_ref=iso,additional_owners=[],
            capacitor_pins={p:nodes[ref,p] for p in ['1','2']},
            actual_owner_endpoints={'1':[dict(ref=iso,pin='2',net=nodes[iso,'2'])],
                '2':[dict(ref=iso,pin=p,net=nodes[iso,p]) for p in ['1','8']]},
            engineering_pad_to_owner_target_mm=2.,numeric_target_is_manufacturer_limit=True,
            manufacturer_layout_requirement='ISO1212 section8.4.1: bypass close to VCC and not more than2mm away',
            return_strategy='Own LOGIC_GND loop, actual return vias and continuous adjacent plane required; pin7 is NC',
            effective_capacitance_qualified=False,layout_qualified=False))
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();source=a.source.resolve()
    if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('New immutable report required')
    inputs=[source/'design.json',source/'netlist.xml',ROOT/'research/digital-inputs/iso1212.pdf',Path(__file__)]
    before={str(f.relative_to(ROOT)):sha(f) for f in inputs}
    parts=json.loads(inputs[0].read_text(encoding='utf-8'))['components'];nodes,nc,_=native(inputs[1]);rows=owners(parts,nodes,nc)
    out.mkdir(parents=True)
    write(out/'capacitor-owners.json',dict(schema_version=1,source_only=True,pcb_modified=False,source_modified=False,
        layout_qualified=False,capacitor_count=len(rows),capacitors=rows,input_sha256=before,
        note='Owner/pin proof only; corrected DI placement/routing is independently reviewed in the exact native candidate.'))
    assert before=={str(f.relative_to(ROOT)):sha(f) for f in inputs}
    print(json.dumps(dict(capacitor_count=len(rows),native_pin_check='PASS',source_or_board_modified=False)))


if __name__=='__main__':main()
