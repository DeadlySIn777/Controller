"""Small ordinary-via C1024 nominees with real old FPGA1V2 In3 attachment.

No actual regulator source credit until the independent complete model proves
L2001.2 membership. Full reference/reservation/native/retained-contact gates
remain explicit; no board or earlier geometry is changed by this probe.
"""
import json,pickle,hashlib,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
import complete_geometry_r2 as G
import core_inner_feed_r18 as I
L=G.L;p=G.p;C=I.C;O=L.OUT/'c1024-ordinary-escape-nominees-r107'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir();mp=L.OUT/'unused-new-core-fragment-removal-r91/model.pkl';g,h,b,z,c=pickle.loads(mp.read_bytes());cached=pickle.loads((L.OUT/'full-power-source-contact-audit-r89/groups.pkl').read_bytes())['/CORE_1V2'];island=unary_union([s for s,j in zip(cached['new_parts']['In3.Cu'],cached['new_assign']['In3.Cu']) if j==1]);pad=next(q for q in h['pads'] if (q['ref'],q['num'])==('C1024','1'));raw=pad['net'];body=unary_union(p.base.polygons(pad['layers']['F.Cu']));rows=[];accepted=[]
    for xy in [(157.14,80.877),(158.19,82.1),(157.3,81.9),(159.2,79.75),(157.14,81.2),(157.2,81.6),(158.3,81.98)]:
        pt=Point(xy);ann=pt.buffer(.25).difference(pt.buffer(.1));source_overlap=ann.intersection(island).area
        if source_overlap<.01:rows.append({'site':xy,'actual_existing_FPGA_In3_annular_overlap_mm2':source_overlap,'errors':[{'gate':'no_actual_FPGA_island_attachment'}]});continue
        start=nearest_points(body.buffer(-.04),pt)[0];points=[[round(x,6),round(y,6)] for x,y in (start.coords[0],xy)];line=LineString(points);errors=[]
        for q in h['pads']:
            if abs(q['x']-xy[0])>10 or abs(q['y']-xy[1])>10:continue
            for layer,rs in q['layers'].items():
                for sh in p.base.polygons(rs):
                    if q['smd'] and pt.distance(sh)-.1<.280:errors.append({'gate':'hole_every_SMD','other':q['uuid'],'ref':q['ref'],'pin':q['num'],'gap_mm':pt.distance(sh)-.1,'required_mm':.275})
                    if q['net']!=raw:
                        req=G.gap(h,raw,q['net'])+.025;gap=pt.distance(sh)-.25
                        if gap<req:errors.append({'gate':'via_Cu','other':q['uuid'],'layer':layer,'gap_mm':gap,'required_mm':req})
                        if layer=='F.Cu' and line.distance(sh)-.1<req:errors.append({'gate':'stub_Cu','other':q['uuid'],'gap_mm':line.distance(sh)-.1,'required_mm':req})
            for sh in p.base.polygons(q.get('hole') or []):
                if pt.distance(sh)-.1<.280:errors.append({'gate':'hole_every_pad_hole','other':q['uuid'],'gap_mm':pt.distance(sh)-.1,'required_mm':.275})
        for q in h['vias']:
            d=pt.distance(Point(q['x'],q['y']))
            if d-.1-q['drill']/2<.280:errors.append({'gate':'hole_every_via_drill','other':q['uuid'],'gap_mm':d-.1-q['drill']/2,'required_mm':.275})
            if q['net']!=raw:
                req=G.gap(h,raw,q['net'])+.025
                if d-.25-q['d']/2<req:errors.append({'gate':'via_all_layer_Cu','other':q['uuid'],'gap_mm':d-.25-q['d']/2,'required_mm':req})
                if 'F.Cu' in q['flashed'] and line.distance(Point(q['x'],q['y']))-.1-q['d']/2<req:errors.append({'gate':'stub_foreign_via','other':q['uuid'],'gap_mm':line.distance(Point(q['x'],q['y']))-.1-q['d']/2,'required_mm':req})
        for q in h['tracks']:
            if q['net']==raw:continue
            if max(q['a'][0],q['b'][0])+q['w']/2+2<min(xy[0],points[0][0]) or min(q['a'][0],q['b'][0])-q['w']/2-2>max(xy[0],points[0][0]) or max(q['a'][1],q['b'][1])+q['w']/2+2<min(xy[1],points[0][1]) or min(q['a'][1],q['b'][1])-q['w']/2-2>max(xy[1],points[0][1]):continue
            actual=LineString([q['a'],q['b']]);req=G.gap(h,raw,q['net'])+.025;gap=pt.distance(actual)-.25-q['w']/2
            if gap<req:errors.append({'gate':'via_analytic_track_Cu','other':q['uuid'],'layer':q['layer'],'gap_mm':gap,'required_mm':req})
            if q['layer']=='F.Cu' and line.distance(actual)-.1-q['w']/2<req:errors.append({'gate':'stub_analytic_track_Cu','other':q['uuid'],'gap_mm':line.distance(actual)-.1-q['w']/2,'required_mm':req})
        for q in z:
            if q['net']==raw:continue
            req=max(G.gap(h,raw,q['net']),float(q.get('clearance_mm',.15)))+.025
            if pt.distance(q['shape'])-.25<req:errors.append({'gate':'all_layer_foreign_owned_plane','other':q['uuid'],'layer':q['layer'],'gap_mm':pt.distance(q['shape'])-.25,'required_mm':req})
            if q['layer']=='F.Cu' and line.distance(q['shape'])-.1<req:errors.append({'gate':'stub_foreign_owned_plane','other':q['uuid'],'gap_mm':line.distance(q['shape'])-.1,'required_mm':req})
        rows.append({'site':xy,'points':points,'actual_existing_FPGA_In3_annular_overlap_mm2':source_overlap,'errors':errors});print('C1024_SITE',xy,'ann',source_overlap,'errors',len(errors),errors[:2],flush=True)
        if not errors:
            v=C.via('C1024-ordinary-escape-r107',raw,xy);v.update(d=.5,drill=.2);t=C.track('C1024-ordinary-escape-r107-stub',raw,'F.Cu',points[0],points[1],.2);accepted=[v,t];break
    f=O/'proposed-discrete.pkl';f.write_bytes(pickle.dumps({'vias':accepted[:1],'tracks':accepted[1:]},protocol=5));(O/'receipt.json').write_text(json.dumps({'verdict':'ORDINARY_ESCAPE_NOMINEE_ONLY_COMPLETE_GATES_OPEN','parent_model_sha256':sha(mp),'rows':rows,'new_discrete_sha256':sha(f),'actual_L2001_regulator_source_membership':'OPEN','candidate_existing_FPGA_In3_source_island':1,'graphics_native_reservations_reference_foreign_contact_and_native_flashes':'OPEN','native_jobs':0,'board_written':False},indent=2)+'\n')
if __name__=='__main__':main()
