"""Exact physical endpoint/simplex allocation of the preserved full field ledger.

Algebraic planning evidence only: no equal pad sharing, mesh, or device rating.
"""
import collections,hashlib,json,math,pickle,re,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import inventory as I
OUT=H/'field-signed-port-allocation-r3';GROUND={'FA':'/motherboard_motors{slash}FIELD_GND','FB':'/motherboard_do{slash}FIELD_B_0V'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return s.replace('{slash}','/')
def main():
    if OUT.exists():raise ValueError('Fresh physical field allocation required')
    model_path=H/'field-power/normal-model-r3.json';model=json.loads(model_path.read_bytes());source=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';native_root=H/'field-power/native-bound-field-base-r5';br=json.loads((native_root/'receipt.json').read_bytes())
    if sha(model_path)!='63366d0a6f649300b99675b2c08b82e0da6fe75166b3fdd26852e4f35cd53ad0' or sha(source)!='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2' or sha(native_root/'model.pkl')!=br['model_sha256']:raise ValueError('Exact planning/native source changed')
    I.NET=source;parts,pins,nets=I.load();g=pickle.loads((native_root/'model.pkl').read_bytes())['discrete'];physical=collections.defaultdict(list)
    for pad in g['pads']:physical[(pad['ref'],pad['num'])].append(pad)
    terms=[];unresolved=[];notes=[]
    def ground_ports(refs,domain):
        rows=[]
        for ref in refs:
            for p in pins[ref]:
                if p['net']!=GROUND[domain]:continue
                if ref.startswith('U') and not re.search(r'(GND|^EP_|^FGND|^D_|^S_)',p['pinfunction']):continue
                rows.append((ref,p['pin']))
        return sorted(set(rows))
    def endpoints(pairs):
        rows=[]
        for ref,pin in sorted(set(pairs)):
            node=next(p for p in pins[ref] if p['pin']==pin);pads=physical[(ref,pin)]
            if not pads or any(p['net']!=node['net'] for p in pads):raise ValueError('Native physical endpoint identity mismatch '+ref+'.'+pin)
            rows.extend({'ref':ref,'pin':pin,'pinfunction':node['pinfunction'],'raw_net':node['net'],'physical_pad_uuid':pad['uuid'],'at_mm':[pad['x'],pad['y']],'actual_pad_layers':sorted(pad['layers'])} for pad in pads)
        return rows
    def add(name,domain,current,pairs,kind='load',basis='',extra=None):
        rows=endpoints(pairs)
        if not rows:unresolved.append({'term':name,'domain':domain,'current_a':current,'reason':'No physically eligible exact source return endpoint'})
        terms.append({'name':name,'domain':domain,'signed_current_a':current,'kind':kind,'eligible_physical_endpoints':rows,'allocation':'One conserved term; unknown nonnegative simplex weights sum to 1 across listed actual pads. Every vertex is a required worst-case routing scenario; no equal sharing claim.' if len(rows)>1 else 'Exact sole physical endpoint','basis':basis,**(extra or {})})
    def pool(domain):
        refs={p['ref'] for p in nets[GROUND[domain]] if not p['ref'].startswith(('C','J'))}
        return ground_ports(refs,domain)
    def sinks(net,domain,excluded):
        seen=set();queue=collections.deque([(net,0)]);found=set();trace=[]
        while queue:
            node,depth=queue.popleft()
            if node in seen or depth>5:continue
            seen.add(node)
            for p in nets.get(node,[]):
                ref=p['ref']
                if ref in excluded or ref.startswith(('C','J')):continue
                grounds=ground_ports([ref],domain)
                if grounds:found.update(grounds);trace.append({'from_net':node,'through_part':ref,'actual_return_ports':[list(x) for x in grounds]});continue
                if ref.startswith(('R','D','Q')):
                    for other in pins[ref]:
                        if other['net']!=node and other['net'] not in GROUND.values() and not other['net'].startswith('unconnected-'):queue.append((other['net'],depth+1))
        return sorted(found),trace
    def resistors(rows,domain,tag):
        for row in rows:
            ref=row['ref'];other=next(p for p in pins[ref] if p['pin']==row['other_pin'])
            if norm(other['net'])!=norm(row['other_net']):raise ValueError('Exact resistor topology differs '+ref)
            if other['net']==GROUND[domain]:pairs=[(ref,other['pin'])];trace=[]
            else:pairs,trace=sinks(other['net'],domain,{ref})
            add(tag+'/'+ref,domain,row['current_upper_a'],pairs,'resistor_zero_drop_bound',row['basis'],{'source_feed_ref_pin':[ref,row['source_pin']],'source_downstream_raw_net':other['net'],'downstream_source_endpoint_walk':trace,'active_semiconductor_state_path_qualification':'OPEN; candidate endpoints conservatively nominated from exact source incidence, not guaranteed conduction or current sharing'})
    def qterms(q,domain,tag):
        for label,current in q.items():
            refs=re.findall(r'U\d+',label)
            if refs:add(tag+'/'+label,domain,current,ground_ports(refs,domain),'IC_row_envelope',label)
            else:add(tag+'/'+label,domain,current,pool(domain),'planning_reservation','Preserved explicit leak/switching reservation across real installed eligible returns; not a fictitious load')
    # Preserve all fitted external contracts and require arbitrary connector sharing.
    for domain,letter in [('FA','A'),('FB','B')]:
        add('External eight smart DO outputs',domain,4.,[('JD09',letter+str(i)) for i in range(9,13)],'external_contract','Eight simultaneous .5-A outputs; 4-A total. Distribution over four actual return terminals depends on the harness, not an assumed equal split.',{'output_ports':[{'ref':'JD09','pin':letter+str(i),'raw_net':next(p['net'] for p in pins['JD09'] if p['pin']==letter+str(i)),'simultaneous_current_a':.5} for i in range(1,9)]})
    add('All twelve motor AUX24 returns','FA',model['normal_external_output_contracts_a']['FA']['all12_motor_AUX24'],[(f'JD{i:02d}',letter+'13') for i in range(1,7) for letter in ('A','B')],'external_contract','Preserved .148+.074-A total for all twelve fitted motor AUX24 interfaces; actual per-interface allocation/harness bounds require qualification, no eight-channel derating')
    for i,pin in [(0,'B3'),(1,'B6')]:add('Probe '+str(i)+' external return','FA',.1,[('JD14',pin)],'external_contract','Preserved full .1-A probe contract')
    for i,ref,letter in [(0,'JD07','A'),(1,'JD07','B'),(2,'JD08','B')]:add('Sensor group '+str(i)+' external return','FB',.2,[(ref,letter+'11'),(ref,letter+'12')],'external_contract','Preserved .2-A branch; external harness return sharing is an unqualified simplex')
    add('Six safety DI wetting returns','FB',.0165,ground_ports(['U19001','U19002','U19003'],'FB'),'external_contract','Six .00275-A wetting channels preserved; device/channel allocation remains conservative over actual field-side return pins')
    add('Armed lamp external return','FB',.05,[('JD08','A9')],'external_contract','Full .05-A armed lamp current, actual local return terminal')
    # Each regulator obeys signed KCL; buck ground injection is negative.
    for ref,port in model['signed_regulator_ports'].items():
        domain='FA' if ref in ('U11009','U11017') else 'FB'
        add(ref+' signed ground port',domain,port['GND_injection_a'],ground_ports([ref],domain),'signed_regulator_port','Exact preserved IN = OUT + GND signed planning ports; negative buck current is real local circulating current',{'regulator_ports':port})
    q=model['component_current_terms'];feeds=model['resistor_source_upper_bounds']
    qterms(q['A3V3'],'FA','DOA3V3');resistors(feeds['DOA_FIELD_3V3'],'FA','DOA3V3')
    add('DOA3V3 unused route envelope','FA',.05-model['computed_local_output_envelopes_a']['DOA3V3'],pool('FA'),'planning_reservation','Difference between .05-A route target and actual complete source row envelope; preserve reservation across eligible installed load returns')
    for label,target in [('B_retained_rail',.09),('B_DO_rail',.04)]:
        block=model['pin_load_allocation'][label];qterms(block['IC_terms'],'FB',label);resistors(block.get('retained_resistors',block.get('moved_pullups',[])),'FB',label)
        if label=='B_DO_rail':
            add('Dedicated DO3V3 R11088 bleed','FB',block['new_R11088_bleed_a'],ground_ports(['R11088'],'FB'),'resistor_zero_drop_bound','Exact new resistor ground endpoint')
            add('Dedicated DO3V3 leak reservation','FB',block['additional_leak_switching_reservation_a'],pool('FB'),'planning_reservation','Explicit preserved installed-load leak/switching margin')
        actual=model['computed_local_output_envelopes_a']['DOB3V3_retained_safety_diagnostics' if label=='B_retained_rail' else 'DOB_DO3V3_new_dedicated']
        add(label+' unused route envelope','FB',target-actual,pool('FB'),'planning_reservation','Explicit target-minus-complete-load route reservation, not invented installed load')
    qterms(q['FIELD5V'],'FA','FIELD5V');resistors(feeds['FIELD_5V']+feeds['AUX_5V_A']+feeds['AUX_5V_B'],'FA','FIELD5V_AUX5')
    add('All twelve motor AUX5 external returns','FA',.192,[(f'JD{i:02d}',letter+'13') for i in range(1,7) for letter in ('A','B')],'external_contract','Preserved full .192-A AUX5 load; separate from AUX24 and not converted into a CORE-equivalent current')
    add('FIELD5V unused route envelope','FA',.36-model['computed_local_output_envelopes_a']['FIELD5V_after_A_prereg'],pool('FA'),'planning_reservation','Buck output .36 A minus actual .3411309812-A local load estimate, including .051-A LDO input')
    resistors(feeds['FIELD_B_5V_PRE'],'FB','FIELD_B5V_PRE')
    add('C11095 preserved DC leakage reservation','FB',model['C11095_local_bypass']['DC_leak_reservation_a'],ground_ports(['C11095'],'FB'),'capacitor_DC_leak_reservation','Exact separately documented10-uA C11095 DC leak reservation from frozen model; startup/ripple currents remain distinct and open')
    add('FIELD_B5V_PRE unused route envelope','FB',.14-model['computed_local_output_envelopes_a']['FIELD_B5V_PRE_after_split'],pool('FB'),'planning_reservation','Buck .14-A target minus actual .1325853846-A complete local inputs, including .091/.041-A LDO inputs')
    for domain,refs in [('FA',['U10004','U10009']),('FB',['U10017','U10022'])]:
        for ref in refs:add(ref+' VS own ground reservation',domain,.003,ground_ports([ref],domain),'IC_row_envelope','TPS274 VS .003-A reservation; VDD .0016-A term is separate and external DO load return is not device GND')
    for domain,refs,current in [('FA',['U14026','U14027'],.0015),('FB',['U19004','U19005','U19006'],.0015),('FB',['U19007','U19018'],.008)]:
        for ref in refs:add(ref+' local own ground reservation',domain,current,ground_ports([ref],domain),'IC_row_envelope','Preserved upstream IC own consumption; powered output load returns separately through actual external return terminals')
    for ref in ('U11015','U11016'):
        pairs=[(ref,p['pin']) for p in pins[ref] if re.match(r'(GND_|RTN_|EP_RTN_)',p['pinfunction'])]
        add(ref+' aggregate GND RTN IQ','FA',.0006,pairs,'multi_net_IC_simplex','Aggregate .600-mA IQ counted once; unbounded internal GND/RTN sharing across exact separate native raw-net terminals',{'different_raw_net_ports_must_remain_distinct':True,'RTN_support_circuit_and_path_to_actual_field_source_qualification':'OPEN; no generic-ground short or external-load rerouting onto RTN','individual_port_routing_reservation_a':.001})
    for row in model['exact_branch_passive_networks']:
        add('Passive '+row['name'],row['domain'],row['planning_upper_a'],ground_ports(row['refs'],row['domain']),'exact_passive_network_bound',row['planning_basis'],{'exact_resistor_refs':row['refs'],'ground_branch_sharing':'Conservative simplex; source series/parallel total retained, no arbitrary repeated total at every parallel resistor'})
    resistors(feeds['AUX_24V_A']+feeds['AUX_24V_B'],'FA','AUX24 bleed/monitor')
    resistors([r for r in feeds['FIELD_A_24V_PROTECTED'] if r['ref'] not in {'R14058','R14064'}],'FA','Protected24 direct')
    resistors([r for r in feeds['FIELD_B_24V_PROTECTED'] if r['ref'] not in {'R19021','R19028','R19034'}],'FB','Protected24 direct')
    for domain in ('FA','FB'):
        add('Protected24 aggregate unbounded leakage reservation',domain,.005,pool(domain),'planning_reservation','Preserved IC input/TVS/FET/switching aggregate unknown; allocated over real installed eligible returns')
        ref='U11004' if domain=='FA' else 'U11006';add(ref+' upstream own IQ',domain,.002,ground_ports([ref],domain),'planning_reservation','TPS26630 .002-A entry IQ reservation')
        resistors(feeds[domain+'_RAW']+feeds[domain+'_IN'],domain,'Upstream raw divider/control')
        add('Upstream reverse-block gate/TVS leak reservation',domain,.001,pool(domain),'planning_reservation','Preserved explicit entry margin; full hot/fault transient bounds remain open')
        ref='J11003' if domain=='FA' else 'J11005';add('Actual external source return sink',domain,-model['real_connector_input_return_envelopes_a'][domain],[(ref,'2')],'source_sink','Sole actual field supply-return source; shutdown contacts J11004/J11006 are not alternative current sinks')
    sums={d:math.fsum(t['signed_current_a'] for t in terms if t['domain']==d) for d in GROUND}
    if any(abs(v)>1e-12 for v in sums.values()):raise ValueError('Preserved signed whole-domain KCL does not conserve: '+repr(sums))
    caps=[{'domain':d,'ref':node['ref'],'pin':node['pin'],'raw_net':GROUND[d],'physical_pads':endpoints([(node['ref'],node['pin'])]),'steady_DC_current_a':model['C11095_local_bypass']['DC_leak_reservation_a'] if node['ref']=='C11095' else 0,'DC_reservation_counted_once_in_terms':node['ref']=='C11095','startup_ripple_and_fault_current':'OPEN; DC zero cannot size these local loops'} for d in GROUND for node in nets[GROUND[d]] if node['ref'].startswith('C')]
    ledger={(r['physical_pad_uuid'],r['raw_net']) for t in terms for r in t['eligible_physical_endpoints']};rootchecks={d:{'signed_KCL_sum_a':sums[d],'actual_source_return_a':model['real_connector_input_return_envelopes_a'][d],'positive_ground_injections_a':math.fsum(t['signed_current_a'] for t in terms if t['domain']==d and t['signed_current_a']>0),'negative_local_converter_ground_a':math.fsum(t['signed_current_a'] for t in terms if t['domain']==d and t['kind']=='signed_regulator_port' and t['signed_current_a']<0)} for d in GROUND}
    OUT.mkdir();report={'verdict':'PASS_SIGNED_PLANNING_KCL_AND_EXACT_PHYSICAL_ENDPOINTS_ACTIVE_PATHS_CURRENT_SHARING_OPEN' if not unresolved else 'SIGNED_PLANNING_ENDPOINT_ALLOCATION_INCOMPLETE','terms':terms,'unresolved_endpoint_terms':unresolved,'domain_checks':rootchecks,'all_terms_counted_once':True,'all16_DO_12_motor_interfaces_3_sensors_2_probes_6_wetting_and_lamp_preserved':True,'arbitrary_equal_sharing_forbidden':True,'simplex_vertices_must_be_checked_in_actual_resistive_mesh':True,'steady_DC_capacitor_ports':caps,'actual_distinct_physical_pad_net_pairs':len(ledger),'source_sha256':sha(source),'model_sha256':sha(model_path),'native_discrete_sha256':br['native_discrete_sha256'],'read_files_sha256':{str(p.resolve()):sha(p) for p in (source,model_path,native_root/'receipt.json',native_root/'model.pkl',I.PARSER,Path(I.__file__),Path(__file__))},'physical_ground_root_completion':'OPEN','active_semiconductor_conduction_state_and_RTNGND_internal_split':'OPEN','mesh_drop_barrel_current_thermal_transient_and_manufacturing_qualification':'OPEN','native_jobs':0,'board_or_source_changed':False,'adopted':False,'preserved_failed_r2_helper_sha256':sha(H/'allocate_field_signed_ports_r2.py'),'r2_cap_port_serialization_cause':'Net member records contain ref and pin only; bind capacitor raw net to exact iteration key, independently verify pad source net in endpoints.','preserved_failed_r1_helper_sha256':sha(H/'allocate_field_signed_ports_r1.py'),'r1_missing_10uA_term_cause':'Frozen model already includes C11095 DC leak10uA in B5 output. Explicit physical-ground term restored without changing model or balancing reservation.'}
    (OUT/'receipt.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':report['verdict'],'terms':len(terms),'unresolved':unresolved,'domain_checks':rootchecks,'physical_pad_net_pairs':len(ledger)}),flush=True)
if __name__=='__main__':main()
