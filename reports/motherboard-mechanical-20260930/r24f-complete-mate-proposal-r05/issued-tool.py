"""Verify the exact seven-field/six-power proposal on the actual2688 native board."""
import json,argparse
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,overlap,grown,body_box,graphic_box,transformed_box

path=ROOT/'reports/motherboard-pcb-integration-20260930/current-source-population-r24f/motherboard-current-source-candidate.kicad_pcb'
recipe_path=ROOT/'reports/motherboard-power-entry-20260930/layout-r09/full-board-fit-r01/power-groups-geometry-candidate.kicad_pcb'
recipe_receipt=recipe_path.with_name('placement-receipt.json')
field_receipt=ROOT/'reports/motherboard-mechanical-20260930/r23-field-mate-candidates-r02-global/review.json'
power_receipt=ROOT/'reports/motherboard-mechanical-20260930/r20-power-mate-candidates-r03-power-groups/review.json'
parser=argparse.ArgumentParser()
parser.add_argument('--output',default='reports/motherboard-mechanical-20260930/r24f-complete-mate-proposal-r03')
parser.add_argument('--xm6-y',type=float,default=59.0)
parser.add_argument('--xm8-y',type=float,default=4.0)
parser.add_argument('--search-j19525',action='store_true')
args=parser.parse_args()
out=ROOT/args.output
assert not out.exists();out.mkdir()
inputs=[path,recipe_path,recipe_receipt,field_receipt,power_receipt];before={str(f):sha(f)for f in inputs}
b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()};tracks=list(b.GetTracks());assert len(fps)==2688
recipe=p.LoadBoard(str(recipe_path));recipe_fps={f.GetReference():f for f in recipe.GetFootprints()}
power=json.loads(power_receipt.read_text());field=json.loads(field_receipt.read_text())
poses={**{r:v['new_pose']for r,v in power['poses'].items()},**{r:v['new_pose']for r,v in field['poses'].items()}}
assert len(poses)==13 and all(poses.values())
poses.update({'J19506':[434,args.xm6_y,90],'J19508':[55.5,args.xm8_y,180]})
assert len(poses)==15
contacts={}
for ref in poses:
    seen={}
    for pad in fps[ref].Pads():
        for t in tracks:
            layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
            if pad.IsOnLayer(layer)and overlap(rect(pad.GetBoundingBox()),rect(t.GetBoundingBox()))and pad.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),0):seen[t.m_Uuid.AsString()]={'pad':pad.GetNumber(),'net':t.GetNetname(),'same_native_net':pad.GetNetCode()==t.GetNetCode(),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd())}
    contacts[ref]=seen
for group in json.loads(recipe_receipt.read_text())['groups']:
    for ref in group['refs']:
        fps[ref].SetPosition(recipe_fps[ref].GetPosition());fps[ref].SetOrientationDegrees(recipe_fps[ref].GetOrientationDegrees())
for ref,(x,y,a)in poses.items():fps[ref].SetOrientationDegrees(a);fps[ref].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
objects={r:(graphic_box(f,p.F_CrtYd)or body_box(f)[0])for r,f in fps.items()}
objects.update({'CM_MODULE':transformed_box(fps['J15001'],[-3,-30,37,25]),'ESP_MODULE':transformed_box(fps['J16001'],[-1.27,-1.565,24.13,61.3]),'ESP_RF15':grown(transformed_box(fps['J16001'],[2.48,-7.85,20.48,-1.54]),15)})
for ref in ['H22001','H22002','H22003','H22004','H22005','H22006']:
    x,y=xy(fps[ref].GetPosition());objects[ref+'_M3_WASHER']=[x-4.25,y-4.25,x+4.25,y+4.25]
ports={};mate_mpns={2:'1840366',3:'1840379',6:'1840405',10:'1840447',12:'1840463',14:'1840489'}
for ref,f in fps.items():
    if ref.startswith('J195'):
        n=len(list(f.Pads()));mate=mate_mpns[n];boxes={'header':objects[ref],'full_plug':transformed_box(f,[-1.75,8,n*3.5-1.75,24.1]),'withdraw_wire_service':transformed_box(f,[-2.75,24.1,n*3.5-.75,44.1])}
    elif ref in power['poses']:
        mate='1757019';boxes={'header':objects[ref],'full_plug':transformed_box(f,[-2.54,10,7.62,28.3]),'withdraw_wire_service':transformed_box(f,[-3.54,28.3,8.62,48.3])}
    else:continue
    ports[ref]={'mate':mate,'pose':[*xy(f.GetPosition()),f.GetOrientationDegrees()],'envelopes_mm':boxes}
    for kind,box in boxes.items():objects[ref+'_'+kind]=box
