"""Isolated exact seven-ball status deallocation plan; no hardware edits."""
import copy,csv,hashlib,json,sys,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_fpga_core import primary_pins
HERE=Path(__file__).resolve().parent
PINS=(('DOOR_STATUS_FPGA','H13','GPIOR_125_CLK10','BANK3D',122),
      ('SPINDLE_FAULT_FPGA','G14','GPIOR_127_CLK8','BANK3D',124),
      ('SPINDLE_READY_FPGA','H14','GPIOR_128_CTRL11','BANK3D',125),
      ('FEED_HOLD_FPGA','H15','GPIOR_129_CTRL10','BANK3D',126),
      ('CYCLE_START_FPGA','H16','GPIOR_130_CTRL9','BANK3D',127),
      ('LUBE_STATUS_FPGA','J15','GPIOR_131_CTRL8','BANK3D',128),
      ('SPARE_FPGA','K14','GPIOR_138','BANK3D',133))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def reconcile(metadata,xml,official,copper):
    if (metadata.get('assigned_user_pins'),metadata.get('free_user_gpio'),metadata.get('promoted_nc_pin_count'),metadata.get('deallocated_user_pin_count'))!=(142,41,66,21):
        raise ValueError('Exact adopted142/41/66/21 metadata required')
    native={}
    for net in xml.findall('./nets/net'):
        for node in net.findall('node'):
            key=node.attrib['ref'],node.attrib['pin']
            if key in native:raise ValueError('Duplicate native node')
            native[key]=net.attrib['name']
    lib=next(p for p in xml.findall('./libparts/libpart') if p.attrib['part']=='T20F256I4')
    functions={p.attrib['num']:p.attrib for p in lib.findall('./pins/pin')}
    result=copy.deepcopy(metadata);ledger=[]
    for signal,ball,pn,bank,row in PINS:
        if (official[ball]['name'],official[ball]['bank'],official[ball]['row'])!=(pn,bank,row):raise ValueError('Official ball/bank differs '+ball)
        if functions[ball]['name']!=pn or functions[ball]['type']!='bidirectional':raise ValueError('Manufacturer native function/type differs '+ball)
        old='/fpga_core/'+signal
        if native['U1001',ball]!=old or result['desired_directions'].get(signal)!='input':raise ValueError('Actual old allocation differs '+ball)
        matches=[r for r in copper['rows'] if r['native_net']==old and (r['ref'],r['pin'])==('U1001',ball)]
        if len(matches)!=1 or any(matches[0][k] for k in ('track_or_via_items','zone_items')) or not matches[0]['zero_existing_copper']:raise ValueError('Not exact zero-copper proof '+ball)
        new='unconnected-(U1001-'+pn+'-Pad'+ball+')'
        ledger.append(dict(reference='U1001',pin=ball,signal=signal,manufacturer_pin=pn,manufacturer_native_function=functions[ball]['name'],
          bank=bank,worksheet_row=row,old_native_net=old,new_native_net=new,reason='obsolete_dedicated_machine_status_input_moves_to_DI24_IOL1',
          scope='exact single originalMC pin only; no wildcard',zero_copper_verified=True,native_export_verified=False))
        result['root_sheet_port_map'].pop(signal,None)
        result['desired_directions'].pop(signal)
    result.update(revision='motherboard-fpga-status-deallocation-r01-proposed',assigned_user_pins=135,free_user_gpio=48,
      deallocated_user_pin_count=28,status_deallocation_pin_rename_ledger=ledger,status_deallocation_applied=False,
      original_MC_source_changed=False,vendor_fit=False,manufacturing_ready=False)
    result['exact_pin_rename_ledger']=result['exact_pin_rename_ledger']+ledger
    result['new_fpga_hierarchy_ports']=len(result['root_sheet_port_map'])
    result['parent_endpoint_obligations']=[r for r in result.get('parent_endpoint_obligations',[]) if r.get('signal') not in {p[0] for p in PINS}]
    return result,ledger,native
