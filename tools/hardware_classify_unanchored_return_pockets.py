"""Classify native unanchored fill against actual owned pad/track projection.

Report-only. Source-bearing pockets require real grounding; empty generated
fill can be geometrically removed after bounded source-cluster review. This
does not claim a net name or an IC pin internally connects copper islands.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_validate_motherboard_return_planes import validate
from hardware_zone_motherboard_returns import return_net,pad_supports_reference,track_supports_reference,split_polygons,rectangle
from hardware_route_local_signals import GeometryIndex
from hardware_collect_native_reference_fills import collect_native_reference_fills


def classify(b,mapping):
    anchors=validate(b,mapping);unanchored={(r['net'],r['reference_layer'],r['filled_piece'])for r in anchors['unanchored_components']}
    fills=collect_native_reference_fills(b,{r[0]for r in unanchored},[pcbnew.In1_Cu,pcbnew.In4_Cu])
    domains={p['net']:p['domain']for p in mapping['pads']};tracks=list(b.GetTracks());rows=[]
    spatial={}
    for name in ['In1.Cu','In4.Cu']:
        for p in mapping['pads']:
            net=return_net(p)
            if not net or not pad_supports_reference(p,name):continue
            spatial.setdefault((net,name),GeometryIndex()).add(('pad',rectangle(p['copper_aabb_mm']),p),p['copper_aabb_mm'])
        for t in tracks:
            net=return_net(dict(domain=domains.get(t.GetNetname()),net=t.GetNetname()))
            if not net or not track_supports_reference(b,t,name):continue
            q=t.GetBoundingBox();box=[pcbnew.ToMM(x)for x in [q.GetX(),q.GetY(),q.GetRight(),q.GetBottom()]]
            spatial.setdefault((net,name),GeometryIndex()).add(('copper',t.GetEffectiveShape(),t),box)
    for (net,layer),fill in sorted(fills.items()):
        name=b.GetLayerName(layer)
        for index,piece in enumerate(split_polygons(fill)):
            if(net,name,index)not in unanchored:continue
            box=piece.BBox();bounds=[pcbnew.ToMM(x)for x in [box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]]
            #Keep source-adjacent reference around actual through-contact
            #antipads and future source endpoints, not just copper directly
            #under a pad centre. Empty-pocket removal must be conservative.
            projection_margin=.4;ownpads=[];owntracks=[]
            candidates=spatial.get((net,name))
            if candidates:
                for kind,shape,obj in candidates.candidates(bounds[:2],bounds[2:],projection_margin):
                    if piece.Collide(shape,pcbnew.FromMM(projection_margin)):
                        (ownpads if kind=='pad'else owntracks).append(obj)
            needed=bool(ownpads or owntracks)
            rows.append(dict(net=net,reference_layer=name,filled_piece=index,area_mm2=piece.Area()/1e12,bounds_mm=[pcbnew.ToMM(x)for x in [box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]],
                source_projection_needed=needed,empty_reference_pocket=not needed,
                exact_owned_pad_projections=[dict(reference=p['reference'],pin=p['pin'],pad_uuid=p['uuid'])for p in ownpads],
                exact_owned_copper_projections=[t.m_Uuid.AsString()for t in owntracks]))
    return dict(board_sha256=None,scope='native unanchored reference pocket semantic classification only; no mutation',
        source_adjacent_projection_allowance_mm=.4,unanchored_count=len(rows),source_bearing_count=sum(r['source_projection_needed']for r in rows),empty_count=sum(r['empty_reference_pocket']for r in rows),rows=rows,passed=False,manufacturing_ready=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--map',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    b=pcbnew.LoadBoard(str(a.board));m=json.loads(a.map.read_text(encoding='utf-8'));r=classify(b,m);r['board_sha256']=sha(a.board);r['map_sha256']=sha(a.map);r['tool_sha256']=sha(Path(__file__));write(a.out,r)
    print(json.dumps({k:v for k,v in r.items()if k!='rows'},indent=2))


if __name__=='__main__':main()