if args.search_j19525:
    import math
    f=fps['J19525'];oldpose=ports['J19525']['pose'];selected=None
    candidates=sorted((math.dist([x,y],oldpose[:2])+(0 if angle==oldpose[2]else 2),x,y,angle) for x in range(max(3,int(oldpose[0])-90),min(457,int(oldpose[0])+90)+1)for y in range(max(3,int(oldpose[1])-55),min(337,int(oldpose[1])+15)+1)for angle in [0,90,180,270])
    obstacles={k:v for k,v in objects.items()if k!='J19525'and not k.startswith('J19525_')}
    for score,x,y,angle in candidates:
        f.SetOrientationDegrees(angle);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
        if any(z[0]<.5 or z[1]<.5 or z[2]>459.5 or z[3]>339.5 for z in [rect(q.GetBoundingBox())for q in f.Pads()]):continue
        n=len(list(f.Pads()));boxes={'header':graphic_box(f,p.F_CrtYd)or body_box(f)[0],'full_plug':transformed_box(f,[-1.75,8,n*3.5-1.75,24.1]),'withdraw_wire_service':transformed_box(f,[-2.75,24.1,n*3.5-.75,44.1])}
        if any(overlap(grown(box,.25),other)for box in boxes.values()for other in obstacles.values()):continue
        bad=False
        for pad in f.Pads():
            for t in tracks:
                if pad.GetNetCode()==t.GetNetCode()or not overlap(grown(rect(pad.GetBoundingBox()),.15),rect(t.GetBoundingBox())):continue
                layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
                if pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),p.FromMM(.15)):bad=True;break
            if bad:break
        if bad:continue
        selected=[x,y,angle];ports['J19525']['pose']=selected;ports['J19525']['envelopes_mm']=boxes;poses['J19525']=selected;objects['J19525']=boxes['header']
        for kind,box in boxes.items():objects['J19525_'+kind]=box
        break
    assert selected,'No bounded J19525 service-corridor candidate'
for ref,r in ports.items():
    r['conflicts']={kind:sorted(name for name,other in objects.items()if name!=ref and not name.startswith(ref+'_')and overlap(grown(box,.25),other))for kind,box in r['envelopes_mm'].items()}
    r['pass']=not any(r['conflicts'].values())
foreign=[]
for ref in poses:
    for pad in fps[ref].Pads():
        for t in tracks:
            if pad.GetNetCode()==t.GetNetCode()or not overlap(grown(rect(pad.GetBoundingBox()),.15),rect(t.GetBoundingBox())):continue
            layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
            if pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),p.FromMM(.15)):foreign.append({'reference':ref,'pad':pad.GetNumber(),'uuid':t.m_Uuid.AsString(),'net':t.GetNetname()})
report={'input_hashes':before,'input_board_sha256':sha(path),'native_physical_parts':len(fps),'native_track_via_items':len(tracks),
        'exact_proposed_poses':poses,'actual_source2688_new_parts_and_six_M3_mounts_checked':True,'bounded_conflict_closures':{'J19506':'Move whole XM6 header down while retaining angle and all six M3 poses; clear real top-right washer from mate/service projection.','J19508':'Move whole XM8 header up while retaining angle and MC_1V2 whole-group recipe; close actual C2003/R2001 courtyard overlap.'},'actual40_ports_mutually_checked':ports,
        'old_actual_attached_copper':contacts,'foreign_copper_conflicts':foreign,'pass':all(v['pass']for v in ports.values())and not foreign,
        'scope':'Read-only exact fifteen-header pose proposal plus six power recipes; full standard mate and20mm withdrawal projections clear native component courtyards, CM/ESP and8mm M3washer/tool projections by.25mm. Final actual movement/nativeDRC/zone refill/source connection and electrical trace routing remain root operations. Exact mated Z/cable bend and loaded physical fit remain prototype qualification.',
        'manufacturing_ready':False,'source_or_PCB_mutated':False}
assert before=={str(f):sha(f)for f in inputs}
(out/'review.json').write_text(json.dumps(report,indent=2)+chr(10));(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'pass':report['pass'],'ports':len(ports),'parts':len(fps),'tracks':len(tracks),'foreign_copper_conflicts':foreign,'occupied':{r:v['conflicts']for r,v in ports.items()if not v['pass']}}))
