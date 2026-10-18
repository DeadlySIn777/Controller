"""Report-only finite native placement proposals; never saves or mutates an input PCB."""
import json
import math
from pathlib import Path
import sys
import pcbnew as p
from motherboard_mechanical_audit import ROOT, sha, xy, body_box, graphic_box, rect, overlap, grown, transform, transformed_box, segment_hit

board_path=ROOT/'reports/motherboard-pcb-integration-20260930/usb-locating-rule-r19/motherboard-populated-candidate.kicad_pcb'
out=ROOT/'reports/motherboard-mechanical-20260930/r19-finite-near-compute-proposal'
if (out/'proposal.json').exists():
    raise SystemExit('Use a new immutable receipt directory')
out.mkdir(parents=True,exist_ok=True)
before=sha(board_path)
b=p.LoadBoard(str(board_path))
fps={x.GetReference():x for x in b.GetFootprints()}
tracks=list(b.GetTracks())
proposal={
    'J19508':[60,10,180],       # Motor7: top edge in the existing free left window.
    'J19512':[450,289,90],      # Motor11: right edge below current motor10.
    'J19526':[192,330,0],       # PWM: bounded existing bottom gap after moving motor11.
    'J19528':[380,330,0],       # PEN1: away from ESP RF reservation.
    'J15005':[225,327.67,90],   # Upright USB-A, horizontal mouth towards bottom edge.
    'J15006':[245,336.325,0],
    'J15007':[264,320.22,0],    # Native body front; exact Würth datum still needs reconciliation.
    'J15004':[298,329.45,0],
    'J16001':[446,338.6,180],
    'J16002':[423.14,338.6,180],
}
oldposes={r:[*xy(fps[r].GetPosition()),fps[r].GetOrientationDegrees()]for r in proposal}
attached={}
for r in proposal:
    z=[]
    for pad in fps[r].Pads():
        for t in tracks:
            if t.GetStart()==pad.GetPosition() or t.GetEnd()==pad.GetPosition():
                z.append({'pad':pad.GetNumber(),'pad_net':pad.GetNetname(),'track_net':t.GetNetname(),
                          'uuid':t.m_Uuid.AsString(),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd()),
                          'same_actual_native_net_pass':pad.GetNetCode()==t.GetNetCode()})
    attached[r]=z
for r,(x,y,a)in proposal.items():
    fps[r].SetOrientationDegrees(a)
    fps[r].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))

def courtyard(f):
    return graphic_box(f,p.F_CrtYd) or body_box(f)[0]

def component_conflicts(f):
    r=courtyard(f)
    return [g.GetReference()for g in fps.values()if g.GetReference()!=f.GetReference()and courtyard(g)and overlap(grown(r,.15),courtyard(g))]

def copper_conflicts(f):
    ans=[]
    for pad in f.Pads():
        if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:
            # Locate holes clear all retained copper by .25 mm; same-net exemption does not apply.
            margin=.25
        else:
            margin=.15
        box=grown(rect(pad.GetBoundingBox()),margin)
        for t in tracks:
            if not overlap(box,rect(t.GetBoundingBox())):
                continue
            if pad.GetAttribute()!=p.PAD_ATTRIB_NPTH and pad.GetNetCode()==t.GetNetCode():
                continue
            layer=t.GetLayer()
            if isinstance(t,p.PCB_VIA):
                layer=p.F_Cu
            if not pad.IsOnLayer(layer):
                continue
            if pad.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),p.FromMM(margin)):
                ans.append({'pad':pad.GetNumber(),'net':pad.GetNetname(),'track_net':t.GetNetname(),
                            'uuid':t.m_Uuid.AsString(),'start':xy(t.GetStart()),'end':xy(t.GetEnd())})
    return ans

checks={r:{'new_pose':q,'old_pose':oldposes[r],'courtyard_mm':courtyard(fps[r]),
           'component_courtyard_conflicts':component_conflicts(fps[r]),
           'retained_foreign_track_pad_conflicts':copper_conflicts(fps[r]),
           'old_attached_endpoints':attached[r]}for r,q in proposal.items()}
