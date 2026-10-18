"""Editable IS-2 sixteen-path differential receiver region, not a released board."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import shutil
import uuid
from hardware_build_tx_schematic import effects, quote, symbol

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_fast_inputs'
REPORT=ROOT/'reports/motherboard-fast-inputs-20260930'
NS=uuid.UUID('17aaeb62-6aeb-49e2-bb95-9c90e3d4fefb')


def uid(value):
    return str(uuid.uuid5(NS,value))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pins=[(1,'1B',-12.7,20.32,0,'input'),(2,'1A',-12.7,25.4,0,'input'),(3,'1Y',12.7,25.4,180,'tri_state'),
          (4,'G',-12.7,40.64,0,'input'),(5,'2Y',12.7,10.16,180,'tri_state'),
          (6,'2A',-12.7,10.16,0,'input'),(7,'2B',-12.7,5.08,0,'input'),(8,'GND',0,-45.72,90,'power_in'),
          (9,'3B',-12.7,-10.16,0,'input'),(10,'3A',-12.7,-5.08,0,'input'),(11,'3Y',12.7,-5.08,180,'tri_state'),
          (12,'~{G}',-12.7,35.56,0,'input'),(13,'4Y',12.7,-20.32,180,'tri_state'),
          (14,'4A',-12.7,-20.32,0,'input'),(15,'4B',-12.7,-25.4,0,'input'),(16,'VCC',0,50.8,270,'power_in')]
    rectangle='(rectangle (start -10.16 48.26) (end 10.16 -43.18) (stroke (width 0.254) (type default)) (fill (type background)))'
    passive=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    resistor='(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
    capacitor='(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
              '(polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
              '(polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))' \
              '(polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    library=[symbol('AM26LV32EIPWR',pins,rectangle),symbol('R',passive,resistor,'R'),symbol('C',passive,capacitor,'C')]
    connector_pins={}
    for count in (3,9,10,18):
        cp=[(i,str(i),-5.08,-(i-1)*2.54,0,'passive') for i in range(1,count+1)]
        body=f'(rectangle (start -2.54 2.54) (end 2.54 {-count*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
        connector_pins[count]=cp
        library.append(symbol(f'Boundary{count}',cp,body,'B'))
    library.append(symbol('PWR_FLAG',[(1,'pwr',0,0,90,'power_out')],'','#FLG'))
    root_id=uid('motherboard-fast-inputs-root')
    items=[];positions={};components=[]

    def place(name,ref,value,x,y,pinlist,footprint='',mpn='',dnp=False,physical=True):
        x=round(x/2.54)*2.54; y=round(y/2.54)*2.54
        positions[ref]={str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pinlist}
        comp={'reference':ref,'value':value,'mpn':mpn,'footprint':footprint,'dnp':dnp,
              'physical':physical,'pins':{}}
        if not ref.startswith('#'):
            components.append(comp)
        props=''.join(f'(property {quote(key)} {quote(val)} (at {x+4 if key in ("Reference","Value") else x} {y-5 if key=="Reference" else y-2.5 if key=="Value" else y} 0) {effects(extra="hide" if key not in ("Reference","Value") else "")})'
                      for key,val in [('Reference',ref),('Value',value),('Footprint',footprint),('MPN',mpn),
                                      ('Scope','physical_component_candidate' if physical else 'schematic_boundary_nonphysical')])
        fitted='yes' if physical and not ref.startswith('#') else 'no'
        items.append(f'(symbol (lib_id "CNC_FAST:{name}") (at {x} {y} 0) (unit 1) (in_bom {fitted}) (on_board {fitted}) (dnp {"yes" if dnp else "no"}) (uuid "{uid(ref)}") {props}'
                     f'(instances (project "motherboard_fast_inputs" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')

    def label(ref,pin,net,dx=0,dy=0):
        x,y=positions[ref][str(pin)];ex,ey=round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')
        for comp in components:
            if comp['reference']==ref:
                comp['pins'][str(pin)]=net
                break

    def note(x,y,value,size=1.1):
        items.append(f'(text {quote(value)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(value)}"))')

    channel_names=[f'ENC{i}_{s}' for i in range(4) for s in 'ABZ']+['FREQ0','FREQ1','MPG_A','MPG_B']
    groups=((2,1,3),(6,7,5),(10,9,11),(14,15,13))
    mapping=[]
    for bank in range(4):
        x,y=150+bank*190,160
        ref=f'U{bank+1}'
        place('AM26LV32EIPWR',ref,'AM26LV32EIPWR',x,y,pins,'Package_SO:TSSOP-16_4.4x5mm_P0.65mm','AM26LV32EIPWR')
        netmap={4:'IO_3V3',12:'IO_3V3',16:'IO_3V3',8:'LOGIC_GND'}
        for local,(positive,negative,output) in enumerate(groups):
            index=bank*4+local;name=channel_names[index]
            netmap.update({positive:name+'_P',negative:name+'_N',output:name+'_FPGA'})
            mapping.append({'channel':name,'receiver':ref,'device_channel':local+1,
                            'positive_pin':positive,'negative_pin':negative,'output_pin':output,
                            'positive_net':name+'_P','negative_net':name+'_N','logic_net':name+'_FPGA',
                            'termination':f'R{index+1}','termination_fitted':index<14})
        for pin,net in netmap.items():
            label(ref,pin,net,dx=0 if pin in (8,16) else 7.62 if pin in (3,5,11,13) else -22.86,
                  dy=-5.08 if pin==16 else 5.08 if pin==8 else 0)
        for local,(value,mpn,cx) in enumerate([('100nF 100V X7R','GRM188R72A104KA35D',x-40.64),('1uF 16V X7R','885012206052',x+5.08)]):
            cr=f'C{bank*2+local+1}'
            place('C',cr,value,cx,70,passive,'Capacitor_SMD:C_0603_1608Metric',mpn)
            label(cr,1,'IO_3V3',dy=-5.08);label(cr,2,'LOGIC_GND',dy=5.08)
        note(x-65,32,f'{ref}: four used receiver paths, G and /G tied IO_3V3\n3.0–3.6V supply; no motion-permission authority.\n0.1uF bypass close to VCC/GND; 1uF local bulk.')
    for index,ch in enumerate(mapping):
        bank,local=divmod(index,4);x,y=150+bank*190,285+local*45
        fit=ch['termination_fitted']
        place('R',ch['termination'],'120R 1% 0.5W / '+('FIT' if fit else 'DNP'),x,y,passive,
              'Resistor_SMD:R_1210_3225Metric','CRCW1210120RFKEA',dnp=not fit)
        label(ch['termination'],1,ch['positive_net'],dy=-5.08)
        label(ch['termination'],2,ch['negative_net'],dy=5.08)

    boundary_map={}
    for enc in range(4):
        ref=f'B{enc+1}'
        nets=[f'ENC{enc}_5V_LIMITED','LOGIC_GND']+[f'ENC{enc}_{s}_{p}' for s in 'ABZ' for p in 'PN']+['LOGIC_GND','CHASSIS']
        boundary_map[ref]={str(i):n for i,n in enumerate(nets,1)}
        place('Boundary10',ref,f'XE{enc} FUNCTION / NONPHYSICAL',80+enc*190,100,connector_pins[10],physical=False)
        for pin,net in boundary_map[ref].items():label(ref,pin,net,dx=-25.4)
    boundary_map['B5']=dict(enumerate(['FREQ_5V_LIMITED','LOGIC_GND','FREQ0_P','FREQ0_N','FREQ1_P','FREQ1_N',
                                         'FREQ_MOD_ID_TO_FRONTEND','FREQ_MOD_PRESENT_TO_FRONTEND','LOGIC_GND','CHASSIS'],1))
    boundary_map['B6']=dict(enumerate(['MPG_5V_LIMITED','LOGIC_GND','MPG_A_P','MPG_A_N','MPG_B_P','MPG_B_N',
                                       'MPG_VREF_2V5','MPG_ENABLE_TO_STATUS','LOGIC_GND','CHASSIS'],1))
    for ref,x in [('B5',80),('B6',270)]:
        place('Boundary10',ref,('XF' if ref=='B5' else 'XH1')+' FUNCTION / NONPHYSICAL',x,230,connector_pins[10],physical=False)
        for pin,net in boundary_map[ref].items():label(ref,pin,net,dx=-25.4)
    power_nets=[f'ENC{i}_5V_LIMITED' for i in range(4)]+['FREQ_5V_LIMITED','MPG_5V_LIMITED','MPG_VREF_2V5','LOGIC_GND','CHASSIS']
    boundary_map['B7']=dict(enumerate(power_nets,1))
    place('Boundary9','B7','EXTERNALLY PROTECTED FEEDS / NONPHYSICAL',415,480,connector_pins[9],physical=False)
    for pin,net in boundary_map['B7'].items():label('B7',pin,net,dx=-40.64)
    logic_nets=['IO_3V3','LOGIC_GND']+[ch['logic_net'] for ch in mapping]
    boundary_map['B8']=dict(enumerate(logic_nets,1))
    place('Boundary18','B8','FPGA LOGIC BOUNDARY / NONPHYSICAL',605,460,connector_pins[18],physical=False)
    for pin,net in boundary_map['B8'].items():label('B8',pin,net,dx=-40.64)
    status_nets=['FREQ_MOD_ID_TO_FRONTEND','FREQ_MOD_PRESENT_TO_FRONTEND','MPG_ENABLE_TO_STATUS']
    boundary_map['B9']=dict(enumerate(status_nets,1))
    place('Boundary3','B9','MISSING FRONTEND HANDOFF / NONPHYSICAL',760,480,connector_pins[3],physical=False)
    for pin,net in boundary_map['B9'].items():label('B9',pin,net,dx=-30.48)
    # These are explicit interfaces to missing acquisition/identity regions,
    # not claimed detectors. Two labels on a nonphysical boundary are not HW.
    for i,(net,x) in enumerate([('IO_3V3',60),('LOGIC_GND',120)],1):
        place('PWR_FLAG',f'#FLG0{i}','EXTERNAL RATED LOGIC FEED',x,520,[(1,'pwr',0,0,90,'power_out')],physical=False)
        label(f'#FLG0{i}',1,net,dy=5.08)
    note(17.78,12.7,'IS-2 MOTHERBOARD: FOUR ABZ + TWO FREQUENCY + MPG A/B RECEIVER REGION r0.1',2)
    note(17.78,450,'All 16 receiver channels used; no receiver output NC. No galvanic isolation or cable-line-fault detector here.\n14 fitted 120R terminations; MPG R15/R16 DNP to avoid loading a 1mA TTL reference. Differential MPG needs a qualified termination variant.\nTerminated/disconnected or shorted pairs do not have guaranteed fail-safe state. Encoder validity must not be invented from a static output.\nNo probes, pendant shift register, sensor power limiter, 2.5V reference, accessory identity/presence or status frontend implemented in this receiver region.')
    note(17.78,550,'BOUNDARIES ARE NONPHYSICAL: no unverified connector MPN/footprint. Preserve XE0–3 / XF / XH1 logical field ordering.\n5V protected feeds and MPG_VREF enter from future parent regions; this block does not generate or protect them.\nInput bound: RS422 5.5V maximum differential for termination arithmetic; receiver common-mode -7..+7V, not a field-voltage rating.\nExternal line surge protection, source/cable load, footprints/stencil, thermal/EMC and rates still require qualification. Manufacturing blocked.')
    sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A1")\n(title_block (title "IS-2 motherboard differential fast inputs") (date "2026-09-30") (rev "r0.1") (comment 1 "16 receiver paths; partial motherboard region; not a manufacturing release"))\n(lib_symbols {"".join(library)})\n'+ '\n'.join(items)+'\n)\n'
    (OUT/'motherboard_fast_inputs.kicad_sch').write_text(sch,encoding='utf-8')
    lib='\n'.join(s.replace('(symbol "CNC:','(symbol "',1) for s in library)
    # helper emits CNC:<name>; local library identifier is CNC_FAST in instances.
    sch_path=OUT/'motherboard_fast_inputs.kicad_sch'
    sch_path.write_text(sch.replace('(symbol "CNC:','(symbol "CNC_FAST:'),encoding='utf-8')
    (OUT/'CNC_FAST.kicad_sym').write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {lib})\n',encoding='utf-8')
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "CNC_FAST")(type "KiCad")(uri "${KIPRJMOD}/CNC_FAST.kicad_sym")(options "")(descr "Source-reviewed IS-2 fast receiver region")))\n',encoding='utf-8')
    rules={'lib_symbol_issues':'warning','similar_labels':'warning','single_global_label':'warning',
           'four_way_junction':'warning','simulation_model_issue':'warning','footprint_filter':'warning'}
    (OUT/'motherboard_fast_inputs.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_fast_inputs.kicad_pro','version':1},'erc':{'rule_severities':rules}},indent=2)+'\n',encoding='utf-8')
    minimum=120*.99*.985;power=5.5**2/minimum
    model={'schema_version':1,'revision':'MB-FAST-r0.1','interface_revision':'IS-2','manufacturing_ready':False,
           'scope':'on-motherboard 4ABZ/2FREQ/MPG differential receiver region only',
           'components':{c['reference']:c for c in components},'channels':mapping,'boundary_map':boundary_map,
           'boundary_inputs':['IO_3V3','LOGIC_GND','CHASSIS']+power_nets[:-2]+[ch[k] for ch in mapping for k in ('positive_net','negative_net')],
           'boundary_outputs':[ch['logic_net'] for ch in mapping]+status_nets,
           'unused_receiver_channels':[],'always_enabled':{'G_pin4':'IO_3V3','G_N_pin12':'IO_3V3','function':'G high independently enables all channels; /G high does not disable while G high'},
           'termination':{'mpn':'CRCW1210120RFKEA','ohms':120,'tolerance':.01,'tcr_ppm_per_k':100,
                          'conservative_temperature_excursion_k':150,'maximum_applied_differential_v':5.5,
                          'minimum_ohms':minimum,'worst_w_per_fitted_channel':power,'worst_w_all_14_fitted':14*power,
                          'worst_w_if_all16_fitted':16*power,'rating_w_at70c':.5,'initial_local_ambient_max_c':70,
                          'MPG_default':'DNP_open_only','MPG_TTL_reason':'120R against 2.5V at 1mA maximum reference would require ~20.8mA at 2.5V differential; cannot offer this loading.',
                          'physical_thermal_qualified':False},
           'source_refs':{'TI_datasheet':'https://www.ti.com/lit/ds/symlink/am26lv32e.pdf','TI_document':'SLLS849E August2023 / package addendum November2025',
                          'Vishay_datasheet':'https://www.vishay.com/docs/20035/dcrcwe3.pdf'},
           'open_gates':['parent supplies ENC0-3 protected5V at200mA normal target/port; FREQ150mA and MPG100mA limited feeds','parent 2.5V MPG reference 1mA and status/identity/presence frontends','exact source/mating connector, terminal coding, shield routing and mechanics','external line surge protection and sustained fault containment','dedicated PCB placement, termination power/cable loading, decoupling/return and SI review','stock TSSOP lands differ from TI example; fabricator/stencil process qualification required','FPGA ball/bank reconciliation for all sixteen outputs','physical 10M encoder transitions/s, >=1MHz frequency and100kHz MPG goals are unqualified','shorted/terminated cable-loss detection and validity policies remain unresolved']}
    (OUT/'design.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
    (OUT/'channel-map.json').write_text(json.dumps({'schema_version':1,'channels':mapping,'unused_channels':[],'manufacturing_ready':False},indent=2)+'\n',encoding='utf-8')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status','Scope']);w.writeheader()
        for c in components:
            if c['physical']:
                w.writerow({'Reference':c['reference'],'Value':c['value'],'MPN':c['mpn'],'Footprint':c['footprint'],
                            'Status':'DNP_optional_qualification_required' if c['dnp'] else 'candidate_not_qualified','Scope':'physical_component_candidate'})
    print(json.dumps({'output':str(OUT),'receiver_paths':len(mapping),'physical_footprints':sum(c['physical'] for c in components),'fitted_parts':sum(c['physical'] and not c['dnp'] for c in components),'DNP_parts':sum(c['dnp'] for c in components)},indent=2))


if __name__=='__main__':main()
