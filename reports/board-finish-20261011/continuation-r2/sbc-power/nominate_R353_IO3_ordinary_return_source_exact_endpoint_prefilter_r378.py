"""Exact endpoint neighborhood prefilter; no far LG port can meet .90–1.0 mm."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/exact-expanded-current-ordinary-return-route-r377.py'
s=p.read_text(encoding='utf-8').replace('r377','r378').replace('R377','R378')
needle=";lgports=[]\n for v in h['vias']:\n  if L.norm(v['net'])!='/LOGIC_GND':continue"
assert s.count(needle)==1
replacement=";lgports=[];portEndpoints=[Point(p[side]['x'],p[side]['y'])for p in pairs for side in ('source_existing_annulus','detached_existing_annulus')];endpointTree=STRtree(portEndpoints);nearLG=0\n for v in h['vias']:\n  if L.norm(v['net'])!='/LOGIC_GND':continue\n  center=Point(v['x'],v['y']);nearby=[portEndpoints[int(j)]for j in endpointTree.query(center.buffer(1.000001),predicate='intersects')]\n  if not any(.9<=center.distance(p)<=1. for p in nearby):continue\n  nearLG+=1"
s=s.replace(needle,replacement)
s=s.replace("put(O/'all-saved-cross-group-port-pair-true-two-plane-ordinary-return-census.json',pairCensus);", "put(O/'exact-endpoint-neighborhood-prefilter-proof.json',{'all_saved_endpoint_count':len(portEndpoints),'nearby_LG_examined':nearLG,'only_omitted_LG_has_no_endpoint_at_ordinary0p9_to1p0_distance':True,'no_omitted_LG_can_qualify_for_any_saved_pair':True});put(O/'all-saved-cross-group-port-pair-true-two-plane-ordinary-return-census.json',pairCensus);")
(H/'sbc-power/exact-expanded-ordinary-return-endpoint-source-prefilter-r378.py').write_text(s,encoding='utf-8')
exec(compile(s,str(__file__),'exec'))
