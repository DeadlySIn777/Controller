"""Check the integrated export against all source nets, with explicit interfaces."""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/controller_assembly'
ALLOWED={'CORE_24V_PROTECTED','FIELD_24V_PROTECTED','LOGIC_GND','FIELD_GND','CORE_5V','IO_3V3',
         'CORE_1V2','ESP_3V3','FIELD_5V','C_PGOOD','F_PGOOD','ENC0_5V_LIMITED','ENC1_5V_LIMITED',
         'CORE_1V2_EN','IO_3V3_EN','ESP_3V3_EN'}
ALIASES={'tx_six':{'SIGNAL_5V':'CORE_5V'}}
BLOCKS=('power_entry','core_converter','logic_power','field_power','encoder_power','tx_six','rx_abz',
        'sbc_power','power_sequence','digital_inputs')


def remap(ref,index):
    m=re.fullmatch(r'([^0-9]+)([0-9]+)',ref)
    if not m:raise ValueError('Unknown source reference')
    return m[1]+str(index*1000+int(m[2]))


def validate(tree, mapping, *, check_source_hashes=True):
    errors=[];expected=defaultdict(set);actual={};nc_expected=set();nc_actual=set();seen=set();components={}
    names=list(mapping['blocks'])
    if names!=list(BLOCKS):return ['Complete ten-block scope/order changed']
    sources={name:ET.parse(ROOT/'hardware'/name/'netlist.xml') for name in names}
    sets={name:{ALIASES.get(name,{}).get(n.attrib['name'].lstrip('/'),n.attrib['name'].lstrip('/')) for n in src.findall('.//nets/net')} for name,src in sources.items()}
    public={n for n in ALLOWED if sum(n in s for s in sets.values())>1}
    if set(mapping['interface_nets'])!=public or mapping.get('aliases')!=ALIASES:errors.append('Interface contract changed')
    if check_source_hashes:
        required=set()
        for name,src in sources.items():
            libs={c.find('libsource').attrib['lib'] for c in src.findall('.//components/comp')}
            if len(libs)!=1:return ['Source must have one local symbol library: '+name]
            base=ROOT/'hardware'/name
            required.update((p.relative_to(ROOT).as_posix() for p in
                             (base/(name+'.kicad_sch'),base/'netlist.xml',base/(next(iter(libs))+'.kicad_sym'))))
            required.update(p.relative_to(ROOT).as_posix() for p in (base/'CNC_Power.pretty').glob('*.kicad_mod'))
        if set(mapping['input_sha256'])!=required:errors.append('Source identity inventory differs')
        builder=ROOT/'tools/hardware_build_assembly.py'
        if mapping.get('builder_sha256')!=hashlib.sha256(builder.read_bytes()).hexdigest():errors.append('Builder identity differs')
        for name,want in mapping['input_sha256'].items():
            if name not in required:continue
            p=ROOT/name
            if not isinstance(want,str) or re.fullmatch('[0-9a-f]{64}',want) is None or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=want:
                errors.append('Source changed or invalid identity: '+name)
    for index,(name,source) in enumerate(sources.items(),1):
        for c in source.findall('.//components/comp'):
            ref=c.attrib['ref']
            if ref.startswith('#'):continue
            new=remap(ref,index)
            if mapping['blocks'][name]['references'].get(ref)!=new:errors.append('Reference map differs: '+ref)
            components[new]=c
        for net in source.findall('.//nets/net'):
            old=net.attrib['name'].lstrip('/')
            nodes={(remap(n.attrib['ref'],index),n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')}
            if old.startswith('unconnected-'):
                nc_expected.update(nodes);continue
            alias=ALIASES.get(name,{}).get(old,old)
            target='/'+alias if alias in public else '/'+name+'/'+alias
            expected[target].update(nodes)
    for net in tree.findall('.//nets/net'):
        name=net.attrib['name']
        nodes=[(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')]
        if len(nodes)!=len(set(nodes)) or seen.intersection(nodes):errors.append('Duplicate pin membership')
        seen.update(nodes)
        if 'unconnected-(' in name:
            nc_actual.update(nodes)
            if len(nodes)!=1:errors.append('Joined no-connect pins')
        else:
            if name in actual:errors.append('Duplicate named net')
            actual[name]=set(nodes)
    if nc_actual!=nc_expected:errors.append('No-connect set differs')
    for net in set(expected)|set(actual):
        if actual.get(net,set())!=expected.get(net,set()):errors.append('Integrated connectivity differs: '+net)
    comps=tree.findall('.//components/comp');cs={c.attrib['ref']:c for c in comps}
    if len(comps)!=len(cs) or set(cs)!=set(components):errors.append('Integrated population differs')
    for ref,source in components.items():
        c=cs.get(ref)
        if c is None:continue
        for field in ('value','footprint',"./fields/field[@name='MPN']"):
            if c.findtext(field)!=source.findtext(field):errors.append('Component differs: '+ref+'/'+field)
        if any(p.attrib.get('name','').lower()=='dnp' for p in c.findall('property')):errors.append('Unreviewed DNP: '+ref)
    if {'core_converter','field_power','power_entry'}<=set(names):
        for name in ('C_PGOOD','F_PGOOD'):
            # Exact converter pin for field is checked against its own source;
            # this independent integration gate excludes low-voltage pullups.
            nodes=actual.get('/'+name,set())
            entry_index=names.index('power_entry')+1
            forbidden={(remap('R9',entry_index),'2'),(remap('R29',entry_index),'2')}
            if nodes&forbidden:errors.append('Downstream PGOOD pullup reintroduced')
    return errors


def validate_erc(erc, blocks):
    """Keep the 22 isolated substrate islands visible, reject every other issue."""
    expected={str(uuid.uuid5(uuid.UUID('86d2737f-dd12-4428-95b0-38daecf1f8cf'),
                            f'U{i//2+1}{13 if i%2==0 else 12}label')):f"Label 'DI{i:02d}_SUB_ISLAND'"
              for i in range(22)} if 'digital_inputs' in blocks else {}
    seen=set();errors=[]
    if erc.get('source')!='controller_assembly.kicad_sch':errors.append('ERC source differs')
    if set(erc.get('included_severities',[]))!={'error','warning'}:errors.append('ERC severities changed')
    if {x['key'] for x in erc.get('ignored_checks',[])}-{'single_global_label','four_way_junction','simulation_model_issue','footprint_filter'}:
        errors.append('Extra ERC check suppression')
    for sheet in erc['sheets']:
        for v in sheet['violations']:
            labels=[i['description'] for i in v['items']]
            key=v['items'][0].get('uuid') if len(labels)==1 else None
            # KiCad 10.0.4 places these child-label warnings under the root.
            # Identify the actual preserved label UUID, never a broad sheet waiver.
            if (sheet['path'] in ('/','/digital_inputs/') and v['type']=='isolated_pin_label'
                    and v['severity']=='warning' and key in expected and labels==[expected[key]]
                    and key not in seen):
                seen.add(key)
            else:errors.append('Unexpected ERC issue: '+sheet['path']+v['description'])
    if seen!=set(expected):errors.append('Expected isolated substrate-island warning set differs')
    return errors


def main():
    mapping=json.loads((OUT/'assembly-map.json').read_text())
    tree=ET.parse(OUT/'netlist.xml')
    errors=validate(tree,mapping)
    erc=json.loads((OUT/'erc.json').read_text())
    count=sum(len(s['violations']) for s in erc['sheets'])
    errors.extend(validate_erc(erc,mapping['blocks']))
    origin={new:(block,old) for block,data in mapping['blocks'].items() for old,new in data['references'].items()}
    rows=[]
    for c in tree.findall('.//components/comp'):
        ref=c.attrib['ref'];block,source=origin[ref]
        mpn=c.findtext("./fields/field[@name='MPN']") or ''
        footprint=c.findtext('footprint') or ''
        rows.append({'reference':ref,'source_block':block,'source_reference':source,'quantity':1,
                     'value':c.findtext('value'),'mpn':mpn,'footprint':footprint,
                     'status':'boundary connector; selection open' if source.startswith('J') else
                              'part selection open' if not mpn or 'TBD' in mpn else 'candidate; not qualified'})
    with (OUT/'review-bom.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='validation.json']
    files += [Path(__file__),ROOT/'tools/hardware_build_assembly.py',ROOT/'tests/test_hardware_assembly.py']
    result={'schema_version':1,'manufacturing_ready':False,'consistency_pass':not errors,'errors':errors,
            'blocks':list(mapping['blocks']),'kicad_version':erc['kicad_version'],'erc_violations':count,
            'erc_errors':sum(v['severity']=='error' for s in erc['sheets'] for v in s['violations']),
            'erc_expected_warnings':22 if 'digital_inputs' in mapping['blocks'] else 0,
            'erc_warning_basis':'ISO1212 SUB1/SUB2 each require a distinct floating copper island; no waiver or dummy connection added',
            'component_count':len(rows),'net_count':len(tree.findall('.//nets/net')),
            'review_bom_only':True,'unselected_or_boundary_parts':sum(r['status']!='candidate; not qualified' for r in rows),
            'unassigned_footprints':sum(not r['footprint'] for r in rows),
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'scope':'Preserved source circuits with checked cross-sheet connections; missing full-board functions remain missing'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Assembly:', 'PASS' if not errors else errors)
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
