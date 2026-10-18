"""Independent model/native-netlist audit of the bounded IO3 correction."""
from __future__ import annotations
import copy,json,xml.etree.ElementTree as ET
from pathlib import Path
from hardware_build_assembly import parse,child,children,value
from hardware_apply_motherboard_io3_upgrade import ROOT,OUT,REPORT,ENDS,LOCAL,RREF,RMPN,RFP,PIN_NAMES,TOPREF,FB_TOP_MPN,FB_BOTTOM_MPN

def native_nodes(path):
    nodes={}
    for net in ET.parse(path).findall('.//nets/net'):
        for node in net.findall('node'):
            key=(node.attrib['ref'],node.attrib['pin'])
            if key in nodes:raise ValueError('Duplicate native pin '+str(key))
            nodes[key]=net.attrib['name'].lstrip('/')
    return nodes

def validate(model,native=None,baseline=None):
    errors=[];parts=model['components']
    if parts.get('U2002',{}).get('mpn')!='TPS62902RPJR':errors.append('Exact2A orderable regulator absent')
    if parts.get('U2002',{}).get('footprint')!='CNC_MC_Power:TPS62901_RPJ9':errors.append('Unreviewed RPJ9 footprint substitution')
    for ref,pin in ENDS:
        if parts.get(ref,{}).get('pins',{}).get(pin)!=LOCAL:errors.append('Local VOS/reservoir endpoint mismatch '+ref+'.'+pin)
    resistor=parts.get(RREF,{})
    if resistor.get('mpn')!=RMPN or resistor.get('footprint')!=RFP:errors.append('Exact damping MPN/land mismatch')
    if resistor.get('pins')!={'1':LOCAL,'2':'IO_3V3'}:errors.append('Damping feed endpoints reversed/bypassed')
    if resistor.get('resistance_ohm')!=.015:errors.append('Damping nominal is not15mohm')
    if resistor.get('tolerance')!=.01 or resistor.get('temperature_coefficient_ppm_k')!=50:errors.append('Damping corner metadata mismatch')
    top=parts.get(TOPREF,{})
    if top.get('mpn')!=FB_TOP_MPN or top.get('resistance_ohm')!=11500 or top.get('pins')!={'1':LOCAL,'2':'IO_3V3_VSET'}:
        errors.append('Exact low-impedance external-FB top missing')
    if parts.get('R2008',{}).get('mpn')!=FB_BOTTOM_MPN or parts.get('R2008',{}).get('resistance_ohm')!=2550:
        errors.append('Exact low-impedance external-FB bottom missing')
    if parts.get('R2005',{}).get('pins')!={'1':'IO_3V3_MODE','2':'CORE_5V'} or parts.get('R2005',{}).get('mpn')!='CRCW06030000Z0EA':
        errors.append('MODE is not directly HIGH with VIN through fitted0ohm')
    if baseline:
        for ref,old in baseline['components'].items():
            if ref not in parts:errors.append('Retained part removed '+ref);continue
            expected=copy.deepcopy(old)
            for r,p in ENDS:
                if ref==r:expected['pins'][p]=LOCAL
            if ref=='U2002':
                expected.update(value='TPS62902RPJR',mpn='TPS62902RPJR',inherited_mpn='TPS62901RPJR',component_substitution='MB-IO3-001',io3_source_current_allocation_a=2)
            if ref=='R2005':
                expected['pins']['2']='CORE_5V';expected.update(value='0ohm MODE tied VIN',mpn='CRCW06030000Z0EA',inherited_mpn='CRCW060332K4FKEA',resistance_ohm=0,component_substitution='MB-IO3-001')
            if ref=='R2008':
                expected.update(value='2.55k 0.1% 10ppm',mpn=FB_BOTTOM_MPN,inherited_mpn='CRCW0603301KFKEA',resistance_ohm=2550,tolerance=.001,temperature_coefficient_ppm_k=10,component_substitution='MB-IO3-001')
            if parts[ref]!=expected:errors.append('Unbounded retained mutation '+ref)
    if native is not None:
        for ref,c in parts.items():
            for pin,net in c['pins'].items():
                if native.get((ref,pin))!=net:errors.append('Independent native/model pin mismatch '+ref+'.'+pin)
    # Exact full-temperature reference limit, resistor initial/TCR/drift screen,
    # and full magnitude of FB leakage. Do not use a typical1nA input current.
    rmax=.015*1.01*(1+150*50e-6)
    eps=.001+60*10e-6+.0005
    rtmax=11500*(1+eps);rtmin=11500*(1-eps)
    rbmax=2550*(1+eps);rbmin=2550*(1-eps)
    fb_error=70e-9*rtmax
    local_min=.6*.991*(1+rtmin/rbmax)-fb_error
    local_max=.6*1.009*(1+rtmax/rbmin)+fb_error
    vmin=local_min-.9087077446234255*rmax
    screening={'rmin_ohm':.015*.99*(1-150*50e-6),'rmax_ohm':rmax,
        'nominal_local_v':.6*(1+11500/2550),'fb_error_max_v':fb_error,
        'resistor_error_fraction_including_tcr_drift':eps,
        'local_min_v':local_min,'local_max_v':local_max,
        'downstream_min_v_before_extra_copper_noise':vmin,
        'receiving_health_uv_max_v':3.247426050232732,
        'receiving_health_ov_min_v':3.3515478280344664,
        'available_distribution_noise_budget_v':vmin-3.247426050232732,
        'upper_arming_margin_v':3.3515478280344664-local_max,
        'divider_current_nominal_a':(.6*(1+11500/2550))/(11500+2550)}
    if screening['available_distribution_noise_budget_v']<=0 or screening['upper_arming_margin_v']<=0:
        errors.append('External FB/damping conditional corner does not fit receiving-health arming')
    return {'consistency_pass':not errors,'errors':errors,'screening':screening,
        'manufacturing_ready':False,'physical_qualification':False}

def run():
    model=json.loads((OUT/'design.json').read_text())
    result=validate(model,native_nodes(OUT/'netlist.xml'))
    erc=json.loads((REPORT/'erc.json').read_text())
    v=[x for s in erc['sheets'] for x in s['violations']]
    result.update(erc_errors=sum(x['severity']=='error' for x in v),
        erc_warnings=sum(x['severity']=='warning' for x in v),erc_ignored_checks=erc.get('ignored_checks',[]))
    (REPORT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return result

if __name__=='__main__':print(json.dumps(run(),indent=2))
