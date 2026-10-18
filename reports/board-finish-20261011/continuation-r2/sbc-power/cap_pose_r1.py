import json,copy,math
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import layout_r1 as L
p=L.p;stage=L.stage;A=L.A
def main():
    g,h,scope,native,prior,omit=L.load();stage.REFS=set(prior['new_component_poses'])
    stage.TARGET=box(108,156,124,172)
    areas=L.live.reservations();masks,courts=stage.cache(h,areas)
    findings=[]
    for dx in (1.15,1.2,1.25,1.3):
        for dy in (0.,-.05,-.1,-.15,-.2):
            trial=stage.caps.moved(h,{'C15001':[dx,dy]})
            placement=A.T.check_placement(trial,masks,courts)
            ground=next(r for r in trial['pads'] if r['ref']=='C15001' and r['num']=='2')
            via=next(r for r in trial['vias'] if r['uuid']==L.C.GROUND_VIA)
            body=L.body_pad(ground)
            hole=Point(via['x'],via['y']).buffer(via['drill']/2,quad_segs=256)
            length=math.dist((ground['x'],ground['y']),(via['x'],via['y']))
            errors=[]
            for pad in trial['pads']:
                if pad['ref']!='C15001':continue
                for v in trial['vias']:
                    distance=L.body_pad(pad).distance(Point(v['x'],v['y']).buffer(v['drill']/2))
                    if distance<.275-1e-8:errors.append({'pad':pad['num'],'via':v['uuid'],'distance':distance})
            row={'dx':dx,'dy':dy,'placement':placement,'ordinary_hole_errors':errors,'ground_stub_length':length,'own_return_within1p2':length<=1.2,'gap_to_retained_ground_drill':body.distance(hole),'drill_overlap':body.intersection(hole).area}
            findings.append(row)
            print('CAPPOSE',dx,dy,placement['verdict'],'HOLES',len(errors),'GNDL',length,flush=True)
    dest=L.OUT/'cap-pose-r1.json'
    if dest.exists():raise ValueError('Immutable output')
    dest.write_text(json.dumps({'source_sha256':L.live.SHA,'pose_base':prior['new_component_poses'],'trials':findings,'source_hashes':p.READS},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
