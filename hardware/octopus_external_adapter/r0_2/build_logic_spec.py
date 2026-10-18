"""Write independently reviewed OEA r0.2 logic/connector design inputs.

This creates engineering source, not fabrication or qualification evidence.
"""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parent
LIB = ROOT / 'Adapter.pretty'
LIB.mkdir(exist_ok=True)
parts = {}

def part(ref, value, mpn, manufacturer, footprint, pins, labels=None, types=None,
         kind='generic', source=None, notes=None):
    parts[ref] = dict(reference=ref, value=value, mpn=mpn, manufacturer=manufacturer,
                      footprint=footprint, pins={str(k):v for k,v in pins.items()},
                      pin_labels={str(k):v for k,v in (labels or {}).items()},
                      pin_types={str(k):v for k,v in (types or {}).items()},
                      kind=kind, source=source, notes=notes or [])

def resistor(ref, value, mpn, a, b, size='0603'):
    fp = 'Resistor_SMD:R_0603_1608Metric' if size=='0603' else 'Resistor_SMD:R_0805_2012Metric'
    part(ref, value, mpn, 'Yageo', fp, {1:a,2:b}, {1:'1',2:'2'}, {1:'passive',2:'passive'}, 'resistor',
         'https://www.yageo.com/en/ProductSearch/PartNumberSearch')

def bypass(ref):
    part(ref,'100nF 50V X7R','CL10B104KB8NNNC','Samsung Electro-Mechanics',
         'Capacitor_SMD:C_0603_1608Metric',{1:'V_LOGIC',2:'GND'},
         {1:'1',2:'2'},{1:'passive',2:'passive'},'capacitor',
         'https://product.samsungsem.com/mlcc/CL10B104KB8NNNC.do')

for n in [7,8]:
    name=f'Wurth_61300{n}11121_1x0{n}_P2.54mm.kicad_mod'
    src=ROOT.parent/'r0_1'/'Adapter.pretty'/name
    shutil.copyfile(src,LIB/name)

part('J1','StepStick logic row','61300811121','Wurth Elektronik',
     'Adapter:Wurth_61300811121_1x08_P2.54mm',
     {1:'EN',2:None,3:None,4:None,5:None,6:None,7:'STEP',8:'DIR'},
     {1:'EN',2:'MS1_NC',3:'MS2_NC',4:'MS3_NC',5:'RST_NC',6:'SLP_NC',7:'STEP',8:'DIR'},
     {i:'passive' for i in range(1,9)},'connector',
     'https://www.we-online.com/components/products/datasheet/61300811121.pdf',
     ['Underside male header. Local pad1 at original EN end. Pitch2.54mm.'])
part('J2','StepStick power row; VM physically omitted','61300711121','Wurth Elektronik',
     'Adapter:Wurth_61300711121_1x07_P2.54mm',
     {1:'GND',2:None,3:None,4:None,5:None,6:'HOST_VIO',7:'GND'},
     {1:'GND_VM',2:'MOTOR_NC1',3:'MOTOR_NC2',4:'MOTOR_NC3',5:'MOTOR_NC4',6:'HOST_VIO',7:'GND'},
     {i:'passive' for i in range(1,8)},'connector',
     'https://www.we-online.com/components/products/datasheet/61300711121.pdf',
     ['Underside seven-position header begins one2.54mm pitch below VM location.',
      'No VM pin, pad, plated hole, copper or testpoint.',
      'HOST_VIO is only a weak EN input reference; never powers adapter or driver.'])
part('J3','Keyed driver signal output','B4B-XH-A(LF)(SN)','JST',
     'Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical',
     {1:'COM_PLUS',2:'PUL_MINUS',3:'DIR_MINUS',4:'ENA_MINUS'},
     {1:'COM+',2:'PUL-',3:'DIR-',4:'ENA-'},{i:'passive' for i in range(1,5)},'connector',
     'https://www.jst-mfg.com/product/pdf/eng/eXH.pdf',
     ['Female XHP-4 cable housing and SXH-001T-P0.6 crimp contacts mate with shrouded male PCB header.',
      'Factory harness splits COM+ to the three driver-positive terminals.'])
