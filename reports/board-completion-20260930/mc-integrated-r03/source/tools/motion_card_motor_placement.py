"""Pack source motor components around retained MC placement using native geometry.

Run with KiCad Python. This is a placement proposal, not a routed/qualified design.
Existing physical footprints are obstacles; their geometry is never moved.
"""
import hashlib
import json
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'hardware/board_review/revisions/20260930-06/motion-card-route-candidate.kicad_pcb'
OUT=ROOT/'hardware/motion_card/motor-placement.json'
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
REGION=(24.,29.,61.,86.)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rect(fp):
    b=fp.GetBoundingBox(False,False)
    return tuple(pcbnew.ToMM(v) for v in (b.GetX(),b.GetY(),b.GetRight(),b.GetBottom()))
def overlaps(a,b,gap=.15):
    return not (a[2]+gap<=b[0] or b[2]+gap<=a[0] or a[3]+gap<=b[1] or b[3]+gap<=a[1])
def inside(b):return b[0]>=REGION[0] and b[1]>=REGION[1] and b[2]<=REGION[2] and b[3]<=REGION[3]


def main():
    model_path=ROOT/'hardware/mc_motor_buffers/design.json'
    model=json.loads(model_path.read_text())
    original={str(BASE.relative_to(ROOT)):sha(BASE),str(model_path.relative_to(ROOT)):sha(model_path)}
    board=pcbnew.LoadBoard(str(BASE)); occupied=[rect(f) for f in board.GetFootprints()]
    fixed_count=len(occupied); positions={}; envelopes={}; anchors={}; native_ics={}; fitted={}
    preferred={'U1':(33,36),'U2':(50,36),'U3':(33,53),'U4':(50,53),
               'U5':(28,69),'U6':(38,69),'U7':(47,76),'U8':(57,76),
               'U9':(28,80),'U10':(38,80),'U11':(47,83)}
    path_by_net={n:p for p in model['paths'] for n in (p['input'],p['raw'],p['output'])}
    order=sorted((r for r,c in model['components'].items() if c.get('physical',False)),
                 key=lambda r:('UCR'.index(r[0]),int(r[1:])))
    grid=[(x/2,y/2) for x in range(49,122) for y in range(59,172)]
    for ref in order:
        part=model['components'][ref]
        if not part.get('physical',False):continue
        lib,name=part['footprint'].split(':')
        fp=pcbnew.FootprintLoad(str(LIB/(lib+'.pretty')),name)
        if fp is None:raise ValueError('Missing source footprint '+ref)
        angle=0
        if ref.startswith('U'):target=preferred[ref]
        elif ref.startswith('C'):
            owner='U'+ref[1:];ic=native_ics[owner]
            pin=next(p for p in ic.Pads() if model['components'][owner]['pins'].get(p.GetNumber())=='IO_3V3')
            px,py=(pcbnew.ToMM(v) for v in pin.GetPosition())
            side=1 if px>=anchors[owner][0] else -1
            target=(px+2*side,py);angle=0 if side==1 else 180
        else:
            net=next((n for n in part['pins'].values() if n in path_by_net),None)
            path=path_by_net.get(net)
            center=anchors[path['buffer_ref'] if path else 'U5']
            if 'series' in part['role']:
                ic=native_ics[path['buffer_ref']]
                pin=next(p for p in ic.Pads() if p.GetNumber()==path['output_pin'])
                px,py=(pcbnew.ToMM(v) for v in pin.GetPosition())
                side=1 if px>=center[0] else -1
                target=(px+2*side,py);angle=0 if side==1 else 180
            else:target=(center[0]-6,center[1]+((int(ref[1:])%5)-2)*2)
        fp.SetOrientationDegrees(angle)
        candidates=sorted(set(grid+[target]),key=lambda xy:((xy[0]-target[0])**2+(xy[1]-target[1])**2,xy[1],xy[0]))
        chosen=None
        for x,y in candidates:
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
            b=rect(fp)
            if inside(b) and not any(overlaps(b,z) for z in occupied):
                chosen=(x,y);occupied.append(b);envelopes[ref]=b;break
        if chosen is None:raise ValueError('No geometric placement for '+ref)
        positions[ref]=[*chosen,angle];fitted[ref]=fp
        if ref.startswith('U'):anchors[ref]=chosen;native_ics[ref]=fp
    if len(positions)!=124:raise ValueError('Motor block inventory differs')
    if any(sha(ROOT/p)!=h for p,h in original.items()):raise ValueError('Input changed during placement')
    distances=[]
    for path in model['paths']:
        output=next(p for p in native_ics[path['buffer_ref']].Pads() if p.GetNumber()==path['output_pin'])
        series=next(p for p in fitted[path['series_ref']].Pads() if p.GetNumber()=='1')
        distance=((output.GetPosition().x-series.GetPosition().x)**2+(output.GetPosition().y-series.GetPosition().y)**2)**.5/1e6
        distances.append({'raw':path['raw'],'series':path['series_ref'],'pad_to_pad_minimum_mm':distance})
    result={'schema_version':1,'revision':'motor-placement-r0.2-pad-anchored',
        'scope':'Native source footprint-envelope placement proposal, all retained203 parts fixed; source-series/caps target actual output/VCC pads',
        'positions':positions,'native_envelopes_mm':envelopes,'region_mm':REGION,'minimum_envelope_gap_mm':.15,
        'source_sha256':original,'fixed_existing_footprints':fixed_count,'parts':len(positions),
        'series_distances':distances,'signal_integrity_qualified':False,'manufacturing_ready':False}
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'motor_parts_placed':len(positions),'existing_parts_retained':fixed_count,'output':str(OUT)}))


if __name__=='__main__':main()
