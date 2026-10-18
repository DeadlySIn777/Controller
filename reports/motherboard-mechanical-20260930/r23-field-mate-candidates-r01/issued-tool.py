"""Finite read-only placement search: whole mates plus withdrawal corridors."""
import json,math
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,overlap,grown,body_box,graphic_box,transformed_box

path=ROOT/'reports/motherboard-pcb-integration-20260930/mechanical-library-r23-r03/motherboard-mechanical-candidate.kicad_pcb'
recipe_path=ROOT/'reports/motherboard-power-entry-20260930/layout-r05/full-board-fit-r02/power-groups-geometry-candidate.kicad_pcb'
audit_path=ROOT/'reports/motherboard-mechanical-20260930/r23-all-field-mates-r01/review.json'
power_path=ROOT/'reports/motherboard-mechanical-20260930/r20-power-mate-candidates-r03-power-groups/review.json'
out=ROOT/'reports/motherboard-mechanical-20260930/r23-field-mate-candidates-r01'
assert not out.exists();out.mkdir();before=sha(path)
b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()};tracks=list(b.GetTracks())
recipe=p.LoadBoard(str(recipe_path));recipe_fps={f.GetReference():f for f in recipe.GetFootprints()}
for group in json.loads(recipe_path.with_name('placement-receipt.json').read_text())['groups']:
    for ref in group['refs']:
        fps[ref].SetPosition(recipe_fps[ref].GetPosition());fps[ref].SetOrientationDegrees(recipe_fps[ref].GetOrientationDegrees())
power=json.loads(power_path.read_text())
for ref,r in power['poses'].items():
    x,y,a=r['new_pose'];fps[ref].SetOrientationDegrees(a);fps[ref].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
audit=json.loads(audit_path.read_text());refs=['J19522','J19523','J19531','J19534','J19525','J19532','J19533']
objects={r:(graphic_box(f,p.F_CrtYd)or body_box(f)[0])for r,f in fps.items()if r not in refs}
objects.update({'CM_MODULE':transformed_box(fps['J15001'],[-3,-30,37,25]),'ESP_MODULE':transformed_box(fps['J16001'],[-1.27,-1.565,24.13,61.3]),'ESP_RF':grown(transformed_box(fps['J16001'],[2.48,-7.85,20.48,-1.54]),15)})
for ref,r in power['poses'].items():
    for kind,box in r['envelopes_mm'].items():objects[ref+'_'+kind]=box
for ref,r in audit['ports'].items():
    if ref in refs:continue
    for kind,box in r['envelopes_mm'].items():objects[ref+'_'+kind]=box
for i,(x,y)in enumerate([(6,13),(454,6),(454,320),(17,323),(230,17),(234,334)]):objects['M3_WASHER_'+str(i)]=[x-4.25,y-4.25,x+4.25,y+4.25]
bins={}
def rebuild():
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
rebuild()
def boxes(f):
    n=len(list(f.Pads()));return {'header':graphic_box(f,p.F_CrtYd)or body_box(f)[0],
        'full_plug':transformed_box(f,[-1.75,8,n*3.5-1.75,24.1]),
        'withdraw_wire_service':transformed_box(f,[-2.75,24.1,n*3.5-.75,44.1])}
def clashes(f):return {kind:sorted(r for r in query(grown(box,.25))if overlap(grown(box,.25),objects[r]))for kind,box in boxes(f).items()}
def copper(f):
    for pad in f.Pads():
        for t in tracks:
            if pad.GetNetCode()==t.GetNetCode()or not overlap(grown(rect(pad.GetBoundingBox()),.15),rect(t.GetBoundingBox())):continue
            layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
            if pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),p.FromMM(.15)):return True
    return False
selected={};contacts={}
for ref in refs:
    f=fps[ref];old=[*xy(f.GetPosition()),f.GetOrientationDegrees()];seen={}
    for pad in f.Pads():
        for t in tracks:
            layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
            if pad.IsOnLayer(layer)and overlap(rect(pad.GetBoundingBox()),rect(t.GetBoundingBox()))and pad.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),0):seen[t.m_Uuid.AsString()]={'pad':pad.GetNumber(),'net':t.GetNetname(),'same_native_net':pad.GetNetCode()==t.GetNetCode(),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd())}
    contacts[ref]=seen;candidates=[]
    for x in range(max(3,math.floor(old[0]-80)),min(457,math.ceil(old[0]+80))+1):
        for y in range(max(3,math.floor(old[1]-80)),min(337,math.ceil(old[1]+80))+1):
            for a in [0,90,180,270]:candidates.append((math.dist([x,y],old[:2])+(0 if a==old[2] else 2),x,y,a))
    # Edge-facing poses outside the local box are considered only after closer
    # placements. Field-terminal length is not a high-speed compute trace.
    for x,y,a in [(x,6,180)for x in range(3,458)]+[(x,334,0)for x in range(3,458)]+[(6,y,270)for y in range(3,338)]+[(454,y,90)for y in range(3,338)]:candidates.append((math.dist([x,y],old[:2])+2,x,y,a))
    candidates.sort();chosen=None
    for score,x,y,a in candidates:
        f.SetOrientationDegrees(a);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
        if any(q[0]<.5 or q[1]<.5 or q[2]>459.5 or q[3]>339.5 for q in [rect(z.GetBoundingBox())for z in f.Pads()]):continue
        cs=clashes(f)
        if any(cs.values())or copper(f):continue
        chosen={'original_pose':old,'new_pose':[x,y,a],'score':score,'component_conflicts':cs,'foreign_copper_conflicts':0,'envelopes_mm':boxes(f)};break
    if chosen is None:
        f.SetOrientationDegrees(old[2]);f.SetPosition(p.VECTOR2I(p.FromMM(old[0]),p.FromMM(old[1])));chosen={'original_pose':old,'new_pose':None,'bounded_search_not_closed':True}
    selected[ref]=chosen
    for kind,box in boxes(f).items():objects[ref+'_'+kind]=box
    rebuild();print(json.dumps({ref:chosen}),flush=True)
assert sha(path)==before
report={'input_board_sha256':before,'native_parts':len(fps),'native_tracks_vias':len(tracks),'poses':selected,'old_actual_attached_copper':contacts,'all_source_inputs_read_only':True,'matings_scope':'Standard MC1.5/..-ST3.5 whole16.1mm projection plus20mm withdrawal; clear all other placed source parts, all27 retained field mates, six power mates and reserved CM/ESP/M3 envelopes by.25mm. Exact source population2688 and final nativeDRC must be rechecked by root after actual changes. No board file saved.'}
(out/'review.json').write_text(json.dumps(report,indent=2)+chr(10));(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes())
