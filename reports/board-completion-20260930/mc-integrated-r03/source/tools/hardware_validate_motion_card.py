"""Check native MC integration against retained source netlists and boundaries."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motion_card'


def nodes(tree):
    result={}
    for net in tree.findall('.//nets/net'):
        for n in net.findall('node'):
            k=(n.attrib['ref'],n.attrib['pin'])
            if k in result:raise ValueError('Duplicate native pin '+repr(k))
            result[k]=net.attrib['name']
    return result


def validate(tree,model,mapping,check_hashes=True):
    errors=[]; actual=nodes(tree); parts=model['components']; interfaces=set(mapping['interface_nets'])
    if model.get('manufacturing_ready') or model.get('physical_qualification') or model.get('interface_agreed'):
        errors.append('Unqualified candidate cannot assert release/agreement/measurement')
    expected={}
    for name,block in mapping['blocks'].items():
        source_path=next(p for p in mapping['input_sha256'] if p.endswith('/netlist.xml') and
            ('hardware/fpga_core/' in p if name=='fpga_core' else 'startup_conditioning_r0_2' in p if name=='watchdog_conditioning' else '/'+name+'/' in p))
        for (old,pin),net in nodes(ET.parse(ROOT/source_path)).items():
            ref=block['references'].get(old)
            if ref not in parts:continue
            bare=net.lstrip('/');bare=mapping['aliases'].get(name,{}).get(bare,bare)
            if bare.startswith('unconnected-'):
                expected[ref,pin]=None
            else:expected[ref,pin]=('/'+bare if bare in interfaces else '/'+name+'/'+bare)
    for key,net in expected.items():
        got=actual.get(key)
        if net is None:
            if got is None or not got.lstrip('/').startswith('unconnected-'):errors.append('Native NC changed: '+repr(key))
        elif got!=net:errors.append('Native source pin/net mismatch '+repr(key)+' expected '+net+' got '+str(got))
    extra={k for k in actual if k[0] in parts}-set(expected)
    if extra:errors.append('Unexpected fitted native pins '+repr(sorted(extra)))
    refs=[x.attrib['ref'] for x in tree.findall('.//comp') if x.attrib['ref'] in parts]
    if len(refs)!=len(set(refs)) or set(refs)!=set(parts):errors.append('Physical component inventory differs')
    for comp in tree.findall('.//comp'):
        ref=comp.attrib['ref']
        if ref not in parts:continue
        if (comp.findtext('footprint') or '')!=parts[ref].get('footprint',''):errors.append('Footprint/source mismatch '+ref)
        if (comp.findtext('value') or '')!=parts[ref].get('value',''):errors.append('Value/source mismatch '+ref)
        mpn=comp.find("./fields/field[@name='MPN']")
        if (mpn.text if mpn is not None else '')!=parts[ref].get('mpn',''):errors.append('MPN/source mismatch '+ref)
    replaced=[c for c in parts.values() if c.get('component_substitution')]
    if len(replaced)!=41 or any(c.get('mpn')!='GRM188R72A104KA35D' or c.get('inherited_mpn')!='GRM188R71E104KA01D' for c in replaced):
        errors.append('Active decoupling part substitution is incomplete or changed')
    if check_hashes:
        for path,h in mapping['input_sha256'].items():
            p=ROOT/path
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append('Stale source hash '+path)
    # Separately reviewed voltage/isolation constraints, not generator equality.
    if actual.get(('U4001','1'))!='/FPGA_CRESET_N':errors.append('Permission rail qualifier must be destination3V3')
    if actual.get(('U2006','4'))!='/FPGA_CRESET_N':errors.append('Destination reset buffer output missing')
    if actual.get(('U1001','A2'))!='/RAW_INHIBIT_N' or actual.get(('U4003','7'))!='/RAW_INHIBIT_N':
        errors.append('Independent raw inhibit must reach FPGA A2')
    raw=[k for k,v in actual.items() if v=='/mc_local_power/MC_RAILS_OK_5V']
    if set(raw)!={('B2001','6'),('R2106','2'),('R2107','1'),('U2005','12'),('U2006','2')}:
        errors.append('Raw5V rail qualifier crosses unsafe boundary')
    for domain,timer,gate,tripor,pin in [('M','U3001','U3006','U4017','2'),('O','U3002','U3007','U4017','6')]:
        n='/WD_'+domain+'_SET1_BUF'
        if not all(actual.get(k)==n for k in [(timer,'5'),(gate,'4'),(tripor,pin)]):errors.append('Trip must sample actual SET1 '+domain)
    motors=json.loads((ROOT/'hardware/mc_motor_buffers/design.json').read_text(encoding='utf-8'))
    motor_refs=mapping['blocks']['mc_motor_buffers']['references']
    core=json.loads((ROOT/'hardware/fpga_core/design.json').read_text(encoding='utf-8'))
    motor_paths=[]
    for path in motors['paths']:
        buffer=motor_refs[path['buffer_ref']]; series=motor_refs[path['series_ref']]
        input_net='/'+path['input']
        raw_net='/mc_motor_buffers/'+path['raw']; output_net='/mc_motor_buffers/'+path['output']
        if actual.get((buffer,path['input_pin']))!=input_net:
            errors.append('Motor buffer input boundary mismatch '+path['input'])
        if actual.get((buffer,path['output_pin']))!=raw_net or actual.get((series,'1'))!=raw_net or actual.get((series,'2'))!=output_net:
            errors.append('Motor buffer/series physical path broken '+path['output'])
        balls=[p for (r,p),n in actual.items() if r=='U1001' and n==input_net]
        if path['channel'] is not None:
            old=(f'DRIVE_ENABLE{path["channel"]}_FPGA_RESERVED' if path['signal']=='EN_N' else path['input'])
            expected_balls=[p for p,n in core['components']['U1']['pins'].items() if n==old]
            if len(balls)!=1 or balls!=expected_balls:errors.append('Motor FPGA ball allocation changed '+path['input'])
        motor_paths.append({'input':path['input'],'output':path['output'],'buffer':buffer,'series':series,
                            'fpga_balls':balls,'bank':path['bank'],'vendor_fit':False,'receiver_qualified':False})
    expected_oe={(f'U{5000+i}',p) for i in range(5,11) for p in ('1','7')}|{('U5011','1')}
    if not all(actual.get(k)=='/BANK_B_BUFFER_ENABLE_QUALIFIED' for k in expected_oe|{('U4013','6'),('R4014','1')}):
        errors.append('Bank-B physical OE and OPI_BOE clear must be the same net')
    if actual.get(('U5011','7'))!='/LOGIC_GND':errors.append('Unused Bank-B buffer OE must stay low')
    if len(motor_paths)!=38:errors.append('Twelve motor channels and two TX paths are required')
    for i in range(1,12):
        want='SN74LVC244APWR' if i<=4 else 'SN74LVC2G126DCUR'
        if parts.get(f'U{5000+i}',{}).get('mpn')!=want:errors.append('Ioff buffer part changed without qualification')
    control=[]
    permission=json.loads((ROOT/'hardware/mc_permission/design.json').read_text(encoding='utf-8'))
    for name in permission['boundary_inputs']+permission['boundary_outputs']+['FPGA_PROGRESS_M','FPGA_PROGRESS_O']:
        physical_net=mapping['aliases'].get('mc_permission',{}).get(name,name)
        candidates={v for (r,p),v in actual.items() if r.startswith(('U3','U4')) and v.split('/')[-1]==physical_net}
        if physical_net in {'IO_3V3','LOGIC_GND'}:continue
        fpga_pins=[p for (r,p),v in actual.items() if r=='U1001' and v in candidates]
        control.append({'name':name,'net':physical_net,'fpga_balls':fpga_pins,
                        'implemented_fpga_endpoint':bool(fpga_pins),
                        'note':'Boundary qualification/runtime still required' if fpga_pins else 'External term or unallocated GPIO; not a completed card'})
    return errors,{'physical_components':len(parts),'fitted_source_pins_checked':len(expected),
        'component_groups':dict(Counter(c['source_block'] for c in parts.values())),
        'shared_nets':sorted(interfaces),'control_endpoint_coverage':control,
        'motor_physical_paths':motor_paths,'bank_B_used_OE_pins':len(expected_oe),
        'manufacturing_ready':False,'physical_measurement':False,'fpga_fit':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=OUT/'validation.json');args=p.parse_args()
    errors,evidence=validate(ET.parse(OUT/'netlist.xml'),json.loads((OUT/'design.json').read_text()),json.loads((OUT/'assembly-map.json').read_text()))
    result={'pass':not errors,'errors':errors,'evidence':evidence}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pass':not errors,'errors':errors,'physical_components':evidence['physical_components'],'source_pins_checked':evidence['fitted_source_pins_checked']}))
    raise SystemExit(bool(errors))


if __name__=='__main__':main()
