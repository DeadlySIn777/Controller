"""Build the isolated engineering candidate. Does not release fabrication files.

Run with the KiCad bundled Python. Pin/net data comes from the native schematic
generator's parts.json, never from the unrelated controller motherboard.
"""
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET
import pcbnew as p

ROOT = Path(__file__).resolve().parent
LIB = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
OFF = (100.0, 100.0)

def vec(x, y):
    return p.VECTOR2I(p.FromMM(x + OFF[0]), p.FromMM(y + OFF[1]))

def local(pos):
    return (p.ToMM(pos.x)-OFF[0], p.ToMM(pos.y)-OFF[1])

def build():
    data = json.loads((ROOT/'parts.json').read_text())
    parts = data['parts']
    if isinstance(parts, list):
        parts = {v['reference']:v for v in parts}
    board = p.BOARD()
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    native = ET.parse(ROOT/'adapter.net.xml').getroot()
    pin_nets = {}
    for net in native.findall('./nets/net'):
        for node in net.findall('node'):
            pin_nets[(node.attrib['ref'],node.attrib['pin'])] = net.attrib['name']
    nets = {}
    for name in sorted(set(pin_nets.values())):
        net = p.NETINFO_ITEM(board, name)
        board.Add(net)
        nets[name] = net
    placement = {
        'J1': (1.27,1.27,0,True),
        # Right row intentionally starts one pitch below VM: no VM metal.
        'J2': (13.97,3.81,0,True),
        'J3': (7.62,3.1,-90,False),
        'U1': (7.62,16.0,0,False),
        'R1': (3.0,15.4,90,False),
        'R2': (3.0,18.7,90,False),
        'R3': (2.95,3.5,90,False),
        'R4': (2.95,12.05,90,False),
        'R5': (11.4,18.0,90,False),
        'R6': (2.95,7.0,90,False),
        'C1': (11.4,14.3,90,False),
        'C2': (11.7,9.6,90,False),
    }
    fps = {}
    pads = {}
    for ref, spec in parts.items():
        lib,name = spec['footprint'].split(':')
        folder = ROOT/(lib+'.pretty') if (ROOT/(lib+'.pretty')).exists() else LIB/(lib+'.pretty')
        fp = p.FootprintLoad(str(folder),name)
        if fp is None:
            raise RuntimeError(spec['footprint'])
        fp.SetReference(ref)
        fp.SetValue(spec['value'])
        fp.SetField('MPN',spec['mpn'])
        fp.SetField('Manufacturer',spec['manufacturer'])
        fp.SetFPID(p.LIB_ID(lib,name))
        fp.SetPath(p.KIID_PATH('/'+data['root_uuid']+'/'+spec['uuid']))
        fp.SetSheetfile('adapter.kicad_sch')
        x,y,angle,bottom = placement[ref]
        fp.SetPosition(vec(x,y))
        board.Add(fp)
        if bottom:
            fp.Flip(vec(x,y),False)
        fp.SetOrientationDegrees(fp.GetOrientationDegrees()+angle)
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        for field in fp.GetFields():
            field.SetVisible(False)
        # Keep library 3D models but use an explicit local installation path.
        for model in fp.Models():
            model.m_Filename = model.m_Filename.replace('${KICAD10_3DMODEL_DIR}',
                'C:/Program Files/KiCad/10.0/share/kicad/3dmodels')
        for pad in fp.Pads():
            key = (ref,pad.GetNumber())
            pads[key] = pad
            net_name = pin_nets.get(key)
            if net_name and net_name in nets:
                pad.SetNet(nets[net_name])
        fps[ref] = fp

    for a,b in [((0,0),(15.24,0)),((15.24,0),(15.24,20.32)),
                ((15.24,20.32),(0,20.32)),((0,20.32),(0,0))]:
        line = p.PCB_SHAPE()
        line.SetShape(p.SHAPE_T_SEGMENT)
        line.SetStart(vec(*a)); line.SetEnd(vec(*b))
        line.SetWidth(p.FromMM(.05)); line.SetLayer(p.Edge_Cuts); board.Add(line)

    def text(s,x,y,size=.65,layer=p.F_SilkS,angle=0):
        item = p.PCB_TEXT(board); item.SetText(s); item.SetPosition(vec(x,y))
        item.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)))
        item.SetTextThickness(p.FromMM(.12)); item.SetLayer(layer)
        item.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T))
        if layer == p.B_SilkS:
            item.SetMirrored(True)
        board.Add(item)
    text('EN',3.2,1.0,.8)
    text('5V ONLY',7.6,19.3,.8)
    text('EA r0.1',7.6,13.9,.8)
    text('REVIEW',10.8,7.0,.8,p.B_SilkS,90)
    text('NOT RELEASED',4.8,7.0,.8,p.B_SilkS,90)
    text('1:+5 2:P-',7.6,14.2,.8,p.B_SilkS)
    text('3:D- 4:E-',7.6,16.2,.8,p.B_SilkS)

    # Explicit routes are saved in board coordinates local to the outline.
    routes_path = ROOT/'routes.json'
    if routes_path.exists():
        routes = json.loads(routes_path.read_text())
        for route in routes:
            name = route['net']
            if name not in nets and '/'+name in nets:
                name = '/'+name
            points = route['points']
            layer = p.F_Cu if route.get('layer','F.Cu')=='F.Cu' else p.B_Cu
            for a,b in zip(points,points[1:]):
                tr = p.PCB_TRACK(board); tr.SetStart(vec(*a));tr.SetEnd(vec(*b))
                tr.SetWidth(p.FromMM(route.get('width',.2))); tr.SetLayer(layer)
                tr.SetNet(nets[name]);board.Add(tr)
            for xy in route.get('vias',[]):
                via = p.PCB_VIA(board); via.SetPosition(vec(*xy))
                via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3))
                via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH)
                via.SetFrontTentingMode(p.TENTING_MODE_TENTED)
                via.SetBackTentingMode(p.TENTING_MODE_TENTED)
                via.SetNet(nets[name]);board.Add(via)
    # Both faces provide a real copper return. No isolated islands are retained.
    for layer in (p.F_Cu,p.B_Cu):
        zone = p.ZONE(board);zone.SetLayer(layer);zone.SetNet(nets['/GND'])
        zone.SetZoneName('Ground return')
        zone.SetLocalClearance(p.FromMM(.15));zone.SetMinThickness(p.FromMM(.15))
        zone.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL)
        zone.SetThermalReliefGap(p.FromMM(.2));zone.SetThermalReliefSpokeWidth(p.FromMM(.25))
        zone.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
        outline = zone.Outline();outline.NewOutline()
        for x,y in ((.25,.25),(14.99,.25),(14.99,20.07),(.25,20.07)):
            q = vec(x,y);outline.Append(q.x,q.y)
        board.Add(zone)
    board.GetDesignSettings().SetAuxOrigin(vec(0,20.32))
    p.SaveBoard(str(ROOT/'adapter.kicad_pcb'),board)
    # SaveBoard writes project defaults for a newly constructed BOARD. Restore
    # the intended explicit rules afterward; never suppress any reported issue.
    pro_path = ROOT/'adapter.kicad_pro'
    pro = json.loads(pro_path.read_text()) if pro_path.exists() else {}
    rules = pro.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{})
    rules.update(min_clearance=.15,min_track_width=.15,min_via_diameter=.6,
        min_through_hole_diameter=.3,min_copper_edge_clearance=.25,
        min_hole_clearance=.25,min_silk_clearance=.1,
        min_text_height=.8,min_text_thickness=.1)
    pro.setdefault('erc',{}).setdefault('rule_severities',{}).update(
        single_global_label='warning',four_way_junction='warning',
        simulation_model_issue='warning',footprint_filter='warning')
    drc = pro['board']['design_settings'].setdefault('rule_severities',{})
    for key in ('missing_courtyard','track_not_centered_on_via',
                'tuning_profile_track_geometries','footprint_filters_mismatch','footprint_type_mismatch'):
        drc[key]='warning'
    classes = pro.setdefault('net_settings',{}).setdefault('classes',[])
    if not classes:
        classes.append(dict(name='Default'))
    for c in classes:
        if c['name']=='Default':c.update(clearance=.15,track_width=.15,via_diameter=.6,via_drill=.3)
    pro_path.write_text(json.dumps(pro,indent=2)+'\n')
    coords = {f'{ref}.{num}':{'xy':[round(n,4) for n in local(pad.GetPosition())],
        'net':pad.GetNetname(),'layer':'B.Cu' if fps[ref].GetLayer()==p.B_Cu else 'F.Cu',
        'size':[p.ToMM(pad.GetSizeX()),p.ToMM(pad.GetSizeY())]}
        for (ref,num),pad in pads.items()}
    (ROOT/'pad_coordinates.json').write_text(json.dumps(coords,indent=2)+'\n')
    print(f'Saved candidate: {len(fps)} footprints, {len(nets)} nets, {len(board.GetTracks())} track/via objects')

if __name__=='__main__':
    build()
