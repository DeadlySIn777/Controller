import json,copy,math,hashlib
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import layout_r1 as L
p=L.p;stage=L.stage;A=L.A
def main():
    g,h,scope,native,prior,omit=L.load();stage.REFS=set(prior['new_component_poses'])|{'C15002'};stage.TARGET=box(108,156,124,172)
    caps=[r for r in g['pads'] if r['ref']=='C15002']
    new_own=[]
    for t in h['tracks']:
        if t['layer']!='F.Cu':continue
        for cap in caps:
            if p.norm(t['net'])==p.norm(cap['net']) and L.body_pad(cap).intersects(p.base.body(t)):
                new_own.append(t['uuid']);break
    omit=set(omit)|set(new_own)
    model={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in new_own]}
    areas=L.live.reservations();masks,courts=stage.cache(model,areas)
    rows=[]
    for dx in (1.,1.1,1.2,1.3,1.4):
        for dy in (-.9,-1.,-1.1):
            trial=stage.caps.moved(model,{'C15001':[1.15,0.],'C15002':[dx,dy]})
            result=A.T.check_placement(trial,masks,courts)
            holes=[]
            for pad in trial['pads']:
                if pad['ref'] not in {'C15001','C15002'}:continue
                body=L.body_pad(pad)
                for v in trial['vias']:
                    hole=Point(v['x'],v['y']).buffer(v['drill']/2)
                    d=body.distance(hole)
                    if d<.275-1e-8:holes.append({'ref':pad['ref'],'pad':pad['num'],'via_uuid':v['uuid'],'gap':d})
            row={'C15001_delta_from_previous':[1.15,0.],'C15002_delta_from_original':[dx,dy],'placement':result,'ordinary_hole_errors':holes}
            rows.append(row);print('CAPPAIR',dx,dy,result['verdict'],len(holes),result['findings'][:2],flush=True)
    fp={p.base.ref_of(ch):{'sha256':hashlib.sha256(ch).hexdigest()} for ch in native.values() if p.base.pcbtext.chunk_kind(ch)=='footprint'}
    owners=[{'uuid':u,'old_sha256':hashlib.sha256(native[u]).hexdigest(),'geometry':next(t for t in g['tracks'] if t['uuid']==u),'contacts':L.C.contacts(g,native,fp,p.base.body(next(t for t in g['tracks'] if t['uuid']==u)),next(t for t in g['tracks'] if t['uuid']==u)['net'],'F.Cu',omit=omit,native_vias=L.live.ACTUAL)} for u in new_own]
    (L.OUT/'cap-pair-r1.json').write_text(json.dumps({'source':L.live.SHA,'C15002_new_owned_tracks':owners,'trials':rows,'source_hashes':p.READS},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
