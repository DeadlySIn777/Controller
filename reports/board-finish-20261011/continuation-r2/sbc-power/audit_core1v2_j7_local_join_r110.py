"""Independent whole-inventory analytic gate for the exact J7 local nominee."""
from pathlib import Path
import pickle,json,hashlib
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import complete_geometry_r2 as G
p=G.p;H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/core1v2-j7-independent-local-audit-r110'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    mp=H/'field-power/corrected-regulated-native-bound-search-base-r111/model.pkl'
    assert sha(mp)=='722fae195cecfcfa07729dd243c2d74a0a0088e672582363265a2c15553db4d8'
    g,h,b,z,c=pickle.loads(mp.read_bytes());fp=H/'sbc-power/core1v2-local-outer-join-nominees-r106/proposed-tracks.pkl'
    assert sha(fp)=='ebce5be3f82d0c2de9bf6ee303d287efa78a9f85bc19358ee5249f01152b3073'
    ts=pickle.loads(fp.read_bytes());assert len(ts)==1;t=ts[0]
    assert t['uuid']=='0b49fde8-1487-5a6f-9c1c-5b6036759ad8' and t['w']==.2 and t['layer']=='F.Cu'
    line=LineString([t['a'],t['b']]);raw=t['net'];pairs=[];errors=[]
    def pair(gate,other,gap,required):
        row={'gate':gate,'other_UUID':other['uuid'],'other_raw_net':other.get('net'),'actual_gap_mm':gap,'required_gap_mm':required}
        pairs.append(row)
        if gap<required:errors.append(row)
    for q in h['pads']:
        if q['net']!=raw:
            for sh in p.base.polygons(q['layers'].get('F.Cu',[])):
                d=line.distance(sh)-t['w']/2;req=G.gap(h,raw,q['net'])+.025
                if d<1:pair('exact_pad_polygon_to_round_track',q,d,req)
        for sh in p.base.polygons(q.get('hole') or []):
            d=line.distance(sh)-t['w']/2
            if d<1:pair('track_to_NPTH_or_pad_hole',q,d,.275)
    for q in h['tracks']:
        if q['layer']!='F.Cu' or q['net']==raw:continue
        # A two-mm bbox is conservative for every possible required gap here.
        if max(q['a'][0],q['b'][0])+q['w']/2+2<line.bounds[0] or min(q['a'][0],q['b'][0])-q['w']/2-2>line.bounds[2] or max(q['a'][1],q['b'][1])+q['w']/2+2<line.bounds[1] or min(q['a'][1],q['b'][1])-q['w']/2-2>line.bounds[3]:continue
        pair('true_round_track_to_round_track',q,line.distance(LineString([q['a'],q['b']]))-(t['w']+q['w'])/2,G.gap(h,raw,q['net'])+.025)
    for q in h['vias']:
        if q['net']==raw:continue
        if 'F.Cu' in q['flashed']:
            d=line.distance(Point(q['x'],q['y']))-t['w']/2-q['d']/2
            if d<1:pair('actual_F_annulus_to_round_track',q,d,G.gap(h,raw,q['net'])+.025)
        else:
            d=line.distance(Point(q['x'],q['y']))-t['w']/2-q['drill']/2
            if d<1:pair('unflashed_hole_to_round_track',q,d,.275)
    for q in z:
        if q['layer']=='F.Cu' and q['net']!=raw:
            d=line.distance(q['shape'])-t['w']/2
            if d<1:pair('later_actual_new_F_plane_to_round_track',q,d,max(G.gap(h,raw,q['net']),float(q.get('clearance_mm',.15)))+.025)
    for q in h['rule_areas']:
        if 'F.Cu' in q['layers'] and q.get('no_tracks'):
            for sh in p.base.polygons(q['outline']):
                if line.buffer(t['w']/2).intersects(sh):errors.append({'gate':'native_no_tracks_rule_area','rule_UUID':q.get('uuid')})
    body=line.buffer(t['w']/2,quad_segs=64)
    outline=unary_union(p.base.polygons(h['outline']))
    if not outline.covers(body):errors.append({'gate':'board_outline'})
    endpoints=[]
    for pin,xy in [('J7',t['a']),('J6',t['b'])]:
        pad=next(q for q in h['pads'] if (q['ref'],q['num'])==('U1001',pin));sh=unary_union(p.base.polygons(pad['layers']['F.Cu']))
        assert pad['net']==raw and sh.covers(Point(xy))
        endpoints.append({'ref':'U1001','pin':pin,'physical_pad_UUID':pad['uuid'],'actual_pad_raw_net':pad['net'],'point_inside_actual_pad':True,'actual_pad_polygon_WKB_SHA256':hashlib.sha256(sh.wkb).hexdigest()})
    # This is an observation of the host return model, not a reference waiver.
    refs=[]
    for layer in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'):
        ret=unary_union([sh for q in c['zones'] if p.norm(q['net'])=='/LOGIC_GND' for sh in p.base.polygons(q['fills'].get(layer,[]))])
        refs.append({'layer':layer,'bare_track_reference_coverage':ret.covers(body),'uncovered_track_body_mm2':body.difference(ret).area})
    receipt={'verdict':'PASS_SCOPED_ANALYTIC_LOCAL_GEOMETRY' if not errors else 'FAIL_SCOPED_ANALYTIC_LOCAL_GEOMETRY','current_joint_model_sha256':sha(mp),'frozen_nominee_sha256':sha(fp),'track':t,'endpoints':endpoints,'pairs':pairs,'errors':errors,'host_LOGIC_return_observation':refs,'all_inventory_pads_tracks_actual_via_layers_and_new_owned_F_planes_checked':True,'width_mm':.2,'no_new_width_exception_required':True,'native_rule_parse_and_refill':'OPEN','full_original_foreign_contact_projection_and_source_membership_and_current':'OPEN','no_host_tolerance_waiver':True,'board_written':False,'native_jobs':0}
    (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n')
    print('J7_INDEPENDENT_LOCAL',len(errors),sha(O/'receipt.json'),refs,flush=True)
if __name__=='__main__':main()
