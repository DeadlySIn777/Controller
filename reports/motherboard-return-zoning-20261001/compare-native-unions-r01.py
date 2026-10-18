"""Read-only exact native geometry comparison of the two union recipes."""
import json,sys,time,concurrent.futures,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_map_motherboard_domains import SEEDS,sha,write
from hardware_collect_native_reference_fills import collect_native_reference_fills

def worker(args):
    path,net,name=args;b=pcbnew.LoadBoard(path);layer=b.GetLayerID(name)
    old=pcbnew.SHAPE_POLY_SET();count=0;start=time.monotonic()
    for z in b.Zones():
        if not z.GetIsRuleArea()and z.GetNetname()==net and z.HasFilledPolysForLayer(layer):
            actual=z.GetFilledPolysList(layer)
            if actual.Area():old.BooleanAdd(actual);count+=1
    new=collect_native_reference_fills(b,{net},[layer]).get((net,layer),pcbnew.SHAPE_POLY_SET())
    gone=pcbnew.SHAPE_POLY_SET();gone.Append(old);gone.BooleanSubtract(new)
    added=pcbnew.SHAPE_POLY_SET();added.Append(new);added.BooleanSubtract(old)
    r=dict(net=net,layer=name,nonempty_zones=count,old_contours=old.OutlineCount(),new_contours=new.OutlineCount(),old_area_iu2=old.Area(),new_area_iu2=new.Area(),lost_area_iu2=gone.Area(),added_area_iu2=added.Area(),seconds=time.monotonic()-start)
    def coordinates(poly):
        return [[[list(p)for p in poly.COutline(i).CPoints()]]+[[list(p)for p in poly.CHole(i,h).CPoints()]for h in range(poly.HoleCount(i))]for i in range(poly.OutlineCount())]
    oc=coordinates(old);nc=coordinates(new)
    r['old_exact_native_coordinates_sha256']=hashlib.sha256(json.dumps(oc,separators=(',',':')).encode()).hexdigest()
    r['new_exact_native_coordinates_sha256']=hashlib.sha256(json.dumps(nc,separators=(',',':')).encode()).hexdigest()
    # Native self-subtraction itself leaves a1472 internal-square-unit
    # degenerate sliver on one large contour. Identical exact integer vertex
    # and hole sequences are stronger evidence than that Boolean artefact.
    r['exact_native_vertex_and_hole_sequences_equal']=oc==nc
    r['exact_union_equivalence']=oc==nc;print(json.dumps(r),flush=True);return r

if __name__=='__main__':
    path=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();b=pcbnew.LoadBoard(str(path));keys=[]
    for z in b.Zones():
        if z.GetIsRuleArea()or z.GetNetname()not in set(SEEDS.values())-{'/CHASSIS'}:continue
        for layer in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
            if z.HasFilledPolysForLayer(layer)and z.GetFilledPolysList(layer).Area():keys.append((str(path),z.GetNetname(),b.GetLayerName(layer)))
    keys=sorted(set(keys));del b
    with concurrent.futures.ProcessPoolExecutor(max_workers=4)as pool:rows=list(pool.map(worker,keys))
    write(out,dict(board_sha256=sha(path),scope='read-only exact native filled metal geometry equivalence',rows=rows,passed=all(r['exact_union_equivalence']for r in rows)))
