"""Independent pin-by-pin native validation of the additive motherboard source."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard'


def nodes(tree):
    result={}
    for net in tree.findall('.//nets/net'):
        for node in net.findall('node'):
            key=(node.attrib['ref'],node.attrib['pin'])
            if key in result:raise ValueError('Duplicate native source pin '+repr(key))
            result[key]=net.attrib['name']
    return result


def validate(tree,model,mapping,check_hashes=True):
    errors=[];actual=nodes(tree);parts=model['components'];expected={}
    from hardware_check_source27_feed_reset import check_feed_reset
    feed_errors,feed_overrides,feed_extra=check_feed_reset(tree,model,mapping,actual)
    errors.extend(feed_errors)
    # A native XML exporter may repeat a qualified name on distinct nets.
    # Text equality cannot prove a physical connection across hierarchy.
    named_codes={}
    for net in tree.findall('.//nets/net'):
        if any(n.attrib['ref'] in parts for n in net.findall('node')):
            named_codes.setdefault(net.attrib['name'],set()).add(net.attrib['code'])
    for name,codes in named_codes.items():
        if len(codes)>1:errors.append('Distinct native electrical nets share fitted name '+name)
    if model.get('manufacturing_ready') or model.get('physical_qualification'):
        errors.append('Incomplete source integration cannot assert manufacture/measurement')
    ledger=mapping.get('native_net_renames_allowed',[])
    allowed={}
    if ledger:
        if not isinstance(ledger,list) or any(not isinstance(r,dict) for r in ledger):
            errors.append('Motherboard must preserve one-board topology and retained native nets')
        else:
            proposal=json.loads((OUT/'fpga-allocation-proposal.json').read_text(encoding='utf-8'))
            reviewed={r['ball']:r['signal'] for r in proposal['candidates']['base_preserve_all_current']['signals']
                      if r['allocation_state']=='proposed_NC_to_named_signal'}
            if 'motherboard_operator' in mapping['blocks']:
                # Two independently reviewed BANK4B slow outputs; this exact
                # extension never grants arbitrary renaming of retained GPIO.
                reviewed.update({'M4':'FAST_PORTS_ENABLE','M6':'XF_POWER_ENABLE'})
            real={
                'FPGA_PROGRESS_O':'watchdog_conditioning/FPGA_PROGRESS_O',
                'OPI_REARM_O':'mc_permission/OPI_REARM_OUT','PERMIT_OUT_REQ':'mc_permission/PERMIT_OUT_REQ',
                **{n:'mc_permission/'+n for n in ('OPI_OK_TX','OPI_OK_BOE','OPI_OK_OUT','OUT_PERMIT','PROC_PERMIT','TAMPER_CLEAR_N')},
                'WATCHDOG_TRIP_M':'mc_permission/WD_M_TRIP_N','WATCHDOG_TRIP_O':'mc_permission/WD_O_TRIP_N',
                'MOTION_A_PGOOD':'motherboard_motors/MOTOR_POWER_OK_A_QUALIFIED',
                'MOTION_B_PGOOD':'motherboard_motors/MOTOR_POWER_OK_B_QUALIFIED',
                'OPI_OK_A':'motherboard_motors/OPI_OK_A','OPI_OK_B':'motherboard_motors/OPI_OK_B'}
            seen=set()
            for row in ledger:
                pin=row.get('pin');signal=reviewed.get(pin);key=('U1001',pin)
                old=mapping['retained_native_pin_nets'].get('U1001.'+str(pin),'')
                new='/'+real.get(signal,signal if signal in ('FPGA_OUTPUT_REQUEST','WD_M_OK','WD_O_OK') else 'fpga_core/'+str(signal))
                if (row.get('reference')!='U1001' or pin in seen or not signal or row.get('signal')!=signal
                    or row.get('old_native_net')!=old or not old.startswith('unconnected-(U1001-')
                    or row.get('new_native_net')!=new):
                    errors.append('Unreviewed retained native pin rename '+repr(row))
                else:allowed[key]=new
                seen.add(pin)
            if len(ledger)!=len(reviewed) or seen!=set(reviewed):errors.append('Exact reviewed former FPGA NC ball inventory required')
    home_ledger=mapping.get('native_home_nc_deallocations_allowed',[])
    if home_ledger:
        required={b:('HOME'+str(i)+'_FPGA',pn) for i,(b,pn) in enumerate((
            ('B10','GPIOR_82'),('B11','GPIOR_83'),('A11','GPIOR_84'),
            ('C12','GPIOR_85'),('C11','GPIOR_86'),('D12','GPIOR_89'),
            ('C14','GPIOR_102'),('D13','GPIOR_103'),('B16','GPIOR_106'),
            ('A14','GPIOR_90'),('E12','GPIOR_91'),('B14','GPIOR_92')))}
        seen=set()
        for row in home_ledger:
            ball=row.get('pin');spec=required.get(ball)
            if spec:
                signal,pn=spec;old='/fpga_core/'+signal;new='unconnected-(U1001-'+pn+'-Pad'+ball+')'
            else:old=new=None;signal=None
            if (row.get('reference')!='U1001' or ball in seen or not spec or
                row.get('signal')!=signal or row.get('old_native_net')!=old or
                mapping['retained_native_pin_nets'].get('U1001.'+str(ball))!=old or
                row.get('new_native_net')!=new):errors.append('Unreviewed obsolete HOME NC change '+repr(row))
            else:allowed['U1001',ball]=new
            seen.add(ball)
        if seen!=set(required) or len(home_ledger)!=12:errors.append('Exact twelve obsolete HOME NC endpoints required')
    health_ledger=mapping.get('native_reserved_health_reconciliation_allowed',[])
    if health_ledger:
        required={
            'C8':('HEALTH_SR_CLK','GPIOL_72_EXTFB0_CDI14'),
            'T12':('HEALTH_SR_DATA','GPIOB_RXP07'),
            'D8':('HEALTH_SR_LOAD_N','GPIOL_73_EXTFB1_CDI15'),
            'K16':('XS_CS_N','GPIOR_132_CDI19'),
            'T3':('XS_MISO','GPIOB_TXN03'),
            'J13':('XS_MOSI','GPIOR_133_CDI18'),
            'J14':('XS_REFCLK','GPIOR_135_CDI17'),
            'K15':('XS_SCLK','GPIOR_136_CDI16'),
            'L13':('XS_SYNC_STROBE','GPIOR_157_PLLIN'),
            'P4':('RAILS_OK_FPGA','GPIOB_TXN01')}
        seen=set()
        for row in health_ledger:
            ball=row.get('pin');spec=required.get(ball)
            signal,pn=spec if spec else (None,None)
            old='/fpga_core/'+signal if signal else None
            new=('/FPGA_CRESET_N' if ball=='P4' else
                 'unconnected-(U1001-'+pn+'-Pad'+ball+')') if spec else None
            if (row.get('reference')!='U1001' or ball in seen or not spec or
                row.get('signal')!=signal or row.get('old_native_net')!=old or
                # These ten signals were the exact earlier NC promotions;
                # this second transaction removes nine and bridges one.
                not any(isinstance(p,dict) and p.get('pin')==ball and p.get('signal')==signal and
                        p.get('old_native_net')==mapping['retained_native_pin_nets'].get('U1001.'+str(ball)) and
                        p.get('new_native_net')==old for p in ledger) or
                row.get('new_native_net')!=new):
                errors.append('Unreviewed reserved-health physical pin change '+repr(row))
            else:allowed['U1001',ball]=new
            seen.add(ball)
        if seen!=set(required) or len(health_ledger)!=10:
            errors.append('Exact nine reserved NC and one real rail bridge required')
        if actual.get(('U1001','P4'))!=actual.get(('U2006','4')) or actual.get(('U2006','4'))!='/FPGA_CRESET_N':
            errors.append('FPGA rail readback must observe actual U2006.4 buffered rail')
    if not model.get('one_custom_board'):
        errors.append('Motherboard must preserve one-board topology and retained native nets')
    unused_rows=mapping.get('native_unused_functional_dispositions_allowed',[])
    unused_by_block={}
    if 'motherboard_diagnostics' in mapping['blocks']:
        # This independently frozen review bounds every graphical NC. It
        # does not grant arbitrary aliases or change manufacturer meanings.
        p=ROOT/'reports/motherboard-diagnostics-20260930/r01/bounded-NC-proposals.json'
        if hashlib.sha256(p.read_bytes()).hexdigest()!='f0f373546595840851fd4776cff5b48e9534ae8c0fb3655ef751cb7025dd035f':
            errors.append('Immutable unused-functional endpoint review changed')
        specs=json.loads(p.read_text())['native_physical_NC_proposals']
        required={(r['ref'],r['pin']):r for r in specs};seen=set()
        for row in unused_rows:
            key=(row.get('reference'),row.get('pin'));r=required.get(key)
            # The native XML function appends the pin number. NC net names
            # use the real symbol name without that exporter suffix.
            function=None if not r else r['function'][:-(len(r['pin'])+1)]
            new=None if not r else 'unconnected-('+r['ref']+'-'+function+'-Pad'+r['pin']+')'
            if (not r or key in seen or row.get('old_native_net')!=r['net'] or
                row.get('new_native_net')!=new or row.get('source_block')!=r['source_block'] or
                row.get('native_pin_function')!=r['function'] or row.get('MPN')!=r['MPN'] or
                row.get('electrical_type')!=r['native_electrical_type']):
                errors.append('Unreviewed unused functional endpoint '+repr(row))
            else:
                if r['source_block'] in ('fpga_core','mc_local_power'):allowed[key]=new
                else:unused_by_block.setdefault(r['source_block'],{})[key]=new
            seen.add(key)
        if len(unused_rows)!=20 or seen!=set(required):errors.append('Exact twenty unused functional endpoints required')
    power_delta=mapping.get('reviewed_power_delta')
    if power_delta:
        if (power_delta.get('upgrade',{}).get('id')!='MB-IO3-001'
            or any(power_delta.get(k,{}).get('id')!='MB-IO3-WINDOW-001' for k in ('mc_window','motor_window'))):
            errors.append('Unreviewed power delta')
        for ref,pin in (('U2002','3'),('L2002','2'),('C2005','1'),('C2010','1')):
            allowed[ref,pin]='/mc_local_power/IO_3V3_REG_LOCAL'
        allowed['R2005','2']='/mc_local_power/CORE_5V'
        allowed['R2069','1']='/mc_local_power/IO_3V3_OV_SERIES_MC_R2069'
        expected_mpn={'U2002':'TPS62902RPJR','R2005':'CRCW06030000Z0EA',
            'R2008':'TNPW06032K55BYEA','R2061':'TNPW060353K6BEEA',
            'R2069':'TNPW060357K6BEEA','R9005':'TNPW060353K6BEEA',
            'R9015':'TNPW060353K6BEEA','R9007':'TNPW060357K6BEEA','R9017':'TNPW060357K6BEEA'}
        for ref,mpn in expected_mpn.items():
            if parts.get(ref,{}).get('mpn')!=mpn:errors.append('Exact reviewed IO3 power part required '+ref)
    for key,net in mapping['retained_native_pin_nets'].items():
        ref,pin=key.split('.',1);wanted=allowed.get((ref,pin),net);expected[ref,pin]=wanted
        if actual.get((ref,pin))!=wanted:errors.append('Retained MC fitted pin/net changed '+key)
    if len({r for r,p in expected})!=327:errors.append('Retained 327-part inventory changed')
    for name,block in mapping['blocks'].items():
        source_folder=block.get('source_folder','hardware/'+name)
        expected_folder='hardware/motherboard_probe_limit_upgrade' if name=='motherboard_operator' and 'source_folder' in block else 'hardware/'+name
        if source_folder!=expected_folder:
            errors.append('Unreviewed source replacement '+name)
            source_folder='hardware/'+name
        source=ET.parse(ROOT/source_folder/'netlist.xml')
        overrides={}
        if power_delta and name=='motherboard_motor_power':
            overrides.update({(ref,'1'):'/motherboard_motor_power/IO_3V3_OV_SERIES_MOTOR_'+ref for ref in ('R9007','R9017')})
        for row in block.get('exact_source_pin_overrides',[]):
            bank={'7':'A','3':'B'}.get(row.get('pin'))
            safety_changes={
                ('motherboard_power_entry','U11018','5'):('/FIELD_B_24V_PROTECTED','/motherboard_safety_sensor/FIELD_B_5V_PRE'),
                ('motherboard_power_entry','U11018','8'):('/FIELD_B_24V_PROTECTED','/motherboard_safety_sensor/FIELD_B_5V_PRE'),
                ('motherboard_io_control','U13001','42'):(None,'/motherboard_safety_sensor/DIC_SENSOR_SCL'),
                ('motherboard_io_control','U13001','43'):(None,'/motherboard_safety_sensor/DIC_SENSOR_SDA')}
            exact=safety_changes.get((name,row.get('reference'),row.get('pin')))
            if exact and 'motherboard_safety_sensor' in mapping['blocks']:
                if (row.get('old_source_net'),row.get('new_native_net'))!=exact:
                    errors.append('Unreviewed safety endpoint source pin override '+repr(row))
                else:overrides[(row['reference'],row['pin'])]=row['new_native_net']
            elif (name!='motherboard_motors' or 'motherboard_power_entry' not in mapping['blocks']
                or row.get('reference')!='U6042' or not bank
                or row.get('old_source_net')!='/MOTOR_TX_GATE_'+bank
                or row.get('new_native_net')!='/motherboard_motors/MOTOR_TX_GATE_SOURCE_'+bank):
                errors.append('Unreviewed source pin override '+repr(row))
            else:overrides[('U6042',row['pin'])]=row['new_native_net']
        if name=='motherboard_motors' and 'motherboard_power_entry' in mapping['blocks']:
            if set(overrides)!={('U6042','7'),('U6042','3')}:errors.append('Exactly two motor health-contact interpositions required')
        if 'motherboard_safety_sensor' in mapping['blocks'] and name in ('motherboard_power_entry','motherboard_io_control'):
            required={('U11018','5'),('U11018','8')} if name=='motherboard_power_entry' else {('U13001','42'),('U13001','43')}
            if set(overrides)!=required or len(block.get('exact_source_pin_overrides',[]))!=2:
                errors.append('Exactly two reviewed safety sensor endpoints required '+name)
        unused=unused_by_block.get(name,{})
        declared=block.get('exact_unused_functional_pin_dispositions',[])
        if {(r.get('reference'),r.get('pin')) for r in declared}!=set(unused) or len(declared)!=len(unused):
            errors.append('Exact block unused functional endpoint disposition required '+name)
        overrides.update(unused)
        if name=='motherboard_power_entry':overrides.update(feed_overrides)
        for (old,pin),net in nodes(source).items():
            ref=block['references'].get(old)
            if ref not in parts:continue
            bare=net.lstrip('/')
            if (ref,pin) in overrides:
                wanted=overrides[ref,pin];expected[ref,pin]=wanted
                if actual.get((ref,pin))!=wanted:errors.append('New source pin/net mismatch '+ref+'.'+pin+' expected '+wanted+' got '+str(actual.get((ref,pin))))
            elif bare.startswith('unconnected-'):
                expected[ref,pin]=None
                if not actual.get((ref,pin),'').lstrip('/').startswith('unconnected-'):
                    errors.append('Declared native NC changed '+ref+'.'+pin)
            else:
                wanted=overrides.get((ref,pin),'/'+block['ports'].get(bare,name+'/'+bare))
                expected[ref,pin]=wanted
                if actual.get((ref,pin))!=wanted:errors.append('New source pin/net mismatch '+ref+'.'+pin+' expected '+wanted+' got '+str(actual.get((ref,pin))))
    if power_delta:
        extra_pins={
            'R18001':{'1':'/mc_local_power/IO_3V3_REG_LOCAL','2':'/IO_3V3'},
            'R18002':{'1':'/mc_local_power/IO_3V3_REG_LOCAL','2':'/mc_local_power/IO_3V3_VSET'},
            'R18003':{'1':'/IO_3V3','2':'/mc_local_power/IO_3V3_OV_SERIES_MC_R2069'},
            'R18004':{'1':'/IO_3V3','2':'/motherboard_motor_power/IO_3V3_OV_SERIES_MOTOR_R9007'},
            'R18005':{'1':'/IO_3V3','2':'/motherboard_motor_power/IO_3V3_OV_SERIES_MOTOR_R9017'}}
        extra_mpns={'R18001':'KRL2012E-C-R015-F-T5','R18002':'TNPW060311K5BYEA',
                    **{r:'TNPW0603698RBEEA' for r in ('R18003','R18004','R18005')}}
        if power_delta.get('reset_bypass'):
            if power_delta['reset_bypass'].get('id')!='MB-IO3-002' or power_delta['reset_bypass'].get('added_refs')!=['C18001']:
                errors.append('Exact single receiving-IO3 reset-buffer bypass required')
            extra_pins['C18001']={'1':'/IO_3V3','2':'/LOGIC_GND'}
            extra_mpns['C18001']='GRM188R72A104KA35D'
            if actual.get(('C18001','1'))!=actual.get(('U2006','5')) or actual.get(('C18001','2'))!=actual.get(('U2006','3')):
                errors.append('Reset-buffer bypass must follow actual receiving supply/return')
        for ref,pins in extra_pins.items():
            if parts.get(ref,{}).get('mpn')!=extra_mpns[ref]:errors.append('Actual IO3 helper part required '+ref)
            for pin,net in pins.items():
                expected[ref,pin]=net
                if actual.get((ref,pin))!=net:errors.append('IO3 damping/Kelvin/window topology mismatch '+ref+'.'+pin)
        if actual.get(('R18001','1'))==actual.get(('R18001','2')):
            errors.append('Distributed IO3 cannot bypass damping resistor')
    for key,wanted in feed_extra.items():
        expected[key]=wanted
        if wanted is None:
            if not actual.get(key,'').startswith('unconnected-'):errors.append('Exact new reset NC endpoint required '+repr(key))
        elif actual.get(key)!=wanted:errors.append('Exact receiving CLR native endpoint required '+repr(key))
    extra={key for key in actual if key[0] in parts}-set(expected)
    if extra:errors.append('Unexpected fitted native pins '+repr(sorted(extra)))
    native_parts={c.attrib['ref']:c for c in tree.findall('.//components/comp') if c.attrib['ref'] in parts}
    if set(native_parts)!=set(parts):errors.append('Physical inventory differs from native netlist')
    for ref,c in native_parts.items():
        model_part=parts[ref]
        if (c.findtext('footprint') or '')!=model_part.get('footprint',''):errors.append('Footprint mismatch '+ref)
        if (c.findtext('value') or '')!=model_part.get('value',''):errors.append('Value mismatch '+ref)
        mpn=c.find("./fields/field[@name='MPN']")
        if (mpn.text if mpn is not None and mpn.text else '')!=model_part.get('mpn',''):errors.append('MPN mismatch '+ref)
    if check_hashes:
        for relative,wanted in mapping['input_sha256'].items():
            p=ROOT/relative
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=wanted:errors.append('Input changed '+relative)
    try:
        from hardware_check_source26_parts import check_source26
    except ModuleNotFoundError:
        from tools.hardware_check_source26_parts import check_source26
    errors.extend(check_source26(parts, actual, model, mapping))
    from hardware_check_source27_parts import check_source27
    errors.extend(check_source27(parts, actual, model, mapping))
    adc_delta=mapping.get('reviewed_adc_bypass_delta')
    adc_metadata=model.get('adc_bypass_correction')
    if adc_delta or adc_metadata:
        wanted={
            'C14744':('885012206052',1e-6,'Capacitor_SMD:C_0603_1608Metric','9','8'),
            'C14745':('885012206052',1e-6,'Capacitor_SMD:C_0603_1608Metric','30','29'),
            'C14746':('GRM21BR71A106MA73L',10e-6,'Capacitor_SMD:C_0805_2012Metric','34','33')}
        if not adc_delta or adc_delta.get('id')!='MB-AI-ADC-001' or adc_delta.get('references')!=list(wanted):
            errors.append('Exact three-cap ADC source ledger required')
        for ref,(mpn,cap,footprint,power,ground) in wanted.items():
            c=parts.get(ref,{})
            if c.get('mpn')!=mpn or abs(c.get('capacitance_f',0)-cap)>1e-15 or c.get('footprint')!=footprint:
                errors.append('Exact local ADC bypass part required '+ref)
            if (actual.get((ref,'1'))!=actual.get(('U14734',power)) or
                actual.get((ref,'2'))!=actual.get(('U14734',ground)) or
                actual.get((ref,'1'))!='/motherboard_analog_input/AI_5V' or
                actual.get((ref,'2'))!='/motherboard_analog_input/AI_AGND'):
                errors.append('Local ADC bypass must follow exact supply/return pins '+ref)
        if (not adc_metadata or not adc_metadata.get('direct_AVDD_DVDD_REFCAP_no_via_routes_required') or
            not adc_metadata.get('all_seven_local_ADC_caps_generic_router_excluded') or
            adc_metadata.get('reference_effective_bias_age_temp_ESR_qualified') or
            adc_metadata.get('LDO_startup_discharge_transient_new_capacitive_loading_qualified')):
            errors.append('ADC source correction must preserve direct-loop and physical qualification gates')
    if 'motherboard_diagnostics' in mapping['blocks']:
        diagnostics={
            ('U22001','3'):'/motherboard_power_entry/FA_PGOOD',
            ('U22001','5'):'/motherboard_do/DOA_FIELD_3V3',
            ('U22001','2'):'/motherboard_motors/FIELD_GND',
            ('U22001','4'):'/motherboard_motors/FIELD_GND',
            ('U22002','3'):'/motherboard_do/DOA_FIELD_3V3',
            ('U22002','1'):'/motherboard_motors/FIELD_GND',
            ('U22002','8'):'/motherboard_motors/FIELD_GND',
            ('U22003','3'):'/motherboard_do/DOB_FIELD_3V3',
            ('U22003','4'):'/motherboard_power_entry/FB_PGOOD',
            ('U22003','1'):'/motherboard_do/FIELD_B_0V',
            ('U22003','8'):'/motherboard_do/FIELD_B_0V',
            **{(r,p):n for r in ('U22002','U22003') for p,n in (
                ('9','/LOGIC_GND'),('16','/LOGIC_GND'),('14','/IO_3V3'))}}
        for key,net in diagnostics.items():
            if actual.get(key)!=net:errors.append('Diagnostic source must preserve actual separate field domain '+'.'.join(key))
        pairs=[(('U22002','13'),('U13004','16')), (('U22003','13'),('U13008','16')),
            (('U22001','1'),('U22002','4')), (('R22001','1'),('U22001','1')),
            (('R22002','1'),('U11006','16')), (('R22002','2'),('U22003','3'))]
        pairs.extend((('TP2200'+str(i),'1'),('U1001',b)) for i,b in enumerate(('A3','C6','A4','E5'),1))
        for a,b in pairs:
            if not actual.get(a) or actual.get(a)!=actual.get(b):
                errors.append('Diagnostic source must join actual hardware provider '+'.'.join(a)+'/'+'.'.join(b))
        for r in ('U22002','U22003'):
            if parts.get(r,{}).get('mpn')!='ISO7720FDWR':errors.append('Diagnostic field PG requires actual defaultLOW F isolator '+r)
        for i in range(1,7):
            c=parts.get('H2200'+str(i),{})
            if (c.get('pins')!={} or c.get('footprint')!='MountingHole:MountingHole_3.2mm_M3' or
                c.get('purchased') is not False or c.get('conductive_pad') is not False):
                errors.append('Mounting hole must remain real unelectrical NPTH geometry H2200'+str(i))
    # Actual field path continuity is required, independently of having matching
    # words in a contract. Native source classes cannot silently masquerade as
    # connectors or completed removable cards.
    if 'motherboard_motors' in mapping['blocks']:
        block=mapping['blocks']['motherboard_motors'];new_refs=set(block['references'].values()) & set(parts)
        for signal in ('STEP','DIR','EN'):
            for i in range(12):
                bare=f'{signal}{i}{"_N" if signal=="EN" else ""}_TO_{"MIA" if i<8 else "MX4"}'
                name='/mc_motor_buffers/'+bare
                connected={r for (r,p),n in actual.items() if n==name and r in parts}
                if not connected & new_refs or not any(r.startswith('R5') for r in connected):
                    errors.append('Actual retained buffer-to-field path missing '+name)
    if 'motherboard_control_bridges' in mapping['blocks']:
        # Pin-name agreement can mirror an incorrect design. Check against the
        # retained physical INPUTS, not the similarly named driven clear nets.
        for branch,input_pin,driven_pin in (('R12003',('U4018','1'),('U4019','7')),
                                            ('R12004',('U4018','3'),('U4019','3'))):
            receiving=actual.get((branch,'2'))
            if receiving!=actual.get(input_pin) or receiving==actual.get(driven_pin):
                errors.append('Watchdog clear must drive rearm input, never push-pull output '+branch)
        if actual.get(('R12006','2'))!='/LOGIC_GND':errors.append('Watchdog clear request must default LOW')
    if 'motherboard_io_control' in mapping['blocks']:
        # Verify cross-region physical endpoints without trusting the parent
        # alias dictionary. A consistently renamed but isolated stub is wrong.
        dic_pins=(1,2,3,8,9,11,12,13,14,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33)
        for i,pin in enumerate(dic_pins):
            name=f'/motherboard_di/DI{i}_LOGIC'
            if actual.get(('U13001',str(pin)))!=name:
                errors.append('Actual DI receiver must reach DIC acquisition pin '+str(i))
            receivers=[(r,p) for (r,p),n in actual.items() if n==name and r.startswith('U8') and p in ('4','5')]
            if len(receivers)!=1:errors.append('Exactly one actual isolated DI receiver output required '+str(i))
        for name,mcu,reset_gate,dff,and4,iso in (
            ('DOA','U13004','U13007','U10001','U10002','U10003'),
            ('DOB','U13008','U13011','U10014','U10015','U10016')):
            endpoints=(('7',dff,'1','IO_ENABLE_STROBE'),('8',and4,'10','CARD_EN'),
                       ('9',dff,'5','OUT_EN_LATCH'),('20',and4,'8','DO_EN_LOGIC'),
                       ('15',iso,'7','FLT_N_HOST'))
            for pin,receiver,rpin,suffix in endpoints:
                wanted='/motherboard_do/'+name+'_'+suffix
                if actual.get((mcu,pin))!=wanted or actual.get((receiver,rpin))!=wanted:
                    errors.append('DO control/readback must reach actual frontend '+name+'_'+suffix)
            reset='/motherboard_do/'+name+'_CONTROLLER_RESET_N'
            if actual.get((reset_gate,'4'))!=reset or actual.get((and4,'2'))!=reset:
                errors.append('Buffered actual MCU reset must reach DO permission gate '+name)
            if actual.get((mcu,'10'))!='/mc_permission/OUT_PERMIT':
                errors.append('DO MCU must observe actual hardware output permission '+name)
        for lane,buffer in enumerate(('U13003','U13006','U13010')):
            for suffix,pin in (('CS_N','2'),('SCLK','5'),('MOSI','9')):
                name=f'/fpga_core/IOL1_L{lane}_{suffix}'
                if actual.get((buffer,pin))!=name or not any(r=='U1001' and n==name for (r,p),n in actual.items()):
                    errors.append('IOL1 host input must reach exact FPGA endpoint '+name)
        if any(r in parts for r in ('R13025','R13026','R13043','R13044')):
            errors.append('Duplicate DO frontend-owned control bias reintroduced')
        # DMA byte counts alone cannot detect a partial extra trailing byte.
        # The qualified receiver counts every actual MCU-side SPI clock on
        # PB5/TIM3_CH2. These native endpoints are independent of aliases.
        taps=(('U13001','44','R13057',0,'DIC','motherboard_io_control'),
              ('U13004','29','R13058',1,'DOA','motherboard_io_control'),
              ('U13008','29','R13059',2,'DOB','motherboard_io_control'),
              ('U14501','44','R14533',3,'ACC','motherboard_acc_control'))
        for mcu,pin,resistor,lane,label,block in taps:
            counted=f'/{block}/IOL1_L{lane}_SCLK_COUNT'
            clock=f'/{block}/{label}_IOL1_CLK_MCU'
            if (actual.get((mcu,pin))!=counted or actual.get((resistor,'2'))!=counted
                    or actual.get((resistor,'1'))!=clock
                    or parts.get(resistor,{}).get('mpn')!='CRCW06030000Z0EA'):
                errors.append('Actual IOL1 clock counter must tap post-buffer MCU clock '+str(lane))
    if 'motherboard_operator' in mapping['blocks']:
        for threshold,sense_resistor,sense_pin,in_pin in (
                ('R14069','R14070','16','15'),('R14072','R14073','11','10')):
            sense=actual.get(('U14031',sense_pin));inp=actual.get(('U14031',in_pin))
            if (not sense or not inp or actual.get((threshold,'2'))!=sense or
                    {actual.get((sense_resistor,'1')),actual.get((sense_resistor,'2'))}!={sense,inp}):
                errors.append('Actual probe RTHR must feed SENSE before RSENSE bridges SENSE/IN '+threshold)
        for fpga,pin,frontend in (('G12','4','PROBE_FPGA'),('G15','5','TOOLSETTER_FPGA')):
            if actual.get(('U1001',fpga))!='/fpga_core/'+frontend or actual.get(('U14031',pin))!=actual.get(('U1001',fpga)):
                errors.append('Actual fast probe must reach retained FPGA pin '+fpga)
        for ball,gate,resistor,signal in (('M4','U14015','R14025','FAST_PORTS_ENABLE'),('M6','U14016','R14026','XF_POWER_ENABLE')):
            net='/fpga_core/'+signal
            if any(actual.get(k)!=net for k in (('U1001',ball),(gate,'2'),(resistor,'1'))) or actual.get((resistor,'2'))!='/LOGIC_GND':
                errors.append('Slow enable requires actual FPGA endpoint and independent LOW default '+signal)
    if 'motherboard_power_entry' in mapping['blocks']:
        receipt=json.loads((ROOT/'reports/motherboard-power-entry-20260930/receipt-r02.json').read_text())
        for bank,row in receipt['parent_interposition_rules']['exactly_two_output_pin_changes_permitted'].items():
            source='/motherboard_motors/MOTOR_TX_GATE_SOURCE_'+bank;final='/motherboard_motors/MOTOR_TX_GATE_'+bank
            if actual.get(tuple(row['old_driver']))!=source:errors.append('Motor permission source output must enter independent contacts '+bank)
            for endpoint in row['final_consumers_must_remain_exact']:
                if actual.get(tuple(endpoint))!=final:errors.append('Motor final gate consumer bypasses hardware contacts '+repr(endpoint))
    if 'motherboard_acc_control' in mapping['blocks']:
        # Independent native connectivity, not the integration's alias table.
        # These fitted pin pairs are fixed by the two frozen source receipts.
        pairs=[(('U14504','4'),('U14402','2')),
            (('U14501','11'),('U14401','1')),(('U14501','12'),('U14402','5')),
            (('U14501','13'),('U14401','5')),(('U14501','14'),('U14405','5')),
            (('U14501','21'),('U14402','8')),(('U14501','22'),('U14406','4')),
            (('U14501','23'),('U14419','3'))]
        codes={}
        for net in tree.findall('.//nets/net'):
            for n in net.findall('node'):codes[n.attrib['ref'],n.attrib['pin']]=net.attrib['code']
        for provider,receiver in pairs:
            if provider not in codes or receiver not in codes or codes[provider]!=codes[receiver]:
                errors.append('Actual ACC control/readback must join process frontend '+repr((provider,receiver)))
        if 'motherboard_analog_output' in mapping['blocks']:
            # Fixed receiving pins from the manufacturer-reviewed AO source;
            # an alias dictionary cannot replace the actual SPI/I2C/reset path.
            analog_pairs=[]
            for island,iso,ret,gate,health,i2c in (
                (0,'U14605','U14609','U14604','U14615','U14617'),
                (1,'U14623','U14627','U14622','U14633','U14635')):
                analog_pairs.extend([
                    (('U14501','25'),(iso,'2')),
                    (('U14501','27'),(iso,'3')),
                    (('U14501',str(42+island)),(iso,'4')),
                    (('U14501',str(42+island)),(ret,'1')),
                    (('U14501','26'),(ret,'4')),
                    (('U14501',str(28+island)),(gate,'1')),
                    (('U14501',str(33+island)),(health,'13')),
                    (('U14501','47'),(i2c,'3')),
                    (('U14501','48'),(i2c,'2')),
                    (('U14402','8'),(gate,'2')),
                    (('U14402','3'),(iso,'6'))])
            for provider,receiver in analog_pairs:
                if provider not in codes or receiver not in codes or codes[provider]!=codes[receiver]:
                    errors.append('Actual AO isolated control/readback must reach provider '+repr((provider,receiver)))
        if 'motherboard_analog_input' in mapping['blocks']:
            pairs=[(('U14501','25'),('U14707','2')),(('U14501','27'),('U14707','3')),
                (('U14501','24'),('U14707','4')),(('U14501','24'),('U14709','1')),
                (('U14501','26'),('U14709','4')),(('U14501','32'),('U14739','13')),
                (('U14501','40'),('U14740','4')),(('U14501','47'),('U14710','3')),
                (('U14501','48'),('U14710','2'))]
            for provider,receiver in pairs:
                if provider not in codes or receiver not in codes or codes[provider]!=codes[receiver]:
                    errors.append('Actual AI isolated acquisition/readback must reach ACC provider '+repr((provider,receiver)))
    if 'motherboard_safety_sensor' in mapping['blocks']:
        codes={}
        for net in tree.findall('.//nets/net'):
            for n in net.findall('node'):codes[n.attrib['ref'],n.attrib['pin']]=net.attrib['code']
        pairs=[(('U4002','3'),('U19010','4')),(('U4010','6'),('U19012','4')),
            (('U4009','3'),('U19014','1')),
            (('U1001','G16'),('U19013','6')),(('U1001','N12'),('U19013','4')),
            (('U1001','N13'),('U19002','5')),(('U1001','P9'),('U19002','4')),
            (('U1001','M13'),('U19003','4')),(('U1001','N9'),('U19003','5')),
            (('U1001','L4'),('U19017','4')),
            (('U13001','42'),('U19025','3')),(('U13001','43'),('U19025','2')),
            (('U13001','34'),('U19020','4')),(('U13001','37'),('U19021','4')),
            (('U13001','38'),('U19022','4')),(('U13001','39'),('U19023','4')),
            (('U13001','40'),('U19024','4')),
            (('U11018','5'),('L19001','2')),(('U11018','8'),('L19001','2'))]
        for provider,receiver in pairs:
            if provider not in codes or receiver not in codes or codes[provider]!=codes[receiver]:
                errors.append('Actual safety/sensor endpoint must physically join provider '+repr((provider,receiver)))
        if actual.get(('U11018','5'))==actual.get(('U11017','5')):
            errors.append('Field-B regulator cannot bypass its real5V preregulator or join fieldA')
    if 'motherboard_comms' in mapping['blocks']:
        codes={}
        for net in tree.findall('.//nets/net'):
            for n in net.findall('node'):codes[n.attrib['ref'],n.attrib['pin']]=net.attrib['code']
        pairs=[(('U15002','4'),('U14801','3')),(('U15002','4'),('U14803','2')),
            (('U15002','4'),('U14811','2')),
            (('R15064','2'),('U14812','2')),(('R15067','2'),('U14811','1')),
            (('U15038','2'),('U14812','4')),
            (('R15070','2'),('U14805','2')),(('R15073','2'),('U14805','5')),
            (('R15076','2'),('U14805','9')),(('U15039','2'),('U14806','12')),
            (('U15040','2'),('U14805','11')),
            (('U14501','38'),('U14821','4')),(('U14501','39'),('U14822','4'))]
        for provider,receiver in pairs:
            if provider not in codes or receiver not in codes or codes[provider]!=codes[receiver]:
                errors.append('Actual communications path must join module/acquisition provider '+repr((provider,receiver)))
    if 'motherboard_status' in mapping['blocks']:
        codes={(n.attrib['ref'],n.attrib['pin']):net.attrib['code']
            for net in tree.findall('.//nets/net') for n in net.findall('node')}
        pairs=[(('U4014','3'),('U17013','1')),(('U4015','3'),('U17013','2')),
            (('U2006','2'),('U17013','4')),(('U4007','4'),('U17013','9')),
            (('U1001','D5'),('U17013','10')),(('U11028','4'),('U17013','12')),
            (('U11030','4'),('U17013','13')),
            (('U14501','47'),('U17016','2')),(('U14501','48'),('U17016','3'))]
        pins=('1','3','5','9','11','13')
        for i in range(24):
            pairs.append(((f'U{8001+i//2}',str(4+i%2)),(f'U{17001+2*(i//6)}',pins[i%6])))
        for i,ball in enumerate(('B12','B13','B15','C13','C16','E14','F12','D16','G13','F14','E16','E15')):
            pairs.append((('U1001',ball),(f'U{17009+2*(i//6)}',pins[i%6])))
        for i in range(16):
            pairs.append(((f'J{19522+i//8}',str(1+i%8)),(f'R{17073+2*i}','1')))
        for provider,receiver in pairs:
            if provider not in codes or receiver not in codes or codes[provider]!=codes[receiver]:
                errors.append('Actual status observation must join hardware provider '+repr((provider,receiver)))
        for i in range(16):
            if actual.get((f'R{17073+2*i}','1'))!='/motherboard_do/DO'+str(i).zfill(2):
                errors.append('Output LED must observe actual terminal voltage '+str(i))
    if 'motherboard_identity_io' in mapping['blocks']:
        codes={(n.attrib['ref'],n.attrib['pin']):net.attrib['code']
            for net in tree.findall('.//nets/net') for n in net.findall('node')}
        for provider,receiver in [(('U14501','41'),('U21001','6')),
            (('J19525','7'),('R21003','1')),(('J19525','7'),('D21002','1'))]:
            if provider not in codes or receiver not in codes or codes[provider]!=codes[receiver]:
                errors.append('Actual identity path must join existing frequency/ACC provider '+repr((provider,receiver)))
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--source',type=Path,default=OUT);a=p.parse_args()
    model=json.loads((a.source/'design.json').read_text(encoding='utf-8'))
    mapping=json.loads((a.source/'assembly-map.json').read_text(encoding='utf-8'))
    errors=validate(ET.parse(a.source/'netlist.xml'),model,mapping)
    report={'schema_version':1,'source_checks_pass':not errors,'errors':errors,'physical_parts':len(model['components']),
            'retained_mc_parts':327,'retained_mc_fitted_pin_nets':len(mapping['retained_native_pin_nets']),
            'manufacturing_ready':False,'native_erc_run_by_this_validator':False,'pcb_drc_run_by_this_validator':False,
            'physical_qualification':False,'scope':'Native fitted pin/value/MPN/footprint and exact retained-net validation; not electrical/physical qualification'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report));raise SystemExit(bool(errors))


if __name__=='__main__':main()
