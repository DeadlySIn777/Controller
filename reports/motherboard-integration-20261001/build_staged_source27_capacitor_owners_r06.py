"""Reverify every actual staged native owner; live Source26 stays untouched."""
from pathlib import Path
import json,hashlib,copy,collections,xml.etree.ElementTree as ET
R=Path.cwd();S=R/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02';C=S/'candidate/motherboard';O=R/'reports/motherboard-bypass-owners-20261001/complete727-source27-staged-r04';O.mkdir(exist_ok=False)
P=R/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior=json.loads(P.read_text());model=json.loads((C/'design.json').read_text());parts=model['components'];root=ET.parse(C/'netlist.xml').getroot();native={}
for n in root.find('nets'):
    for v in n.findall('node'):native[v.get('ref'),v.get('pin')]=dict(net=n.get('name'),function=v.get('pinfunction'))
rows=copy.deepcopy(prior['capacitors']);byref={r['ref']:r for r in rows}
assert len(parts)==2698 and len(byref)==723
owner_changes=[]
for cap,schmitt,supervisor,bank in [('C11082','U11036','U11035','A'),('C11085','U11038','U11037','B')]:
    r=byref[cap];old=copy.deepcopy(r);slow='MOTOR_FEED_CLEAR_N_'+bank
    r.update(owner=schmitt,power_nodes=[dict(ref=schmitt,pin='2',net=slow),dict(ref=supervisor,pin='1',net=slow)],return_nodes=[dict(ref=schmitt,pin='3',net='LOGIC_GND'),dict(ref=supervisor,pin='2',net='LOGIC_GND')],source_role='Existing slow contact/reset RC filter now at genuine Schmitt input and supervisor RESET; old DFF CLR moved to FAST_CLR',evidence=str(S/'freeze-receipt-r02.json'),manifest=str(S/'source27-successor-rebinding-plan-r02.json'))
    owner_changes.append(dict(cap=cap,old_owner=old['owner'],old_power_nodes=old['power_nodes'],old_return_nodes=old['return_nodes'],new_owner=schmitt,new_power_nodes=r['power_nodes'],new_return_nodes=r['return_nodes'],old_DFF_CLR_endpoint_no_longer_valid=True,cap_MPN_and_terminal_nets_unchanged=True))
new=[('C11089','U11035','6','2'),('C11090','U11036','5','3'),('C11091','U11037','6','2'),('C11092','U11038','5','3')]
for cap,owner,power,ret in new:
    c=parts[cap];u=parts[owner]
    assert c['owner']==owner and c['mpn']=='GRM188R72A104KA35D'and c['pins']=={'1':'MOTION_5V_RAW','2':'LOGIC_GND'}
    assert u['mpn']in ('TPS3808G50DBVR','SN74LVC1G17DBVR')and u['pins'][power]=='MOTION_5V_RAW'and u['pins'][ret]=='LOGIC_GND'
    row=dict(ref=cap,owner=owner,cap_power='1',cap_return='2',power_nodes=[dict(ref=owner,pin=power,net='MOTION_5V_RAW')],return_nodes=[dict(ref=owner,pin=ret,net='LOGIC_GND')],target=2.,category='local_bypass',reviewed_series_path=[],manufacturer_numeric_maximum=False,physical_loop_or_effective_capacitance_qualified=False,evidence=str(S/'freeze-receipt-r02.json'),manifest=str(S/'source27-successor-rebinding-plan-r02.json'),source_role=c['role'])
    rows.append(row);byref[cap]=row
assert len(rows)==727 and set(byref)=={r for r in parts if r.startswith('C')}
expected_owners={r['ref']:{k:copy.deepcopy(r.get(k))for k in ('owner','cap_power','cap_return','power_nodes','return_nodes','category','reviewed_series_path','generic_router_permitted','dedicated_owner_cell','same_side_required','no_vias_to_owner')}for r in rows}
def verify(inventory):
    assert len(inventory)==727 and {r['ref']for r in inventory}==set(expected_owners)
    for r in inventory:
        for k,value in expected_owners[r['ref']].items():assert r.get(k)==value,(r['ref'],'Source-declared physical owner/function',k)
        if 'actual_MPN'in r:assert r['actual_MPN']==parts[r['ref']]['mpn']

        cap=parts[r['ref']];owner=parts[r['owner']];power=native[r['ref'],str(r['cap_power'])]['net'];ret=native[r['ref'],str(r['cap_return'])]['net']
        assert power!=ret
        nodes={}
        for side,expected in [('signal',power),('return',ret)]:
            ns=r['power_nodes'if side=='signal'else'return_nodes'];assert ns
            actual=[]
            for n in ns:
                entry=native[n['ref'],str(n['pin'])]
                direct=entry['net']==expected
                path=r.get('reviewed_series_path',[])
                if not direct and side=='signal'and len(path)==3:
                    one,two,three=path
                    direct=one['reference']==n['ref']and str(one['pin'])==str(n['pin'])and two['reference']==three['reference']and two['reference'].startswith('R')and native[one['reference'],str(one['pin'])]['net']==native[two['reference'],str(two['pin'])]['net']and native[three['reference'],str(three['pin'])]['net']==expected
                assert direct,(r['ref'],side,n,entry,expected)
                actual.append(dict(ref=n['ref'],pin=str(n['pin']),net=entry['net'],function=entry['function']))
            nodes[side]=actual
        r.update(actual_owner_MPN=owner['mpn'],actual_owner_footprint=owner['footprint'],actual_MPN=cap['mpn'],actual_cap_signal_net=power,actual_cap_return_net=ret,actual_native_function_nodes=nodes,actual_native_signal_pin_match=True,actual_native_return_pin_match=True,owner_mapping_verified=True,source_block=cap['source_block'],staged_parent_source_sha256=sha(C/'design.json'),staged_parent_native_sha256=sha(C/'netlist.xml'))
    return True
