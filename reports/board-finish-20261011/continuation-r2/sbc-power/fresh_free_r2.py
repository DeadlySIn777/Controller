"""Fresh nearest-reference routing-layer free regions, reusable for multilayer search."""
import json,hashlib
from shapely.geometry import box,Point
import fresh_model_r2 as F
L=F.L;p=L.p
def main():
    g,h,scope,native,prior,omit=F.load();p.WINDOW=box(100,95,275,180);rows=[]
    # Six-part ordinary assembly correction extends the explicitly ledgered scope.
    pair=json.loads((L.OUT/'cap-pair-r1.json').read_text());extra={r['uuid'] for r in pair['C15002_new_owned_tracks']}
    h={**h,'tracks':[r for r in h['tracks'] if r['uuid'] not in extra]}
    h=L.stage.caps.moved(h,{'C15001':[1.15,0.],'C15002':[1.,-.9]})
    # LOGIC_GND pours on routing layers will be regenerated around new copper;
    # In1/In4 source references and foreign power/domain pours remain obstacles.
    h['zones']=[{**z,'fills':{k:v for k,v in z['fills'].items() if k not in ('F.Cu','B.Cu','In2.Cu','In3.Cu')}} if p.norm(z['net'])=='/LOGIC_GND' else z for z in h['zones']]
    for layer,plane in (('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('In3.Cu','In4.Cu'),('B.Cu','In4.Cu')):
        print('FREE',layer,flush=True)
        old=p.base.layer_reference;p.base.layer_reference=lambda gg,ll:g['_rooted_refs'][plane]
        try:free=p.free_copper(h,[],L.stage.caps.CORE,layer,window=p.WINDOW)
        finally:p.base.layer_reference=old
        path=L.OUT/('fresh-core-'+layer.replace('.','-')+'-free.wkb');path.write_bytes(free.wkb)
        widths=[]
        for width in (3.,2.,1.5,1.,.6):
            cs=p.hubs.components(free.buffer(-width/2));source=Point(224.425,107.15).buffer(10);load=Point(116,161.4).buffer(10)
            widths.append({'width':width,'components':len(cs),'source_components':[x.area for x in cs if x.intersects(source)],'load_components':[x.area for x in cs if x.intersects(load)],'shared':sum(x.intersects(source) and x.intersects(load) for x in cs)})
        rows.append({'layer':layer,'reference':plane,'free_file':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'widths':widths})
        print('COMPONENTS',layer,[(x['width'],x['components'],x['shared']) for x in widths],flush=True)
    (L.OUT/'fresh-core-free-r2.json').write_text(json.dumps({'exact_board':L.live.SHA,'fresh_geometry':scope,'window':p.WINDOW.bounds,'routing_LOGIC_GND_repours_required':True,'component_moves':prior['new_component_poses'],'additional_delta':{'C15001':[1.15,0.],'C15002':[1.,-.9]},'additional_owned_track_ids':sorted(extra),'rows':rows,'source_hashes':p.READS,'board_written':False,'native_jobs':0},indent=2)+'\n')
if __name__=='__main__':main()
