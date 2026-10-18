"""Bounded parent-only graphical NC dispositions on actual functional pins.

The immutable source22 review identifies exactly twenty unused functional
lands. Manufacturer names/types and package geometry are preserved. No
child source, retained copper, power protection or field capability is removed.
"""
import copy, hashlib, json, uuid
from pathlib import Path
from hardware_build_assembly import child, children, value, q, point, ref_property
from hardware_apply_motherboard_io3_upgrade import symbol_for, coords

ROOT=Path(__file__).resolve().parents[1]
PROPOSAL=ROOT/'reports/motherboard-diagnostics-20260930/r01/bounded-NC-proposals.json'
NS=uuid.UUID('087155a3-c3d3-5658-b46e-4d32d3b2c595')

def reviewed():
    if hashlib.sha256(PROPOSAL.read_bytes()).hexdigest()!='f0f373546595840851fd4776cff5b48e9534ae8c0fb3655ef751cb7025dd035f':
        raise ValueError('Immutable twenty-endpoint source22 review changed')
    data=json.loads(PROPOSAL.read_text(encoding='utf8'))
    rows=data['native_physical_NC_proposals']
    expected={('U1001',p) for p in ('H13','G14','H14','H15','H16','J15','K14')}|{
        ('J15002',p) for p in ('2','9','10','12','16','18','22','24')}|{
        ('U2001','1'),('U2002','1'),('U11002','14'),('U11004','14'),('U11006','14')}
    if len(rows)!=20 or {(r['ref'],r['pin']) for r in rows}!=expected:
        raise ValueError('Exact twenty functional NC proposal inventory required')
    return rows

def apply_unused_endpoints(tree,model,scope):
    t,m=copy.deepcopy(tree),copy.deepcopy(model)
    parts=m['components'] if 'components' in m else m
    rows=[r for r in reviewed() if r['source_block']==scope]
    if not rows:return t,m,[]
    physical={(r['ref'],r['pin']):r for r in rows}
    unused={r['net'].split('/')[-1] for r in rows}
    endpoints=[]
    # Only exact physical lands plus their now-obsolete logical boundary stubs.
    for s in children(t,'symbol'):
        ref=value(ref_property(s)[2]);xy,definition=coords(t,s)
        functions={value(child(p,'number')[1]):(value(child(p,'name')[1]),p[1])
            for sub in children(definition,'symbol') for p in children(sub,'pin')}
        c=parts.get(ref,m.get('boundaries',{}).get(ref))
        if c:
            for pin,net in c.get('pins',{}).items():
                if net in unused:
                    if c.get('physical',c.get('role')!='schematic_boundary_not_orderable') and (ref,pin) not in physical:
                        raise ValueError('Unused net has an unreviewed fitted consumer '+ref+'.'+pin)
                    endpoints.append((ref,pin,net,xy[pin],functions[pin],c))
        elif scope=='fpga_core' and ref=='J1010':
            boundary={'3':'DOOR_STATUS_FPGA','5':'SPINDLE_FAULT_FPGA','6':'SPINDLE_READY_FPGA',
                '7':'FEED_HOLD_FPGA','8':'CYCLE_START_FPGA','9':'LUBE_STATUS_FPGA','10':'SPARE_FPGA'}
            for pin,net in boundary.items():endpoints.append((ref,pin,net,xy[pin],functions[pin],None))
        elif scope=='mc_local_power' and ref=='B2001':
            for pin,net in {'7':'CORE_1V2_PG_OD','8':'IO_3V3_PG_OD'}.items():
                endpoints.append((ref,pin,net,xy[pin],functions[pin],None))
    if not physical.keys()<= {(r,p) for r,p,*rest in endpoints}:
        raise ValueError('Reviewed unused endpoint absent from model '+scope)
    ledger=[]
    for ref,pin,net,xy,(function,kind),c in endpoints:
        spec=physical.get((ref,pin))
        native_function=function.replace(' ','_')+'_'+pin
        if spec and (c.get('mpn')!=spec['MPN'] or native_function!=spec['function'] or kind!=spec['native_electrical_type']):
            raise ValueError('Exact manufacturer function/type/MPN differs '+ref+'.'+pin)
        wires=[w for w in children(t,'wire') if xy in [point(p) for p in children(child(w,'pts'),'xy')]]
        if len(wires)!=1:raise ValueError('Unused endpoint not one actual source stub '+ref+'.'+pin)
        w=wires[0];ends=[point(p) for p in children(child(w,'pts'),'xy')]
        other=next(p for p in ends if p!=xy)
        labels=[l for tag in ('label','hierarchical_label') for l in children(t,tag) if point(child(l,'at'))==other]
        if len(labels)!=1 or value(labels[0][1])!=net:
            raise ValueError('Unused endpoint label differs '+ref+'.'+pin)
        if any(point(child(j,'at')) in ends for j in children(t,'junction')) or any(
            other in [point(p) for p in children(child(v,'pts'),'xy')] for v in children(t,'wire') if v is not w):
            raise ValueError('Unused endpoint has another actual wired consumer '+ref+'.'+pin)
        if any(point(child(n,'at'))==xy for n in children(t,'no_connect')):
            raise ValueError('Unused endpoint already NC '+ref+'.'+pin)
        t.remove(w);t.remove(labels[0])
        t.append(['no_connect',['at',str(xy[0]),str(xy[1])],
            ['uuid',q(str(uuid.uuid5(NS,scope+'/'+ref+'/'+pin+'/NC')))]])
        if c:c['pins'][pin]=None
        if spec:ledger.append(dict(reference=ref,pin=pin,
            old_native_net=spec['net'],new_native_net='unconnected-('+ref+'-'+function.replace(' ','_')+'-Pad'+pin+')',
            manufacturer_pin=function,native_pin_function=native_function,electrical_type=kind,source_block=scope,
            category=spec['category'],MPN=spec['MPN'],reason='Exact source22 reviewed unused functional endpoint; graphical NC, real pin retained'))
    if len(ledger)!=len(rows):raise ValueError('Unused functional endpoint ledger incomplete '+scope)
    return t,m,ledger
