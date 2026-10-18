"""Source/native validation and ideal-digital permission-core fault exercise.

The state model follows the actual component pin nets. It is host simulation,
not HDL, analogue timing, FPGA fit or physical safety qualification.
"""
import argparse
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/mc_permission'
# TI primary pin tables, reviewed separately from the schematic generator.
EXPECTED={
 'LVC1G11':{'1':'A','2':'GND','3':'B','4':'Y','5':'VCC','6':'C'},
 'LVC2G08':{'1':'1A','2':'1B','3':'2Y','4':'GND','5':'2A','6':'2B','7':'1Y','8':'VCC'},
 'LVC2G74':{'1':'CLK','2':'D','3':'Q_N','4':'GND','5':'Q','6':'CLR_N','7':'PRE_N','8':'VCC'}}
PARTS={'LVC1G11':('SN74LVC1G11DBVR','Package_TO_SOT_SMD:SOT-23-6'),
       'LVC2G08':('SN74LVC2G08DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
       'LVC2G74':('SN74LVC2G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm')}


class Circuit:
    def __init__(self, design):
        self.parts=design['components'];self.values={'IO_3V3':1,'LOGIC_GND':0}
        self.values.update({name:0 for name in design['boundary_inputs'] if name not in self.values})
        self.q={r:0 for r,c in self.parts.items() if c['kind']=='LVC2G74'}
        self.last_clock={r:0 for r in self.q}
        self._settle()

    def _settle(self):
        for _ in range(40):
            before=(dict(self.values),dict(self.q))
            for ref,part in self.parts.items():
                p=part['pins']; get=lambda n:self.values.get(p.get(str(n)),0)
                if part['kind']=='LVC1G11':self.values[p['4']]=get(1)&get(3)&get(6)
                elif part['kind']=='LVC2G08':
                    self.values[p['7']]=get(1)&get(2);self.values[p['3']]=get(5)&get(6)
                elif part['kind']=='LVC2G74':
                    if not get(7):raise ValueError('PRE_N must remain inactive HIGH')
                    if not get(6):self.q[ref]=0
                    self.values[p['5']]=self.q[ref]
                    if p.get('3'):self.values[p['3']]=1-self.q[ref]
            if before==(self.values,self.q):return
        raise ValueError('Combinational permission loop or unsettled source graph')

    def drive(self, **changes):
        self.values.update(changes);self._settle()
        for ref in self.q:
            p=self.parts[ref]['pins'];clock=self.values.get(p['1'],0)
            if not self.last_clock[ref] and clock and self.values.get(p['6'],0):
                self.q[ref]=self.values.get(p['2'],0)
            self.last_clock[ref]=clock
        self._settle();return dict(self.values)


def exercise(design):
    checks=0; errors=[]
    def check(test,message):
        nonlocal checks
        checks+=1
        if not test:errors.append(message)
    # Expected equations come directly from IS-1, not builder gate positions.
    names=('MC_RAILS_OK','CDONE_QUALIFIED','DIC_OK_QUALIFIED','EXT_PERMIT_3V3','TAMPER_CLEAR_N',
           'WD_M_OK','WD_O_OK','FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','FPGA_OUTPUT_REQUEST',
           'PROCESS_PERMIT_EXT_3V3','PERMIT_OUT_REQ')
    for bits in itertools.product((0,1),repeat=len(names)):
        v=dict(zip(names,bits)); circuit=Circuit(design)
        # Q=1 isolates the complete combinational permission equations. Clears
        # then force Q=0 for unhealthy paths, just as the real flip-flops do.
        circuit.q.update({'U5':1,'U6':1});circuit.values.update(v);circuit._settle()
        base=all(v[n] for n in names[:5]);raw=int(base and v['WD_M_OK'])
        tx=int(raw and v['FPGA_ENDPOINT_READY'] and v['FPGA_MOTION_REQUEST'])
        out=int(base and v['WD_O_OK'] and v['FPGA_ENDPOINT_READY'] and v['FPGA_OUTPUT_REQUEST'])
        expected={'RAW_INHIBIT_N':raw,'TX_PERMIT':tx,'OUT_PERMIT':out,
                  'PROC_PERMIT':int(tx and out and v['PROCESS_PERMIT_EXT_3V3']),
                  'PERMIT_OUT_DRIVE':int(tx and v['PERMIT_OUT_REQ'])}
        check(all(circuit.values.get(n)==x for n,x in expected.items()),'IS-1 equation mismatch at '+repr(v))
        if errors:break
    healthy={n:1 for n in names if n not in ('FPGA_MOTION_REQUEST','FPGA_OUTPUT_REQUEST','PERMIT_OUT_REQ')}
    for fault in names[:8]:
        c=Circuit(design);c.drive(**healthy)
        check(c.values['TX_PERMIT']==c.values['OUT_PERMIT']==0,'No request edge must remain disarmed')
        c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1,PERMIT_OUT_REQ=1)
        check(c.values['TX_PERMIT']==c.values['OUT_PERMIT']==1,'Healthy request edges must arm')
        c.drive(**{fault:0})
        if fault=='WD_M_OK':expected=(0,1)
        elif fault=='WD_O_OK':expected=(1,0)
        else:expected=(0,0)
        check((c.values['TX_PERMIT'],c.values['OUT_PERMIT'])==expected,'Fault does not clear expected path: '+fault)
        c.drive(**{fault:1})
        check((c.values['TX_PERMIT'],c.values['OUT_PERMIT'])==expected,'Recovery automatically restarted path: '+fault)
        c.drive(FPGA_MOTION_REQUEST=0,FPGA_OUTPUT_REQUEST=0)
        c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1)
        check(c.values['TX_PERMIT']==c.values['OUT_PERMIT']==1,'Deliberate new request failed to rearm: '+fault)
    c=Circuit(design);c.drive(**healthy);c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1)
    c.drive(OPI_REARM_TX=1,OPI_REARM_OUT=1)
    check(c.values['OPI_OK_TX']==c.values['OPI_OK_OUT']==1,'Deliberate OPI rearm failed')
    c.drive(FPGA_MOTION_REQUEST=0,FPGA_OUTPUT_REQUEST=0);c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1)
    check(c.values['OPI_OK_TX']==c.values['OPI_OK_OUT']==0,'Accepted gate interruption was not sticky')
    c.drive(OPI_REARM_TX=0,OPI_REARM_OUT=0);c.drive(OPI_REARM_TX=1,OPI_REARM_OUT=1)
    check(c.values['OPI_OK_TX']==c.values['OPI_OK_OUT']==1,'New OPI strobe failed')
    c.drive(BANK_B_BUFFER_ENABLE_QUALIFIED=1,OPI_REARM_BOE=1)
    check(c.values['OPI_OK_BOE']==1,'Bank-B OPI rearm failed')
    c.drive(BANK_B_BUFFER_ENABLE_QUALIFIED=0);c.drive(BANK_B_BUFFER_ENABLE_QUALIFIED=1)
    check(c.values['OPI_OK_BOE']==0,'Bank-B gate recovery erased interruption')
    for domain in ('M','O'):
        c.drive(**{'WD_REARM_'+domain:1});check(c.values['WD_'+domain+'_TRIP_N']==1,'Watchdog trip rearm failed')
        c.drive(**{'WD_'+domain+'_OK':0});c.drive(**{'WD_'+domain+'_OK':1})
        check(c.values['WD_'+domain+'_TRIP_N']==0,'Watchdog trip not sticky')
    return checks,errors


