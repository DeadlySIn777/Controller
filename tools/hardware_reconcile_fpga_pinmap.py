"""Reconcile the actual PCB/schematic T20F256 resources with its primary workbook.

The output is an exact electrical pin contract, not executable Efinity interface
constraints, placement/timing closure or a qualified target bitstream.
"""
import argparse,collections,csv,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from hardware_validate_fpga_core import primary_pins

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def reconcile(xml,metadata,official,plan,reserved):
    pins=next(v for v in xml.findall('libparts/libpart')if v.attrib['part']=='T20F256I4')
    functions={p.attrib['num']:p.attrib for p in pins.findall('pins/pin')}
    if len(functions)!=256 or set(functions)!=set(official):raise ValueError('Actual manufacturer256-ball symbol differs')
    native={}
    for n in xml.findall('nets/net'):
        for p in n.findall('node'):
            if p.attrib['ref']!='U1001':continue
            ball=p.attrib['pin']
            if ball in native:raise ValueError('Duplicate actual FPGA node')
            native[ball]=n.attrib['name']
    if set(native)!=set(official):raise ValueError('FPGA native256-node inventory differs')
    for ball,p in official.items():
        if functions[ball]['name']!=p['name']:raise ValueError('Manufacturer function differs '+ball)
    constraints={r['ball']:r for r in plan['constraints']}
    if len(constraints)!=len(plan['constraints']):raise ValueError('Duplicate constrained ball')
    rows=[];banks=collections.defaultdict(list)
    for ball,p in official.items():
        if not p['name'].startswith('GPIO')or ball in reserved:continue
        net=native[ball];assigned=not net.startswith('unconnected-')
        c=constraints.get(ball)
        if assigned:
            if c is None or (c['native_net'],c['manufacturer_pin'],c['bank'])!=(net,p['name'],p['bank']):raise ValueError('Actual assigned ball/net/bank contract differs '+ball)
            signal=c['logical_signal'];direction=c['direction']
            expected=metadata['desired_directions'].get(signal)
            if expected is None and (ball,signal)in (('H3','FPGA_CLK_50M'),('D5','FPGA_USER_RESET_N')):expected='input'
            if expected!=direction:raise ValueError('Actual FPGA direction differs '+ball)
            if direction not in ('input','output','bidirectional')or c['io_standard']!='3.3_V_LVCMOS':raise ValueError('Unsupported exact IO contract '+ball)
        else:
            if c is not None:raise ValueError('Constraint drives nativeNC '+ball)
            signal=direction=None
        rows.append(dict(ball=ball,manufacturer_pin=p['name'],bank=p['bank'],worksheet_row=p['row'],allocation='assigned'if assigned else'NC',logical_signal=signal,native_net=net,direction=direction,vccio_net='/IO_3V3',vccio_nominal_v=3.3,io_standard='3.3_V_LVCMOS'if assigned else None))
        banks[p['bank']].append(ball)
    if (len(rows),sum(r['allocation']=='assigned'for r in rows))!=(183,135):raise ValueError('Actual183/135 resources differ')
    if (metadata['assigned_user_pins'],metadata['free_user_gpio'])!=(135,48):raise ValueError('Actual parent metadata count differs')
    supplies=[]
    for ball,p in official.items():
        if p['name'].startswith('VCCIO'):
            if native[ball]!='/IO_3V3':raise ValueError('Actual VCCIO bank rail differs '+ball)
            supplies.append(dict(ball=ball,manufacturer_pin=p['name'],native_net=native[ball],nominal_v=3.3))
    if not supplies:raise ValueError('No actual VCCIO supplies')
    return dict(resources=rows,bank_power_pins=supplies,actual_native_nodes=native,assigned=135,free=48,bank_resource_counts={k:len(v)for k,v in banks.items()},vendor_interface_constraints_generated=False,vendor_package_fit=False,vendor_timing_closed=False,full_RTL_binding_verified=False,manufacturing_ready=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('Use a fresh immutable result')
    paths={'native_netlist':ROOT/'hardware/motherboard/netlist.xml','metadata':ROOT/'hardware/motherboard/fpga-allocation-parent.json','workbook':ROOT/'research/fpga-core/t20-pinout.xlsx','reviewed_plan':ROOT/'reports/motherboard-fpga-source-20260930/status-deallocation-r01/interface-constraint-plan.json','proposal':ROOT/'hardware/motherboard/fpga-allocation-proposal.json','actual_pcb':a.board}
    result=reconcile(ET.parse(paths['native_netlist']).getroot(),json.loads(paths['metadata'].read_text()),primary_pins(paths['workbook']),json.loads(paths['reviewed_plan'].read_text()),json.loads(paths['proposal'].read_text())['reserved_gpio_balls'])
    import pcbnew
    board=pcbnew.LoadBoard(str(a.board));fp=[f for f in board.GetFootprints()if f.GetReference()=='U1001']
    if len(fp)!=1:raise ValueError('Actual PCB FPGA missing/duplicated')
    actual={}
    for pad in fp[0].Pads():
        if not pad.GetNumber():continue
        if pad.GetNumber()in actual:raise ValueError('Duplicate physical FPGA ball')
        actual[pad.GetNumber()]=str(pad.GetNetname())
    if actual!=result['actual_native_nodes']:raise ValueError('Actual PCB/schematic FPGA pads differ')
    result['actual_256_pcb_pad_nets_match']=True;result['input_sha256']={str(v):sha(v)for v in paths.values()}
    a.out.mkdir(parents=True)
    (a.out/'fpga-electrical-contract.json').write_text(json.dumps(result,indent=2)+'\n')
    with (a.out/'fpga-pinmap.csv').open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=list(result['resources'][0]));w.writeheader();w.writerows(result['resources'])
    print(dict(assigned=result['assigned'],free=result['free'],actual256PCBpadsMatch=True,VCCIOpins=len(result['bank_power_pins']),vendor_fit=False))

if __name__=='__main__':main()
