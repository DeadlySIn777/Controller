"""Bounded graph proof for replacing moved-passive return leaf branches.

Shared junctions, vias, unmodified-pad anchors and protected edges terminate
the proof. The function cannot delete a shared trunk merely because a moved
capacitor is on the same connected net.
"""
from collections import defaultdict


def leaf_branches(edges, starts, anchors=(), protected=()):
    """Return exact edge IDs reachable from a genuinely unanchored leaf.

    edges maps ID to two (x, y, layer) vertices. All coordinates are literal
    native integers, with no snapping or geometrical connection inference.
    """
    adjacency=defaultdict(set)
    for uid,(a,b) in edges.items():
        if a==b:raise ValueError('Zero-length graph edge requires separate review')
        adjacency[a].add(uid);adjacency[b].add(uid)
    anchors=set(anchors);protected=set(protected);removed=set();receipts=[]
    for start in sorted(set(starts)):
        if start in anchors or len(adjacency[start])!=1:continue
        node=start;previous=None;path=[]
        while node not in anchors:
            available=adjacency[node]-({previous} if previous else set())
            if len(available)!=1:break
            uid=next(iter(available))
            if uid in protected:break
            a,b=edges[uid];other=b if a==node else a
            path.append(uid);removed.add(uid)
            previous=uid;node=other
            if len(adjacency[node])!=2:break
        if path:receipts.append({'leaf':list(start),'removed_edge_UUIDs':path,'retained_boundary':list(node),
            'boundary_is_anchor':node in anchors,'boundary_degree':len(adjacency[node])})
    return removed,receipts