def main():
    inputs=HERE/'inputs'
    if not inputs.exists():inputs.mkdir()
    paths={'metadata.json':ROOT/'reports/motherboard-audit-20260930/2663-source-r20b-review/inputs/source/fpga-allocation-parent.json',
      'netlist.xml':ROOT/'reports/motherboard-audit-20260930/2663-source-r20b-review/inputs/source/netlist.xml',
      'proposal.json':ROOT/'hardware/motherboard/fpga-allocation-proposal.json',
      't20-pinout.xlsx':ROOT/'research/fpga-core/t20-pinout.xlsx',
      'copper-evidence.json':ROOT/'reports/motherboard-audit-20260930/2663-source-r20b-review/single-pad-copper-evidence.json',
      'modules.json':ROOT/'reports/motherboard-is2-contract-20260930/inputs/spec/modules.json'}
    for name,path in paths.items():shutil.copyfile(path,inputs/name)
    official=primary_pins(inputs/'t20-pinout.xlsx');xml=ET.parse(inputs/'netlist.xml').getroot()
    copper=read(inputs/'copper-evidence.json')
    new,ledger,native=reconcile(read(inputs/'metadata.json'),xml,official,copper)
    write(HERE/'metadata-proposed.json',new);write(HERE/'seven-pin-ledger.json',ledger)
    original=read(inputs/'proposal.json')
    candidates={r['ball']:r for r in original['candidates']['base_preserve_all_current']['signals']}
    reserved=original['reserved_gpio_balls'];rows=[]
    for ball,p in official.items():
        if not p['name'].startswith('GPIO') or ball in reserved:continue
        net=native['U1001',ball]
        if ball in {r['pin'] for r in ledger}:net=next(r['new_native_net'] for r in ledger if r['pin']==ball)
        assigned=not net.startswith('unconnected-')
        logical=candidates.get(ball,{}).get('signal')
        if ball=='M4':logical='FAST_PORTS_ENABLE'
        if ball=='M6':logical='XF_POWER_ENABLE'
        if not assigned:logical=None
        direction=None if not assigned else new['desired_directions'].get(logical)
        if assigned and direction is None:
            if ball in ('H3','D5'):direction='input'
            else:raise ValueError('No reviewed direction for assignedball '+ball+' '+str(logical))
        rows.append(dict(ball=ball,manufacturer_pin=p['name'],bank=p['bank'],worksheet_row=p['row'],
          allocation='assigned' if assigned else 'NC',logical_signal=logical,native_net=net,direction=direction,
          vccio_net='IO_3V3',vccio_nominal_v=3.3,io_standard='3.3_V_LVCMOS' if assigned else None,
          vendor_constraint_export=False,full_RTL_binding_verified=False))
    if len(rows)!=183 or sum(r['allocation']=='assigned' for r in rows)!=135:raise ValueError('183resource/135assigned count mismatch')
    write(HERE/'all-183-user-resources.json',rows)
    with (HERE/'reviewed-pinmap-proposed.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    constraints=[dict(logical_signal=r['logical_signal'],ball=r['ball'],bank=r['bank'],direction=r['direction'],io_standard=r['io_standard'],
      native_net=r['native_net'],manufacturer_pin=r['manufacturer_pin']) for r in rows if r['allocation']=='assigned']
    write(HERE/'interface-constraint-plan.json',dict(schema_version=1,package='T20F256',assigned_user_resources=135,
      constraints=constraints,omitted_obsolete_status_balls=[r['pin'] for r in ledger],
      executable_vendor_constraint_file=False,reason='Complete Efinity interface/RTL integration and package-fit are not available; no invented vendor Tcl/API.',
      original_fixed_configuration_JTAG_power_resources_unchanged=True,hardware_parent_mutated=False,vendor_fit=False,manufacturing_ready=False))
    write(HERE/'receipt.json',dict(schema_version=1,input_sha256={n:sha(inputs/n) for n in paths},
      exact_deallocations=7,assigned_before=142,assigned_proposed=135,free_before=41,free_proposed=48,
      promoted_original_transaction_preserved=66,prior_deallocation_transaction_preserved=21,new_cumulative_deallocations=28,
      all_seven_BANK3D=True,all_seven_vccio_nominal_v=3.3,source_or_RTL_mutated=False,
      executable_vendor_constraints_exist=False,vendor_fit=False,manufacturing_ready=False))
if __name__=='__main__':main()
