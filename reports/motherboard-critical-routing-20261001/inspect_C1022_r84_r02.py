from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import xy,mm,segment_distance
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_populate_motherboard_pcb import write,sha
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb');OUT=Path('reports/motherboard-critical-routing-20261001/source26-r84-C1022-exact-blocker-review-r02');OUT.mkdir(parents=True,exist_ok=False)
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();f=next(x for x in b.GetFootprints()if x.GetReference()=='C1022');parts={x.GetReference():x for x in b.GetFootprints()};g=w.Geometry(b)
attachments=[]
for pad in f.Pads():
    touched=[]
    for t in b.GetTracks():
        layer=t.GetLayer();via=t.Type()==pcbnew.PCB_VIA_T
        if via:
            for layer in b.GetEnabledLayers().CuStack():
                if pad.IsOnLayer(layer)and t.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(pcbnew.SHAPE_CIRCLE(t.GetPosition(),t.GetWidth(layer)//2)):
                    touched.append(dict(uuid=t.m_Uuid.AsString(),type='via',net=t.GetNetname(),at=mm(t.GetPosition())));break
        elif pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(pcbnew.SEG(t.GetStart(),t.GetEnd()),t.GetWidth()//2):
            touched.append(dict(uuid=t.m_Uuid.AsString(),type='track',net=t.GetNetname(),start=mm(t.GetStart()),end=mm(t.GetEnd())))
    attachments.append(dict(pin=pad.GetNumber(),net=pad.GetNetname(),xy=mm(pad.GetPosition()),actual_pad_touching_Cu=touched))
neighbors=[dict(ref=r,xy=mm(x.GetPosition()),angle=x.GetOrientationDegrees(),layer=b.GetLayerName(x.GetLayer()))for r,x in parts.items()if x.GetLayer()==pcbnew.B_Cu and math.dist(mm(x.GetPosition()),mm(f.GetPosition()))<6]
write(OUT/'review.json',dict(base_sha256=sha(BASE),exact_C1022_pose=dict(xy=mm(f.GetPosition()),angle=f.GetOrientationDegrees(),layer=b.GetLayerName(f.GetLayer()),FPID=str(f.GetFPID().GetLibItemName())),native_pad_attachments=attachments,actual_nearby_backside_parts=neighbors,source_owned_target=dict(power='U1001.L6',returns=['U1001.K7','U1001.L8']),no_geometry_changed=True,manufacturing_ready=False));print(json.dumps(dict(attachments=attachments,neighbors=neighbors)))