assert verify(rows)
for cap in ('C11078','C11080'):assert byref[cap]['actual_owner_MPN']=='74LVC2G14GW,125'
unchanged=[]
for old in prior['capacitors']:
    now=byref[old['ref']]
    for k in ('ref','owner','cap_power','cap_return','power_nodes','return_nodes','category','reviewed_series_path','target'):
        assert (old['ref']in ('C11082','C11085')and k in ('owner','power_nodes','return_nodes'))or now.get(k)==old.get(k),(old['ref'],k)
    for k in ('generic_router_permitted','dedicated_owner_cell','same_side_required','no_vias_to_owner'):
        assert now.get(k)==old.get(k),(old['ref'],k)
    assert now['actual_MPN']==old['actual_MPN']
    assert old['ref']in ('C11078','C11080','C11082','C11085')or now['actual_owner_MPN']==old['actual_owner_MPN']
    unchanged.append(old['ref'])
negatives=[]
for name,cap,field,bad in [('wrong_new_supervisor_power_pin','C11089','power_nodes',[dict(ref='U11035',pin='1')]),('wrong_new_schmitt_return_pin','C11090','return_nodes',[dict(ref='U11036',pin='5')]),('wrong_old_reference_owner_pin','C14741','power_nodes',[dict(ref='U14734',pin='7')]),('swapped_new_cap_power','C11091','cap_power','2'),('stale_DFF_CLR_owner_rejected','C11082','power_nodes',[dict(ref='U11032',pin='6')]),('same_RAW_wrong_supervisor_owner','C11089','power_nodes',[dict(ref='U11037',pin='6')]),('same_rail_FPGA_bank_swap','C1028','power_nodes',[dict(ref='U1001',pin='H6')]),('wrong_current_cap_MPN','C11089','actual_MPN','unverified'),('precision_ADC_exclusion_removed','C14741','generic_router_permitted',True)]:
    trial=copy.deepcopy(rows);r=next(r for r in trial if r['ref']==cap);r[field]=bad
    try:verify(trial);rejected=False
    except (AssertionError,KeyError):rejected=True
    assert rejected;negatives.append(dict(name=name,rejected=True,actual_staged_native_pin_check=True))
report=dict(source_revision='source27 staged successor, not adopted',source_physical_parts=2698,source_capacitor_count=727,capacitors=rows,owner_mapping_count=727,pending=[],errors=[],exclusive_full_population_accounted=True,all_owner_mappings_verified=True,categories=dict(collections.Counter(r['category']for r in rows)),input_hashes={str(p):sha(p)for p in (P,C/'design.json',C/'netlist.xml',S/'freeze-receipt-r02.json',S/'source27-successor-rebinding-plan-r02.json',Path(__file__))},source26_owner_receipt_provenance_preserved=True,all721_unchanged_old_owner_pin_roles_reverified=True,two_existing_slow_CLR_filter_owner_endpoints_corrected=owner_changes,all723_existing_cap_MPNs_terminal_nets_and_precision_exclusions_retained=True,source_or_PCB_mutated=False,live_source26_manifests_unchanged=True,live_routing_source_hash_guards_not_rebound=True,live_promotion_requires_fresh_exact_parent_receipt=True,negative_controls=negatives,physical_layout_or_loop_qualified=False,manufacturing_ready=False,scope='Every actual staged native capacitor/function endpoint reverified; no shared allowlist rebind or PCB placement claim')
(O/'capacitor-owners.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,source_parts=2698,owners=727,negative_controls=len(negatives),live_source_untouched=True)))
