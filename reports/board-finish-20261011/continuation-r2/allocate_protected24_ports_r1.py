"""Bind the full protected24 planning current to actual native physical ports."""
import collections,hashlib,json,math,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import inventory as I
OUT=H/'protected24-port-allocation-r1'
RAW={d:'/motherboard_power_entry{slash}FIELD_'+d[-1]+'_24V_PROTECTED' for d in ('FA','FB')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    model_path=H/'field-power/normal-model-r3.json';source=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';base=H/'field-power/native-bound-field-base-r5';census=H/'protected24-source-census-r2'
    br=json.loads((base/'receipt.json').read_bytes());cr=json.loads((census/'receipt.json').read_bytes())
    assert sha(model_path)=='63366d0a6f649300b99675b2c08b82e0da6fe75166b3fdd26852e4f35cd53ad0' and sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
    assert sha(base/'model.pkl')==br['model_sha256'] and sha(census/'groups.pkl')==cr['protected_groups_sha256']
    frozen={str(p.resolve()):sha(p) for p in (Path(__file__),model_path,source,base/'receipt.json',base/'model.pkl',census/'receipt.json',census/'groups.pkl')}
    model=json.loads(model_path.read_bytes());I.NET=source;parts,pins,nets=I.load();g=pickle.loads((base/'model.pkl').read_bytes())['discrete'];groups=pickle.loads((census/'groups.pkl').read_bytes());physical=collections.defaultdict(list)
    for p in g['pads']:physical[(p['ref'],p['num'])].append(p)
    terms=[]
    def endpoints(domain,pairs):
        result=[]
        for ref,pin in sorted(set(pairs)):
            node=next(q for q in pins[ref] if q['pin']==pin)
            assert node['net']==RAW[domain]
            ps=physical[(ref,pin)];assert ps and all(p['net']==RAW[domain] for p in ps)
            result.extend({'ref':ref,'pin':pin,'pinfunction':node['pinfunction'],'raw_net':p['net'],'physical_pad_uuid':p['uuid'],'at_mm':[p['x'],p['y']],'actual_pad_layers':sorted(p['layers'])} for p in ps)
        assert result
        return result
    def add(domain,name,value,pairs,basis,kind='load'):
        terms.append({'domain':domain,'name':name,'signed_supply_current_a':value,'kind':kind,'eligible_physical_endpoints':endpoints(domain,pairs),'basis':basis,'allocation':'Unknown nonnegative simplex sharing across exact physical pads; conserved term and every vertex retained, no equal split'})
    def inputs(domain,ref):
        out=[(ref,p['pin']) for p in pins[ref] if p['net']==RAW[domain] and p['pintype']=='power_in']
        assert out
        return out
    for d,refs in [('FA',['U10004','U10009']),('FB',['U10017','U10022'])]:
        for ref in refs:
            block=model['TPS274_source_and_return_port_groups'][ref];ports=inputs(d,ref)
            assert set(p for r,p in ports)==set(block['VS_pads'])
            add(d,ref+' four simultaneous outputs',sum(block['simultaneous_external_outputs_a']),ports,'Four fitted .5A outputs; external return remains separate and does not flow through device GND')
            add(d,ref+' VS quiescent',block['VS_quiescent_reservation_a'],ports,'Frozen separate VS reservation; VDD is supplied by isolated3V3 and excluded from this24V port')
    for ref,value in [('U11015',.148),('U11016',.074)]:
        assert parts[ref]['fields']['MPN']=='TPS26624DRCR'
        add('FA',ref+' full fitted AUX24 output load',value,inputs('FA',ref),'Preserved all12 motor AUX24 contract .148+.074; no motor/channel reduction')
        add('FA',ref+' TPS26624 IQ',.0006,inputs('FA',ref),'Aggregate IQ counted once; distinct RTN/GND internal allocation remains open')
    for d,refs,load in [('FA',['U14026','U14027'],.1),('FB',['U19004','U19005','U19006'],.2)]:
        for ref in refs:
            assert parts[ref]['fields']['MPN']=='MAX17612AATB+T'
            add(d,ref+' external output load',load,inputs(d,ref),'Full preserved probe/sensor normal contract at actual upstream IN port')
            add(d,ref+' MAX17612 IQ',.0015,inputs(d,ref),'Frozen1.5mA device planning reservation')
    for ref,load in [('U19007',.0165),('U19018',.05)]:
        assert parts[ref]['fields']['MPN']=='TPS1H000AQDGNRQ1'
        add('FB',ref+' actual output branch',load,inputs('FB',ref),'SAFE six wetting channels .00275A each; ARM lamp .05A; exact source output identity retained')
        add('FB',ref+' TPS1H000 IQ',.008,inputs('FB',ref),'Frozen8mA reservation')
    for d,ref in [('FA','U11009'),('FB','U19028')]:add(d,ref+' signed buck input',model['signed_regulator_ports'][ref]['IN_load_a'],inputs(d,ref),'Exact VIN=OUT+GND signed converter planning envelope, including bias once','converter_input')
    # Input divider currents enter their actual source resistor pad. Output
    # networks enter the exact upstream protected switch, not its ground port.
    mapping={'PRB0 input UVLO':('R14058','1'),'PRB1 input UVLO':('R14064','1'),'PRB0 output bleed':('U14026','1'),'PRB1 output bleed':('U14027','1'),'SENS0 input UVLO':('R19021','1'),'SENS1 input UVLO':('R19028','1'),'SENS2 input UVLO':('R19034','1')}
    for row in model['exact_branch_passive_networks']:
        name=row['name'];d=row['domain']
        if name in mapping:pair=mapping[name]
        elif name.startswith('SENS'):pair=('U1900'+str(4+int(name[4])),'1')
        elif name.startswith('SAFE'):pair=('U19007','8')
        elif name.startswith('ARM_LAMP'):pair=('U19018','8')
        else:raise ValueError('Unmapped protected source passive network '+name)
        add(d,name,row['planning_upper_a'],[pair],row['planning_basis'],'passive_network')
    for d,refs in [('FA',{'R11012','R11038','R11057','R11061'}),('FB',{'R11019','R19083'})]:
        rows=model['resistor_source_upper_bounds']['FIELD_'+d[-1]+'_24V_PROTECTED'];selected=[r for r in rows if r['ref'] in refs]
        assert set(r['ref'] for r in selected)==refs
        for r in selected:add(d,'Other direct protected resistor '+r['ref'],r['current_upper_a'],[(r['ref'],r['source_pin'])],r['basis'],'direct_resistor')
        assert math.isclose(sum(r['current_upper_a'] for r in selected),model['normal_protected24_consumption_terms_a'][d]['other_direct_protected24_resistors'],abs_tol=1e-14)
    add('FA','AUX24 output bleed/monitor planning envelope',model['normal_protected24_consumption_terms_a']['FA']['AUX24_external_bleed_monitor_bounds'],inputs('FA','U11015')+inputs('FA','U11016'),'Frozen aggregate bound across exact two upstream AUX24 inputs; internal branch division remains unknown','conservative_aggregate')
    for d,root in [('FA','U11004'),('FB','U11006')]:
        eligible=[(p['ref'],p['pin']) for p in nets[RAW[d]] if p['ref']!=root]
        add(d,'Protected installed leak/dynamic margin',.005,eligible,'Preserved5mA aggregate reservation across actual installed protected pads; conservative placement does not establish a device corner guarantee','planning_reservation')
        add(d,root+' protected OUT injection',-model['normal_protected24_trunk_envelopes_a'][d],[(root,'17'),(root,'18')],'Exact eFuse protected output source, excluding separate upstream raw/control/IQ currents','source')
    kcl={d:sum(t['signed_supply_current_a'] for t in terms if t['domain']==d) for d in RAW}
    assert all(abs(x)<1e-12 for x in kcl.values()),kcl
    ranges=[]
    for d in RAW:
        net=RAW[d].replace('{slash}','/');gs=groups[net]
        for index,xs in enumerate(gs):
            ids={q['uuid'] for q in xs if q['kind']=='pad'};lo=hi=0.;impacts=[]
            for t in terms:
                if t['domain']!=d:continue
                allids={e['physical_pad_uuid'] for e in t['eligible_physical_endpoints']};hit=ids&allids
                if not hit:continue
                value=t['signed_supply_current_a'];a=b=value if hit==allids else None
                if a is None:a,b=min(0.,value),max(0.,value)
                lo+=a;hi+=b;impacts.append({'term':t['name'],'signed_interval_a':[a,b],'physical_pad_uuid_hits':sorted(hit)})
            ranges.append({'domain':d,'group':index,'signed_group_interval_a':[lo,hi],'physical_pad_uuid_set':sorted(ids),'term_impacts':impacts,'sum_of_independent_group_extrema_is_not_one_simultaneous_operating_case':True})
    for p,h in frozen.items():assert sha(p)==h
    OUT.mkdir();receipt={'verdict':'PASS_PROTECTED24_PLANNING_KCL_EXACT_NATIVE_ENDPOINTS_CURRENT_MESH_OPEN','terms':terms,'KCL_residual_a':kcl,'group_signed_bounds':ranges,'input_sha256':frozen,'normal_protected_output_current_a':model['normal_protected24_trunk_envelopes_a'],'distinct_connector_input_current_a':model['real_connector_input_return_envelopes_a'],'ordinary_via_bank_package_neck_sheet_barrel_drop_thermal_and_transient_qualification':'OPEN','capacitors':'Zero ideal DC;5mA explicit leak margin retained. Every real cap C*dVdt/startup/ripple path remains separate and unbounded here','6p5A_copper_policy_and_all_fitted_interfaces_preserved':True,'source_or_board_changed':False,'native_jobs':0};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':receipt['verdict'],'terms':len(terms),'KCL':kcl,'groups':len(ranges),'receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
