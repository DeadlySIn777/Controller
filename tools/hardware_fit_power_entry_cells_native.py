"""Fit the existing three protection cells on a copy, preserving all old Cu.

Layer-aware footprint/track obstacles include all unrelated installed parts.
Only exact private local nets whose every fitted pad is in the moving scope
are excluded from the placement obstacle search for reviewed rerouting.
"""
from pathlib import Path
import pcbnew,json,math,argparse,hashlib,shutil,collections
from hardware_power_entry_cell_layout import recipes
from hardware_fit_power_recipes_native import box,rect,overlap,inflate,copper
from hardware_build_assembly import parse,dump,child,value
from hardware_route_logic_return import identity
def mm(v):return pcbnew.ToMM(v)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);digest=hashlib.sha256(a.board.read_bytes()).hexdigest();b=pcbnew.LoadBoard(str(a.board.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};original=copper(b);rec=recipes();groups=rec['groups'];scope={r for g in groups.values()for r in g};netrefs=collections.defaultdict(set)
    for p in b.GetPads():
        if p.GetNetname():netrefs[p.GetNetname()].add(p.GetParentFootprint().GetReference())
    private={n for n,refs in netrefs.items()if refs<=scope};removed=[dict(uuid=t.m_Uuid.AsString(),identity=identity(t),reason='Every fitted pad belongs to the moving entry cell; private local Cu is retired atomically before placement to avoid native automatic reassignment')for t in b.GetTracks()if t.GetNetname()in private];remove_ids={r['uuid']for r in removed};source_tree=parse(a.board.read_text());source_tree[:]=[x for x in source_tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in remove_ids)];cleared=a.out/'private-cleared-placement-input.kicad_pcb';cleared.write_text(dump(source_tree)+'\n');b=pcbnew.LoadBoard(str(cleared.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};original=copper(b);obstacles=[]
    for r,f in fs.items():
        if r not in scope:obstacles.append(('FP '+r,inflate(box(f),.05),{f.GetLayer()}))
    for t in b.GetTracks():
        if t.GetNetname()in private:continue
        ls={l for l in [pcbnew.F_Cu,pcbnew.B_Cu]if t.IsOnLayer(l)}
        if ls:obstacles.append(('CU '+t.m_Uuid.AsString(),inflate(rect(t.GetBoundingBox()),.20),ls))
    grid=collections.defaultdict(list);unit=5;indexed=[]
    def cells(r):return[(x,y)for x in range(math.floor(r[0]/unit),math.floor(r[2]/unit)+1)for y in range(math.floor(r[1]/unit),math.floor(r[3]/unit)+1)]
    def add(o):
        i=len(indexed);indexed.append(o)
        for c in cells(o[1]):grid[c].append(i)
    for o in obstacles:add(o)
    bounds=rect(b.GetBoardEdgesBoundingBox());rows=[];poses=[]
    for name,g in groups.items():
        rel=[]
        for r,(x,y,ang)in g.items():
            f=pcbnew.FOOTPRINT(fs[r])
            intended=pcbnew.B_Cu if r in rec['bottom_refs']else pcbnew.F_Cu
            if f.GetLayer()!=intended:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)));f.SetOrientationDegrees(ang);rel.append((r,box(f),f.GetLayer()))
        ext=(min(q[0]for _,q,_ in rel),min(q[1]for _,q,_ in rel),max(q[2]for _,q,_ in rel),max(q[3]for _,q,_ in rel));u=next(r for r in g if r.startswith('U'));old=fs[u].GetPosition();origin=(mm(old.x),mm(old.y));candidates=[(x,y)for x in range(5,456)for y in range(5,336)if bounds[0]+1<x+ext[0]and x+ext[2]<bounds[2]-1 and bounds[1]+1<y+ext[1]and y+ext[3]<bounds[3]-1];candidates.sort(key=lambda p:math.dist(p,origin));winner=None
        for ox,oy in candidates:
            ok=True
            # The already native-DRC-clean routed fixture occupies a bounded
            # rectangle on both outer layers. Reserving that complete local
            # loop avoids a capacitor-only fit whose via escape hits foreign
            # copper immediately outside its courtyard.
            envelope=(ox-18,oy-6.2,ox+6.8,oy+8.5);eids={i for c in cells(envelope)for i in grid.get(c,[])}
            if any(overlap(envelope,indexed[i][1])for i in eids):continue
            for r,q,layer in rel:
                bb=(q[0]+ox,q[1]+oy,q[2]+ox,q[3]+oy);ids={i for c in cells(bb)for i in grid.get(c,[])}
                if any(layer in indexed[i][2]and overlap(bb,indexed[i][1])for i in ids):ok=False;break
            if ok:winner=(ox,oy);break
        assert winner is not None,f'No native full-board fit for {name}'
        ox,oy=winner
        for r,(x,y,ang)in g.items():
            f=fs[r];poses.append(dict(ref=r,before_mm=[mm(f.GetPosition().x),mm(f.GetPosition().y)],before_angle_deg=f.GetOrientationDegrees(),before_layer=b.GetLayerName(f.GetLayer()),after_mm=[x+ox,y+oy],after_angle_deg=ang,after_layer='B.Cu'if r in rec['bottom_refs']else'F.Cu'))
            intended=pcbnew.B_Cu if r in rec['bottom_refs']else pcbnew.F_Cu
            if f.GetLayer()!=intended:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x+ox),pcbnew.FromMM(y+oy)));f.SetOrientationDegrees(ang);add(('NEW '+r,inflate(box(f),.05),{f.GetLayer()}))
        rows.append(dict(group=name,origin_mm=winner,bounding_box_mm=[ext[0]+ox,ext[1]+oy,ext[2]+ox,ext[3]+oy],fit=True,refs=list(g)))
    assert original==copper(b);dest=a.out/'power-entry-cells-geometry-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
    # Removed private old escapes cannot be reassigned to new ground pads on
    # native loading. Every retained item must still match after reload.
    assert original==copper(pcbnew.LoadBoard(str(dest.resolve()))),'Saved fit changed a retained Cu net or geometry'
    for suffix in ['.kicad_pro','.kicad_dru']:
        p=a.board.with_suffix(suffix)
        if p.exists():shutil.copyfile(p,dest.with_suffix(suffix))
    (a.out/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()));assert digest==hashlib.sha256(a.board.read_bytes()).hexdigest();receipt=dict(source_board=str(a.board),source_sha256=digest,source_unchanged=True,scope_refs=sorted(scope),exact_poses=poses,groups=rows,exact_removed_private_copper=removed,private_copper_retired_atomically_before_native_pose_change=True,all_unrelated_copper_preserved=True,no_pin_or_component_change=True,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
