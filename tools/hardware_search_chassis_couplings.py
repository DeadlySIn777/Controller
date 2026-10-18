"""Read-only finite native nine-Y2 coupling pose search, actual mate guarded."""
import argparse,json,math
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,graphic_box,body_box,overlap,grown,transformed_box
from hardware_route_local_signals import GeometryIndex
from hardware_route_logic_return import distance
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--board',type=Path);a=ap.parse_args();out=a.out.resolve();assert not out.exists();out.mkdir(parents=True)
    bp=(a.board or ROOT/'reports/motherboard-pcb-integration-20261001/isow-local-caps-merge-r28/motherboard-bounded-merged-candidate.kicad_pcb').resolve();mp=ROOT/'reports/motherboard-bypass-owners-20260930/complete723-source-r06/capacitor-owners.json';mates=ROOT/'reports/motherboard-mechanical-20260930/r24f-complete-mate-proposal-r05/review.json';power=ROOT/'reports/motherboard-power-entry-20260930/layout-r10/full-board-fit-r01/power-groups-geometry-candidate.kicad_pcb';pr=power.with_name('placement-receipt.json')
    inputs={str(q):sha(q)for q in[bp,mp,mates,power,pr,Path(__file__)]};b=p.LoadBoard(str(bp));fs={f.GetReference():f for f in b.GetFootprints()};pb=p.LoadBoard(str(power));pf={f.GetReference():f for f in pb.GetFootprints()};future={r:pf[r]for g in json.loads(pr.read_text())['groups']for r in g['refs']};rows=[z for z in json.loads(mp.read_text())['capacitors']if z['ref'].startswith('C195')];assert len(rows)==9;refs={z['ref']for z in rows};ob=GeometryIndex();cu=GeometryIndex();chosen=[]
    for ref,f in fs.items():
        if ref in refs:continue
        f=f if a.board else future.get(ref,f);box=graphic_box(f,p.F_CrtYd)or graphic_box(f,p.B_CrtYd)or body_box(f)[0];ob.add((ref,grown(box,.25)),grown(box,.25))
    for ref,row in json.loads(mates.read_text())['actual40_ports_mutually_checked'].items():
        for name,box in row['envelopes_mm'].items():ob.add((ref+'_'+name,box),box)
    for name,box in [('CM_MODULE',transformed_box(fs['J15001'],[-3,-30,37,25])),('ESP_MODULE',transformed_box(fs['J16001'],[-1.27,-1.565,24.13,61.3]))]:ob.add((name,box),box)
    for ref in['H22001','H22002','H22003','H22004','H22005','H22006','H19501']:
        x,y=xy(fs[ref].GetPosition());radius=6 if ref=='H19501'else 4.25;ob.add((ref+'_WASHER',[x-radius,y-radius,x+radius,y+radius]),[x-radius,y-radius,x+radius,y+radius])
    for ic,box in [('ISOW_RS485',[362.475,85.010,390.500,102.175]),('ISOW_CAN',[314.475,53.010,342.500,70.175])]:ob.add((ic,box),box)
    for t in b.GetTracks():
        box=rect(t.GetBoundingBox());w=p.ToMM(t.GetWidth(p.F_Cu)if isinstance(t,p.PCB_VIA)else t.GetWidth());cu.add((t.GetNetname(),xy(t.GetStart()),xy(t.GetEnd()),w),box)
    def pins(f):return {z.GetNumber():z for z in f.Pads()}
    results=[]
    for row in sorted(rows,key=lambda z:z['ref']):
        ref=row['ref'];f=fs[ref];pp=[pins(fs[z['ref']])[z['pin']]for z in row['power_nodes']];gg=[pins(fs[z['ref']])[z['pin']]for z in row['return_nodes']];net=(pins(f)['1'].GetNetname(),pins(f)['2'].GetNetname());targets=[xy(z.GetPosition())for z in pp+gg];center=[sum(z[k]for z in targets)/len(targets)for k in[0,1]];candidates=[];old=[*xy(f.GetPosition()),f.GetOrientationDegrees()]
        oldpads={pin:xy(z.GetPosition())for pin,z in pins(f).items()};oldbox=graphic_box(f,p.F_CrtYd)
        for angle in[0,90,180,270]:
            f.SetOrientationDegrees(angle);f.SetPosition(p.VECTOR2I(0,0));relative=graphic_box(f,p.F_CrtYd);rels={pin:xy(z.GetPosition())for pin,z in pins(f).items()};sizes={pin:p.ToMM(z.GetSize().x)/2 for pin,z in pins(f).items()};drills={pin:p.ToMM(z.GetDrillSize().x)/2 for pin,z in pins(f).items()}
            for dx in range(-60,61):
                x=round(center[0]+dx*.5,4)
                for dy in range(-60,61):
                    y=round(center[1]+dy*.5,4);box=[relative[k]+(x if k%2==0 else y)for k in range(4)]
                    if box[0]<.8 or box[1]<.8 or box[2]>459.2 or box[3]>339.2:continue
                    if any(overlap(box,z)for _,z in ob.candidates((box[0],box[1]),(box[2],box[3]),0)):continue
                    if any(overlap(box,z)for _,z in chosen):continue
                    p1=(x+rels['1'][0],y+rels['1'][1]);p2=(x+rels['2'][0],y+rels['2'][1]);d1=min(math.dist(p1,xy(z.GetPosition()))for z in pp);d2=min(math.dist(p2,xy(z.GetPosition()))for z in gg)
                    blocked=False
                    for pin,point in[('1',p1),('2',p2)]:
                        for tn,s,e,w in cu.candidates(point,point,sizes[pin]+.25):
                            if tn==net[int(pin)-1]:continue
                            if distance(point,s,e)<max(sizes[pin]+.15,drills[pin]+.25)+w/2-1e-6:blocked=True;break
                        if blocked:break
                    if blocked:continue
                    score=max(d1,d2)+.10*(d1+d2)
                    candidates.append((score,x,y,angle,d1,d2,box))
        assert candidates,'No legal ordinary Y2 pose '+ref
        candidates.sort();best=candidates[0]
        # Preserve the two already local, routed couplings when the legal
        # new pose only changes a small engineering-distance screen.
        oldcandidate=next((z for z in candidates if abs(z[1]-old[0])<1e-4 and abs(z[2]-old[1])<1e-4 and z[3]%360==old[2]%360),None)
        if ref in['C19504','C19507']and not any(overlap(oldbox,z)for _,z in ob.candidates((oldbox[0],oldbox[1]),(oldbox[2],oldbox[3]),0))and not any(overlap(oldbox,z)for _,z in chosen):
            d1=min(math.dist(oldpads['1'],xy(z.GetPosition()))for z in pp);d2=min(math.dist(oldpads['2'],xy(z.GetPosition()))for z in gg);oldcandidate=(max(d1,d2)+.10*(d1+d2),*old[:2],old[2],d1,d2,oldbox)
        if ref in['C19504','C19507']and oldcandidate and oldcandidate[0]<=best[0]+1:best=oldcandidate
        chosen.append((ref,best[6]));results.append(dict(ref=ref,owner=row['owner'],source_category=row['category'],old_pose=old,new_pose=list(best[1:4]),actual_power_owner_pin_distance_mm=best[4],actual_CHASSIS_owner_pin_distance_mm=best[5],body_courtyard_mm=best[6],original_5mm_engineering_screen_pass=best[4]<=5 and best[5]<=5,no_manufacturer_5mm_limit_claim=True,top3=[list(z[:6])for z in candidates[:3]]))
        f.SetOrientationDegrees(old[2]);f.SetPosition(p.VECTOR2I(p.FromMM(old[0]),p.FromMM(old[1])))
    assert inputs=={q:sha(Path(q))for q in inputs}
    report=dict(input_hashes=inputs,actual_Y2_parts=9,all_finite_body_copper_mate_pose_screens_pass=True,proposal=results,source_or_PCB_modified=False,manufacturing_ready=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