print(json.dumps({'phase':'native proposal checks','conflicts':{r:{'component':v['component_courtyard_conflicts'],'copper':len(v['retained_foreign_track_pad_conflicts'])}for r,v in checks.items()}}),flush=True)
component_cache={r:courtyard(f)for r,f in fps.items()}
pad_cache=[(f.GetReference()+'.'+z.GetNumber(),rect(z.GetBoundingBox()))for f in fps.values()for z in f.Pads()]
track_cache=[(t.m_Uuid.AsString(),xy(t.GetStart()),xy(t.GetEnd()),p.ToMM(t.GetWidth())/2,rect(t.GetBoundingBox()))for t in tracks]

def nearest_rect_dist(pt,r):
    return math.hypot(max(r[0]-pt[0],0,pt[0]-r[2]),max(r[1]-pt[1],0,pt[1]-r[3]))

def mount_ok(x,y):
    pt=[x,y]
    # 8 mm metallic washer/tool disk (4 mm radius) plus .25 mm guard, no component/Cu contact.
    component=[r for r,box in component_cache.items()if box and nearest_rect_dist(pt,box)<4.25]
    copper=[]
    r=[x-4.25,y-4.25,x+4.25,y+4.25]
    for uuid,a,c,half_width,box in track_cache:
        if not overlap(r,box):
            continue
        dx,dy=c[0]-a[0],c[1]-a[1]
        n=0 if dx*dx+dy*dy==0 else max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
        if math.hypot(x-a[0]-n*dx,y-a[1]-n*dy)<4.25+half_width:
            copper.append(uuid)
    pads=[name for name,box in pad_cache if nearest_rect_dist(pt,box)<4.25]
    cm=transformed_box(fps['J15001'],[-3,-30,37,25])
    esp=transformed_box(fps['J16001'],[-1.27,-1.565,24.13,61.3])
    ant=grown(transformed_box(fps['J16001'],[2.48,-7.85,20.48,-1.54]),15)
    module=[name for name,box in [('CM',cm),('ESP',esp),('ESP_RF',ant)]if nearest_rect_dist(pt,box)<4.25]
    return {'components':component,'pads':pads,'tracks':copper,'modules':module}

anchors=[[6,6],[454,6],[454,334],[6,334],[230,6],[230,334]]
mounts=[]
for anchor in anchors:
    candidates=[]
    # Search bounded edge-adjacent patches, ranked by distance to intended support location.
    for x in [anchor[0]+i for i in range(-25,26)]:
        for y in [anchor[1]+i for i in range(-25,26)]:
            if not(5.1<=x<=454.9 and 5.1<=y<=334.9):
                continue
            if min(x,460-x,y,340-y)>20:
                continue
            candidates.append((math.hypot(x-anchor[0],y-anchor[1]),x,y))
    candidates.sort()
    selected=None
    for _,x,y in candidates:
        v=mount_ok(x,y)
        if not any(v.values()) and all(math.dist([x,y],a['center_mm'])>=12 for a in mounts if a.get('center_mm')):
            selected={'center_mm':[x,y],'drill_mm':3.2,'nearest_drill_edge_margin_mm':min(x,460-x,y,340-y)-1.6,
                      '8mm_washer_tool_disk_plus_p25guard_conflicts':v,
                      'filled_zone_keepout_or_insulating_standoff_required':True}
            break
    mounts.append({'anchor_mm':anchor,**(selected or {'center_mm':None,'no_clear_bounded_patch':True})})

receipt={'board_path':str(board_path),'board_sha256':before,'native_parts':len(fps),
         'read_only_input_sha256_unchanged':sha(board_path)==before,'native_in_RAM_proposals_only':True,
         'proposal_checks':checks,'M3_mount_candidates':mounts,
         'invariant_old_copper_count':len(tracks),
         'plane_refill_after_moves_required':True,'strict_native_DRC_not_run_on_unsaved_proposal':True,
         'engineering_gate':'0component and0retained-foreign-pad/track conflicts required before adoption; actual service/mate and 3D qualification still separate.'}
(out/'proposal.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
(out/'issued-search-tool.py').write_bytes(Path(__file__).read_bytes())
assert receipt['read_only_input_sha256_unchanged']
print(json.dumps({'conflicts':{r:{'component':v['component_courtyard_conflicts'],'copper':len(v['retained_foreign_track_pad_conflicts'])}for r,v in checks.items()},'mounts':[x.get('center_mm')for x in mounts]}))