def validate(design=None, directory=OUT, native=True):
    d=deepcopy(design) if design is not None else json.loads((directory/'design.json').read_text())
    errors=[];parts=d.get('components',{})
    if d.get('manufacturing_ready') is not False:errors.append('Manufacturing-ready claim is forbidden')
    if d.get('operating_supply_v')!=[3.14,3.465]:errors.append('Changed electrical domain')
    for path,digest in d.get('sources',{}).items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:errors.append('Primary source changed: '+path)
    for ref,c in parts.items():
        if c['kind'] in PARTS:
            if (c['mpn'],c['footprint'])!=PARTS[c['kind']]:errors.append('Package/MPN mismatch: '+ref)
            if set(c['pins'])!=set(EXPECTED[c['kind']]):errors.append('Physical pin set mismatch: '+ref)
            ground,supply=(('2','5') if c['kind']=='LVC1G11' else ('4','8'))
            if c['pins'].get(ground)!='LOGIC_GND' or c['pins'].get(supply)!='IO_3V3':errors.append('Power pin mismatch: '+ref)
            if c['kind']=='LVC2G74' and (c['pins'].get('2')!='IO_3V3' or c['pins'].get('7')!='IO_3V3' or c['pins'].get('3') is not None):errors.append('Unsafe D/PRE or NC latch mapping: '+ref)
        if c.get('physical') and (not c.get('mpn') or not c.get('footprint')):errors.append('Incomplete fitted part: '+ref)
    if native:
        xml=ET.parse(directory/'netlist.xml').getroot();actual={}
        for n in xml.findall('./nets/net'):
            for p in n.findall('node'):
                ref,pin=p.attrib['ref'],p.attrib['pin'];name=n.attrib['name'].lstrip('/')
                if name.startswith('unconnected-') and parts.get(ref,{}).get('pins',{}).get(pin,'UNKNOWN') is None:
                    continue
                actual[(ref,pin)]=name
        expected={(r,p):n for r,c in parts.items() for p,n in c['pins'].items() if n is not None}
        if actual!=expected:errors.append('Native netlist does not match declared component pins')
        for c in xml.findall('./components/comp'):
            ref=c.attrib['ref'];kind=parts.get(ref,{}).get('kind')
            if kind not in EXPECTED:continue
            # The functions attached to actual exported package pins must agree
            # with the independently read primary table, not just with nets.
            lib=c.find('libsource');libpart=next((p for p in xml.findall('./libparts/libpart')
                                               if p.attrib['part']==lib.attrib['part']),None)
            actual_functions={p.attrib['num']:p.attrib['name'] for p in libpart.findall('./pins/pin')}
            if actual_functions!=EXPECTED[kind]:errors.append('Exported physical functions mismatch: '+ref)
        erc=json.loads((directory/'erc.json').read_text());violations=[v for s in erc.get('sheets',[]) for v in s.get('violations',[])]
        if violations:errors.append('Native ERC has '+str(len(violations))+' violations')
    checks=0
    if not errors:
        checks,new=exercise(d);errors.extend(new)
    return {'passed':not errors,'errors':errors,'host_ideal_digital_checks':checks,
            'physical_parts':sum(c.get('physical',False) for c in parts.values()),
            'evidence_class':'source + native netlist/ERC + host ideal-digital component-net simulation',
            'physical_measurement':False,'manufacturing_ready':False,'open_gates':d.get('open_gates',[])}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=validate()
    if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
