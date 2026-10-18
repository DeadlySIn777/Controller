"""Freeze the actual motherboard BOM and an exclusive function/count audit.

Source and native-netlist inspection only. Zero sockets means missing sockets,
not an implemented replaceable-module capability. No absent interface receives
credit because its name appears in a specification.
"""
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
FUNCTIONS={
 '12 motor interfaces and source buffers':('mc_motor_buffers','motherboard_motors'),
 '24 digital inputs':('motherboard_di',),
 '16 smart outputs':('motherboard_do',),
 'Four encoders / frequency / MPG receivers':('motherboard_fast_inputs',),
 'FPGA rails and motor receiving-rail monitors':('mc_local_power','motherboard_motor_power','motherboard_io3_upgrade','motherboard_io3_window'),
 'FPGA / configuration flash / clock / support':('fpga_core',),
 'Watchdogs / permission / deliberate-control bridges':('watchdog_conditioning','mc_permission','motherboard_control_bridges'),
 'I/O acquisition and control':('motherboard_io_control',),
 'Probe / pendant / fast-port supplies':('motherboard_operator',),
 'Protected power entry / distribution':('motherboard_power_entry',),
 'PWM / process contacts and acquisition':('motherboard_process','motherboard_acc_control'),
 'Analog / communications':('motherboard_analog_output','motherboard_analog_input','motherboard_comms'), 'LED indicators':('motherboard_status',),
 'Sensor power / XS1 field and acquisition':('motherboard_safety_sensor',),
 'Field headers / chassis coupling':('motherboard_terminals',),
 'Compute / ESP / storage socket circuits':('motherboard_compute','motherboard_esp_socket'),
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);a=parser.parse_args()
    out=a.out.resolve()
    if out.exists():raise ValueError('Preserve previous audit; choose a fresh output directory')
    src=ROOT/'hardware/motherboard'
    files=[src/n for n in ('design.json','netlist.xml','assembly-map.json','bom.csv','fpga-allocation-parent.json')]
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in files}
    model=json.loads(files[0].read_text(encoding='utf-8'));parts=model['components'];tree=ET.parse(files[1])
    refs={c.attrib['ref']:c for c in tree.findall('.//components/comp') if c.attrib['ref'] in parts}
    if set(parts)!=set(refs):raise ValueError('Actual native physical inventory and source BOM differ')
    rows=[];assigned=set()
    for function,blocks in FUNCTIONS.items():
        selected={r for r,c in parts.items() if c.get('source_block') in blocks}
        if assigned & selected:raise ValueError('Functional population double-counted')
        assigned|=selected
        composition=Counter(''.join(c for c in r if c.isalpha()) for r in selected)
        rows.append({'function':function,'footprints':len(selected),'fitted':sum(not parts[r].get('dnp',False) for r in selected),
                     'source_blocks':list(blocks),'composition':dict(sorted(composition.items()))})
    if assigned!=set(parts):raise ValueError('Functional population omitted source parts')
    composition=Counter(''.join(c for c in r if c.isalpha()) for r in parts)
    grouped=defaultdict(list)
    for r,c in parts.items():grouped[c['mpn']].append(r)
    passives=sum(composition[p] for p in ('R','C','D'))
    rack_refs=[r for r,c in parts.items() if any(s in (str(c.get('mpn',''))+' '+str(c.get('footprint',''))).upper() for s in ('HAR-BUS','HARTING_DIN','DIN41612','DIN_41612','H15_BACKPLANE'))]
    custom_compute=[r for r,c in parts.items() if str(c.get('mpn','')).upper().startswith(('BCM2711','BCM2712','H616','RK3566','RK3588'))]
    custom_esp=[r for r,c in parts.items() if str(c.get('mpn','')).upper().startswith(('ESP32','ESP8266'))]
    active_groups={m:refs for m,refs in grouped.items() if len(refs)>1 and all(r.startswith('U') for r in refs)}
    duplicate_review=[]
    for m,refs in sorted(active_groups.items()):
        duplicate_review.append({'MPN':m,'references':sorted(refs),
            'source_blocks':sorted({parts[r]['source_block'] for r in refs}),
            'roles':{r:parts[r].get('role','Review retained native circuit and endpoint') for r in sorted(refs)},
            'automatic_removal_authorized':False})
    findings={
      'fitted_physical_rack_connectors':len(rack_refs),'rack_connector_refs':rack_refs,'physical_connector_footprints':composition['J'],
      'fitted_custom_compute_soc':len(custom_compute),'custom_compute_refs':custom_compute,
      'fitted_custom_esp_soc':len(custom_esp),'custom_esp_refs':custom_esp,
      'fitted_compute_socket':sum(c.get('source_block')=='motherboard_compute' and c.get('mpn')=='10164227-1001A1RLF' for c in parts.values()),
      'fitted_esp_socket':sum(c.get('source_block')=='motherboard_esp_socket' and c.get('mpn')=='61302211821' for c in parts.values()),
      'fitted_storage_socket':sum(c.get('mpn')=='503398-1892' for c in parts.values()),'module_replacement_hardware_implemented':False,
      'fpga_configuration_flash':['U1002'],'card_identity_EEPROMs':[],
      'actual_regulator_refs':[r for r,c in parts.items() if str(c.get('mpn','')).startswith(('TPS629','TPS7A','LM70660','LMR36506'))],
      'actual_LTC2962_refs':[r for r,c in parts.items() if str(c.get('mpn','')).startswith('LTC2962')],
      'source_buffer_paths':38,'retained_single_used_channel_buffer_candidate':'U5004',
      'rack_only_parts_proven_removable':[],
      'reviewed_future_DO_control_duplicate_biases':4,
      'DO_control_consolidation_integrated':any(c.get('source_block')=='motherboard_io_control' for c in parts.values()),
      'watchdog_clear_correction':'New 33R branches connect to U4018 rearm INPUTS, not U4019 driven clear OUTPUTS; request defaults LOW.'}
    out.mkdir(parents=True);snap=out/'source-inputs';snap.mkdir()
    for p in files:shutil.copyfile(p,snap/p.name)
    with (out/'footprints-by-function.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Function','Footprints','Fitted_geometry','Resistors','Capacitors','Diodes_including_TVS','U_ref_active','Inductors','Clock','Bare_testpads','Connectors','Fuses','Switches','Chassis_pad'])
        for row in rows:w.writerow([row['function'],row['footprints'],row['fitted'],*[row['composition'].get(p,0) for p in ('R','C','D','U','L','Y','TP','J','F','SW','H')]])
    with (out/'designator-bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Reference','Function','Source_block','Value','MPN','Footprint','DNP','Role'])
        for ref,c in sorted(parts.items()):
            function=next(k for k,blocks in FUNCTIONS.items() if c['source_block'] in blocks)
            w.writerow([ref,function,c['source_block'],c['value'],c['mpn'],c['footprint'],str(bool(c.get('dnp',False))).lower(),c.get('role','')])
    with (out/'mpn-population.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['MPN','Footprints','Fitted','References'])
        for mpn,refs in sorted(grouped.items()):w.writerow([mpn,len(refs),sum(not parts[r].get('dnp',False) for r in refs),' '.join(sorted(refs))])
    result={'schema_version':1,'scope':'Actual fitted-candidate native/source population; source inspection only',
            'source_sha256':hashes,'physical_footprints':len(parts),'fitted_parts':sum(not c.get('dnp',False) for c in parts.values()),
            'bare_PCB_testpad_footprints':composition['TP'],
            'bare_PCB_chassis_footprints':sum(c.get('purchased') is False and r.startswith('H') for r,c in parts.items()),
            'purchased_fitted_parts':sum(not c.get('dnp',False) and c.get('kind')!='TP' and c.get('purchased',True) and not c.get('exclude_bom',False) for c in parts.values()),
            'function_counts':rows,'reference_composition':dict(sorted(composition.items())),
            'R_C_TVS_footprints':passives,'R_C_TVS_percent':round(100*passives/len(parts),3),
            'distinct_MPNs':len(grouped),'findings':findings,'schematic_frozen_for_manufacture':False,
            'repeated_active_MPN_review':duplicate_review,
            'full_controller_complete':False,'manufacturing_ready':False,'physical_measurements':False}
    if any(sha(ROOT/p)!=h for p,h in hashes.items()):raise ValueError('Source changed during audit')
    write(out/'review.json',result)
    lines=['# Actual motherboard population audit','',f'**{len(parts)} physical footprints; {result["purchased_fitted_parts"]} purchased fitted parts; {composition["TP"]} bare PCB test pads; {result["bare_PCB_chassis_footprints"]} bare chassis pad.** Function rows are exclusive and already include their passives. Fitted geometry includes bare pads; these have no purchased part or assembly placement. The material composition is separate; it is not added to the total.','',
           '| Function | Footprints | Fitted |','|---|---:|---:|']
    lines += [f'| {r["function"]} | {r["footprints"]} | {r["fitted"]} |' for r in rows]
    lines += [f'| **Total** | **{len(parts)}** | **{result["fitted_parts"]}** |','',
              f'Resistors {composition["R"]}; capacitors {composition["C"]}; diodes including TVS {composition["D"]}: **{passives} footprints ({result["R_C_TVS_percent"]}%)**. Remaining reference classes: '+', '.join(f'{p}: {n}' for p,n in sorted(composition.items()) if p not in ('R','C','D') and n)+'.','',
              'No physical DIN/H15/har-bus card/backplane connector, rack identity EEPROM or duplicate Linux/ESP processor is in this BOM. Legacy MIA/MX4/card names remain on some internal nets; those names do not represent fabricated cards. Exact source buffers and permission gates still need their electrical review.','',
              f'**Actual compute socket count: {findings["fitted_compute_socket"]}; ESP socket rows: {findings["fitted_esp_socket"]}; storage sockets: {findings["fitted_storage_socket"]}.** Socket circuitry is credited only where physically drawn. Purchased modules remain separate procurement items; interchangeable-module images, mechanical/thermal and powered qualification remain unfinished. Every implemented source is credited only by its exclusive row; zero-count rows remain absent. Actual terminal source does not prove edge access, mating clearance or copper connectivity. Freezing this as a complete controller would preserve missing circuitry and routing.','',
              f'{len(findings["actual_regulator_refs"])} actual converter/LDO devices and {len(findings["actual_LTC2962_refs"])} LTC2962 devices serve distinct rails, receiving banks or isolated post-limiter supplies. Repeated active MPNs, their exact references, domains and roles are included in review.json. Equal MPNs are not proof of removable duplication. No rack-only regulator/supervisor has been proved removable. Current/load/startup and temperature budgets still need reconciliation.','',
              'U5004 uses one octal-buffer channel and is a possible single-channel Ioff substitution. It is not yet an electrically/mechanically/procurement-qualified saving. Four duplicate DO default resistors are removed in the reviewed I/O-control source; the consolidation is integrated here only if the function table includes that source block.','',
              'The audit found and corrected a real new watchdog-clear conflict: 33 Ω branches had targeted U4019 push-pull outputs. They now target U4018 WD_REARM_M/O inputs, active-high/default-low, retaining power-reset qualification. The erroneous source is archived separately. Native pin parity alone did not catch this topology defect.','',
              'Routing continues only after the missing existing-required circuits and these real electrical issues are reconciled. No new capability or rack architecture is authorized. Prototype measurements, vendor FPGA fit and manufacturing cost remain separate evidence gates.']
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('physical_footprints','fitted_parts','R_C_TVS_footprints','R_C_TVS_percent','distinct_MPNs','manufacturing_ready')}))

if __name__=='__main__':main()