part('J4','External reference/power 5/12/24V','1725656','Phoenix Contact',
     'Adapter:Phoenix_1725656_MPT_0p5_2_2p54_SilkClearance',
     {1:'EXT_RAW',2:'GND'},{1:'EXT+',2:'0V'},{1:'passive',2:'passive'},'connector',
     'https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mpt-05-2-254-1725656?type=pdf',
     ['MPT0.5/2-2.54, body5.54x6.2mm, height8.5mm, pinlength3.5mm, drill1.1mm.',
      'Polarity defined by PCB labels; maintain permanent shared ground.',
      'Use regulated5V only in EXT; 12/24V may use5V or EXT as appropriate to drive.',
      'KiCad library derivative: upper outline segment moved to Dwgs.User for polarity-label clearance; lands/Fab/courtyard unchanged. See Adapter.pretty/KICAD-J4-ATTRIBUTION.txt.'])

part('U1','SN74LVC2G126DCUR','SN74LVC2G126DCUR','Texas Instruments',
     'Package_SO:VSSOP-8_2.3x2mm_P0.5mm',
     {1:'LOGIC_READY',2:'STEP_IN',3:'DIR_BUF',4:'GND',5:'DIR_IN',6:'STEP_BUF',7:'LOGIC_READY',8:'V_LOGIC'},
     {1:'1OE',2:'1A',3:'2Y',4:'GND',5:'2A',6:'1Y',7:'2OE',8:'VCC'},
     {1:'input',2:'input',3:'tri_state',4:'power_in',5:'input',6:'tri_state',7:'input',8:'power_in'},'buffer',
     'https://www.ti.com/lit/ds/symlink/sn74lvc2g126.pdf')
part('U2','SN74LVC1G126DCKR','SN74LVC1G126DCKR','Texas Instruments',
     'Package_TO_SOT_SMD:SOT-353_SC-70-5',
     {1:'LOGIC_READY',2:'EN_IN',3:'GND',4:'EN_BUF',5:'V_LOGIC'},
     {1:'OE',2:'A',3:'GND',4:'Y',5:'VCC'},
     {1:'input',2:'input',3:'power_in',4:'tri_state',5:'power_in'},'buffer',
     'https://www.ti.com/lit/ds/symlink/sn74lvc1g126.pdf')
part('U3','TPS3839G33DBZR','TPS3839G33DBZR','Texas Instruments',
     'Package_TO_SOT_SMD:SOT-23',
     {1:'GND',2:'LOGIC_READY',3:'V_LOGIC'},
     {1:'GND',2:'RESET_N',3:'VDD'},{1:'power_in',2:'output',3:'power_in'},'supervisor',
     'https://www.ti.com/lit/ds/symlink/tps3839.pdf',
     ['3.08V nominal reset threshold, push-pull active-low output,200ms typical release delay.',
      'RESET_N high permits active-high OE; low tri-states buffers; gate pulldowns turn sinks off.',
      'Valid reset specified above0.6V. This is power qualification, not machine safety or no-pulse proof.'])
for idx,signal,output in [(1,'STEP','PUL_MINUS'),(2,'DIR','DIR_MINUS'),(3,'EN','ENA_MINUS')]:
    part(f'Q{idx}','NX6008NBKW','NX6008NBKW,115','Nexperia',
         'Package_TO_SOT_SMD:SOT-323_SC-70',
         {1:f'{signal}_GATE',2:'GND',3:output},
         {1:'G',2:'S',3:'D'},{1:'input',2:'passive',3:'passive'},'nmos',
         'https://assets.nexperia.com/documents/data-sheet/NX6008NBKW.pdf',
         ['60V open-drain sink; not differential driver and not isolated.',
          'Normal proposed load20mA max/channel; physical levels/timing not qualified.'])

for n,signal in [(1,'STEP'),(2,'DIR'),(3,'EN')]:
    resistor(f'R{n}','220R 1%','RC0603FR-07220RL',signal,f'{signal}_IN')
resistor('R4','100k 1%','RC0603FR-07100KL','STEP_IN','GND')
resistor('R5','100k 1%','RC0603FR-07100KL','DIR_IN','GND')
resistor('R6','10k 1%','RC0603FR-0710KL','HOST_VIO','EN_IN')
resistor('R7','100k 1%','RC0603FR-07100KL','EN_IN','GND')
for n,signal in [(8,'STEP'),(9,'DIR'),(10,'EN')]:
    resistor(f'R{n}','220R 1%','RC0603FR-07220RL',f'{signal}_BUF',f'{signal}_GATE')
for n,signal in [(11,'STEP'),(12,'DIR'),(13,'EN')]:
    resistor(f'R{n}','10k 1%','RC0603FR-0710KL',f'{signal}_GATE','GND')
