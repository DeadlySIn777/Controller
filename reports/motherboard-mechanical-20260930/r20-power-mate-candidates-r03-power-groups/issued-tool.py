"""Read-only finite poses with whole 1757019 plug and service corridors clear."""
import json,math
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,overlap,grown,body_box,graphic_box,transformed_box

path=ROOT/'reports/motherboard-power-entry-20260930/layout-r05/full-board-fit-r02/power-groups-geometry-candidate.kicad_pcb'
out=ROOT/'reports/motherboard-mechanical-20260930/r20-power-mate-candidates-r03-power-groups'
if (out/'review.json').exists():raise SystemExit('Use new immutable receipt')
out.mkdir(exist_ok=True,parents=True);before=sha(path);b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()};tracks=list(b.GetTracks())
refs=['J11006','J11001','J11002','J11003','J11004','J11005']
for ref,pose in {'J19508':[55.5,6,180],'J19512':[454,289,90],'J19526':[192,330,0],'J19528':[387,333,0],'J15005':[225,327.67,90],'J15006':[245,336.325,0],'J15007':[274.4,321.7,0],'J15004':[310,329.45,0],'J16001':[446,338.6,180],'J16002':[423.14,338.6,180]}.items():
    f=fps[ref];f.SetOrientationDegrees(pose[2]);f.SetPosition(p.VECTOR2I(p.FromMM(pose[0]),p.FromMM(pose[1])))
objects={f.GetReference():(graphic_box(f,p.F_CrtYd)or body_box(f)[0])for f in fps.values()if f.GetReference()not in refs}
objects.update({'CM_MODULE':transformed_box(fps['J15001'],[-3,-30,37,25]),'ESP_MODULE':transformed_box(fps['J16001'],[-1.27,-1.565,24.13,61.3]),'ESP_RF':grown(transformed_box(fps['J16001'],[2.48,-7.85,20.48,-1.54]),15)})
selected={};old_contacts={};newchecks={}
bins={}
def rebuild_bins():
    bins.clear()
    for name,box in objects.items():
        if not box:continue
        for x in range(math.floor(box[0]/10),math.floor(box[2]/10)+1):
            for y in range(math.floor(box[1]/10),math.floor(box[3]/10)+1):bins.setdefault((x,y),set()).add(name)
def query(box):
    found=set()
    for x in range(math.floor(box[0]/10),math.floor(box[2]/10)+1):
        for y in range(math.floor(box[1]/10),math.floor(box[3]/10)+1):found.update(bins.get((x,y),()))
    return found
rebuild_bins()
def boxes(f):
    # Full plug dimensions are wholly reserved beyond the header mouth. Actual
    # insertion overlap only shrinks this conservative external reservation.
    return {'header':graphic_box(f,p.F_CrtYd)or body_box(f)[0],
            'full_plug':transformed_box(f,[-2.54,10,7.62,28.3]),
            'withdraw_wire_service':transformed_box(f,[-3.54,28.3,8.62,48.3])}
def clashes(f):
    q=boxes(f);return {n:[r for r in query(grown(box,.25))if overlap(grown(box,.25),objects[r])]for n,box in q.items()}
def copper(f):
    ans=[]
    for z in f.Pads():
        for t in tracks:
            if z.GetNetCode()==t.GetNetCode()or not overlap(grown(rect(z.GetBoundingBox()),.15),rect(t.GetBoundingBox())):continue
            layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
            if z.IsOnLayer(layer)and z.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),p.FromMM(.15)):
                ans.append({'pad':z.GetNumber(),'uuid':t.m_Uuid.AsString(),'track_net':t.GetNetname()})
    return ans
for r in refs:
    f=fps[r];old=[*xy(f.GetPosition()),f.GetOrientationDegrees()];seen={}
    for z in f.Pads():
        for t in tracks:
            layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
            if z.IsOnLayer(layer)and overlap(rect(z.GetBoundingBox()),rect(t.GetBoundingBox()))and z.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),0):
                seen[t.m_Uuid.AsString()]={'pad':z.GetNumber(),'net':t.GetNetname(),'same_native_net':z.GetNetCode()==t.GetNetCode(),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd())}
    old_contacts[r]=seen
    original={n:v for n,v in clashes(f).items()};candidates=[]
    for x in range(math.floor(old[0]-65),math.ceil(old[0]+65)+1):
        for y in range(math.floor(old[1]-65),math.ceil(old[1]+65)+1):
            if not(3<=x<=457 and 3<=y<=337):continue
            for a in [0,90,180,270]:
                candidates.append((math.dist([x,y],old[:2])+(0 if a==old[2] else 2),x,y,a))
    candidates.sort();chosen=None
    for score,x,y,a in candidates:
        f.SetOrientationDegrees(a);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
        qs=boxes(f)
        # All header copper stays well inside the profile; service may extend
        # outside the board, as ordinary panel-facing connector access does.
        if any(q[0]<.5 or q[1]<.5 or q[2]>459.5 or q[3]>339.5 for q in [rect(z.GetBoundingBox())for z in f.Pads()]):continue
        cs=clashes(f)
        if any(cs.values()):continue
        cu=copper(f)
        if cu:continue
        chosen={'original_pose':old,'new_pose':[x,y,a],'ranked_displacement_score':score,'component_conflicts':cs,'foreign_copper_conflicts':cu,'envelopes_mm':qs,'original_component_conflicts':original};break
    if chosen is None:
        f.SetOrientationDegrees(old[2]);f.SetPosition(p.VECTOR2I(p.FromMM(old[0]),p.FromMM(old[1])));chosen={'original_pose':old,'new_pose':None,'bounded_search_not_closed':True,'original_component_conflicts':original}
    selected[r]=chosen
    for name,box in boxes(f).items():objects[r+'_'+name]=box
    rebuild_bins()
    print(json.dumps({r:chosen}),flush=True)
receipt={'native_board':str(path),'sha256':before,'input_unchanged':sha(path)==before,'native_parts':len(fps),'native_tracks_vias':len(tracks),
         'manufacturer_header':'1757242','manufacturer_plug':'1757019','poses':selected,'old_actual_attached_copper':old_contacts,
         'method':'All full18.3 mm plug-body projections and20 mm withdrawal/wire corridors clear every other native component courtyard by.25 mm. Whole plug beyond mouth is conservative; real insertion overlap can only reduce body reservation. No generic 3D fit claim.',
         'remaining':['A minimum15 mm mate-height reservation above its lowest datum and vertical screwdriver access must be included in the enclosure; exact relative assembled Z remains physical-fit qualification.',
                      'Customer wire bend radius and harness clamp depend on selected wire/ferrule; the20 mm withdrawal corridor is an engineering allowance, not a universal cable rating.',
                      'Any attached native copper must be handled by exact UUID and rejoined after root moves; all zones must refill and native DRC rerun.',
                      'No source, PCB or public CAD was saved or changed by this search.']}
(out/'review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes());assert receipt['input_unchanged']
