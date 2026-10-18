"""Build r0.2 engineering candidate from exported native schematic and placement.

This file is confined to this adapter revision. Routing and qualification are
separate steps. A generated file is never evidence of a passed check.
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import pcbnew as p

ROOT = Path(__file__).resolve().parent
LIB = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
OFF = (100.,100.)

def vec(x,y): return p.VECTOR2I(p.FromMM(x+OFF[0]),p.FromMM(y+OFF[1]))
def local(pos): return [round(p.ToMM(pos.x)-OFF[0],5),round(p.ToMM(pos.y)-OFF[1],5)]

def build():
    data=json.loads((ROOT/'parts.json').read_text())
    parts=data['parts']
    if isinstance(parts,list): parts={v['reference']:v for v in parts}
    layout=json.loads((ROOT/'placement.json').read_text())
    placement=layout['parts']; width,height=layout['board_mm']; layers=layout['layers']
    assert set(placement)==set(parts), 'Every physical part requires an explicit placement'
    native=ET.parse(ROOT/'adapter.net.xml').getroot()
    pin_nets={(n.attrib['ref'],n.attrib['pin']):net.attrib['name']
        for net in native.findall('./nets/net') for n in net.findall('node')}
    board=p.BOARD();board.SetCopperLayerCount(layers)
    board.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    nets={}
    for name in sorted(set(pin_nets.values())):
        net=p.NETINFO_ITEM(board,name);board.Add(net);nets[name]=net
    fps={};pads=[]
    for ref,spec in parts.items():
        lib,name=spec['footprint'].split(':')
        folder=ROOT/(lib+'.pretty') if (ROOT/(lib+'.pretty')).exists() else LIB/(lib+'.pretty')
        fp=p.FootprintLoad(str(folder),name)
        if fp is None: raise RuntimeError(spec['footprint'])
        fp.SetReference(ref);fp.SetValue(spec['value'])
        fp.SetField('MPN',spec['mpn']);fp.SetField('Manufacturer',spec['manufacturer'])
        fp.SetFPID(p.LIB_ID(lib,name));fp.SetPath(p.KIID_PATH('/'+data['root_uuid']+'/'+spec['uuid']))
        fp.SetSheetfile('adapter.kicad_sch')
        x,y,angle,side=placement[ref]
        fp.SetPosition(vec(x,y));board.Add(fp)
        if side=='bottom': fp.Flip(vec(x,y),False)
        fp.SetOrientationDegrees(fp.GetOrientationDegrees()+angle)
        for edit in layout.get('footprint_silk_edits',[]):
            if edit['reference'] != ref: continue
            matched=0
            for graphic in fp.GraphicalItems():
                if graphic.GetLayer()!=p.F_SilkS or not hasattr(graphic,'GetStart'): continue
                a,b=local(graphic.GetStart()),local(graphic.GetEnd())
                if all(abs(a[i]-edit['start'][i])<.001 and abs(b[i]-edit['end'][i])<.001 for i in range(2)):
                    graphic.SetLayer(p.Dwgs_User);matched+=1
            assert matched==1, f'Expected one explicit silkscreen segment for {ref}'
        for field in fp.GetFields(): field.SetVisible(False)
        fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
        for model in fp.Models():
            model.m_Filename=model.m_Filename.replace('${KICAD10_3DMODEL_DIR}',
                'C:/Program Files/KiCad/10.0/share/kicad/3dmodels')
        for pad in fp.Pads():
            name=pin_nets.get((ref,pad.GetNumber()))
            if name: pad.SetNet(nets[name])
            bb=pad.GetBoundingBox()
            pads.append(dict(ref=ref,pin=pad.GetNumber(),xy=local(pad.GetPosition()),net=pad.GetNetname(),
                layer=side,size=[p.ToMM(pad.GetSizeX()),p.ToMM(pad.GetSizeY())],
                bounding_box=[p.ToMM(bb.GetLeft())-100,p.ToMM(bb.GetTop())-100,
                    p.ToMM(bb.GetRight())-100,p.ToMM(bb.GetBottom())-100],
                drill_mm=p.ToMM(pad.GetDrillSizeX()),attribute=int(pad.GetAttribute())))
        fps[ref]=fp
    for a,b in [((0,0),(width,0)),((width,0),(width,height)),((width,height),(0,height)),((0,height),(0,0))]:
        line=p.PCB_SHAPE();line.SetShape(p.SHAPE_T_SEGMENT);line.SetStart(vec(*a));line.SetEnd(vec(*b))
        line.SetWidth(p.FromMM(.05));line.SetLayer(p.Edge_Cuts);board.Add(line)
    layer_ids={'F.Cu':p.F_Cu,'B.Cu':p.B_Cu,'In1.Cu':p.In1_Cu,'In2.Cu':p.In2_Cu,
        'F.SilkS':p.F_SilkS,'B.SilkS':p.B_SilkS,'Dwgs.User':p.Dwgs_User}
    for spec in layout.get('texts',[]):
        t=p.PCB_TEXT(board);t.SetText(spec['text']);t.SetPosition(vec(*spec['xy']))
        size=spec.get('size',.8);t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)))
        t.SetTextThickness(p.FromMM(.12));lid=layer_ids[spec.get('layer','F.SilkS')];t.SetLayer(lid)
        t.SetTextAngle(p.EDA_ANGLE(spec.get('angle',0),p.DEGREES_T))
        if lid==p.B_SilkS:t.SetMirrored(True)
        board.Add(t)
    routepath=ROOT/'routes.json'
    routes=json.loads(routepath.read_text()) if routepath.exists() else []
    for route in routes:
        name=route['net'];name=name if name in nets else '/'+name
        for a,b in zip(route['points'],route['points'][1:]):
            tr=p.PCB_TRACK(board);tr.SetStart(vec(*a));tr.SetEnd(vec(*b))
            tr.SetWidth(p.FromMM(route.get('width',.15)));tr.SetLayer(layer_ids[route.get('layer','F.Cu')])
            tr.SetNet(nets[name]);board.Add(tr)
        for xy in route.get('vias',[]):
            via=p.PCB_VIA(board);via.SetPosition(vec(*xy));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3))
            via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH)
            via.SetFrontTentingMode(p.TENTING_MODE_TENTED);via.SetBackTentingMode(p.TENTING_MODE_TENTED)
            via.SetNet(nets[name]);board.Add(via)
    # In1 is the continuous ground reference. In2 also carries signal crossings
    # and has a grounded copper fill. Native filled-zone connectivity is checked.
    gnd=next(nets[n] for n in ('/GND','GND') if n in nets)
    for lid in ([p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu] if layers==4 else [p.F_Cu,p.B_Cu]):
        zone=p.ZONE(board);zone.SetLayer(lid);zone.SetNet(gnd);zone.SetZoneName('GND return')
        zone.SetLocalClearance(p.FromMM(.15));zone.SetMinThickness(p.FromMM(.15))
        zone.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL)
        zone.SetThermalReliefGap(p.FromMM(.2));zone.SetThermalReliefSpokeWidth(p.FromMM(.25))
        zone.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
        polygon=zone.Outline();polygon.NewOutline()
        for x,y in ((.25,.25),(width-.25,.25),(width-.25,height-.25),(.25,height-.25)):
            pos=vec(x,y);polygon.Append(pos.x,pos.y)
        board.Add(zone)
    board.GetDesignSettings().SetAuxOrigin(vec(0,height))
    p.SaveBoard(str(ROOT/'adapter.kicad_pcb'),board)
    pp=ROOT/'adapter.kicad_pro';pro=json.loads(pp.read_text()) if pp.exists() else {}
    ds=pro.setdefault('board',{}).setdefault('design_settings',{})
    ds.setdefault('rules',{}).update(min_clearance=.10,min_track_width=.15,min_via_diameter=.6,
        min_through_hole_diameter=.3,min_copper_edge_clearance=.25,min_hole_clearance=.25,
        min_silk_clearance=.1,min_text_height=.8,min_text_thickness=.1)
    for key in ('missing_courtyard','track_not_centered_on_via','tuning_profile_track_geometries',
                'footprint_filters_mismatch','footprint_type_mismatch'):
        ds.setdefault('rule_severities',{})[key]='warning'
    classes=pro.setdefault('net_settings',{}).setdefault('classes',[])
    if not classes:classes.append(dict(name='Default'))
    for c in classes:
        if c['name']=='Default':c.update(clearance=.15,track_width=.15,via_diameter=.6,via_drill=.3)
    pp.write_text(json.dumps(pro,indent=2)+'\n')
    (ROOT/'pad_coordinates.json').write_text(json.dumps(pads,indent=2)+'\n')
    print(f'Saved {len(fps)} parts; {len(nets)} nets; {len(board.GetTracks())} copper objects; native checks pending')

if __name__=='__main__':build()
