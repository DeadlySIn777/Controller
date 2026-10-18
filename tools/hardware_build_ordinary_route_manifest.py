"""Review an exact, conservative ordinary-logic subset of the adopted source.

This is a routing allowlist, not a name-based electrical classifier. Every
selected endpoint is reconciled to the native XML and its actual part, pin,
return and producer. Unselected nets remain excluded. Binding to a particular
board/plane receipt is a later operation; source review does not qualify planes.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CLASSES={'isolated_general_input_state','isolated_motor_alarm_state',
         'digital_fault_observation','permission_control','strapped_configuration',
         'status_logic'}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,o):Path(p).write_text(json.dumps(o,indent=2)+'\n',encoding='utf8')


def exact_review():
    # Each entry is a specifically reviewed source function, not a wildcard
    # acceptance rule. Clock/data buses and terminal-side inputs are absent.
    rows={}
    def add(name,kind,driver=None,voltage=3.6):
        rows[name]=dict(signal_class=kind,driver=driver,maximum_voltage_v=voltage)
    for i in range(24):
        add('/motherboard_di/DI%d_LOGIC'%i,'isolated_general_input_state',
            ('U%d'%(8001+i//2),'4'if i%2==0 else'5'))
    for i in range(12):
        add('/fpga_core/ALM%d_FPGA'%i,'isolated_motor_alarm_state',
            ('U%d'%(6035+i//2),'4'if i%2==0 else'5'))
    for n,p in [('FPGA_LINK_FAULT','A3'),('FPGA_WATCHDOG_FAULT','C6'),
                ('FPGA_INHIBIT_FAULT','A4'),('FPGA_TIMING_FAULT','E5')]:
        add('/fpga_core/'+n,'digital_fault_observation',('U1001',p))
    for region in ('DIC','DOA','DOB'):
        for i in range(4):
            add('/motherboard_io_control/%s_SLOT%d'%(region,i),'strapped_configuration')
    for i in range(4):add('/motherboard_acc_control/ACC_SLOT%d'%i,'strapped_configuration')
    for i in range(3):
        add('/motherboard_io_control/DI_SENSOR_G%d_FAULT'%i,'digital_fault_observation',('U%d'%(19020+i),'4'))
    for n,u in [('DI_SAFETY_SUPPLY_FAULT','U19023'),('DI_SAFETY_SECONDARY_FAULT','U19024')]:
        add('/motherboard_io_control/'+n,'digital_fault_observation',(u,'4'))
    for n,u in [('DOA_FIELD_POWER_GOOD','U22002'),('DOB_FIELD_POWER_GOOD','U22003')]:
        add('/motherboard_io_control/'+n,'digital_fault_observation',(u,'13'))
    for n,p in [('WD_M_OK','6'),('WD_O_OK','4')]:add('/'+n,'digital_fault_observation',('U3005',p))
    for n,u in [('WD_M_TRIP_N','U4014'),('WD_O_TRIP_N','U4015')]:
        add('/mc_permission/'+n,'digital_fault_observation',(u,'3'))
    for n,u,p in [('OUT_PERMIT','U4008','4'),('PROC_PERMIT','U4010','4'),
                  ('PERMIT_OUT_DRIVE','U4009','3')]:
        add('/mc_permission/'+n,'permission_control',(u,p))
    add('/TX_PERMIT','permission_control',('U4007','4'))
    # Source-qualified 5 V AHCT status outputs are deliberately separate from
    # 3.3 V input observations. This does not raise any receiver rail rating.
    for n,u,p in [('STATUS_HW_GOOD','U17013','6'),('STATUS_NO_WDT_TRIP','U17013','3'),
                  ('STATUS_MOTION_FEEDS_GOOD','U17013','11'),
                  ('STATUS_MOTION_REQUEST_GOOD','U17013','8'),
                  ('STATUS_MOTION_RGB_ENABLE','U17014','3')]:
        add('/motherboard_status/'+n,'status_logic',(u,p),5.5)
    return rows


def native(model,xml):
    root=ET.parse(xml).getroot();physical=model['components']
    parts={c.attrib['ref']:c for c in root.findall('.//components/comp')if c.attrib['ref']in physical}
    if set(parts)!=set(physical):raise ValueError('Native/full physical component inventory differs')
    libs={(l.attrib['lib'],l.attrib['part']):{p.attrib['num']:dict(p.attrib)for p in l.findall('./pins/pin')}
          for l in root.findall('.//libparts/libpart')}
    functions={ref:libs[c.find('libsource').attrib['lib'],c.find('libsource').attrib['part']]
               for ref,c in parts.items()}
    nodes={};nets={}
    for n in root.findall('.//nets/net'):
        name=n.attrib['name'];endpoints=[]
        for p in n.findall('node'):
            key=p.attrib['ref'],p.attrib['pin']
            if key[0]not in physical:continue
            if key in nodes:raise ValueError('Duplicate native endpoint')
            nodes[key]=name;endpoints.append(key)
        if endpoints:nets[name]=sorted(endpoints)
    return nodes,nets,functions


def review(source,adoption):
    source=Path(source).resolve();model=load(source/'design.json');accepted=load(adoption)
    hashes=accepted.get('hashes')or accepted['source_hashes']
    for p,expected in hashes.items():
        if str(Path(p).resolve()).startswith(str(source)) and sha(p)!=expected:
            raise ValueError('Adopted source has changed: '+p)
    nodes,nets,functions=native(model,source/'netlist.xml');rows={}
    for name,definition in exact_review().items():
        if name not in nets or len(nets[name])<2:raise ValueError('Reviewed function absent: '+name)
        endpoints=[];driver=definition['driver']
        if driver and (tuple(driver)not in nets[name]or functions[driver[0]][driver[1]]['type']not in
                       ('output','open_collector','bidirectional')):
            raise ValueError('Exact reviewed producer differs: '+name)
        for ref,pin in nets[name]:
            component=model['components'][ref];f=functions[ref][pin]
            if f['type']in ('power_in','power_out')or ref.startswith(('C','D','L','F')):
                raise ValueError('Precision/power/terminal protection endpoint is excluded: '+name+' '+ref)
            ret=[];supply=[]
            for p,pf in functions[ref].items():
                actual=nodes.get((ref,p))
                if pf['type']=='power_in'and actual=='/LOGIC_GND':ret.append(p)
                elif pf['type']=='power_in'and actual in ('/IO_3V3','/mc_local_power/CORE_5V'):
                    supply.append(dict(pin=p,net=actual))
            if ref.startswith('U')and not ret:
                raise ValueError('Active endpoint lacks an actual own-domain return: '+name+' '+ref)
            endpoints.append(dict(reference=ref,pin=pin,mpn=component.get('mpn'),
                function=f['name'],electrical_type=f['type'],source_block=component.get('source_block','retained_mc'),
                actual_logic_return_pins=sorted(ret),actual_logic_supply_pins=supply,
                model_pin_net=component['pins'].get(pin)))
        if driver and driver[0]!='U1001':
            supplies=[s['net']for e in endpoints if(e['reference'],e['pin'])==tuple(driver)for s in e['actual_logic_supply_pins']]
            rail='/mc_local_power/CORE_5V'if definition['maximum_voltage_v']==5.5 else'/IO_3V3'
            if rail not in supplies:raise ValueError('Producer actual supply differs from voltage class: '+name)
        rows[name]=dict(type='ordinary_logic',controlled_impedance=False,
            signal_class=definition['signal_class'],maximum_voltage_v=definition['maximum_voltage_v'],
            return_domain='LOGIC',return_net='/LOGIC_GND',
            layers=['F.Cu','In2.Cu','In3.Cu','B.Cu'],
            reference_layers={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu','B.Cu':'In4.Cu'},
            width_mm=.20,clearance_mm=.15,reference_corridor_margin_mm=.10,
            allow_vias=True,via_diameter_mm=.60,via_drill_mm=.30,return_stitch_distance_mm=1.0,
            source_pins=[list(k)for k in nets[name]],source_endpoints=endpoints,
            declared_producer=list(driver)if driver else None,
            review_basis='Exact native source function/pin/MPN/producer/return; no bus or analog routing',
            loaded_timing_and_physical_SI_qualified=False)
    excluded=[dict(net=n,physical_endpoints=len(p),reason='not in exact reviewed ordinary-logic allowlist')
              for n,p in sorted(nets.items())if n not in rows]
    return dict(schema_version=2,electrical_review='source-r24 exact ordinary-logic functions',
        source_review_sha256={str(source/'design.json'):sha(source/'design.json'),
                              str(source/'netlist.xml'):sha(source/'netlist.xml'),
                              str(Path(adoption).resolve()):sha(adoption)},
        source_physical_footprints=len(model['components']),nets=rows,excluded_nets=excluded,
        denied_categories=['all power/returns','high speed','STEP/DIR','encoders','frequency/probes',
                           'PWM/process timing','SPI/IOL1 and other serial data/clock','analog/reference/filter/timing'],
        routing_run=False,plane_geometry_qualified=False,board_binding_required=True,
        manufacturing_ready=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=ROOT/'hardware/motherboard')
    ap.add_argument('--adoption',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve()
    if out.exists()or not out.is_relative_to(ROOT/'reports'):raise ValueError('Use a new report directory')
    out.mkdir(parents=True);r=review(a.source,a.adoption);write(out/'ordinary-source-review.json',r)
    write(out/'receipt.json',dict(tool_sha256=sha(__file__),source_review_sha256=sha(out/'ordinary-source-review.json'),
          exact_ordinary_nets=len(r['nets']),excluded_nets=len(r['excluded_nets']),routing_run=False))
    print(json.dumps(dict(exact_ordinary_nets=len(r['nets']),excluded_nets=len(r['excluded_nets']))))


if __name__=='__main__':main()
