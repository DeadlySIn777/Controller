"""Publish a reproducible MC circuit placement proposal; no copper or fab files."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'hardware/board_review'


def build():
    old=json.loads((REVIEW/'revisions/20260930-03/board-view.json').read_text(encoding='utf-8'))
    mapping=json.loads((ROOT/'hardware/motion_card/assembly-map.json').read_text(encoding='utf-8'))['blocks']
    model=json.loads((ROOT/'hardware/motion_card/design.json').read_text(encoding='utf-8'))
    core=old['boards'][0]
    positions={mapping['fpga_core']['references'][c['reference']]:[c['x_mm'],c['y_mm'],c['rotation_deg']] for c in core['components']}
    # Separate watchdog channels; service/permission logic occupies the lower band.
    wd={'U1':[158,21],'U2':[184,21],'U3':[149,21],'U4':[175,21],'U5':[205,22],
        'U6':[157,34],'U7':[183,34],
        'C1':[159,15],'C2':[185,15],'C3':[154,15],'C4':[180,15],
        'C5':[149,16],'C6':[175,16],'C7':[205,17],'C8':[156,29],'C9':[182,29],
        'R1':[163,21,90],'R2':[189,21,90],
        'R3':[149,28],'R4':[163,34],'R5':[149,34],'R6':[162,15],
        'R7':[175,28],'R8':[189,34],'R9':[175,34],'R10':[188,15],
        'R11':[157,39],'R12':[183,39],'R13':[201,34]}
    positions.update({mapping['watchdog_conditioning']['references'][r]:p for r,p in wd.items()})
    for i in range(1,20):
        col,row=(i-1)%7,(i-1)//7
        x,y=151+col*9.5,49+row*11
        positions[mapping['mc_permission']['references'][f'U{i}']]=[x,y]
        positions[mapping['mc_permission']['references'][f'C{i}']]=[x,y-4]
    # GPIO defaults/receiver pulls stay together for initial source review.
    refs=[r for r in mapping['mc_permission']['references'] if r.startswith('R')]
    for i,r in enumerate(refs):positions[mapping['mc_permission']['references'][r]]=[150+(i%9)*7,78+(i//9)*4]
    power_file=ROOT/'hardware/motion_card/local-power-placement.json'
    if not power_file.exists():raise ValueError('Source-reviewed local power placement is required')
    power=json.loads(power_file.read_text(encoding='utf-8'))
    positions.update({mapping['mc_local_power']['references'][r]:p for r,p in power['positions'].items()})
    motor=json.loads((ROOT/'hardware/motion_card/motor-placement.json').read_text(encoding='utf-8'))
    positions.update({mapping['mc_motor_buffers']['references'][r]:p for r,p in motor['positions'].items()})
    if set(positions)!=set(model['components']):raise ValueError('Placement missing/extra '+repr(set(positions)^set(model['components'])))
    spec={'id':'motion-card','title':'MC — integrated motion-card circuit candidate','source_block':'motion_card',
      'summary':'327 physical parts: FPGA core, local rails, dual watchdogs, permission latches and38 motor/TX Ioff paths. Circuit ERC passed; remaining interfaces, connectors, routing and qualification remain open.',
      'status':'Connected circuit / layout candidate','width_mm':220,'height_mm':100,'thickness_mm':1.6,
      'copper_layers':6,
      'assembly_reference_layer':'F.Fab',
      'layout_rules':{'clearance_mm':0.15,'signal_track_width_mm':0.2,
          'status':'low_voltage_layout_candidate_not_vendor_process_approval',
          'basis':'Selected VSSOP pads have 0.15mm gaps; PCBWay standard published trace/spacing floor is0.1mm. Power, BGA escape and final stackup need separate review.'},
      'outline_status':'220 × 100 mm proposed standing card. Six copper layers and 1.6 mm thickness are layout assumptions; stackup and fabrication process remain unqualified.',
      'zones':[
        {'x':7,'y':10,'width':51,'height':17,'label':'Local rail converters','kind':'new'},
        {'x':7,'y':30,'width':16,'height':48,'label':'Rail supervision','kind':'new'},
        {'x':24,'y':29,'width':37,'height':57,'label':'12-motor / TX Ioff buffers','kind':'new'},
        {'x':63,'y':10,'width':80,'height':68,'label':'FPGA core — sourced BGA pads','kind':'implemented'},
        {'x':145,'y':10,'width':68,'height':31,'label':'Dual watchdogs — conditioned','kind':'new'},
        {'x':145,'y':43,'width':68,'height':40,'label':'Permission / OPI / trip latches','kind':'new'},
        {'x':7,'y':88,'width':206,'height':8,'label':'P1 / P2, other Ioff, identity, SSR, restore — pending','kind':'pending'}],
      'positions':positions,'placement_only_footprints':{},
      'highlight':['U1001','U2001','U2002','U3001','U3002','U4014','U4015'],
      'previous_references':{new:old for old,new in mapping['fpga_core']['references'].items()},
      'open_work':[
        'Motor/TX Ioff source circuits are connected; other card-bound Ioff paths, presence filters, identity/temperature, slot-status register and flash restore remain absent.',
        'Bank-B buffer OE and OPI_BOE clear share one physical net; its upstream qualification and powered receiver enable pull-ups are not implemented here.',
        'P1/P2 connector gender/orientation correction is a proposed IS-2 change; native connector footprint, contact-to-net map and cage mechanics remain open.',
        'New output/progress/OPI/trip and full I/O GPIO allocation require a separate vendor FPGA fit. Existing six/two runtime is historical and incompatible with the new watchdog pulse contract.',
        'Power loops, BGA escape, plane assignment, loaded fault timing, EMC, thermal behavior and physical bring-up remain unqualified.',
        'Six-layer count is a layout candidate, not an approved stackup or a cost quote. No fabrication release.']}
    doc={'interface_spec':'C:/Users/Gluis/claude-worktrees/controller-interface-spec/docs/interface-spec/02-modules-and-boundaries.md','boards':[spec]}
    (REVIEW/'placement.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'parts':len(positions),'manufacturing_ready':False}))


if __name__=='__main__':build()