resistor('R14','100k 1%','RC0603FR-07100KL','LOGIC_READY','GND')
resistor('R15','10k 1% 0.125W','RC0805FR-0710KL','COM_PLUS','GND',size='0805')
for ref in ['C1','C2','C3']: bypass(ref)
part('D1','PMEG6010CEH','PMEG6010CEH,115','Nexperia','Diode_SMD:D_SOD-123F',
     {1:'V5_SELECT',2:'V5_REG'},{1:'K',2:'A'},{1:'passive',2:'passive'},'schottky',
     'https://assets.nexperia.com/documents/data-sheet/PMEG6010CEH.pdf',
     ['Anode on5Vbuck; cathode onselector5Vthrow. Blocks chargedCOM returning to5Vbuck.',
      'Forward drop means cable5V mode is nominal5V signalling; calculate actual minimum loaded COM.'])
part('SW1','5V / EXT','EG1218','E-Switch','Adapter:E-Switch_EG1218_P040040',
     {1:'V5_SELECT',2:'COM_PLUS',3:'V_EXT_PROT'},
     {1:'5V',2:'COM',3:'EXT'},{1:'passive',2:'passive',3:'passive'},'switch_spdt',
     'https://spec_sheets.e-switch.com/specs/P040040.pdf',
     ['Manufacturer drawingP040040revC:0.2A30VDC,SPDT,NONSHORTING,three0.90mmdrills2.50mmpitch.',
      'Drawing depicts actuator-left and schematic1-2 closed but does not explicitly cross-reference mechanical state; physical direction remains unconfirmed.',
      'Continuity fixture must verify actual production slide position versus5V/EXTsilkscreen before use.',
      'Power off both host and external supply before selecting; ground is never switched.',
      'Body11.6x4.0mm,height5.4mm plus2mm actuator; pins4.7mm below body.'])

footprint = '''(footprint "E-Switch_EG1218_P040040"
 (version 20241229) (generator "OEA_r0_2_drawing_transcription") (layer "F.Cu")
 (descr "E-Switch EG1218 P040040 rev C; 0.2A30VDC nonshorting SPDT; exact manufacturer hole pattern; body11.6x4.0mm")
 (tags "EG1218 SPDT nonshorting 30V")
 (property "Reference" "SW1" (at 0 -3.0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
 (property "Value" "EG1218" (at 0 3.0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
 (attr through_hole)
 (fp_rect (start -5.8 -2) (end 5.8 2) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))
 (fp_rect (start -5.95 -2.15) (end 5.95 2.15) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS"))
 (fp_rect (start -6.3 -2.5) (end 6.3 2.5) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
 (fp_rect (start -2.25 -1) (end -0.25 1) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))
 (fp_line (start -2.5 -1.5) (end -2.5 -2) (stroke (width 0.15) (type default)) (layer "F.SilkS"))
 (pad "1" thru_hole rect (at -2.5 0) (size 1.8 1.8) (drill 0.9) (layers "*.Cu" "*.Mask"))
 (pad "2" thru_hole circle (at 0 0) (size 1.8 1.8) (drill 0.9) (layers "*.Cu" "*.Mask"))
 (pad "3" thru_hole circle (at 2.5 0) (size 1.8 1.8) (drill 0.9) (layers "*.Cu" "*.Mask"))
)
'''
(LIB/'E-Switch_EG1218_P040040.kicad_mod').write_text(footprint,encoding='utf-8')

spec=dict(schema_version=1,revision='r0.2',status='ENGINEERING CANDIDATE - NOT RELEASED',
          shared_nets=['V_LOGIC','V5_REG','V_EXT_PROT','GND','COM_PLUS','EXT_RAW'],
          logic_supply_v=3.3428,host_input_nominal_v=[3.3,5.0],input_abs_operating_max_v=5.5,
          proposed_output_channel_max_ma=20,proposed_output_aggregate_max_ma=60,
          selectors={'SW1':{'common':'2','5V':['1','2'],'EXT':['2','3'],'ground_switched':False,
                           'actuator_direction_verified':False,'actuator_direction_release_gate':'Physical continuity test against final silkscreen'}},
          parts=parts,
          physical_limitations=['15.24mm width retained; original20.32mm length not proven feasible.',
          'EG1218 body must clear host-header solder tails; likely needs DIR-end length extension.',
          'Bottom SMT maxheight and throughholetail-to-hostcomponent clearances require actual host geometry.',
          'No current host-revision qualification; no universalBTT/SKRfit claim.'],
          evidence_boundaries=['Manufacturer source inspection and exact schematic pin mapping only.',
          'No loaded timing,current,thermal,startup,EMC,physical assembly or safety validation.'])
(ROOT/'logic_spec.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
print(f'Wrote {len(parts)} logic/connector parts and verified-drawing switch footprint')
