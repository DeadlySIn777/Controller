import json,re
import local_copper_r3 as T
L=T.L;p=T.p
def main():
    g,h,tail=T.model();native=tail[1];pads=[q for q in g['pads'] if q['ref']=='R11049'];fp=next(f for f in g['footprints'] if f['ref']=='R11049');ch=next(ch for ch in native.values() if p.base.pcbtext.chunk_kind(ch)=='footprint' and p.base.ref_of(ch)=='R11049')
    net=p.norm(pads[0]['net']);ts=[t for t in g['tracks'] if p.norm(t['net'])==net and any(p.base.body(t).intersects(L.body_pad(q,t['layer'])) for q in pads)];vs=[v for v in g['vias'] if p.norm(v['net'])==net and any(L.body_pad(q).intersects(__import__('shapely').geometry.Point(v['x'],v['y']).buffer(v['d']/2)) for q in pads)]
    print(json.dumps({'pads':pads,'fp':fp,'native_at':re.search(rb'\(at ([^)]+)\)',ch).group(1).decode(),'native_layer':re.search(rb'\(layer "([^"]+)"',ch).group(1).decode(),'contact_tracks':ts,'contact_vias':vs},indent=2))
if __name__=='__main__':main()
