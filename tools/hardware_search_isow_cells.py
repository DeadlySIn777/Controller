"""Read-only search for complete ISOW cells against native pending obstacles."""
import argparse,json,math
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,graphic_box,body_box,overlap,grown,segment_hit
from hardware_route_local_signals import GeometryIndex

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out;assert not out.exists();out.mkdir(parents=True)
    fixture=ROOT/'reports/motherboard-chassis-20261001/isow-layout-fixture-r05/receipt.json';recipe=json.loads(fixture.read_text());owned=set().union(*[set(z)for z in recipe['recipes']]);assert len(owned)==26
    base=ROOT/'reports/motherboard-bypass-owners-20260930/local-placement723-r04/motherboard-local-capacitors-candidate.kicad_pcb';power=ROOT/'reports/motherboard-power-entry-20260930/layout-r10/full-board-fit-r01/power-groups-geometry-candidate.kicad_pcb';pr=power.with_name('placement-receipt.json');di=ROOT/'reports/motherboard-return-zoning-20260930/r09-di-complete-side-placement/receipt.json';mates=ROOT/'reports/motherboard-mechanical-20260930/r24f-complete-mate-proposal-r05/review.json'
    inp={str(q):sha(q)for q in[fixture,base,power,pr,di,mates,Path(__file__)]};b=p.LoadBoard(str(base));fps={f.GetReference():f for f in b.GetFootprints()};pb=p.LoadBoard(str(power));pf={f.GetReference():f for f in pb.GetFootprints()};future={r:pf[r]for g in json.loads(pr.read_text())['groups']for r in g['refs']}
    index=GeometryIndex();obstacles={}
    for ref,f in fps.items():
        if ref in owned:continue
        f=future.get(ref,f);box=graphic_box(f,p.F_CrtYd)or graphic_box(f,p.B_CrtYd)or body_box(f)[0]
        obstacles[ref]=grown(box,.25);index.add((ref,obstacles[ref]),obstacles[ref])
    for i,box in enumerate(json.loads(di.read_text())['reserved_DI_cells']):
        if isinstance(box,dict):
            pts=box['reserved_cell_polygon_mm'];box=[min(q[0]for q in pts),min(q[1]for q in pts),max(q[0]for q in pts),max(q[1]for q in pts)]
        assert isinstance(box,list),box
        obstacles['DI_CELL_'+str(i)]=box;index.add(('DI_CELL_'+str(i),box),box)
    for ref,row in json.loads(mates.read_text())['actual40_ports_mutually_checked'].items():
        for name,box in row['envelopes_mm'].items():obstacles[ref+'_'+name]=box;index.add((ref+'_'+name,box),box)
    copper=[]
    for t in b.GetTracks():
        box=rect(t.GetBoundingBox());copper.append((t.m_Uuid.AsString(),box));index.add(('Cu_'+t.m_Uuid.AsString(),grown(box,.25)),grown(box,.25))
    # Complete controlled cell including source bulk caps and field ferrites.
    local=[-11.525,-6.99,16.50,10.175];chosen=[];results=[]
    for ic,old in [('U14812',(353,126)),('U14813',(326,111))]:
        candidates=[]
        for x in range(20,439,2):
            for y in range(20,321,2):
                box=[local[0]+x,local[1]+y,local[2]+x,local[3]+y]
                if any(overlap(box,q)for _,q in index.candidates((box[0],box[1]),(box[2],box[3]),0)):continue
                if any(overlap(box,z['cell_bbox_mm'])for z in chosen):continue
                candidates.append((math.dist((x,y),old),x,y,box))
        assert candidates,'No unoccupied complete cell for '+ic
        candidates.sort();best=candidates[0];row=dict(IC=ic,origin_mm=list(best[1:3]),cell_bbox_mm=best[3],displacement_mm=best[0],top10=[dict(displacement_mm=z[0],origin_mm=list(z[1:3]),cell_bbox_mm=z[3])for z in candidates[:10]])
        chosen.append(row);results.append(row)
    assert inp=={q:sha(Path(q))for q in inp}
    report=dict(input_hashes=inp,whole_cell_candidates=results,source_or_PCB_modified=False,all_existing_copper_reserved=True,global_old_planes_not_qualified=True,manufacturing_ready=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['whole_cell_candidates'],indent=2))
if __name__=='__main__':main()
